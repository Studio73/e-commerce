ARG BASE_TAG=14
FROM r.studio73.es/odoo/enterprise:${BASE_TAG}
RUN --mount=type=ssh,uid=1000 cd $SRC/studio73 && gitaggregate --jobs 8 -c repos.yaml -d extra/*
RUN install-requirements $SRC/studio73
