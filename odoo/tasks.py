from invoke import task


@task
def base(c, version):
    base_image = "ubuntu:22.04"
    if version in ["9", "10", "11", "12"]:
        base_image = "ubuntu:18.04"
    elif version in ["13", "14"]:
        base_image = "ubuntu:20.04"
    _build(c, version, "base", base_image)


@task
def community(c, version, force=False):
    if force:
        base(c, version)
    base_image = f"r.studio73.es/odoo/base:{version}"
    _build(c, version, "community", base_image)


@task
def enterprise(c, version, force=False):
    if force:
        community(c, version, force)
    base_image = f"r.studio73.es/odoo/community:{version}"
    _build(c, version, "enterprise", base_image)


@task
def openupgrade(c, version, force=False):
    if force:
        community(c, version, force)
    base_image = f"r.studio73.es/odoo/community:{version}"
    _build(c, version, "openupgrade", base_image)


def _build(c, version, edition, base_image):
    print(f"Building odoo/{edition}:{version}")
    c.run(
        f"""
set -e
export BUILD_DATE=`date -u +"%Y-%m-%dT%H:%M:%SZ"`
export SSH_KEY=`cat ~/.ssh/id_rsa`
docker buildx build \
--build-arg BUILD_DATE=$BUILD_DATE \
--build-arg SSH_KEY="$SSH_KEY" \
--build-arg base_image={base_image} \
-t odoo/{edition}:{version} \
-f {version}.0/Dockerfile.{edition} .
docker tag odoo/{edition}:{version} r.studio73.es/odoo/{edition}:{version}
    """,
        pty=True,
    )
