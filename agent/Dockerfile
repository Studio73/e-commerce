from docker:latest

VOLUME /data
RUN apk add --no-cache python3 py3-pip tzdata && mkdir /agent
RUN cp /usr/share/zoneinfo/Europe/Madrid /etc/localtime && echo "Europe/Madrid" >  /etc/timezone
COPY ./requirements.txt /agent
RUN pip3 install -r /agent/requirements.txt
COPY ./src /agent/src
CMD ["python3", "/agent/src"]
