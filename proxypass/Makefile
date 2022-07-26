.PHONY: Build tools
build:
	DOCKER_BUILDKIT=1 docker build -t odoo/proxypass .

.PHONY: Push tools
push:
	docker tag odoo/proxypass r.studio73.es/odoo/proxypass
	docker push r.studio73.es/odoo/proxypass
