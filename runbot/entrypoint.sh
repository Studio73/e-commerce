#!/bin/bash

if [ -e /var/run/docker.sock ]; then
    chown odoo:odoo /var/run/docker.sock;
fi
python3 /entrypoint.py $@