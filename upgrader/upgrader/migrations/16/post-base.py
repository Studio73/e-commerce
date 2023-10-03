#!/usr/bin/env click-odoo
# (c) Studio73 - Óscar Seguí <oscar@studio73.es>
env = env  # noqa


def migrate_attachment_checksum(env):
    attachment_ids = env['ir.attachment'].search([['mimetype', 'in', ['image/png', 'image/jpeg', 'image/gif']]])
    query = ""
    for attachment_ in attachment_ids:
        checksum = attachment_._compute_checksum(attachment_.datas)
        query += "UPDATE ir_attachment SET checksum = '%s' WHERE id = %s;" % (checksum, attachment_.id)
    if query:
        env.cr.execute(query)

migrate_attachment_checksum(env)
