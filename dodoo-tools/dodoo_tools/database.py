#!/usr/bin/env python
# Copyright 2019 Studio73 <https://www.studio73.es>
import os
import calendar

import click
import humanfriendly
import inquirer

from datetime import datetime, timedelta
from getpass import getpass
from os.path import join as pjoin

from minio import Minio
from tabulate import tabulate

from ._utils import echo, run, copy
from .cli import cli


BACKUP_PATH = pjoin(os.environ["DATA"], "backup")
XZ_DB_NAME = pjoin(BACKUP_PATH, "{}_{}.tar.xz").format
XZ_FSTORE_NAME = pjoin(BACKUP_PATH, "{}-fstore-{}.tar.xz").format
GZIP_DB_NAME = pjoin(BACKUP_PATH, "{}_{}.tar.gz").format
GZIP_FSTORE_NAME = pjoin(BACKUP_PATH, "{}-fstore-{}.tar.gz").format


def _database_exists(dbname):
    r = run([["psql", "-l"], ["grep", "-w", dbname], ["wc", "-l"]], check_call=True)
    return r.out != "0"


@cli.group()
def database():
    pass


@database.command()
@click.option("-f", "--filestore", is_flag=True, help="Backup also the filestore")
@click.option("-s", "--skip-rotation", is_flag=True, help="Skip database rotation")
@click.argument("dbname", envvar="DATABASE")
@click.pass_context
def backup(ctx, dbname, filestore, skip_rotation):
    if not os.path.isdir(BACKUP_PATH):
        run(["mkdir", BACKUP_PATH], "odoo")
    weekday = datetime.now().strftime("%A").upper()
    with echo("Creating database backup ({} {})".format(dbname, weekday)):
        if not _database_exists(dbname):
            raise Exception("Database %s does not exist" % dbname)
        run(
            [
                ["pg_dump", "-Ft", "--no-owner", dbname],
                ["pixz", "-7k", "-o", XZ_DB_NAME(dbname, weekday)],
            ]
        )
    base_fs = pjoin(os.environ["DATA"], "data", "filestore")
    if filestore and os.path.isdir(pjoin(base_fs, dbname)):
        with echo("Creating filestore backup ({} {})".format(dbname, weekday)):
            backup_fstore = XZ_FSTORE_NAME(dbname, weekday)
            run(["tar", "-I", "pixz -7k", "-C",  base_fs, "-cf", backup_fstore, dbname])
    if not skip_rotation:
        ctx.invoke(rotate, dbname=dbname)


@database.command()
@click.argument("dbname", envvar="DATABASE")
def rotate(dbname):
    """Rotation strategy\n
    - 1 copy per week of Month. Monday rotate database from last Sunday\n
    - 1 copy last 3 months. Day 1 rotate database from last day of past month
    """
    today = datetime.today()
    dday = today - timedelta(days=1)
    wday = dday.strftime("%A").upper()
    backup_path = XZ_DB_NAME(dbname, wday)
    if today.day == 1:
        # Monthly rotation
        suffix = "M{}".format(dday.month % 3 or 3)
        backup_dest = XZ_DB_NAME(dbname, suffix)
        msg = "Running database rotation ({})".format(suffix)
        copy(backup_path, backup_dest, msg)
    if today.weekday() == 0:
        # Weekly rotation
        suffix = "W{}".format(dday.day // 7)
        backup_dest = XZ_DB_NAME(dbname, suffix)
        msg = "Running database rotation ({})".format(suffix)
        copy(backup_path, backup_dest, msg)


@database.command()
@click.option("-f", "--format", default="psql")
@click.argument("dbname", envvar="DATABASE")
def ls(dbname, format):
    table = []
    base_path = pjoin(os.environ["DATA"], "backup")
    for i in range(0, 7):
        weekday = calendar.day_name[int(i)].upper()
        row = [weekday]
        backup_file = pjoin(base_path, XZ_DB_NAME(dbname, weekday))
        fstore_file = pjoin(base_path, XZ_FSTORE_NAME(dbname, weekday))
        if os.path.exists(backup_file):
            row += ["X", datetime.fromtimestamp(os.path.getmtime(backup_file))]
        else:
            backup_file = pjoin(base_path, GZIP_DB_NAME(dbname, weekday))
            if os.path.exists(backup_file):
                row += ["X", datetime.fromtimestamp(os.path.getmtime(backup_file))]
            else:
                row += ["-", "-"]
        if os.path.exists(fstore_file):
            row += ["X", datetime.fromtimestamp(os.path.getmtime(fstore_file))]
        else:
            fstore_file = pjoin(base_path, GZIP_FSTORE_NAME(dbname, weekday))
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
    location = location or BACKUP_PATH
    if not os.path.isdir(location):
        run(["mkdir", "-p", location], "odoo")
    if weekday is None:
        weekday = int(datetime.today().weekday()) - 1
        if weekday == -1:  # Monday
            weekday = 6
    day = calendar.day_name[weekday].upper()
    if download:
        backup_path = XZ_DB_NAME(source, day)
        if not download_from_s3(os.path.split(backup_path)[-1], location):
            backup_path = GZIP_DB_NAME(source, day)
            download_from_s3(os.path.split(backup_path)[-1], location)
        if filestore:
            fstore_path = XZ_FSTORE_NAME(source, day)
            if not download_from_s3(os.path.split(fstore_path)[-1], location):
                fstore_path = GZIP_FSTORE_NAME(source, day)
                download_from_s3(os.path.split(fstore_path)[-1], location)

    backup_path = XZ_DB_NAME(source, day)
    if not os.path.isfile(backup_path):
        backup_path = GZIP_DB_NAME(source, day)
        if not os.path.isfile(backup_path):
            raise Exception(
                "{} backup for {} ({}) does not exist, please check".format(
                    source, day.capitalize(), weekday
                )
            )
    backup_size = humanfriendly.format_size(os.path.getsize(backup_path))
    with echo("Restoring database {} ({}) {}".format(dbname, day, backup_size)):
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
            run(["createdb", "-U", pguser, "-O", pguser, dbname], check_call=True)
            if ".tar.gz" in backup_path:
                run(
                    [["gunzip", "-c", backup_path], ["psql", dbname, "-U", pguser]],
                    check_call=True,
                )
            else:
                run(
                    [
                        ["xz", "-dkc", backup_path],
                        ["pg_restore", "-Ox", "-U", pguser, "-d", dbname],
                    ],
                    check_call=True,
                )
    if filestore:
        fstore_path = XZ_FSTORE_NAME(source, day)
        if not os.path.isfile(fstore_path):
            fstore_path = GZIP_FSTORE_NAME(source, day)
            if not os.path.isfile(fstore_path):
                raise Exception(
                    "{} filestore for {} ({}) does not exist, please check".format(
                        source, day.capitalize(), weekday
                    )
                )
        fstore_size = humanfriendly.format_size(os.path.getsize(fstore_path))
        with echo("Restoring filestore {} ({}) {}".format(dbname, day, fstore_size)):
            fstore_dest = pjoin(os.environ["DATA"], "data", "filestore")
            run(["mkdir", "-p", fstore_dest])
            run(["tar", "-xf", fstore_path, "-C", "/tmp"])
            source_path = pjoin("/tmp", source)
            if not os.path.exists(source_path):
                # Old backups data structure
                source_path = pjoin("/tmp", "data", "filestore", source)
                if not os.path.exists(source_path):
                    raise Exception("Unknown filestore data structure")
            run(["mv", source_path, fstore_dest])
            host_uid = os.environ.get("HOST_UID", "odoo")
            host_gid = os.environ.get("HOST_GID", "odoo")
            run(["chown", "-R", "%s:%s" % (host_uid, host_gid), fstore_dest])


def download_from_s3(name, dest):
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
            "From which bucket do you want to download?",
            choices=download_dict.keys(),
        )
        download_obj = download_dict[ans]
    if not download_obj:
        return False
    with echo("Downloading %s" % (name)):
        data = client.get_object(download_obj.bucket_name, download_obj.object_name)
        with open(pjoin(dest, name), "wb") as file_data:
            for d in data.stream(32 * 1024):
                file_data.write(d)
    return True


if __name__ == "__main__":
    pass
