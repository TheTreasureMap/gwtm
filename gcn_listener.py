
import gcn
import healpy as hp
import sys
import datetime
import time
from models import db, gw_alert


@gcn.handlers.include_notice_types(
    gcn.notice_types.LVC_PRELIMINARY,
    gcn.notice_types.LVC_INITIAL,
    gcn.notice_types.LVC_UPDATE,
    gcn.notice_types.LVC_RETRACTION)

# Define your custom handler here.
def handler(payload, root):

    params = {elem.attrib['name']:
              elem.attrib['value']
              for elem in root.iterfind('.//Param')}

    for key, value in params.items():
        print(key, '=', value)

    keys = params.keys()

    #should I test for the alerttype Preliminary, Initial, Update, Retraction? IDK

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
            role = "Find Later",
            description =  "Not sure what to put here",
        )

    if 'skymap_fits' in params:
        print("it here")
        # Read the HEALPix sky map and the FITS header.
        skymap, header = hp.read_map(params['skymap_fits'],
                                     h=True, verbose=False)
        header = dict(header)
        hkeys = header.keys()

        gwa.time_of_signal = header['DATE-OBS'] if 'DATE-OBS' in hkeys else '1991-12-23T19:15:00'
        gwa.distance = header['DISTMEAN'] if 'DISTMEAN' in hkeys else "-999.9"
        gwa.distance_error = header['DISTSTD'] if 'DISTSTD' in hkeys else "-999.9"
        gwa.timesent = header['DATE'] if 'DATE' in hkeys else '1991-12-23T19:15:00'

    db.session.add(gwa)
    #print("commiting\n")
    db.session.commit()
    #print("This worked")
    #print("sleeping 20 for test. quit now.\n\n")
    #time.sleep(20.0)

gcn.listen(handler=handler)
#TEST LOCAL
#gcn.listen(host='127.0.0.1', port=8099, handler=handler)
