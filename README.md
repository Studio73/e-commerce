Dodoo: D(ocker)odoo
===================

Mandatory environment variables:

* `GIT_REPO`: URL to repository, e.g. https://github.com/Studio73/studio73-addons.git
* `ADMINPASSWORD`: Odoo admin password
* `PGHOST`: Postgresql host
* `PGUSER`: Postgresql user
* `PGPASSWORD`: Postgresql password

Optional environment variables:

* `PGPORT`: Postgresql port - default 5432
* `BRANCH`: Custom branch, e.g. 14-dev - Default Odoo branch
* `DEV`: Block SMTP ports and other dev stuff
* `BLOCK_SMTP`: Block SMTP ports
* `DEBUGGER`: Enable `debug_odoo` script for debugging odoo throught debugpy or pycharm
* `DEBUGGER_HOST`: Custom debugger host - default debugpy 0.0.0.0, pycharm localhost
* `DEBUGGER_PORT`: Custom debugger port - default debugpy 5678, pycharm 12345
* `DEMO`: When creating database do it with demo data
* `LANG`: When creating database do it with the selected language
* `ODOO_REPO`: URL for Odoo repository - default Github Odoo URL
* `GITHUB_TOKEN`: Github token
* `S3_URL`: S3 storage url, e.g. s3.studio73.es
* `S3_USER`: S3 storage user
* `S3_SECRET`: S3 storage secret
* `GIT_IDENTITY_FILE`:  Selects a file from which the identity (private key) for public key authentication is read
