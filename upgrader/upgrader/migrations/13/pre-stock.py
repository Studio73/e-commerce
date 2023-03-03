#!/usr/bin/env python3
# (c) Studio73 - Pablo Fuentes <pablo@studio73.es>


def migrate(cr):
    # Renombrar stock.production.lot duplicados
    query = """

    UPDATE stock_production_lot s SET name = name || '-' || id
    WHERE s.id > (
        SELECT MIN(id) FROM stock_production_lot s2
        WHERE s.name = s2.name
    );
    """
    cr.execute(query)
