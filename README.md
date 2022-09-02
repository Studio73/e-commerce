# Dodoo: D(ocker)odoo

## Environment variables

All environment variables starting with `ODOO_` will be used to build `.odoorc` file:

- `ODOO_ADMINPASSWORD`: Odoo admin password - default `changeme`

Mandatory Postgresql environment variables:

- `PGHOST`: Postgresql host - default `localhost`
- `PGUSER`: Postgresql user - default `odoo`
- `PGPASSWORD`: Postgresql password - default `changeme`
- `PGPORT`: Postgresql port - default `5432`

## Copier template usage

### Bootstrap new repo

```bash
pipx install copier
pipx install pre-commit
pipx ensure path

copier copy git@github.com:Studio73/dodoo awesome_repo
# Answer the questions
pre-commit install
git commit -am "[ADD] Dodoo template"

```

### Bootstrap existing repo

```bash
pipx install copier
pipx install pre-commit
pipx ensure path

cd awesome_repo
copier git@github.com:Studio73/dodoo .
# Answer the questions
git add .
git commit -am "[ADD] Dodoo template"
pre-commit install
pre-commit run -a
# Commit your changes following your team guidelines, like one commit per module
```

### Updating repo

```bash
cd your_awesomer_repo
copier update
# If you don't want to answer the questions again use: copier -f update
git add .
git commit -am "[UPD] Dodoo template"
```

## Development

### Installation

```bash
pip install --user invoke python-dotenv
mkdir -p ~/.config/dodoo/{data,backup}
```

Create environment file `.env`. This file can be located in the project directory (make
sure that is git ignored) or in a parent directory.

```bash
...
ODOO_LIST_DB=True
ODOO_LIMIT_MEMORY_HARD=46843545600
ODOO_LIMIT_MEMORY_SOFT=41474836480
ODOO_UNACCENT=True
ODOO_WORKERS=0
ODOO_MAX_CRON_THREADS=0
...
```

Available environment variables

- `NET`: docker network - default `bridge`
- `VOLUMES`: Comma separated relative path to `/opt/odoo/src` to mount as a volume into
  the container, e.g.: `oca/web,studio73/studio73-private-addons`
- `PORT`: Default port to publish, can be overwritten with `invoke ... --port=...` -
  default `8096`
- `DEBUGGER_PORT`: Debugger port to publish - default `5678`

### Usage

```bash
cd project
# List all available tasks
inv --list

# Start a bash into the project container
inv exec
# Run odoo
inv run
# Run odoo in dev mode
inv dev
# Run odoo with the debugger activated
inv debug
```
