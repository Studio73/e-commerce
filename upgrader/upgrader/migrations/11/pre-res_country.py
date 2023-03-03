# (c) Studio73 - Pablo Fuentes <pablo@studio73.es>


def migrate(cr):
    # Delete or mark as legacy all states created by hand.
    cr.execute(
        """
        DELETE FROM res_country_state WHERE id NOT IN
            (SELECT res_id FROM ir_model_data WHERE model = 'res.country.state')
            AND id NOT IN (SELECT state_id FROM res_partner WHERE state_id IS NOT null);
        UPDATE res_country_state SET code = code || '_' || 'legacy' WHERE id NOT IN
            (SELECT res_id FROM ir_model_data WHERE model = 'res.country.state');
    """
    )
