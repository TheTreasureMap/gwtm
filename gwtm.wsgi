#!/home/samuel/anaconda2/envs/py3/bin/python
import sys
import logging
import hashlib
import os

logging.basicConfig(stream=sys.stderr)
sys.path.insert(0,"/var/www/gwtm")

from src import app as application
BASE = os.getcwd()
application.secret_key = KEY = hashlib.sha256(BASE.encode('utf-8')).hexdigest()


if __name__ == "__main__":
    application.run()


