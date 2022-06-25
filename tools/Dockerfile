# (c) Studio73 - Pablo Fuentes <pablo@studio73.es>
FROM python:3.8-slim-buster

RUN apt-get update && apt-get install -y --no-install-recommends git
RUN pip install pre-commit click PyYaml requests
RUN mkdir /src /cache
VOLUME ["/src", "/cache"]
ENV PRE_COMMIT_HOME=/cache
WORKDIR /src
COPY --chmod="+x" tools/tools.py /usr/local/bin/tools
RUN git config --global user.email "pablo@studio73.es" && \
    git config --global user.name "fuentes73"
CMD ["/bin/bash"]

