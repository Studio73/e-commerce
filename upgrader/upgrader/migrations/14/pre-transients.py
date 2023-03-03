# (c) Studio73 - Pablo Fuentes <pablo@studio73.es>
from psycopg2.extensions import AsIs


def migrate(cr):
    # Delete all transient models
    select_query = "SELECT model from ir_model where transient = 't'"
    cr.execute(select_query)
    for model in cr.fetchall():
        name = model[0].replace(".", "_")
        cr.execute("DELETE from %s", [AsIs(name)])
