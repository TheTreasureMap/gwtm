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

from src.gwtmconfig import config

sys.path.insert(0, '/var/www/gwtm/')
from src.models import db, gw_alert

@gcn.handlers.include_notice_types(
    gcn.notice_types.LVC_PRELIMINARY,
    gcn.notice_types.LVC_INITIAL,
    gcn.notice_types.LVC_UPDATE,
    gcn.notice_types.LVC_RETRACTION)

# Define your custom handler here.
def handler(payload, root):

    role = ''

    role = root.attrib['role']

    print("ROLE is ", role)
    params = {elem.attrib['name']:
              elem.attrib['value']
              for elem in root.iterfind('.//Param')}

    for key, value in params.items():
        print(key, '=', value)
    keys = params.keys()

    notices = [150, 151, 152, 153, 164]

    #should I test for the alerttype Preliminary, Initial, Update, Retraction? IDK
    if int(params['Packet_Type']) in notices:
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

        if 'skymap_fits' in params:
            # Read the HEALPix sky map and the FITS header.
            #skymap, header = hp.read_map(params['skymap_fits'],
            #                             h=True, verbose=False)


            #header = dict(header)
            #hkeys = header.keys()

            print("downloading skymap_fits")
            s3 = boto3.client('s3')
            downloadpath = 'fit/' + gwa.graceid + '.fits.gz'
            r = requests.get(params['skymap_fits'])
            with io.BytesIO() as f:
                f.write(r.content)
                f.seek(0)
                s3.upload_fileobj(f, Bucket=config.AWS_BUCKET, Key=downloadpath)

                print("download finished")

                f.seek(0)
                hdu = fits.open(f)

                header = hdu[0].header
                hkeys = header.keys()

                gwa.time_of_signal = header['DATE-OBS'] if 'DATE-OBS' in hkeys else '1991-12-23T19:15:00'
                gwa.distance = header['DISTMEAN'] if 'DISTMEAN' in hkeys else "-999.9"
                gwa.distance_error = header['DISTSTD'] if 'DISTSTD' in hkeys else "-999.9"
                gwa.timesent = header['DATE'] if 'DATE' in hkeys else '1991-12-23T19:15:00'


        db.session.add(gwa)
        print("commiting\n")
        db.session.commit()
        #print("sleeping quit now")
        #time.sleep(20)
    else:
        print("\nNot Ligo, Don't Care\n")

def main():
    print('LISTENING')
    gcn.listen(handler=handler)
main()

#TEST LOCAL
#gcn.listen(host='127.0.0.1', port=8099, handler=handler)
