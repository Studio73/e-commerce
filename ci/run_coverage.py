#!/usr/bin/python
# (c) Studio73 - Pablo Fuentes <pablo@studio73.es>
import click
import dodoo_tools
from set_env import set_env


@click.command()
@click.option("-f", "--fail-under", default=50, type=int)
@click.argument("addons", default="")
@click.pass_context
def main(ctx, addons, fail_under):
    set_env()
    return ctx.invoke(dodoo_tools.tests.coverage, addons=addons, fail_under=fail_under)


if __name__ == "__main__":
    main()
