FROM python:3.11-slim
ARG MDBTOOLS_VER=100.12.2

RUN apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates wget \
      libgssapi-krb5-2 libkrb5-3 libk5crypto3 libcom-err2 libkrb5support0 libkeyutils1 \
    && wget -O /tmp/mongodb-database-tools.deb \
         "https://fastdl.mongodb.org/tools/db/mongodb-database-tools-debian12-x86_64-${MDBTOOLS_VER}.deb" \
    && apt-get install -y /tmp/mongodb-database-tools.deb \
    && rm -f /tmp/mongodb-database-tools.deb \
    && rm -rf /var/lib/apt/lists/*


# optional: fast decompressor for pre-unzip step
RUN apt-get update && apt-get install -y --no-install-recommends pigz && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir boto3 pymongo

COPY main.py .
CMD ["python", "-u", "main.py"]
