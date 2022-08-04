DATE := `date -u +"%Y-%m-%dT%H:%M:%SZ"`
SSH_KEY=`cat ~/.ssh/id_rsa`
.PHONY: build base Odoo images
build:
	#DOCKER_BUILDKIT=1 docker build --build-arg BUILD_DATE=$(DATE) -t odoo/base:$(VERSION) . -f $(VERSION).0/Dockerfile.base
	DOCKER_BUILDKIT=1 docker build --build-arg BUILD_DATE=$(DATE) --build-arg SSH_KEY="${SSH_KEY}" --build-arg base_image=odoo/base:$(VERSION) -t odoo/community:$(VERSION) -f $(VERSION).0/Dockerfile.community .
	DOCKER_BUILDKIT=1 docker build --build-arg BUILD_DATE=$(DATE) --build-arg SSH_KEY="${SSH_KEY}" --build-arg base_image=odoo/community:$(VERSION) -t odoo/enterprise:$(VERSION) -f $(VERSION).0/Dockerfile.enterprise .

.PHONY: Push base Odoo images
push:
	docker tag odoo/base:$(VERSION) r.studio73.es/odoo/base:$(VERSION)
	docker push r.studio73.es/odoo/base:$(VERSION)
	docker tag odoo/community:$(VERSION) r.studio73.es/odoo/community:$(VERSION)
	docker push r.studio73.es/odoo/community:$(VERSION)
	docker tag odoo/enterprise:$(VERSION) r.studio73.es/odoo/enterprise:$(VERSION)
	docker push r.studio73.es/odoo/enterprise:$(VERSION)
