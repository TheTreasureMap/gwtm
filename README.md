# GW Treasure Map 
Website environment

### Step-by-step installation

To install a local copy of Treasure Map, please follow these steps:
1. Clone repository
2. Create a `conda` environment with `conda create -n gwtm-dev python=3.11`
3. Activate the `conda` environment with `conda activate gwtm-dev`
4. Install the requirements file with `pip install -r requirements.txt`
5. Run `source envars.sh` to activate environment variables, ask Sam for this file if needed.
6. Start the server by running `python gwtm.wsgi`  (starts Flash application)
7. Should be running on `127.0.0.1:5000/`, go to the webpage to check it out!
8. You should be able to sign in with your pre-registered account info.



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
    REDIS_URL
    ...

See [gwtmconfig.py](src/gwtmconfig.py) for other configration options and defaults for other values.

Env vars can be set by using export:

```bash
export MAIL_PASSWORD=ASecretPassword
export RECAPTCHA_PUBLIC_KEY=ASecretPassword2
```
Or by using a utility like [direnv](https://direnv.net).
