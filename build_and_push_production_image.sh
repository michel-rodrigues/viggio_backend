#!/bin/sh
CLOUDSDK_PYTHON=$(which python) docker build -t us.gcr.io/viggio/viggio-backend:latest -f Dockerfile.production .
CLOUDSDK_PYTHON=$(which python) docker push us.gcr.io/viggio/viggio-backend:latest