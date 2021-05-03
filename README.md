Dodoo: D(ocker)odoo
===================

Mandatory environment variables:

* `GIT_REPO`: URL to repository, e.g. https://github.com/Studio73/studio73-addons.git
* `ADMINPASSWORD`: self-explanatory
* `PGHOST`: self-explanatory
* `PGUSER`: self-explanatory
* `PGPASSWORD`: self-explanatory

Optional environment variables:

* `PGPORT`: self-explanatory - default 5432
* `DEV`: Block SMTP ports and other dev stuff
* `BLOCK_SMTP`: Block SMTP ports
* `DEBUGGER`: Enable `debug_odoo` script for debugging odoo throught vscode or pycharm
* `DEBUGGER_HOST`: self-explanatory
* `DEBUGGER_HOST`: self-explanatory
* `DEMO`: When creating database do it with demo data
* `LANG`: When creating database do it with the selected language
* `ODOO_REPO`: URL for Odoo repository - default Github Odoo URL
* `GITHUB_TOKEN`: Github token
* `S3_URL`: S3 storage url, e.g. s3.studio73.es
* `S3_USER`: S3 storage user
* `S3_SECRET`: S3 storage secret
* `GIT_IDENTITY_FILE`:  Selects a file from which the identity (private key) for public key authentication is read
