BUILD_DATE := `date -u +"%Y-%m-%dT%H:%M:%SZ"`
SSH_KEY := `cat ~/.ssh/id_rsa`

_build edition version base_image:
    #!/usr/bin/env bash
    set -e
    docker buildx build \
    --build-arg BUILD_DATE={{ BUILD_DATE }} \
    --build-arg SSH_KEY="{{ SSH_KEY }}" \
    --build-arg base_image={{ base_image }} \
    -t odoo/{{ edition }}:{{ version }} \
    -f {{ version }}.0/Dockerfile.{{ edition }} .

base version:
    just _build base {{ version }} "ubuntu:20.04"

community version: (base version)
    just _build community {{ version }} "odoo/base:{{ version }}"

enterprise version: (base version) (community version)
    just _build enterprise {{ version }} "odoo/community:{{ version }}"
