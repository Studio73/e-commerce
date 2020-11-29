import os
import logging
import random
import string
import threading
import time
import sys
import getpass
import subprocess as sp
import glob
import click
from datetime import timedelta

try:
    from contextlib import ContextDecorator  # py3
except ImportError:
    from contextdecorator import ContextDecorator

    reload(sys)
    sys.setdefaultencoding("utf8")
try:
    from subprocess import DEVNULL  # py3
except ImportError:
    DEVNULL = open(os.devnull, "wb")

_logger = logging.getLogger(__name__)


class Cmd(object):
    def __init__(self, cmd, force_user):
        if not isinstance(cmd[0], list):
            cmd = [cmd]
        self.cmd = cmd
        self.force_user = force_user if force_user != getpass.getuser() else False
        self.out = None
        self.error = None
        self.returncode = None

    def run(self, check_call=True, stdout=sp.PIPE):
        p_out = None
        for idx, cmd in enumerate(self.cmd):
            p_stdout = stdout if idx == len(self.cmd) - 1 else sp.PIPE
            if self.force_user:
                cmd = ["gosu", self.force_user] + cmd
            try:
                p = sp.Popen(
                    cmd, stdin=p_out, stdout=p_stdout, stderr=sp.PIPE, encoding="utf8"
                )  # py3
            except TypeError:
                p = sp.Popen(cmd, stdin=p_out, stdout=p_stdout, stderr=sp.PIPE)
            p_out = p.stdout
        out, error = p.communicate()
        self.out = out and out.strip() or ""
        self.error = error
        self.returncode = int(p.returncode)
        if check_call and self.returncode != 0:
            raise sp.CalledProcessError(
                self.returncode,
                " | ".join([" ".join(cmd) for cmd in self.cmd]),
                self.error,
            )
        return self.returncode


def run(cmd, force_user=False, check_call=False, stdout=sp.PIPE):
    c = Cmd(cmd, force_user)
    c.run(check_call, stdout)
    return c


class echo(ContextDecorator):
    def __init__(self, msg):
        self.msg = msg
        self.should_run = True
        self.start_time = False
        self.stop_time = False
        self.stopped = True
        self.error = False
        self.error_msg = False

    def __enter__(self):
        self.start_time = time.time()
        t = threading.Thread(target=self.show)
        t.start()

    def __exit__(self, type, val, traceback):
        if self.stopped:
            return True
        self.stop_time = time.time()
        if type or val or traceback:
            self.error = True
            self.error_msg = val
        self.should_run = False
        while not self.stopped:
            time.sleep(0.05)

    def write(self, prefix, msg, keep=False, tme=None):
        if not tme:
            tme = round(time.time() - self.start_time, 2)
        h, m, s = map(float, str(timedelta(seconds=tme)).split(":"))
        h = "%sh " % int(h) if h else ""
        m = "%sm " % int(m) if m else ""
        s = "%05.2fs" % s
        suffix = ""
        if keep and sys.stdout.isatty():
            suffix = "\n"
        text = "%s %s - %s%s%s%s" % (prefix, msg, h, m, s, suffix)
        if sys.stdout.isatty():
            sys.stdout.write("\r%s" % text)
            sys.stdout.flush()
        else:
            if prefix == "!":
                _logger.error(text)
            else:
                _logger.info(text)

    def show(self):
        idx = 0
        spinner = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        spinne_len = len(spinner) - 1
        self.stopped = False
        while self.should_run:
            if sys.stdout.isatty():
                self.write(click.style(spinner[idx], fg="blue", bold=True), self.msg)
            time.sleep(0.05)
            idx = idx + 1 if idx < spinne_len else 0
        elapsed_time = round(self.stop_time - self.start_time, 2)
        prefix = ""
        msg = self.msg
        if sys.stdout.isatty():
            if self.error:
                prefix = click.style("!", fg="white", bg="red")
                msg = click.style(self.msg, fg="white", bg="red")
            else:
                prefix = click.style("✔", fg="green", bold=True)
        self.write(prefix, msg, True, elapsed_time)
        if self.error:
            print("\n%s\n" % self.error_msg)
        self.stopped = True
        return True


def copy(src, dest, msg=None, user="odoo"):
    if os.path.exists(src):
        if msg:
            with echo(msg):
                run(["cp", src, dest], user)
        else:
            run(["cp", src, dest], user)


def build_ssh_conf():
    if os.environ.get("DEV"):
        return True
    ssh_folder = os.path.join(os.environ["DATA"], ".ssh")
    identityfiles = glob.glob(os.path.join(ssh_folder, "*.pub"))
    if len(identityfiles):
        cfg = open(os.path.join(ssh_folder, "config"), "w+")
        for identityfile in identityfiles:
            if "id_rsa" in identityfile:
                continue
            identityfile = identityfile.replace(".pub", "")
            cfg.writelines(
                [
                    "Host %s github.com\n" % identityfile.split("/")[-1],
                    "\tHostName github.com\n",
                    "\tIdentityFile %s\n" % identityfile,
                ]
            )


def gen_password(length=18):
    return "".join(
        [random.choice(string.ascii_letters + string.digits) for n in range(length)]
    )
