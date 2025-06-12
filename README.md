# GW Treasure Map 
Website environment

## Quick Start

**For the modern FastAPI backend (recommended):**
The FastAPI application requires database and cache services. Use Skaffold for the complete development environment:
```bash
cd gwtm-helm
skaffold dev    # Starts full stack including FastAPI, database, and cache
```
FastAPI will be available at http://localhost:8000 with API docs at http://localhost:8000/docs

See the [FastAPI README](server/README.md) for detailed setup instructions and testing.

**For the legacy Flask application:**
```bash
python gwtm.wsgi            # Development server on :5000
```

### Step-by-step installation

### Python:
 * Python Version 3.11

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

### Running the application and dependencies via Docker

#### Using Skaffold with Kubernetes for Development

For a more complete development environment with Kubernetes, you can use Skaffold with the Helm chart:

1. Prerequisites:
   - Install [Skaffold](https://skaffold.dev/docs/install/)
   - Install [kubectl](https://kubernetes.io/docs/tasks/tools/install-kubectl/)
   - Have a Kubernetes cluster running (Minikube, Docker Desktop Kubernetes, etc.)

2. Navigate to the Helm chart directory:
```bash
cd gwtm-helm
```

3. Start the development environment:
```bash
skaffold dev
```
   This will:
   - Build the Docker image
   - Deploy the application to your Kubernetes cluster
   - Set up port-forwarding (frontend: localhost:8081, backend: localhost:8080)
   - Display logs in real-time
   - Automatically redeploy when files change

4. To restore sample data to the database:
```bash
cd gwtm-helm
./restore-db /path/to/your/dump.sql
```
   This script copies the SQL dump to the database pod and executes it directly.

5. Access the application:
   - Frontend dashboard: http://localhost:8081
   - Flask application: http://localhost:8080
   - Specific endpoints like http://localhost:8080/reported_instruments

6. When finished, stop Skaffold with Ctrl+C or run:
```bash
skaffold delete
```

This Kubernetes setup includes:
- PostgreSQL database with PostGIS
- Redis cache
- Flask backend API
- Frontend dashboard

### Running tests

Tests can be run from the root directory using pytest. First create a virtual environment and install the requirements:

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install pytest
```

Then run the tests:
```
pytest
```

### Running Redis

Redis is a fast in memory key/value store. It is used in this project for both caching
and as a message broker for the Celery task worker (next section).

Running redis with Docker is easy:

```bash
docker run --name redis -p6379:6379 -d redis
```

This will start a server listening on localhost:6379, which is the default value Treasuremap will
look for, so no other configuration should be necessary.

### Running the Celery worker

In order to run certain code off the main HTTP thread we use celery to be able to run tasks in the background.
This requires Redis to be running (previous section).

Once redis is up, we can start a worker:

```bash
celery -A src.tasks.celery worker
```

You can test this is working but using the probability calculator for an event.


### Running the application in production
The application can be built and deployed as a docker image.

To build the image only, use the build command:

`docker build -t gwtm_web .`

To deploy an image, it first must be pushed up to the Elastic Cloud Registry endpoint. First, tag
the image with the repository name:

`docker tag gwtm_web:latest 929887798640.dkr.ecr.us-east-2.amazonaws.com/gwtreasuremap:latest`

Then make sure you are logged into the registry:

`./ecrlogin.sh`

Finally, push the image:

`docker push 929887798640.dkr.ecr.us-east-2.amazonaws.com/gwtreasuremap:latest`

Now, log into the Amazon dashboard and navigate to the ECS (Elastic Container Service).
Find the Tasks Definitions section and create a new revision of gwtm_web. Leave
all the values as they are, unless there is something specific about the deployment that you want to change.

Once the new task is created, go the gwtmweb [service definition](https://us-east-2.console.aws.amazon.com/ecs/v2/clusters/default/services/gwtmweb/edit?region=us-east-2)
and edit it, changing the revision of the task to the latest one (the one we just created).
After clicking update, the service should pull the new image and deploy the new version of the code.
