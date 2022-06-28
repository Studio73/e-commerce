.PHONY: Build oci-build
build:
	DOCKER_BUILDKIT=1 docker build -t odoo/oci-build . 

.PHONY: Push oci-build
push:
	docker tag odoo/oci-build r.studio73.es/odoo/oci-build
	docker push r.studio73.es/odoo/oci-build
