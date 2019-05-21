Dodoo: D(ocker)odoo
===================

Mandatory environment variables:

* `GIT_REPO`: URL to repository, e.g. https://github.com/Studio73/studio73-addons.git
* `ODOO_VERSION`: Odoo version (8.0, 10.0, 12.0)

Available environment variables:

* `DEV`: Block SMTP ports
* `DEBUG`: Enable ptvsd for vscode debugging
* `DEMO`: When creating database do it with demo data
* `LANG`: When creating database do it with the selected language
* `ODOO_REPO`: URL for Odoo repository, default value is Github Odoo URL
* `ENTERPRISE`: Add Odoo entreprise addons to addons path
* `ENTERPRISE_REPO`: URL for Odoo enterprise repository, default value is our enterprise fork