# MCXD REST API

REST API (built with FastAPI) to serve data from the Materials Cloud MC3D and MC2D Mongo databases.

Note, make sure the MongoDB is running (see `../mongodb`).

## Development setup

- `pip install -r requirements.txt`
- set MongoDB URI (if not default): `export MC_MONGODB_URI=mongodb://localhost:27017`
- start the API: `fastapi dev app/main.py`
- open e.g. http://localhost:8000/docs

## Production setup

Inspired by https://fastapi.tiangolo.com/deployment/docker/

Use the `docker-compose.yml`, this will start the fastapi in production mode, in a container, also with a restart policy.

Redeploy with

```
docker compose up -d --build
```

## Build & push the REST API image

Build and push the image to harbor with

```bash
TAG=$(date +%Y.%m.%d)
IMAGE=harbor.materialscloud.cscs.ch/materialscloud/mcxd-rest-api

docker build -t $IMAGE:latest .
docker push $IMAGE:latest
docker tag $IMAGE:latest $IMAGE:$TAG
docker push $IMAGE:$TAG
```
