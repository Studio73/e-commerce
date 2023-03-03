#!/usr/bin/env python3
# (c) Studio73 - Pablo Fuentes <pablo@studio73.es>


def migrate(cr):
    # FIX ProgrammingError: cannot change data type of view
    # column "total_attendance" from numeric to double precision
    cr.execute(
        """
        DROP VIEW IF EXISTS hr_timesheet_sheet_sheet_day CASCADE;
    """
    )
