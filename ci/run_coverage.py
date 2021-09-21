#!/usr/bin/python
# (c) Studio73 - Pablo Fuentes <pablo@studio73.es>
import dodoo_tools
from set_env import set_env


def main():
    set_env()
    return dodoo_tools.tests.coverage()


if __name__ == "__main__":
    main()
