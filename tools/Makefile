.PHONY: Build tools
build:
	DOCKER_BUILDKIT=1 docker build -t odoo/tools .

.PHONY: Push tools
push:
	docker tag odoo/tools r.studio73.es/odoo/tools
	docker push r.studio73.es/odoo/tools
