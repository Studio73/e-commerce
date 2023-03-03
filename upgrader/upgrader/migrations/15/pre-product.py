# (c) Studio73 - Pablo Fuentes <pablo@studio73.es>


def migrate(cr):
    cr.execute(
        """
        UPDATE product_packaging SET name = 'P-' || id WHERE name IS null;
    """
    )
