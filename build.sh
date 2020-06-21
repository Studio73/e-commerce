#!/bin/bash
DATE=`date -u +"%Y-%m-%dT%H:%M:%SZ"`
REF=`git rev-parse --short HEAD`
VERSION=$1
TAG=$1
DEST="py3"
if [ "$1" == "runbot" ]; then
    VERSION="13.0"
    DEST="runbot"
fi
if [ "$VERSION" = "8.0" ] || [ "$VERSION" = "10.0" ]; then
    DEST="py2"
fi

docker build --build-arg BUILD_DATE=$DATE \
             --build-arg VCS_REF=$REF \
             --build-arg VERSION=$VERSION \
             -f $DEST/Dockerfile . -t dodoo:$TAG
