import logging
import coloredlogs

from .cli import cli

logging.basicConfig(
    format="%(asctime)s %(levelname)s: %(message)s", level=logging.INFO,
)
coloredlogs.install(level=logging.INFO)

if __name__ == "__main__":
     cli()

# Test: python3 -m dodoo_tools ... ...