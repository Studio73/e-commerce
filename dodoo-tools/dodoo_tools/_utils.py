import os
import threading
import time
import sys
import getpass
import subprocess as sp
import glob

from contextlib import ContextDecorator

try:
    from subprocess import DEVNULL  # py3
except ImportError:
    DEVNULL = open(os.devnull, "wb")


class Cmd(object):
    def __init__(self, cmd, force_user):
        self.cmd = cmd
        self.force_user = (
            force_user if force_user != getpass.getuser() else False
        )
        self.out = None
        self.error = None
        self.returncode = None

    def run(self):
        cmd = self.cmd
        if self.force_user:
            cmd = ["gosu", self.force_user] + cmd
        try:
            p = sp.Popen(
                cmd, stdout=sp.PIPE, stderr=sp.PIPE, encoding="utf8"
            )  # py3
        except TypeError:
            p = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE)
        out, error = p.communicate()
        self.out = out
        self.error = error
        self.returncode = p.returncode
        return self.returncode


def run(cmd, force_user=False):
    c = Cmd(cmd, force_user)
    c.run()
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
            time.sleep(0.02)

    def show(self):
        idx = 0
        spinner = u"⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
        spinne_len = len(spinner) - 1
        self.stopped = False
        while self.should_run:
            sys.stdout.write(u"\r%s %s" % (spinner[idx], self.msg))
            sys.stdout.flush()
            time.sleep(0.05)
            idx = idx + 1 if idx < spinne_len else 0
        elapsed_time = round(self.stop_time - self.start_time, 2)
        if self.error:
            sys.stdout.write("\r! %s - %ss.\n" % (self.msg, elapsed_time))
            sys.stdout.flush()
            print("\n%s\n" % self.error_msg)
        else:
            sys.stdout.write("\r✔ %s - %ss.\n" % (self.msg, elapsed_time))
            sys.stdout.flush()
        self.stopped = True
        return True
