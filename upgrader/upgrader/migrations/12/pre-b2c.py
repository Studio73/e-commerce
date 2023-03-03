#!/usr/bin/env click-odoo
# (c) Studio73 - Pablo Fuentes <pablo@studio73.es>

env = env  # noqa: F821

# Remove B2C group to internal users
b2c_group = env.ref("sale.group_show_price_total").id
for user in env["res.users"].search([("share", "=", False)]):
    user.write({"groups_id": [(3, b2c_group)]})

env.cr.commit()
