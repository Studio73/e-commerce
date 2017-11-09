FROM ubuntu:16.04
MAINTAINER Pablo Fuentes <pablo@studio73.es>

RUN useradd -md /opt/odoo -s /bin/bash odoo
WORKDIR /opt/odoo/
EXPOSE 8069 8072
# Avoid werkzeug encoding ANSI_X3.4-1968 warning
ENV LC_ALL=C.UTF-8 \
	DATA_PATH='/opt/odoo/data' \
	SETUP_PATH='/opt/odoo/setup' \
	SRC_PATH='/opt/odoo/src'
VOLUME ["/opt/odoo/data", "/opt/odoo/setup", "/opt/odoo/src"]

RUN apt-get update \
	&& apt-get -y upgrade \
    && apt-get install -y --no-install-recommends \
    		apt-utils \
            ca-certificates \
            curl \
            node-less \
			python-dev  \
     		build-essential \
			libssl-dev \
			libffi-dev \
     		libxml2-dev \
			libxslt1-dev \
			zlib1g-dev \
			libldap2-dev \
			libsasl2-dev \
			libfontconfig1 \
			libxrender1 \
			libxext6 \
			python-wheel \
            python-setuptools \
            python-gevent \
            python-renderpm \
            python-watchdog \
            supervisor \
			vim \
            git \
	&& apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false -o APT::AutoRemove::SuggestsImportant=false npm \
	&& rm -Rf /var/lib/apt/lists/* /tmp/*

RUN echo "deb http://apt.postgresql.org/pub/repos/apt/ xenial-pgdg main" >> /etc/apt/sources.list.d/postgres.list \
 	&& curl -SL https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add - \
 	&& apt-get update \
    && apt-get install -y --no-install-recommends postgresql-client \
	&& rm -Rf /var/lib/apt/lists/* /tmp/*

RUN curl -SLo /tmp/wkhtmltox.tar.xz https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/0.12.4/wkhtmltox-0.12.4_linux-generic-amd64.tar.xz \
	&& tar -xf /tmp/wkhtmltox.tar.xz -C /tmp \
	&& mv /tmp/wkhtmltox/bin/* /usr/local/bin \
	&& rm -Rf /tmp/*

# Force install pip 9.0.1
RUN curl -SLo /tmp/pip.tar.gz https://pypi.python.org/packages/11/b6/abcb525026a4be042b486df43905d6893fb04f05aac21c32c638e939e447/pip-9.0.1.tar.gz#md5=35f01da33009719497f01a4ba69d63c9 \
	&& tar -xf /tmp/pip.tar.gz -C /tmp \
	&& cd /tmp/pip-9.0.1/ \
	&& python setup.py install \
	&& rm -Rf /tmp/*

RUN pip install --no-cache-dir git-aggregator \
	&& curl -SLo /tmp/requirements.txt https://raw.githubusercontent.com/odoo/odoo/10.0/requirements.txt \
	&& pip install -r /tmp/requirements.txt \
	&& apt-get -y autoremove \
	&& rm -Rf /var/lib/apt/lists/* /tmp/*
# Odoo manager
COPY oman/ /tmp/oman/
WORKDIR /tmp/oman/
RUN python setup.py install \
	&& rm -Rf /tmp/*
WORKDIR /opt/odoo/
COPY entrypoint.py /
ENTRYPOINT ["python", "/entrypoint.py"]
CMD ["python", "/opt/odoo/src/odoo/odoo-bin", "-c", "/opt/odoo/src/odoo.conf"]
