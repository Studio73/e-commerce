from pathlib import Path

from setuptools import find_packages, setup

CURRENT_DIR = Path(__file__).parent


setup(
    name="odoo-upgrader",
    version="1.0.0",
    install_requires=(CURRENT_DIR / "requirements.txt").read_text().splitlines(),
    packages=find_packages(),
    license="MIT",
    python_requires=">=3.10, <4",
    entry_points={
        "console_scripts": ["odoo-upgrader=upgrader.__main__:main"],
    },
)
