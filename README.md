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
 * ephem
 * psycopg2
 * geoalchemy2
 * shapely
 * pygcn
 * plotly
 * healpy

   this should install astropy, scipy, matplotlib... etc
   if not astropy is required



### Configuration
Configuration is handled via environmental variables. At a minimum, the following env vars must be
present:

    DB_PWD
    MAIL_PASSWORD
    RECAPTCHA_PUBLIC_KEY
    RECAPTCHA_PRIVATE_KEY
    ZENODO_ACCESS_KEY
    AWS_ACCESS_KEY_ID
    AWS_SECRET_ACCESS_KEY

See [gwtmconfig.py](src/gwtmconfig.py) for other configration options and defaults for other values.

Env vars can be set by using export:

```bash
export MAIL_PASSWORD=ASecretPassword
export RECAPTCHA_PUBLIC_KEY=ASecretPassword2
```
Or by using a utility like [direnv](https://direnv.net).


### Docker
The application can be built and deployed as a docker image.

To build and run the docker image locally, use docker compose:

`docker compose up`

To build the image only, use the build command:

`docker build -t gwtm_web .`

To deploy an image, it first must be pushed up to the Elastic Cloud Registry endpoint. First, tag
the image with the repository name:

`docker tag gwtm_web:latest 929887798640.dkr.ecr.us-east-2.amazonaws.com/gwtreasuremap:latest`

Then make sure you are logged into the registry:

`./ecrlogin.sh`

Finally, push the image:

`docker push 929887798640.dkr.ecr.us-east-2.amazonaws.com/gwtreasuremap:latest`

Now, log into the Amazon dashboard and navigate to the ECS (Elastic Container Service). Select
the default cluster. Find the Tasks Definitions section and create a new revision of gwtm_web. Leave
all the values as they are, unless there is something specific about the deployment that you want to change.

Once the new task is created, go the gwtmweb (service definition)[https://us-east-2.console.aws.amazon.com/ecs/v2/clusters/default/services/gwtmweb/edit?region=us-east-2]
and edit it, changing the revision of the task to the latest one (the one we just created).
After clicking update, the service should pull the new image and deploy the new version of the code.
