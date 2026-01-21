# 1. Start an empty MongoDB

Create and run a MongoDB and a docker-network to access the it from other docker containers with

```
docker compose up -d
```

Note: Mongodb Compass is a good way to see/debug the database data.

# 2. Populate the MongoDB from S3

To populate the MongoDB with the latest data from S3:

```bash
cd populate-mongo-from-s3
```

Set in docker-compose

```bash
S3_PREFIX=mc3d-mongo-dumps/collections-v2/
... or ...
S3_PREFIX=mc2d-mongo-dumps/collections-v2/
```

And run

```bash
docker compose up
```

## Build & push s3 population image

```bash
TAG=$(date +%Y.%m.%d)
IMAGE=harbor.materialscloud.cscs.ch/materialscloud/mcxd-mongo-populate

docker build -t $IMAGE:latest ./populate-mongo-from-s3/.
docker push $IMAGE:latest
docker tag $IMAGE:latest $IMAGE:$TAG
docker push $IMAGE:$TAG
```
