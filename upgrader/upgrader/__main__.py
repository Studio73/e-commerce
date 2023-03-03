# (c) Studio73 - Pablo Fuentes <pablo@studio73.es>

import importlib
import os
import subprocess as sp
from datetime import datetime

import click
import psycopg2
from plumbum import local
from plumbum.commands import CommandNotFound
from plumbum.path.local import shutil
from python_on_whales import docker
from python_on_whales.exceptions import DockerException
from python_on_whales.utils import stream_stdout_and_stderr
from rich import box
from rich.console import Group
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table

AVAILABLE_VERSIONS = ["11", "12", "13", "14", "15", "16"]
DOCKER_IMG = "r.studio73.es/odoo"


def get_odoo_version(database):
    conn = psycopg2.connect(dbname=database)
    cr = conn.cursor()
    sql = "SELECT latest_version FROM ir_module_module WHERE name = 'base';"
    cr.execute(sql)
    version = cr.fetchone()[0].split(".")[0]
    conn.close()
    return int(version)


def get_now():
    return datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S")


version_progress = Progress(
    TextColumn("{task.description}"),
    BarColumn(bar_width=None),
    # steps: createdb, pre, migration, post
    TextColumn("({task.completed}/{task.total})"),
    TimeElapsedColumn(),
)
upgrade_progress = Progress(
    SpinnerColumn("dots"),
    TextColumn("  "),
    TextColumn("[bold cyan]{task.description}"),
    TimeElapsedColumn(),
)
total_progress = Progress(
    TextColumn("{task.description}"),
    BarColumn(bar_width=None),
    TextColumn("({task.completed}/{task.total})"),
    TimeElapsedColumn(),
)

layout = Layout()
log_layout = Layout(Panel("", title="Waiting for logs", box=box.SIMPLE))
progress_group = Group(total_progress, version_progress, upgrade_progress)
progress_layout = Layout(
    Panel(progress_group, title="Upgrade progress", border_style="yellow"), size=12
)
layout.split_column(progress_layout, log_layout)


class LiveLog:
    def __init__(self, lines):
        self.lines = lines or []

    def __rich_console__(self, console, options):
        lt = Table(show_header=False, show_footer=False, show_edge=False)
        for line in self.lines[-options.max_height :]:
            lt.add_row(line)
        yield lt


class Upgrader(object):
    def __init__(
        self, edition, database, db_origin, version, version_origin, ee_code=None
    ):
        self.database = database
        self.edition = edition
        self.version = version
        self.db_target = (
            f"{database}_{self.version}_{datetime.now().strftime('%Y_%m_%d_%H_%M_%S')}"
        )
        self.db_origin = db_origin
        self.version_origin = version_origin
        self.ee_code = ee_code
        self.migrations = self.get_migrations()
        self.image = f"{DOCKER_IMG}/openupgrade:{self.version}"
        self.volumes = [
            (os.environ["FILESTORE"], "/opt/odoo/data/filestore"),
            ("/var/run/postgresql", "/var/run/postgresql"),
        ]
        self.envs = {
            "PGHOST": os.environ.get("PGHOST", "/var/run/postgresql"),
            "PGUSER": os.environ.get("PGUSER", os.getlogin()),
            "PGDATABASE": self.db_target,
            "ODOO_WORKERS": 0,
            "ODOO_MAX_CRON_THREADS": 0,
            "ODOO_LIMIT_MEMORY_HARD": 46843545600,
            "ODOO_LIMIT_MEMORY_SOFT": 41474836480,
            # Mute _file_read -> FileNotFoundError
            "ODOO_LOG_HANDLER": "odoo.addons.base.models.ir_attachment:CRITICAL",
        }
        if os.environ.get("PGPASSWORD"):
            self.envs["PGPASSWORD"] = os.environ["PGPASSWORD"]
        if edition == "enterprise":
            self.envs["PGDATABASE"] = self.db_origin
            self.image = f"{DOCKER_IMG}/enterprise:{self.version_origin}"
        self.version_task = version_progress.add_task(
            f"[{get_now()}] [bright_blue]{self.version} - {self.db_target}[/bright_blue]",
            total=4,
        )
        self.task = upgrade_progress.add_task("", name="upgrade")

    def createdb(self):
        if self.edition == "enterprise":
            # Entreprise no need to create a new database
            return
        self.info(f"Creating database {self.db_target} from template {self.db_origin}")
        local["createdb"]["-T", self.db_origin, self.db_target]()

    def mergefs(self):
        fs = os.environ["FILESTORE"]
        if os.path.exists(os.path.join(fs, self.db_target)):
            sp.check_call(
                ["rsync", "-a", self.db_target + os.sep, self.database], cwd=fs
            )
            shutil.rmtree(os.path.join(fs, self.db_target))

    def cleanup(self):
        fs = os.path.join(os.environ["FILESTORE"], self.db_target)
        if os.path.exists(fs):
            shutil.rmtree(fs)
        local["dropdb"]["--if-exists", self.db_target]()

    def info(self, msg):
        upgrade_progress.update(self.task, description=msg)
        return True

    def error(self, msg):
        upgrade_progress.update(self.task, description=f"[bold red]{msg}[/bold red]")
        try:
            notify_send = local["notify-send"]
            notify_send[
                "-u",
                "critical",
                "-t",
                "10000",
                "Odoo Upgrader",
                f"{self.database} - migration to {self.version} failed",
            ]()
        except CommandNotFound:
            pass
        return True

    def get_migrations(self):
        scripts = {
            "pre": [],
            "post": [],
        }
        script_path = os.path.abspath(os.path.dirname(os.path.relpath(__file__)))
        mig_paths = [
            os.path.join(script_path, "migrations", str(self.version)),
        ]
        if os.environ.get("MIGRATIONS") and os.path.exists(os.environ["MIGRATIONS"]):
            mig_paths.append(os.path.join(os.environ["MIGRATIONS"], str(self.version)))
        for mig_path in mig_paths:
            if not os.path.exists(mig_path):
                continue
            for pyfile in sorted(os.listdir(mig_path)):
                name, ext = os.path.splitext(os.path.basename(pyfile))
                if ext.lower() != ".py":
                    continue
                vals = {
                    "name": name,
                    "pyfile": pyfile,
                    "path": os.path.join(mig_path, pyfile),
                }
                if name.startswith("pre-"):
                    scripts["pre"].append(vals)
                if name.startswith("post-"):
                    scripts["post"].append(vals)
        scripts["pre"].sort(key=lambda x: x["name"])
        scripts["post"].sort(key=lambda x: x["name"])
        return scripts

    def load_migration(self, full_path, module_name):
        spec = importlib.util.spec_from_file_location(module_name, full_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def run_migration(self, stage):
        for migration in self.migrations.get(stage, []):
            mod = None
            with open(migration["path"]) as f:
                shebang = f.readline().strip("\n")
            if "click-odoo" in shebang:
                if stage == "pre":
                    image = f"{DOCKER_IMG}/community:{self.version_origin}"
                else:
                    image = self.image
                # click-odoo shebang: #!/usr/bin/env click-odoo
                self.info(f"Running {stage}-migration (click): {migration['pyfile']}")
                docker_path = os.path.join("/tmp", migration["pyfile"])
                self.docker_run(
                    ["python3", "-m", "click_odoo", docker_path],
                    volumes=[(migration["path"], docker_path)],
                    image=image,
                )
            else:
                try:
                    mod = self.load_migration(migration["path"], migration["name"])
                    migrate = mod.migrate
                except ImportError:
                    self.error(
                        f"Unable to load {stage}-migration: {migration['pyfile']}"
                    )
                    self.cleanup()
                    exit(1)
                except AttributeError:
                    self.error(
                        f"Error {stage}-migration: {migration['pyfile']}"
                        f" file must have a 'migrate(cr)' function"
                    )
                    self.cleanup()
                    exit(1)
                else:
                    if stage == "pre" and self.edition == "enterprise":
                        conn = psycopg2.connect(dbname=self.db_origin)
                    else:
                        conn = psycopg2.connect(dbname=self.db_target)
                    self.info(f"Running {stage}-migration: {migration['pyfile']}")
                    try:
                        migrate(conn.cursor())
                        conn.commit()
                    except Exception as e:
                        self.error(e)
                        self.cleanup()
                        exit(1)
                    conn.close()
                finally:
                    if mod:
                        del mod
        return True

    def live_log(self, iterator):
        logfile = f"{os.path.join('/tmp', self.db_target)}.log"
        with open(logfile, "w") as f:
            lines = []
            for _, stream in iterator:
                line = stream.decode()
                f.write(line)
                lines.append(line.strip())
                log_layout.update(Panel(LiveLog(lines), title="Live Logs"))

    def docker_run(self, cmd, image=None, volumes=None):
        try:
            if image is None:
                image = self.image
            if volumes is None:
                volumes = []
            volumes += self.volumes
            if self.version > 10:
                docker.pull(image)
            iterator = docker.run(
                image,
                cmd,
                name=self.db_target,
                hostname=self.db_target,
                envs=self.envs,
                volumes=volumes,
                remove=True,
                stream=True,
            )
            self.live_log(iterator)
        except Exception:
            self.error(f"Error during {' '.join(cmd)}")
            self.cleanup()
            exit(1)
        return True

    def community(self):
        self.info("Running community database migration")
        cmd = ["odoo", "-u", "base", "--stop-after-init", "--no-xmlrpc"]
        return self.docker_run(cmd)

    def pre_enterprise(self):
        conn = psycopg2.connect(dbname=self.db_origin)
        cr = conn.cursor()
        cr.execute(
            "SELECT value FROM ir_config_parameter WHERE key = 'database.enterprise_code'"
        )
        code = cr.fetchone()
        if not code:
            if not self.ee_code:
                self.error("Missing enterprise code ")
                exit(1)
            cr.execute(
                "insert into ir_config_parameter (key, value) "
                "values ('database.enterprise_code', %s);",
                (self.ee_code,),
            )
            conn.commit()
        self.info("Updating all modules")
        docker_path = os.path.join("/tmp", "update_all.py")
        script_path = os.path.abspath(os.path.dirname(os.path.relpath(__file__)))
        script_path = os.path.join(script_path, "scripts", "update_all.py")
        self.docker_run(
            ["python3", "-m", "click_odoo", docker_path],
            volumes=[(script_path, docker_path)],
        )
        conn.commit()
        docker_path = os.path.join("/tmp", "install_enterprise.py")
        script_path = os.path.abspath(os.path.dirname(os.path.relpath(__file__)))
        cr.execute("SELECT state FROM ir_module_module WHERE name = 'web_enterprise'")
        module = cr.fetchone()
        if not module or module[0] != "installed":
            self.info("Installing web_enterprise")
            script_path = os.path.join(script_path, "scripts", "install_enterprise.py")
            self.docker_run(
                ["python3", "-m", "click_odoo", docker_path],
                volumes=[(script_path, docker_path)],
            )
            conn.commit()
        conn.close()
        return

    def enterprise(self):
        # TODO: run only first time
        self.pre_enterprise()
        self.info("Running enterprise database migration")
        ee_script = os.path.join(
            os.path.dirname(os.path.relpath(__file__)), "upgrade.py"
        )
        env = {"SSL_VERIFICATION": "off"}
        cmd = [
            "python3",
            ee_script,
            "production",
            "-e",
            "ODOO_MIG_ENABLE_UOM_INCONSISTENCIES_FIX=FROM_PRODUCT",
            "-e",
            "ODOO_MIG_DO_NOT_IGNORE_ARCHIVED_PRODUCTS_FOR_UOM_INCONSISTENCIES=1",
            "--target",
            f"{self.version}.0",
            "--dbname",
            self.db_origin,
            "--restore-name",
            self.db_target,
        ]
        try:
            iterator = stream_stdout_and_stderr(cmd, env)
            self.live_log(iterator)
        except DockerException:
            self.error("Error during database upgrade")
            exit(1)
        # FIXME:
        # Update OCA modules
        # self.envs["PGDATABASE"] = self.db_target
        # self.image = f"{DOCKER_IMG}/enterprise:{self.version}"
        # self.info("Updating all modules")
        # cmd = ["odoo", "-u", "all", "--stop-after-init", "--no-xmlrpc"]
        # return self.docker_run(cmd)

    def start(self):
        version_progress.update(self.version_task, advance=1)
        self.createdb()
        version_progress.update(self.version_task, advance=1)
        self.run_migration("pre")
        version_progress.update(self.version_task, advance=1)
        # self.community() or self.enterprise()
        res = getattr(self, self.edition)()
        version_progress.update(self.version_task, advance=1)
        self.run_migration("post")
        self.mergefs()
        version_progress.stop_task(self.version_task)
        self.info("Done database upgrade")
        upgrade_progress.stop_task(self.task)
        upgrade_progress.update(self.version_task, visible=False)
        desc = (
            f"[{get_now()}] [bold green]{self.version} - {self.db_target}[/bold green]"
        )
        version_progress.update(
            self.version_task,
            description=desc,
        )
        return res


@click.command()
@click.option(
    "-t",
    "--target",
    required=True,
    type=click.Choice(AVAILABLE_VERSIONS),
    envvar="TARGET",
)
@click.option(
    "-e",
    "--edition",
    required=True,
    type=click.Choice(["community", "enterprise"]),
    envvar="EDITION",
)
@click.option("-d", "--database", required=True, envvar="DATABASE")
@click.option("-s", "--start-from")
@click.option("-c", "--enterprise-code")
@click.option("-m", "--migrations", envvar="MIGRATIONS")
@click.option("-f", "--filestore", envvar="FILESTORE", help="Default /tmp/filestore")
def main(target, edition, database, start_from, enterprise_code, migrations, filestore):
    target = int(target)
    if migrations:
        os.environ["MIGRATIONS"] = migrations
    if not filestore:
        filestore = os.environ.get("FILESTORE") or os.path.join("/tmp", "filestore")
    if not os.path.exists(filestore):
        os.makedirs(filestore)
    os.environ["FILESTORE"] = filestore
    db_origin = database
    if start_from:
        db_origin = start_from
    current_version = get_odoo_version(db_origin)
    next_version = current_version + 1
    total_versions = target - current_version
    total_task = total_progress.add_task(
        f"[{get_now()}] [bright_blue]{current_version} "
        f"to {target} - Migration {database}[/bright_blue]",
        total=total_versions,
    )
    with Live(layout):
        while next_version <= target:
            log_layout.update(Panel("", title="Waiting for logs", box=box.SIMPLE))
            upgrader = Upgrader(
                edition,
                database,
                db_origin,
                next_version,
                current_version,
                enterprise_code,
            )
            upgrader.start()
            db_origin = upgrader.db_target
            current_version = next_version
            next_version += 1
            total_progress.update(total_task, advance=1)
        # TODO: run last script: clean views
    return True


if __name__ == "__main__":
    main()
