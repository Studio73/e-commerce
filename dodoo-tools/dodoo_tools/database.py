#!/usr/bin/env python
# Copyright 2019 Studio73 <https://www.studio73.es>
import os
import calendar

import click
import inquirer

from datetime import datetime
from getpass import getpass

from minio import Minio
from tabulate import tabulate

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
@click.option("-f", "--format", default="psql")
@click.argument("dbname", envvar="DATABASE")
def ls(dbname, format):
    table = []
    base_path = os.path.join(os.environ["DATA"], "backup")
    for i in range(0, 7):
        weekday = calendar.day_name[int(i)].upper()
        row = [weekday]
        backup_file = os.path.join(base_path, "{}_{}.tar.gz".format(dbname, weekday))
        fstore_file = os.path.join(
            base_path, "{}-fstore-{}.tar.gz".format(dbname, weekday)
        )
        if os.path.exists(backup_file):
            row += ["X", datetime.fromtimestamp(os.path.getmtime(backup_file))]
        else:
            row += ["-", "-"]
        if os.path.exists(fstore_file):
            row += ["X", datetime.fromtimestamp(os.path.getmtime(fstore_file))]
        else:
            row += ["-", "-"]
        table.append(row)
    print(
        tabulate(
            table,
            headers=["Day", "Backup", "Last modified", "Filestore", "Last modified"],
            showindex="always",
            tablefmt=format,
        )
    )


@database.command()
@click.option(
    "-F", "--force", is_flag=True, help="Delete database if exists and create a new one"
)
@click.option("-f", "--filestore", is_flag=True, help="Restore also the filestore")
@click.option(
    "-d", "--download", is_flag=True, help="Download the database from S3 storage"
)
@click.option("-w", "--weekday", type=int, help="Weekday, default today (Monday is 0)")
@click.option("-t", "--template", help="Use a template as a restore source")
@click.option("-l", "--location", help="Location where are the database backups")
@click.option("-s", "--source", help="Project database name to use as source")
@click.argument("dbname", envvar="DATABASE")
def restore(dbname, force, filestore, download, weekday, template, location, source):
    if not os.environ.get("DEV"):
        answer = input("You are in a production environment! Continue? (y/N) ")
        if answer != "y":
            print("Aborted!")
            return
    source = source or dbname
    location = location or os.path.join(os.environ["DATA"], "backup")
    if weekday is None:
        weekday = int(datetime.today().weekday()) - 1
        if weekday == -1:  # Monday
            weekday = 6
    day = calendar.day_name[weekday].upper()
    backup_name = "%s_%s.tar.gz" % (source, day)
    fstore_name = "%s-fstore-%s.tar.gz" % (source, day)
    if download:
        download_from_s3(backup_name, location, "backup")
        if filestore:
            download_from_s3(fstore_name, location, "filestore")
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
            backup_path = os.path.join(location, backup_name)
            if not os.path.isfile(backup_path):
                raise Exception(
                    "Selected backup %s for %s (%s) does not exist, please check"
                    % (source, day.capitalize(), weekday)
                )
            run(["createdb", "-U", pguser, "-O", pguser, dbname], check_call=True)
            run(
                [["gunzip", "-c", backup_path], ["psql", dbname, "-U", pguser]],
                check_call=True,
            )
    if filestore:
        with echo("Restoring filestore backup (%s)" % dbname):
            fstore_path = os.path.join(location, fstore_name)
            if os.path.isfile(fstore_path):
                fstore_dest = os.path.join(os.environ["DATA"], "data", "filestore")
                run(["mkdir", "-p", fstore_dest])
                run(["tar", "-xf", fstore_path, "-C", "/tmp"])
                source_path = os.path.join("/tmp", source)
                if not os.path.exists(source_path):
                    # Old backups data structure
                    source_path = os.path.join("/tmp", "data", "filestore", source)
                    if not os.path.exists(source_path):
                        raise Exception("Unknown filestore data structure")
                run(["mv", source_path, fstore_dest])
                host_uid = os.environ.get("HOST_UID", "odoo")
                host_gid = os.environ.get("HOST_GID", "odoo")
                run(["chown", "-R", "%s:%s" % (host_uid, host_gid), fstore_dest])


def download_from_s3(name, dest, ftype):
    url = os.environ.get("S3_URL") or input("? S3 url: ")
    user = os.environ.get("S3_USER") or input("? S3 user: ")
    secret = os.environ.get("S3_SECRET") or getpass("? S3 secret: ")
    client = Minio(url, access_key=user, secret_key=secret, secure=True)
    download_dict = {}
    download_obj = False
    for bucket in client.list_buckets():
        for fil in client.list_objects(bucket.name, recursive=True):
            object_name = os.path.split(fil.object_name)[-1]
            if name == object_name:
                download_dict[fil.bucket_name] = fil
                break
    if len(download_dict.values()) == 1:
        download_obj = list(download_dict.values())[0]
    elif len(download_dict.values()) > 1:
        ans = inquirer.list_input(
            "From which bucket do you want to download?", choices=download_dict.keys(),
        )
        download_obj = download_dict[ans]
    if not download_obj:
        raise Exception("%s file not found" % name)
    with echo("Downloading %s %s" % (ftype, name)):
        data = client.get_object(download_obj.bucket_name, download_obj.object_name)
        with open(os.path.join(dest, name), "wb") as file_data:
            for d in data.stream(32 * 1024):
                file_data.write(d)


if __name__ == "__main__":
    pass
