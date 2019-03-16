FROM ubuntu:16.04

RUN useradd -md /opt/odoo -s /bin/bash odoo
WORKDIR /opt/odoo/
EXPOSE 8069 8072

RUN apt-get update \
	&& apt-get -y upgrade \
    && apt-get install -y --no-install-recommends \
    		apt-utils \
     		build-essential \
            ca-certificates \
			cron \
            curl \
            git \
            gosu \
			libcups2-dev \
			libffi-dev \
			libfontconfig1 \
			libldap2-dev \
			libjpeg-dev \
			libsasl2-dev \
			libssl-dev \
     		libxml2-dev \
			libxslt1-dev \
			libxrender1 \
			libxext6 \
			locales \
            node-less \
            openssh-client \
			python-dev  \
			python-wheel \
            python-setuptools \
            python-gevent \
            python-renderpm \
            python-watchdog \
            ruby \
			ruby-dev \
			vim \
			zlib1g-dev \
    && gem install sass -v 3.4.25 \
    && gem install compass bootstrap-sass \
	&& apt-get purge -y --auto-remove \
	&& rm -Rf /var/lib/apt/lists/* /tmp/*
	# FIX Could not execute command 'sass'
	# https://www.odoo.com/es_ES/forum/ayuda-1/question/ubuntu-16-04-how-to-install-sass-for-odoo-123090

RUN locale-gen es_ES.UTF-8
# Avoid werkzeug encoding ANSI_X3.4-1968 warning
ENV LANG=es_ES.UTF-8 \
    LANGUAGE=es_ES \
    LC_ALL=es_ES.UTF-8 \
    DATA='/opt/odoo/data' \
    SETUP='/opt/odoo/setup' \
    SRC='/opt/odoo/src'
VOLUME ["/opt/odoo/data", "/opt/odoo/setup", "/opt/odoo/src"]

RUN echo "deb http://apt.postgresql.org/pub/repos/apt/ xenial-pgdg main" >> /etc/apt/sources.list.d/postgres.list \
 	&& curl -SL https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add - \
 	&& apt-get update \
    && apt-get install -y --no-install-recommends postgresql-client \
	&& rm -Rf /var/lib/apt/lists/* /tmp/*

RUN curl -SLo /tmp/wkhtmltox.tar.xz https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/0.12.4/wkhtmltox-0.12.4_linux-generic-amd64.tar.xz \
	&& tar -xf /tmp/wkhtmltox.tar.xz -C /tmp \
	&& mv /tmp/wkhtmltox/bin/* /usr/local/bin \
	&& rm -Rf /tmp/*

# Force install latest pip from https://pypi.python.org/pypi/pip/X.X.X
RUN curl -SLo /tmp/pip.tar.gz https://files.pythonhosted.org/packages/45/ae/8a0ad77defb7cc903f09e551d88b443304a9bd6e6f124e75c0fbbf6de8f7/pip-18.1.tar.gz \
	&& tar -xf /tmp/pip.tar.gz -C /tmp \
	&& cd /tmp/pip-18.1/ \
	&& python setup.py install \
	&& rm -Rf /tmp/*

RUN pip install --no-cache-dir --upgrade https://github.com/aeroo/aeroolib/archive/py2.x.zip

ARG VERSION
RUN curl -SLo /tmp/requirements.txt https://raw.githubusercontent.com/odoo/odoo/$VERSION/requirements.txt \
	&& pip install --no-cache-dir --ignore-installed -r /tmp/requirements.txt \
	&& apt-get -y autoremove \
	&& rm -Rf /var/lib/apt/lists/* /tmp/*

COPY $VERSION/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt \
	&& apt-get -y autoremove \
	&& rm -Rf /var/lib/apt/lists/* /tmp/*

COPY entrypoint.py /
# Odoo manager
COPY oman/ /tmp/oman/
WORKDIR /tmp/oman/
RUN python setup.py install \
	&& rm -Rf /tmp/*
WORKDIR /opt/odoo/
ENTRYPOINT ["python", "/entrypoint.py"]
CMD ["python", "/opt/odoo/src/odoo/odoo-bin", "-c", "/tmp/odoo.conf"]

ARG BUILD_DATE
ARG VCS_REF
LABEL org.label-schema.vendor="Studio73" \
      org.label-schema.url="https://www.studio73.es" \
      org.label-schema.vcs-url="https://github.com/Studio73/dodoo" \
	  org.label-schema.vcs-ref=$VCS_REF \
	  org.label-schema.build-date=$BUILD_DATE \
	  org.label-schema.schema-version="1.0.3"
