# GW Treasure Map

## Requirements

### Python:
 * Python Version > 3.6.8
### Python Libraries
(that you will probably have to `pip3 install`)
 * flask-sqlalchemy
 * flask_login
 * flask_wtf
 * flask_mail
 * pyjwt
 * psycopg2
 * geoalchemy2
 * shapely
 * pygcn
 * plotly
 * healpy
 
   this should install astropy, scipy, matplotlib... etc
   if not astropy is required
   


### Database Configuration
You will need to export the pathway to the provided configuration file named `config`
```txt
user   [psqluser]
pwd    [password]
db     [database]
host   [localhost]
port   [5432]
MAIL_USERNAME [email]
MAIL_DEFAULT_SENDER [email]
ADMINS [email]
MAIL_PASSWORD [email_pwd]
MAIL_SERVER [smpt_server]
MAIL_PORT [port]
MAIL_USE_TLS True
RECAPTCHA_PUBLIC_KEY [recaptcha_public_key]
RECAPTCHA_PRIVATE_KEY [recaptcha_private_key]
```
```bash
export CONFIGPATH='/path/to/config'
```
