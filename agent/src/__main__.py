import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Dict

import aiohttp
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from python_on_whales import DockerClient, docker
from python_on_whales.components.compose.cli_wrapper import ComposeCLI
from python_on_whales.exceptions import DockerException

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
        self.name: str = name
        self.project: str = project
        self.compose: ComposeCLI = compose
        self.service: str = service
        self.labels: Dict[str, str] = labels
        self.image: str = image
        self.sha256: str = sha256
        self.logger = logging.getLogger(f"{self.project}.{self.service}.{self.name}")
        self.now = datetime.now().strftime(DATE_FORMAT)

    async def notify_error(self, message):
        self.logger.error(message)
        gchat_url = os.environ.get("GCHAT_WEBHOOK")
        if gchat_url:
            # https://developers.google.com/chat/how-tos/webhooks
            headers = {"Content-Type": "application/json; charset=UTF-8"}
            async with aiohttp.ClientSession() as session:
                payload = f"""
*Rolling update error*
*Project* {self.project}
*Service* {self.service}
*Name* {self.name}
*Status* 🔴FAILED
_{message}_
                    """
                await session.post(gchat_url, headers=headers, json={"text": payload})
        return 75

    def scale(self, replicas):
        self.logger.info(f"Scaling to {replicas} replicas")
        self.compose.up(
            [self.service],
            scales={self.service: replicas},
            detach=True,
            recreate=False,
            quiet=True,
        )

    async def update(self):
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
                return await self.notify_error(
                    f"An error ocurred during pre-update hook ({pre_hook})"
                )
        try:
            self.scale(replicas + 1)
            await asyncio.sleep(1)
            new_container = self.compose.ps([self.service])[-1]
            health = new_container.state.health.status
            status_timeout = 0
            self.logger.info(f"Waiting {new_container.name} to be ready")
            while health != "healthy":
                await asyncio.sleep(1)
                status_timeout += 1
                if status_timeout >= 60:
                    return await self.notify_error(
                        f"Timeout exception waiting {new_container.name} to be ready"
                    )
                health = new_container.state.health.status
            self.scale(replicas)
        except DockerException:
            return await self.notify_error("An error ocurred during scaling replicas")
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
                return await self.notify_error(
                    f"An error ocurred during post-update hook ({post_hook})"
                )
        return True


async def gather():
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
            ctrs = compose.ps([service])
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
        await asyncio.gather(*[container.update() for container in containers])
        docker.image.prune(all=True)
    return True


async def rotate():
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


async def main():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(gather, "interval", minutes=15, next_run_time=datetime.now())
    rotate_next_run = datetime.now().replace(hour=0, minute=0) + timedelta(days=1)
    scheduler.add_job(rotate, "interval", hours=24, next_run_time=rotate_next_run)
    scheduler.start()


if __name__ == "__main__":
    try:
        if not os.path.exists(LOGDIR):
            os.mkdir(LOGDIR)
        loop = asyncio.get_event_loop_policy().get_event_loop()
        loop.create_task(main())
        loop.run_forever()
    except (KeyboardInterrupt, SystemExit):
        pass
