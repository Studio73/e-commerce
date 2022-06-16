DATE := `date -u +"%Y-%m-%dT%H:%M:%SZ"`
.PHONY: build base image Odoo + OCA
build-14:
	DOCKER_BUILDKIT=1 docker build --build-arg BUILD_DATE=$(DATE) -t odoo/base:14.0 . -f 14.0/Dockerfile

.PHONY: Push base image Odoo + OCA
push-14:
	docker tag odoo/base:14.0 r.studio73.es/odoo/base:14.0
	docker push r.studio73.es/odoo/base:14.0

build-15:
	DOCKER_BUILDKIT=1 docker build --build-arg BUILD_DATE=$(DATE) -t odoo/base:15.0 . -f 15.0/Dockerfile

.PHONY: Push base image Odoo + OCA
push-15:
	docker tag odoo/base:15.0 r.studio73.es/odoo/base:15.0
	docker push r.studio73.es/odoo/base:15.0
