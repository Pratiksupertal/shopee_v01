import frappe
from urllib.parse import urlparse, parse_qs

from shopee_v01.api.v1.helpers import format_result
from shopee_v01.api.v1.helpers import validate_filter_field


@frappe.whitelist()
def filter_picklist_for_manufacture():
    """Filter Pick List for Warehouse App Manufacture
    Filter includes: docstatus (0/1/2), purpose, is_external (0/1)
    """
    try:
        url = frappe.request.url
        docstatus = parse_qs(urlparse(url).query).get('docstatus')
        purpose = parse_qs(urlparse(url).query).get('purpose')
        is_external = parse_qs(urlparse(url).query).get('is_external')

        sql = """SELECT
            pl.name AS pick_list,
            pl.purpose AS purpose,
            pl.work_order AS work_order,
            pl.docstatus AS pick_list_status,
            pl.picker AS picker,
            (SELECT full_name FROM `tabUser`
                WHERE name=pl.picker) AS picker_name,
            (SELECT COUNT(*) FROM `tabPick List Item`
                WHERE parent=pl.name and parentfield='locations') AS total_product,
            (SELECT SUM(qty) FROM `tabPick List Item`
                WHERE parent=pl.name and parentfield='locations') AS total_qty,
            (SELECT (SUM(qty)-SUM(picked_qty)) FROM `tabPick List Item`
                WHERE parent=pl.name and parentfield='locations') AS total_picked_qty,
            mwo.name AS main_work_order,
            mwo.spk_date AS spk_date,
            mwo.expected_finish_date AS mwo_expected_finish_date,
            mwo.owner AS mwo_created_by,
            (SELECT full_name FROM `tabUser`
                WHERE name=mwo.owner) AS mwo_created_by_name,
            mwo.supplier AS supplier,
            mwo.is_external AS is_external
        FROM
            `tabPick List` as pl
            JOIN `tabWork Order` as wo ON wo.name = pl.work_order
            JOIN `tabMain Work Order` as mwo ON mwo.name = wo.reference_main_work_order
        """

        docstatus = validate_filter_field(
            filterfield='docstatus',
            value=docstatus,
            datatype=int
        )
        if docstatus is not None:
            sql += " and pl.docstatus='%d'" % docstatus

        purpose = validate_filter_field(
            filterfield='purpose',
            value=purpose
        )
        if purpose:
            sql += " and pl.purpose='%s'" % purpose

        is_external = validate_filter_field(
            filterfield='is_external',
            value=is_external,
            datatype=int
        )
        if is_external is not None:
            sql += " and mwo.is_external='%d'" % is_external

        sql += ";"

        result = frappe.db.sql(sql, as_dict=True)

        return format_result(
            result=result,
            success=True,
            status_code=200,
            message='Data Found'
        )
    except Exception as e:
        return format_result(
            result=None,
            success=False,
            status_code=400,
            message=str(e)
        )
