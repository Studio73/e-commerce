import logging
import os
import time
from datetime import datetime, timedelta
from typing import Dict

import requests
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from python_on_whales import DockerClient, docker
from python_on_whales.components.compose.cli_wrapper import ComposeCLI
from python_on_whales.exceptions import DockerException, NoSuchService

POS = ("true", "True", "TRUE", "1", 1)
NEG = ("false", "False", "FALSE", "0", 0)
LOGDIR = "/data/log"
DATE_FORMAT = "%Y-%m-%d_%H%M%S"

LOGLEVEL = os.environ.get("LOGLEVEL", "INFO").upper()
logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=getattr(logging, LOGLEVEL),
)


class DodooContainer(object):
    def __init__(self, name, project, compose, service, labels, image, sha256):
        self.server_name = os.environ.get("AGENTNAME", os.environ["HOSTNAME"])
        self.name: str = name
        self.project: str = project
        self.compose: ComposeCLI = compose
        self.service: str = service
        self.labels: Dict[str, str] = labels
        self.image: str = image
        self.sha256: str = sha256
        self.logger = logging.getLogger(f"{self.project}.{self.service}.{self.name}")
        self.now = datetime.now().strftime(DATE_FORMAT)

    def notify_error(self, message):
        self.logger.error(message)
        token = os.environ.get("NOTIFY_TOKEN")
        if token:
            url = f"https://www.studio73.es/mail/webhook/{token}"
            headers = {"Content-Type": "application/json; charset=UTF-8"}
            body = f"""
<b>Rolling update error</b><br/>
<b>Server</b> {self.server_name}<br/>
<b>Project</b> {self.project}<br/>
<b>Service</b> {self.service}<br/>
<b>Name</b> {self.name}<br/>
<i>{message}</i>
"""
            params = {
                "body": body,
            }
            requests.post(url, headers=headers, json={"params": params})
        return 75

    def scale(self, replicas):
        self.logger.info(f"Scaling to {replicas} replicas")
        self.compose.up(
            [self.service],
            scales={self.service: replicas},
            detach=True,
            recreate=False,
            quiet=True,
            wait=True,
        )

    def update(self):
        replicas = int(self.labels.get("dodoo.replicas", "1"))
        containers = self.compose.ps([self.service])
        if len(containers) > replicas:
            health = (
                containers[-1].state.health
                and containers[-1].state.health.status
                or "none"
            )
            if health != "healthy":
                self.logger.warning(
                    f"Skipping, another update "
                    f"process is running ({', '.join([c.name for c in containers])})"
                )
                return 75
            self.scale(replicas)
        self.compose.pull(self.service)
        latest_image = docker.image.list(self.image)[0].id
        if self.sha256 == latest_image:
            self.logger.info(f"Up to date ({self.sha256})")
            return True
        # TODO: Stop cron jobs container
        pre_hook = self.labels.get("dodoo.hooks.pre-update", "odoo-update")
        if pre_hook not in NEG:
            # "dodoo.hooks.pre-update=False" to disable odoo-update script
            self.logger.info(f"Running pre-update hook ({pre_hook})")
            iterator = self.compose.run(
                self.service,
                pre_hook.split(),
                remove=True,
                tty=False,
                stream=True,
                labels={"traefik.enable": "false"},
            )
            try:
                logfile = f"{LOGDIR}/{self.now}-{self.name}-pre.log"
                self.logger.info(f"Writting process to {logfile}")
                with open(logfile, "w") as f:
                    for _, stream_bytes in iterator:
                        decoded = stream_bytes.decode()
                        f.write(decoded)
            except DockerException:
                return self.notify_error(
                    f"An error ocurred during pre-update hook ({pre_hook})"
                )
        try:
            self.scale(replicas * 2)
            self.logger.info(f"Scaling down to {replicas} replicas")
            docker.stop(containers, 30)
            docker.remove(containers)
        except DockerException:
            return self.notify_error("An error ocurred during scaling replicas")
        post_hook = self.labels.get("dodoo.hooks.post-update", "").split()
        if post_hook:
            self.logger.info(f"Running post-update hook ({' '.join(post_hook)})")
            iterator = self.compose.run(
                self.service,
                post_hook,
                remove=True,
                tty=False,
                labels={"traefik.enable": "false"},
            )
            try:
                logfile = f"/data/log/{self.now}-{self.name}-post.log"
                self.logger.info(f"Writting process to {logfile}")
                with open(logfile, "w") as f:
                    for _, stream_bytes in iterator:
                        decoded = stream_bytes.decode()
                        f.write(decoded)
            except DockerException:
                return self.notify_error(
                    f"An error ocurred during post-update hook ({post_hook})"
                )
        return True


def gather():
    logger = logging.getLogger("gather")
    containers = []
    for project in docker.compose.ls():
        compose = DockerClient(
            compose_project_name=project.name, compose_files=project.config_files
        ).compose
        is_abs = os.path.isabs(project.config_files[0])
        if not is_abs:
            logger.debug(
                f"{project.name} - Ignored because compose config_file "
                f"is not an absolute path ({project.config_files[0]})"
            )
            continue
        for service, service_config in compose.config().services.items():
            labels = service_config.labels
            enable = labels.get("dodoo.enable") in POS
            if not enable:
                continue
            try:
                ctrs = compose.ps([service])
            except NoSuchService:
                logger.debug(f"{project.name}.{service} - Service not found")
                continue
            if not ctrs:
                logger.debug(f"{project.name}.{service} - Running containers not found")
                continue
            ctr = ctrs[0]
            if ctr.state.health is None:
                logger.debug(
                    f"{project.name}.{service}.{ctr.name} - "
                    "Ignored because Docker healthcheck not implemented"
                )
                continue

            image_name = ctr.config.labels.get("com.docker.compose.image")
            container = DodooContainer(
                ctr.name,
                project.name,
                compose,
                service,
                labels,
                service_config.image,
                image_name,
            )
            containers.append(container)
    if containers:
        for container in containers:
            container.update()
        docker.image.prune(all=True)
    return True


def rotate():
    logger = logging.getLogger("rotate")
    cut_off_date = datetime.now() - timedelta(days=7)
    for log in os.listdir(LOGDIR):
        try:
            create_date = datetime.strptime(log.split("_")[0], "%Y-%m-%d")
            if create_date < cut_off_date:
                logger.debug(f"Removing {LOGDIR}/{log}")
                os.remove(f"{LOGDIR}/{log}")
        except ValueError:
            pass
    return True


if __name__ == "__main__":
    if not os.path.exists(LOGDIR):
        os.mkdir(LOGDIR)
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        gather,
        CronTrigger.from_crontab("*/15 7-20 * * mon-fri"),
        next_run_time=datetime.now(),
    )
    scheduler.add_job(
        rotate,
        CronTrigger.from_crontab("10 0 * * mon-fri"),
        next_run_time=datetime.now(),
    )
    try:
        scheduler.start()
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
