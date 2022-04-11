import frappe
from urllib.parse import urlparse, parse_qs

from shopee_v01.api.v1.helpers import format_result


@frappe.whitelist()
def filter_picklist_for_manufacture():
    """Filter Pick List for Warehouse App Manufacture

    Filter includes
        - docstatus (0/1/2)
        - purpose
        - is_external (0/1)
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
            (SELECT full_name FROM `tabUser` WHERE name=pl.picker) AS picker_name,
            (SELECT COUNT(*) FROM `tabPick List Item` WHERE parent=pl.name) AS total_product,
            (SELECT SUM(qty) FROM `tabPick List Item` WHERE parent=pl.name) AS total_qty,
            (SELECT SUM(picked_qty) FROM `tabPick List Item` WHERE parent=pl.name) AS total_picked_qty,
            mwo.name AS main_work_order,
            mwo.spk_date AS spk_date,
            mwo.expected_finish_date AS mwo_expected_finish_date,
            mwo.owner AS mwo_created_by,
            (SELECT full_name FROM `tabUser` WHERE name=mwo.owner) AS mwo_created_by_name,
            mwo.supplier AS supplier,
            mwo.is_external AS is_external
        FROM
            `tabPick List` as pl,
            `tabMain Work Order` as mwo
        WHERE
            mwo.name=(SELECT reference_main_work_order FROM `tabWork Order` WHERE name=work_order)
        """

        if docstatus:
            sql += " and pl.docstatus='%d'" % int(docstatus[0])
        if purpose:
            sql += " and pl.purpose='%s'" % purpose[0]
        if is_external:
            sql += " and mwo.is_external='%d'" % int(is_external[0])
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
