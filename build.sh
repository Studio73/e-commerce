#!/bin/bash
DATE=`date -u +"%Y-%m-%dT%H:%M:%SZ"`
REF=`git rev-parse --short HEAD`
VERSION=$1
TAG=$1
if [ "$1" == "runbot" ]; then
    VERSION="13.0"
fi

docker build --build-arg BUILD_DATE=$DATE \
             --build-arg VCS_REF=$REF \
             --build-arg VERSION=$VERSION \
             -f $TAG/Dockerfile . -t dodoo:$TAG
