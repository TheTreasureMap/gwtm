# GW Treasure Map

## Requirements

### Python:
 * Python Version > 3.6.8
### Python Libraries
(that you will probably have to `pip3 install`)
 * flask-sqlalchemy
 * flask_login
 * flask_wtf
 * pyscopg2
 * geoalchemy2
 * shapely
 * pygcn
 * healpy
 
   this should install astropy, scipy, matplotlib... etc
   if not astropy is required


### Database Configuration
You will need to export the pathway to the provided configuration file named `config`
```txt
user   psqluser
pwd    password
db     database
host   localhost
port   5432
```
```bash
export CONFIGPATH='/path/to/config'
```
