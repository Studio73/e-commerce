from invoke import task


@task
def build(c, version, edition):
    base_image = "ubuntu:22.04"
    if edition == "base":
        if version in ["11", "12"]:
            base_image = "ubuntu:18.04"
        elif version in ["13", "14"]:
            base_image = "ubuntu:20.04"
    elif edition == "community":
        base_image = f"odoo/base:{version}"
    elif edition in ["enterprise", "openupgrade"]:
        base_image = f"r.studio73.es/odoo/community:{version}"
    print(base_image)
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
    """,
        pty=True,
    )
