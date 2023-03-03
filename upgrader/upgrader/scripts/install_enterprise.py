#!/usr/bin/env click-odoo
# (c) Studio73 - Pablo Fuentes <pablo@studio73.es>


env = env  # noqa: F821

responsive = env["ir.module.module"].search([("name", "=", "web_responsive")])
if responsive.state in ["installed", "to upgrade"]:
    responsive.button_immediate_uninstall()

enterprise = env["ir.module.module"].search([("name", "=", "web_enterprise")])
if enterprise.state != "installed":
    enterprise.button_immediate_install()
env.cr.commit()
