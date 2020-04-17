#!/usr/bin/env python
# Copyright 2019 Studio73 <https://www.studio73.es>
import os
import calendar
import click
from datetime import datetime

from ._utils import echo, run
from .cli import cli


def _database_exists(dbname):
    r = run([["psql", "-l"], ["grep", "-w", dbname], ["wc", "-l"]], check_call=True)
    return r.out != "0"


@cli.group()
def database():
    pass


@database.command()
@click.option(
    "-F", "--force", is_flag=True, help="Do not show error if database does not exist"
)
@click.option("-f", "--filestore", is_flag=True, help="Backup also the filestore")
@click.argument("dbname", envvar="DATABASE")
def backup(dbname, force, filestore):
    tday = datetime.now().strftime("%A").upper()
    backup_path = os.path.join(os.environ["DATA"], "backup")
    if not os.path.isdir(backup_path):
        run(["mkdir", backup_path], "odoo")
    with echo("Creating database backup (%s)" % dbname):
        bpath = os.path.join(backup_path, dbname)
        if not _database_exists(dbname):
            if not force:
                raise Exception("Database %s does not exist" % dbname)
        with open("%s_%s.tar.gz" % (bpath, tday), "w") as bfile:
            run([["pg_dump", "--no-owner", dbname], ["gzip", "--stdout"]], stdout=bfile)
    if filestore:
        with echo("Creating filestore backup (%s)" % dbname):
            # https://orville.thebennettproject.com/articles/tar-removing-leading-slash/
            fstore_name = os.path.join(
                backup_path, "%s-fstore-%s.tar.gz" % (dbname, tday)
            )
            fstore_path = os.path.join(os.environ["DATA"], "data", "filestore")
            if os.path.isdir(os.path.join(fstore_path, dbname)):
                run(["tar", "-C", fstore_path, "-cf", fstore_name, dbname])


@database.command()
@click.option(
    "-F", "--force", is_flag=True, help="Delete database if exists and create a new one"
)
@click.option("-f", "--filestore", is_flag=True, help="Restore also the filestore")
@click.option("-w", "--weekday", type=int, help="Weekday, default today (Monday is 0)")
@click.option("-t", "--template", help="Use a template as a restore source")
@click.argument("dbname", envvar="DATABASE")
def restore(dbname, force, filestore, weekday, template):
    if weekday is None:
        weekday = datetime.today().weekday()
    day = calendar.day_name[int(weekday)].upper()
    with echo("Restoring database backup (%s)" % dbname):
        pguser = os.environ["PGUSER"]
        if _database_exists(dbname):
            if not force:
                raise Exception(
                    "Database %s exist, if you want to continue add -F option" % dbname
                )
            run(["dropdb", dbname])
        if template:
            if not _database_exists(template):
                raise Exception(
                    "Template %s does not exists, please check" % (template)
                )
            run(
                ["createdb", "-U", pguser, "-O", pguser, "-T", template, dbname],
                check_call=True,
            )
        else:
            backup_name = "%s_%s.tar.gz" % (dbname, day)
            backup_path = os.path.join(os.environ["DATA"], "backup", backup_name)
            if not os.path.isfile(backup_path):
                raise Exception(
                    "Selected backup %s for %s (%s) does not exist, please check"
                    % (dbname, day.capitalize(), weekday)
                )
            run(["createdb", "-U", pguser, "-O", pguser, dbname], check_call=True)
            run(
                [["gunzip", "-c", backup_path], ["psql", dbname, "-U", pguser]],
                check_call=True,
            )
    if filestore:
        with echo("Restoring filestore backup (%s)" % dbname):
            data_path = os.environ["DATA"]
            backup_path = os.path.join(data_path, "backup")
            fstore_name = os.path.join(
                backup_path, "%s-fstore-%s.tar.gz" % (dbname, day)
            )
            if os.path.isfile(fstore_name):
                fstore_dest = os.path.join(data_path, "data", "filestore")
                run(["mkdir", "-p", fstore_dest])
                run(["tar", "-xf", fstore_name, "-C", "/tmp"])
                source_path = os.path.join("/tmp", dbname)
                if not os.path.exists(source_path):
                    # Old backups data structure
                    source_path = os.path.join("/tmp", "data", "filestore", dbname)
                    if not os.path.exists(source_path):
                        raise Exception("Unknown filestore data structure")
                run(["mv", source_path, fstore_dest])
                host_uid = os.environ.get("HOST_UID", "odoo")
                host_gid = os.environ.get("HOST_GID", "odoo")
                run(["chown", "-R", "%s:%s" % (host_uid, host_gid), fstore_dest])


if __name__ == "__main__":
    pass
