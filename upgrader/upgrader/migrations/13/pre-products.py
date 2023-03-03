#!/usr/bin/env python3
# (c) Studio73 - Pablo Fuentes <pablo@studio73.es>


def migrate(cr):
    # Archivar productos con combinación duplicado con la ID mas alta
    query = """
    ALTER TABLE product_template_attribute_value ADD COLUMN attribute_id INT4;
    ALTER TABLE product_template_attribute_value ADD COLUMN attribute_line_id INT4;
    ALTER TABLE product_product ADD COLUMN combination_indices varchar;

    UPDATE product_template_attribute_value ptav
        SET attribute_line_id = ptal.id
        FROM product_template_attribute_line ptal
        JOIN product_attribute_value pav ON ptal.attribute_id = pav.attribute_id
        WHERE ptav.product_tmpl_id = ptal.product_tmpl_id
        AND ptav.product_attribute_value_id = pav.id;
    UPDATE product_template_attribute_value ptav
        SET attribute_id = ptal.attribute_id
        FROM product_template_attribute_line ptal
        WHERE ptav.attribute_line_id = ptal.id;

    UPDATE product_product pp
    SET combination_indices = grouped_pvc.indices
    FROM (
        SELECT pavppr.product_product_id,
            STRING_AGG(ptav.id::varchar, ',' ORDER BY ptav.id) indices
        FROM product_attribute_value_product_product_rel pavppr
        JOIN product_attribute_value pav
            ON pav.id = pavppr.product_attribute_value_id
        JOIN product_product pp ON pp.id = pavppr.product_product_id
        JOIN product_template_attribute_value ptav
            ON (ptav.product_attribute_value_id =
                pavppr.product_attribute_value_id
            AND pp.product_tmpl_id = ptav.product_tmpl_id
            AND ptav.attribute_id = pav.attribute_id)
        GROUP BY pavppr.product_product_id
    ) grouped_pvc
    WHERE grouped_pvc.product_product_id = pp.id;

    UPDATE product_product p set active = 'f'
    WHERE p.id > (
        SELECT MIN(id) FROM product_product p2
        WHERE p.product_tmpl_id = p2.product_tmpl_id
        AND p.combination_indices = p2.combination_indices
    );

    ALTER TABLE product_template_attribute_value DROP COLUMN attribute_id;
    ALTER TABLE product_template_attribute_value DROP COLUMN attribute_line_id;
    ALTER TABLE product_product DROP COLUMN combination_indices;
    """
    cr.execute(query)
