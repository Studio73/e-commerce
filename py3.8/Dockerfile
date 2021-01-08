FROM python:3.8-slim-buster

RUN useradd -md /opt/odoo -s /bin/bash odoo
WORKDIR /opt/odoo/
RUN mkdir -p /opt/odoo/data && \
	mkdir -p /opt/odoo/src && \
	mkdir -p /opt/odoo/setup && \
	chown -R odoo:odoo /opt/odoo
VOLUME ["/opt/odoo/data", "/opt/odoo/setup", "/opt/odoo/src"]
ENV DATA='/opt/odoo/data' \
	SETUP='/opt/odoo/setup' \
	SRC='/opt/odoo/src'
EXPOSE 8069 8072
ENV TZ=Europe/Madrid
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
RUN apt-get update \
	&& apt-get -y upgrade \
	&& apt-get install -y --no-install-recommends \
	# From Odoo image https://github.com/odoo/docker/blob/master/14.0/Dockerfile
	ca-certificates \
	curl \
	dirmngr \
	fonts-noto-cjk \
	gnupg \
	libssl-dev \
	node-less \
	npm \
	python3-num2words \
	python3-pdfminer \
	python3-pip \
	python3-phonenumbers \
	python3-pyldap \
	python3-qrcode \
	python3-renderpm \
	python3-setuptools \
	python3-slugify \
	python3-vobject \
	python3-watchdog \
	python3-xlrd \
	python3-xlwt \
	xz-utils \
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
	zip \
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
	# psycopg2==2.8.3 error pg_config executable not found
	libpq-dev \
	# wkhtmltopdf
	fontconfig libx11-6 libxcb1 libxext6 libxrender1 xfonts-75dpi xfonts-base \
	&& curl -SLo /tmp/wkhtmltox.deb https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/0.12.5/wkhtmltox_0.12.5-1.stretch_amd64.deb \
	&& dpkg --force-depends -i /tmp/wkhtmltox.deb\
	&& apt-get purge -y --auto-remove \
	&& rm -Rf /var/lib/apt/lists/* /tmp/*

RUN sed -i -e 's/# es_ES.UTF-8 UTF-8/es_ES.UTF-8 UTF-8/' /etc/locale.gen && \
	locale-gen
# Avoid werkzeug encoding ANSI_X3.4-1968 warning
ENV LANG=es_ES.UTF-8 \
	LANGUAGE=es_ES \
	LC_ALL=es_ES.UTF-8

# Install rtlcss (on Debian buster)
RUN npm install -g rtlcss

# install latest postgresql-client
RUN echo 'deb http://apt.postgresql.org/pub/repos/apt/ buster-pgdg main' > /etc/apt/sources.list.d/pgdg.list \
    && GNUPGHOME="$(mktemp -d)" \
    && export GNUPGHOME \
    && repokey='B97B0AFCAA1A47F044F244A07FCC7D46ACCC4CF8' \
    && gpg --batch --keyserver keyserver.ubuntu.com --recv-keys "${repokey}" \
    && gpg --batch --armor --export "${repokey}" > /etc/apt/trusted.gpg.d/pgdg.gpg.asc \
    && gpgconf --kill all \
    && rm -rf "$GNUPGHOME" \
    && apt-get update  \
    && apt-get install --no-install-recommends -y postgresql-client \
    && rm -f /etc/apt/sources.list.d/pgdg.list \
    && rm -rf /var/lib/apt/lists/*

ARG VERSION
ENV ODOO_VERSION=$VERSION
RUN curl -SLo /tmp/requirements.txt https://raw.githubusercontent.com/odoo/odoo/$VERSION/requirements.txt \
	&& pip3 install --no-cache-dir --ignore-installed -r /tmp/requirements.txt \
	&& apt-get -y autoremove \
	&& rm -Rf /var/lib/apt/lists/* /tmp/*

COPY py3.8/requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt \
	&& apt-get -y autoremove \
	&& rm -Rf /var/lib/apt/lists/* /tmp/*

COPY entrypoint.py /
COPY dodoo-tools/ /tmp/dodoo-tools/
RUN cd /tmp/dodoo-tools/ \
	&& pip3 install . \
	&& rm -Rf /tmp/*

# Avoid "ImportError: No module named odoo" and make pip install persistent
ENV PYTHONPATH='$PYTHONPATH:/opt/odoo/src/odoo:/opt/odoo/data/.cache/pypi'
ENV PIP_TARGET=${DATA}/.cache/pypi

WORKDIR /opt/odoo/
ENTRYPOINT ["python3", "/entrypoint.py"]
CMD ["python3", "/opt/odoo/src/odoo/odoo-bin"]

ARG BUILD_DATE
ARG VCS_REF
LABEL org.label-schema.vendor="Studio73" \
	org.label-schema.url="https://www.studio73.es" \
	org.label-schema.vcs-url="https://github.com/Studio73/dodoo" \
	org.label-schema.vcs-ref=$VCS_REF \
	org.label-schema.build-date=$BUILD_DATE
