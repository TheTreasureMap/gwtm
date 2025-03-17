# GW Treasure Map 
Website environment

## Requirements

### Python:
 * Python Version 3.11

### Python Libraries
(that you will probably have to `pip3 install`)

```
python -m pip install -r requirements.txt
```

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

### Running the application and dependencies locally

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
