from invoke import task


@task
def base(c, version):
    _build(c, version, "base")


@task
def community(c, version, force=False):
    if force:
        base(c, version)
    _build(c, version, "community")


@task
def enterprise(c, version, force=False):
    if force:
        community(c, version, force)
    _build(c, version, "enterprise")


@task
def openupgrade(c, version, force=False):
    if force:
        community(c, version, force)
    _build(c, version, "openupgrade")


def _build(c, version, edition):
    print(f"Building odoo/{edition}:{version}")
    c.run(
        f"""
set -e
export BUILD_DATE=`date -u +"%Y-%m-%dT%H:%M:%SZ"`
export SSH_KEY=`cat ~/.ssh/id_rsa`
docker buildx build \
--build-arg BUILD_DATE=$BUILD_DATE \
--ssh default \
-t odoo/{edition}:{version} \
-f {version}.0/Dockerfile.{edition} .
docker tag odoo/{edition}:{version} r.studio73.es/odoo/{edition}:{version}
    """,
        pty=True,
    )
