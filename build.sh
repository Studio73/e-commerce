#!/bin/bash
DATE=`date -u +"%Y-%m-%dT%H:%M:%SZ"`
REF=`git rev-parse --short HEAD`
VERSION=$1
TAG=$1
if [ "$VERSION" = "8.0" ] || [ "$VERSION" = "9.0" ] || [ "$VERSION" = "10.0" ]; then
    DEST="py2"
fi
if [ "$VERSION" = "11.0" ] || [ "$VERSION" = "12.0" ]; then
    DEST="py3.6"
fi
if [ "$VERSION" = "13.0" ] || [ "$VERSION" = "14.0" ]; then
    DEST="py3.8"
fi

docker build --build-arg BUILD_DATE=$DATE \
             --build-arg VCS_REF=$REF \
             --build-arg VERSION=$VERSION \
             -f $DEST/Dockerfile . -t dodoo:$TAG
