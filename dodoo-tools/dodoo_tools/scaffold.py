#!/usr/bin/env python
# Copyright 2020 Studio73 - Pablo Fuentes <pablo@studio73.es>
import os
import click
import pkg_resources

from jinja2 import Environment, FileSystemLoader

from .cli import cli
from ._utils import echo, gen_password, run


def _scaffold(name):
    base_path = "/opt/odoo/scaffold/"
    if len(os.listdir(base_path)) != 0:
        raise Exception("{} is not empty".format(base_path))
    if not os.path.exists(base_path):
        os.mkdir(base_path)
    env_path = os.path.join(base_path, ".env")
    env_db_path = os.path.join(base_path, ".env-db")
    docker_compose_path = os.path.join(base_path, "docker-compose.yaml")
    os.mkdir(os.path.join(base_path, "data"))
    os.mkdir(os.path.join(base_path, "setup"))
    os.mkdir(os.path.join(base_path, "src"))
    admin_password = gen_password()
    pg_password = gen_password()
    j2_env = Environment(
        loader=FileSystemLoader(
            pkg_resources.resource_filename("dodoo_tools", "templates")
        ),
        trim_blocks=True,
    )
    env_tmpl = j2_env.get_template("env.tmpl").render(
        {
            "name": name,
            "admin_password": admin_password,
            "pg_host": "postgres",
            "pg_port": "5432",
            "pg_password": pg_password,
            "lang": "es_ES",
            "repo": "git@github.com:Studio73/{}-addons.git".format(name),
        }
    )
    with open(env_path, "w") as f:
        f.write(env_tmpl)
    env_db_tmpl = j2_env.get_template("env-db.tmpl").render(
        {"name": name, "pg_password": pg_password, "lang": "es_ES",}
    )
    with open(env_db_path, "w") as f:
        f.write(env_db_tmpl)
    docker_compose_tmpl = j2_env.get_template("docker-compose.tmpl").render(
        {"name": name, "odoo_version": os.environ["ODOO_VERSION"]}
    )
    with open(docker_compose_path, "w") as f:
        f.write(docker_compose_tmpl)
    host_uid = os.environ.get("HOST_UID", "odoo")
    host_gid = os.environ.get("HOST_GID", "odoo")
    run(["chown", "-R", "%s:%s" % (host_uid, host_gid), base_path])


@cli.command()
@click.argument("name", envvar="DO_NAME")
def scaffold(name):
    with echo("Creating scaffold for {}".format(name)):
        _scaffold(name)
