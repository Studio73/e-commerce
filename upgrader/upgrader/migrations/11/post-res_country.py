#!/usr/bin/env click-odoo
# (c) Studio73 - Pablo Fuentes <pablo@studio73.es>

env = env  # noqa: F821

states = {state.code: state for state in env["res.country.state"].search([])}
for state_code, legacy_state in states.items():
    if legacy_state.code.endswith("_legacy"):
        state = states.get(state_code.replace("_legacy", ""))
        if state:
            env.cr.execute(
                "UPDATE res_partner SET state_id = %s WHERE state_id = %s;",
                (state.id, legacy_state.id),
            )
            legacy_state.unlink()
        else:
            legacy_state.code = state_code.replace("_legacy", "")
env.cr.commit()
