#!/usr/bin/env python3
# (c) Studio73 - Pablo Fuentes <pablo@studio73.es>


def migrate(cr):
    cr.execute(
        """
        -- FIX: Almacenes sin stock.picking.type y da error al crear las nuevas rutas
        UPDATE stock_warehouse SET manufacture_to_resupply = 'f';
    """
    )
