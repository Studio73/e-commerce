# Dodoo: D(ocker)odoo

## Environment variables

All environment variables starting with `ODOO_` will be used to build `.odoorc` file:

- `ODOO_ADMINPASSWORD`: Odoo admin password - default `changeme`

Mandatory Postgresql environment variables:

- `PGHOST`: Postgresql host - default `localhost`
- `PGUSER`: Postgresql user - default `odoo`
- `PGPASSWORD`: Postgresql password - default `changeme`
- `PGPORT`: Postgresql port - default `5432`

## Copier template usage:

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

### Intallation to existing repo

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
