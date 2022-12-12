# (c) Studio73 - Pablo Fuentes <pablo@studio73.es>
FROM python:3.10-slim-buster

RUN apt-get update && apt-get install -y --no-install-recommends git openssh-client
RUN mkdir /src /cache
VOLUME ["/src", "/cache"]
ENV PRE_COMMIT_HOME=/cache
COPY requirements.txt /requirements.txt
RUN pip install -r /requirements.txt
WORKDIR /src
COPY --chmod="+x" tools.py /usr/local/bin/tools
RUN git config --global user.email "leonidas@studio73.es" && \
    git config --global user.name "leonidas73"
CMD ["/bin/bash"]
