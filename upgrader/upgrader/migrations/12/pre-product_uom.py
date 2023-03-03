# (c) Studio73 - Pablo Fuentes <pablo@studio73.es>


def migrate(cr):
    # Odoo 12 requires that every UoM category should have only 1 reference unit of measure
    select_query = """
SELECT id, category_id
FROM product_uom
WHERE uom_type = 'reference' and active='t'
ORDER BY id;
    """
    update_query = """
UPDATE product_uom
set uom_type = 'bigger'
WHERE id in %s
"""
    cr.execute(select_query)
    categs = {}
    for uom_id, categ_id in cr.fetchall():
        categs.setdefault(categ_id, []).append(uom_id)
    for _, uoms in categs.items():
        if len(uoms) > 1:
            cr.execute(
                update_query,
                [
                    tuple(uoms[1:]),
                ],
            )
    categ_without_reference = """
SELECT C.id AS category_id, count(U.id) AS uom_count
FROM product_uom_categ C
LEFT JOIN product_uom U ON C.id = U.category_id AND uom_type = 'reference' AND U.active = 't'
GROUP BY C.id order by category_id
"""
    cr.execute(categ_without_reference)
    for categ_id, uom_count in cr.fetchall():
        if uom_count == 0:
            cr.execute(
                "select id from product_uom "
                f"where uom_type = 'reference' and active = 'f' and category_id = {categ_id} "
                "limit 1"
            )
            uom_id = cr.fetchone()
            if uom_id:
                cr.execute("update product_uom set active = 't' where id = %s", uom_id)
            else:
                # Delete categories without any unit of measure
                cr.execute("DELETE from product_uom_categ where id = %s", (categ_id,))
