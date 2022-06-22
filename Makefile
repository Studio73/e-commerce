DATE := `date -u +"%Y-%m-%dT%H:%M:%SZ"`
.PHONY: build base image Odoo + OCA
build:
	DOCKER_BUILDKIT=1 docker build --build-arg BUILD_DATE=$(DATE) -t odoo/base:$(VERSION) . -f $(VERSION)/Dockerfile

.PHONY: Push base image Odoo + OCA
push:
	docker tag odoo/base:$(VERSION) r.studio73.es/odoo/base:$(VERSION)
	docker push r.studio73.es/odoo/base:$(VERSION)
