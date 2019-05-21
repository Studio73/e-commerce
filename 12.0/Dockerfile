FROM ubuntu:18.04

RUN useradd -md /opt/odoo -s /bin/bash odoo
WORKDIR /opt/odoo/
EXPOSE 8069 8072
ENV TZ=Europe/Madrid
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
RUN apt-get update \
	&& apt-get -y upgrade \
	&& apt-get install -y --no-install-recommends \
	# From Odoo image https://github.com/odoo/docker/blob/master/12.0/Dockerfile
	ca-certificates \
	curl \
	dirmngr \
	fonts-noto-cjk \
	gnupg \
	libssl1.0-dev \
	node-less \
	python3-pip \
	python3-pyldap \
	python3-qrcode \
	python3-renderpm \
	python3-setuptools \
	python3-vobject \
	python3-watchdog \
	xz-utils
RUN apt-get install -y --no-install-recommends \
	# Dodoo
	python3-dev \
	apt-utils \
	build-essential \
	cron \
	git \
	gosu \
	vim \
	locales \
	openssh-client \
	iptables \
	# pycups
	libcups2-dev \
	# lxml
	libxml2-dev \
	libxslt1-dev \
	zlib1g-dev \
	# pyldap https://github.com/odoo/odoo/issues/8849#issuecomment-322115976
	libsasl2-dev \
	libldap2-dev \
	# xmlsec l10n-spain
	libxmlsec1-dev \
	libxmlsec1-openssl \
	&& apt-get purge -y --auto-remove \
	&& rm -Rf /var/lib/apt/lists/* /tmp/*

# Avoid werkzeug encoding ANSI_X3.4-1968 warning
ENV LANG=es_ES.UTF-8 \
	LANGUAGE=es_ES \
	LC_ALL=es_ES.UTF-8 \
	DATA='/opt/odoo/data' \
	SETUP='/opt/odoo/setup' \
	SRC='/opt/odoo/src'
RUN locale-gen es_ES.UTF-8
VOLUME ["/opt/odoo/data", "/opt/odoo/setup", "/opt/odoo/src"]

RUN echo "deb http://apt.postgresql.org/pub/repos/apt/ bionic-pgdg main" >> /etc/apt/sources.list.d/postgres.list \
	&& curl -SL https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add - \
	&& apt-get update \
	&& apt-get install -y --no-install-recommends postgresql-client \
	&& rm -Rf /var/lib/apt/lists/* /tmp/*

RUN curl -SLo /tmp/wkhtmltox.deb https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/0.12.5/wkhtmltox_0.12.5-1.bionic_amd64.deb \
	&& apt-get update \
	&& apt-get install -y --no-install-recommends fontconfig libx11-6 libxcb1 libxext6 libxrender1 xfonts-75dpi xfonts-base \
	&& dpkg --force-depends -i /tmp/wkhtmltox.deb\
	&& apt-get -y install -f \
	&& rm -Rf /var/lib/apt/lists/* /tmp/*

ARG VERSION
ENV VERSION=$VERSION
RUN curl -SLo /tmp/requirements.txt https://raw.githubusercontent.com/odoo/odoo/$VERSION/requirements.txt \
	&& pip3 install --no-cache-dir --ignore-installed -r /tmp/requirements.txt \
	&& apt-get -y autoremove \
	&& rm -Rf /var/lib/apt/lists/* /tmp/*

COPY $VERSION/requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt \
	&& apt-get -y autoremove \
	&& rm -Rf /var/lib/apt/lists/* /tmp/*

COPY entrypoint.py /
COPY dodoo-tools/ /tmp/dodoo-tools/
RUN cd /tmp/dodoo-tools/ \
	&& pip3 install . \
	&& rm -Rf /tmp/*

# Avoid "ImportError: No module named odoo" and make pip install persistent
ENV PYTHONPATH='$PYTHONPATH:/opt/odoo/src/odoo:/opt/odoo/data/.pypi'
ENV PIP_TARGET=${DATA}/.pypi

WORKDIR /opt/odoo/
ENTRYPOINT ["python3", "/entrypoint.py"]
CMD ["python3", "/opt/odoo/src/odoo/odoo/odoo-bin"]

ARG BUILD_DATE
ARG VCS_REF
LABEL org.label-schema.vendor="Studio73" \
	org.label-schema.url="https://www.studio73.es" \
	org.label-schema.vcs-url="https://github.com/Studio73/dodoo" \
	org.label-schema.vcs-ref=$VCS_REF \
	org.label-schema.build-date=$BUILD_DATE