import os, sys, requests, json


def main():
    BASE = 'http://127.0.0.1:5000/api/v0/'
    #BASE = 'http://treasuremap.space/api/v0/'
    TARGET = 'pointings'
    METHOD = 'POST'

    #To post pointings you need to first declare the LIGO Gravitational graceid
    graceid = "graceid1"
    #Then your api_token
    api_token = "idcbBa_DwtA8T1ql5YLQWlgutq3sqBPpXodciw"
    #To publish your pointings, it needs to be either just one pointing dictionary, 
    #   or a list of pointing dictionaries
    #
    #Required pointing fields:
    #   position:
    #       Must be decimal format ra/RA, dec/DEC, or geometry type "POINT(RA, DEC)"
    #   instrumentid:
    #       Can be integer id or string name of instrument
    #       -> instruments can be registered/viewd on the website
    #       -> or email swyatt@email.arizona.edu to have your instrument registered
    #           --> field of view in degrees, name, and your gwtm userid
    #   pos_angle:
    #       must be decimal
    #   time:
    #       time at which observation was taken
    #       must be %Y-%m-%dT%H:%M:%S format. e.g. 2019-05-01T12:00:00

    #Not required (but suggested if applicable)
    #   status:
    #       can be either planned or observed. default to planned observation status
    #   galaxy_catalog:
    #       ID of galaxy catalog: -> glade = 1
    #   galaxy_catalogid:
    #       ID of galaxy in the specifed catalog obove
    #   depth:
    #       decimal magnitude depth of instrument
    #   band:
    #       if instrument is photometric, this is required

    #EXAMPLE:

    pointings = [{
            "status":"observed",
            "position":"POINT(42.0 42.0)",
            "instrumentid":"1",
            "pos_angle":0.0,
            "time":"2019-05-01T12:00:00",
            "band":"V",
            "depth":22.5
            }]

    json_data = {
            "graceid":graceid,
            "api_token":api_token,
            "pointings":pointings
            }

    r = requests.post(url = BASE+TARGET, json = json_data)

    print(r.text)

main()
