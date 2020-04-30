FROM dodoo:13.0

RUN apt-get update \
	&& apt-get -y upgrade \
	&& apt-get install -y --no-install-recommends \
	apt-transport-https \
    curl \
    gnupg-agent \
    software-properties-common \
    && apt-get purge -y --auto-remove \
	&& rm -Rf /var/lib/apt/lists/* /tmp/*
RUN curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -
RUN add-apt-repository \
   "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
   $(lsb_release -cs) \
   stable"
RUN apt-get update \
	&& apt-get -y upgrade \
	&& apt-get install -y --no-install-recommends docker-ce \
    && apt-get purge -y --auto-remove \
	&& rm -Rf /var/lib/apt/lists/* /tmp/*
COPY runbot/entrypoint.sh /
ENTRYPOINT ["bash", "/entrypoint.sh"]
