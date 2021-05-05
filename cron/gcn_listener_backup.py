import gcn
import healpy as hp
import sys
import datetime
import time
import os
import sys
import requests
from astropy.io import fits
import boto3
import io
import ligo.skymap
from ligo.skymap.postprocess import contour
from ligo.skymap.healpix_tree import interpolate_nested
import numpy as np
import json
from astropy.coordinates import SkyCoord
from mocpy import MOC

#dirty relative import
sys.path.append(os.path.dirname(os.path.realpath(__file__)).split('/cron')[0])

from src.models import db, gw_alert
from src.gwtmconfig import config
from src import function

@gcn.handlers.include_notice_types(
    gcn.notice_types.LVC_PRELIMINARY,
    gcn.notice_types.LVC_INITIAL,
    gcn.notice_types.LVC_UPDATE,
    gcn.notice_types.LVC_RETRACTION)

# Define your custom handler here.
def handler(payload, root):

    run_test = False

    if run_test:
        s3path = 'test'
    else:
        s3path = 'fit'
    
    role = root.attrib['role']

    print("ROLE is ", role)
    params = {elem.attrib['name']:
              elem.attrib['value']
              for elem in root.iterfind('.//Param')}

    for key, value in params.items():
        print(key, '=', value)
    keys = params.keys()

    notices = [150, 151, 152, 153, 164]

    if int(params['Packet_Type']) in notices:

        #lag for 5 minutes
        time.sleep(60*5)
        #query for the same graceid and alerttype
        #if it exists: return 0
        #   if it doesn't, download procedure alpha go

        gwa = gw_alert(
                graceid = params['GraceID'] if 'GraceID' in keys else 'ERROR',
                packet_type = params['Packet_Type'] if 'Packet_Type' in keys else 0,
                alert_type = params['AlertType'] if 'AlertType' in keys else 'ERROR',
                detectors = params['Instruments'] if 'Instruments' in keys else '',
                far = params['FAR'] if 'FAR' in keys else 0.0,
                skymap_fits_url = params['skymap_fits'] if 'skymap_fits' in keys else '',
                prob_bns = params['BNS'] if 'BNS' in keys else 0.0,
                prob_nsbh =  params['NSBH'] if 'NSBH' in keys else 0.0,
                prob_gap = params['MassGap'] if 'MassGap' in keys else 0.0,
                prob_bbh = params['BBH'] if 'BBH' in keys else 0.0,
                prob_terrestrial = params['Terrestrial'] if 'Terrestrial' in keys else 0.0,
                prob_hasns = params['HasNS'] if 'HasNS' in keys else 0.0,
                prob_hasremenant = params['HasRemnant'] if 'HasRemnant' in keys else 0.0,
                datecreated = datetime.datetime.now(),
                role = role,
                description =  "Not sure what to put here",
            )

        path_info = gwa.graceid + '-' + gwa.alert_type
        filter = [
                gw_alert.graceid == gwa.graceid,
                gw_alert.alert_type == gwa.alert_type
                ]
        alertinfo = db.session.query(gw_alert).filter(*filter).all()

        if len(alertinfo) > 0:
            path_info = path_info + str(len(alertinfo))

        if 'skymap_fits' in params:

            print("downloading skymap_fits")
            s3 = boto3.client('s3')
            downloadpath = '{}/{}.fits.gz'.format(s3path, path_info)
            r = requests.get(params['skymap_fits'])
            with io.BytesIO() as f:
                f.write(r.content)

                f.seek(0)
                s3.upload_fileobj(f, Bucket=config.AWS_BUCKET, Key=downloadpath)

                print("download finished")
                
            skymap, header = hp.read_map(params['skymap_fits'], h=True, verbose=False)

            header = dict(header)
            hkeys = header.keys()

            gwa.time_of_signal = header['DATE-OBS'] if 'DATE-OBS' in hkeys else '1991-12-23T19:15:00'
            gwa.distance = header['DISTMEAN'] if 'DISTMEAN' in hkeys else "-999.9"
            gwa.distance_error = header['DISTSTD'] if 'DISTSTD' in hkeys else "-999.9"
            gwa.timesent = header['DATE'] if 'DATE' in hkeys else '1991-12-23T19:15:00'

            print('Creating 90/50 contours')
            
            prob, _ = ligo.skymap.io.fits.read_sky_map(gwa.skymap_fits_url, nest=None)
            prob = interpolate_nested(prob, nest=True)
            i = np.flipud(np.argsort(prob))
            cumsum = np.cumsum(prob[i])
            cls = np.empty_like(prob)
            cls[i] = cumsum * 100
            paths = list(ligo.skymap.postprocess.contour(cls, [50, 90], nest=True, degrees=True, simplify=True))
        
            contour_download_path = '{}/{}-contours-smooth.json'.format(s3path, path_info)
            with io.BytesIO() as cc:
                tt = json.dumps({
                    'type': 'FeatureCollection',
                    'features': [
                        {
                            'type': 'Feature',
                            'properties': {
                                'credible_level': contour
                            },
                            'geometry': {
                                'type': 'MultiLineString',
                                'coordinates': path
                            }
                        }
                        for contour, path in zip([50,90], paths)
                    ]
                })
                cc.write(tt.encode())
                cc.seek(0)
                s3.upload_fileobj(cc, Bucket=config.AWS_BUCKET, Key=contour_download_path)

            ####################

            print('Creating Fermi and LAT MOC files')
            ####################
            tos = datetime.datetime.strptime(gwa.time_of_signal, "%Y-%m-%dT%H:%M:%S.%f")
            
            fermi_moc_upload_path = '{}/{}-Fermi.json'.format(s3path, gwa.graceid)
            try:
                s3.head_object(Bucket=config.AWS_BUCKET, Key=fermi_moc_upload_path)
                print('Fermi file already exists')
            except:
                #calculate
                try:
                    earth_ra,earth_dec,earth_rad=function.getearthsatpos(tos)
                    contour = function.makeEarthContour(earth_ra,earth_dec,earth_rad)
                    skycoord = SkyCoord(contour, unit="deg", frame="icrs")
                    inside = SkyCoord(ra=earth_ra+180, dec=earth_dec, unit="deg", frame="icrs")
                    moc = MOC.from_polygon_skycoord(skycoord, max_depth=9)
                    moc = moc.complement()
                    mocfootprint = moc.serialize(format='json')
            
                    #store on S3
                    with io.BytesIO() as mm:
                        moc_string = json.dumps(mocfootprint)
                        mm.write(moc_string.encode())
                        mm.seek(0)
                        s3.upload_fileobj(mm, Bucket=config.AWS_BUCKET, Key=fermi_moc_upload_path)
                    print('Successfully Created Fermi MOC File for {}'.format(gwa.graceid))
                except:
                    print('ERROR in Fermi MOC creation for {}'.format(gwa.graceid))
        
            ####LAT Creation#####
            lat_moc_upload_path = '{}/{}-LAT.json'.format(s3path, gwa.graceid)
            try:
                s3.head_object(Bucket=config.AWS_BUCKET, Key=lat_moc_upload_path)
                print('LAT file already exists')
            except:
                try:
                    ra, dec = function.getFermiPointing(tos)
                    pointing_footprint=function.makeLATFoV(ra,dec)
                    skycoord = SkyCoord(pointing_footprint, unit="deg", frame="icrs")
                    moc = MOC.from_polygon_skycoord(skycoord, max_depth=9)
                    mocfootprint = moc.serialize(format='json')
            
                    with io.BytesIO() as ll:
                        moc_string = json.dumps(mocfootprint)
                        ll.write(moc_string.encode())
                        ll.seek(0)
                        s3.upload_fileobj(ll, Bucket=config.AWS_BUCKET, Key=lat_moc_upload_path)
                    print('Successfully Created LAT MOC File for {}'.format(gwa.graceid))
                except:
                    print('ERROR in LAT MOC creation for {}'.format(gwa.graceid))

        ###################

        if not run_test:
            db.session.add(gwa)
            print("commiting\n")
            db.session.commit()
        else:
            print('Sleeping, you should kill')
            time.sleep(20)
    else:
        print("\nNot Ligo, Don't Care\n")

def main():
    print('LISTENING')
    gcn.listen(host='45.58.43.186', port=8099, handler=handler)
main()