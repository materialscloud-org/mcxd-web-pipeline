# Materials Cloud REST API

REST API (built with FastAPI) to serve data from the Materials Cloud Mongo databases. The MongoDB subdatabases are populated by the following pipelines, respectively:

- MC3D (https://github.com/materialscloud-org/discover-mc3d-data)
- MC2D (https://github.com/materialscloud-org/discover-mc2d-data)

This API replaces (partially, currently) the old [materialscloud-org/backend-noexplore](https://github.com/materialscloud-org/backend-noexplore).

## Development setup

- `pip install -r requirements.txt`
- set MongoDB URI (if not default): `export MC_MONGODB_URI=mongodb://localhost:27017`
- start the API: `fastapi dev app/main.py`
- open e.g. http://localhost:8000/mc3d/pbe-v1/entries

## Production setup

Inspired by https://fastapi.tiangolo.com/deployment/docker/

Use the `docker-compose.yml`, this will

- start the MongoDB container, with a restart policy;
- start the fastapi in production mode, in a container, also with a restart policy.

Redeploy with

```
docker compose up -d --build mc-rest-api
```

## Build & push main image

Build and push the image to harbor with

```bash
TAG=$(date +%Y.%m.%d)
IMAGE=harbor.materialscloud.cscs.ch/materialscloud/mc-rest-api

docker build -t $IMAGE:latest .
docker push $IMAGE:latest
docker tag $IMAGE:latest $IMAGE:$TAG
docker push $IMAGE:$TAG
```

## Build & push s3 population image

```bash
TAG=$(date +%Y.%m.%d)
IMAGE=harbor.materialscloud.cscs.ch/materialscloud/mc-mongo-populate

docker build -t $IMAGE:latest ./populate-mongo-from-s3/.
docker push $IMAGE:latest
docker tag $IMAGE:latest $IMAGE:$TAG
docker push $IMAGE:$TAG
```

## Apache proxy (old VM deployment)

To serve this via an Apache proxy, just add the following to the corresponding `VirtualHost`:

```
    ProxyPreserveHost On
    ProxyPass /mc-rest-api http://localhost:8001
    ProxyPassReverse /mc-rest-api http://localhost:8001

    <Location /mc-rest-api>
        Require all granted
    </Location>
```

To enable caching at the Apache-level, make sure the corresponding modules are enabled:

```
a2enmod cache
a2enmod cache_disk
```

and add the following to the `VirtualHost`:

```
    CacheEnable disk /
    CacheHeader on
    CacheIgnoreNoLastMod On
    CacheIgnoreHeaders Set-Cookie
    CacheMaxExpire 3600
    CacheDefaultExpire 600
```
