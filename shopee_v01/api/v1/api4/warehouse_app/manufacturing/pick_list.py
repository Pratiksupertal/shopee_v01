import frappe
from urllib.parse import urlparse, parse_qs

from shopee_v01.api.v1.helpers import format_result
from shopee_v01.api.v1.helpers import validate_filter_field
from shopee_v01.api.v1.helpers import get_last_parameter


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

        sql = """
            SELECT
                pl.name AS pick_list,
                pl.purpose AS purpose,
                pl.work_order AS work_order,
                pl.docstatus AS pick_list_status,
                pl.picker AS picker,
                (SELECT full_name
                    FROM `tabUser`
                    WHERE name=pl.picker) AS picker_name,
                (SELECT COUNT(*)
                    FROM `tabPick List Item`
                    WHERE parent=pl.name and parentfield='locations')
                    AS total_product,
                (SELECT SUM(qty)
                    FROM `tabPick List Item`
                    WHERE parent=pl.name and parentfield='locations'
                    ) AS total_qty,
                (SELECT (SUM(qty)-SUM(picked_qty))
                    FROM `tabPick List Item`
                    WHERE parent=pl.name and parentfield='locations'
                    ) AS total_picked_qty,
                mwo.name AS main_work_order,
                mwo.spk_date AS spk_date,
                mwo.expected_finish_date AS mwo_expected_finish_date,
                mwo.owner AS mwo_created_by,
                (SELECT full_name
                    FROM `tabUser`
                    WHERE name=mwo.owner
                    ) AS mwo_created_by_name,
                mwo.supplier AS supplier,
                mwo.is_external AS is_external
            FROM
                `tabPick List` AS pl
                JOIN `tabWork Order` AS wo
                    ON wo.name = pl.work_order
                JOIN `tabMain Work Order` AS mwo
                    ON mwo.name = wo.reference_main_work_order
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


@frappe.whitelist()
def picklist_details_for_manufacture():
    """Pick List Details API
    To get details of pick list by picker so that they can pick item
    """
    try:
        pick_list = get_last_parameter(
            url=frappe.request.url,
            link='picklist_details_for_warehouse_app'
        )

        details = frappe.db.sql("""
            SELECT
                pl.name AS pick_list,
                pl.purpose AS purpose,
                pl.work_order AS work_order,
                pl.docstatus AS pick_list_status,
                pl.picker AS picker,
                pl.start_time AS picker_start_time,
                pl.end_time AS picker_end_time,
                mwo.name AS main_work_order,
                mwo.creation AS mwo_creation_time,
                mwo.spk_date AS mwo_spk_date,
                mwo.expected_finish_date AS mwo_expected_finish_date,
                mwo.transaction_date AS mwo_transaction_date,
                mwo.owner AS mwo_created_by,
                mwo.supplier AS supplier,
                mwo.is_external AS is_external,
                woid.art_no AS art_no
            FROM
                `tabPick List` as pl
                INNER JOIN `tabWork Order` AS wo
                    ON wo.name = pl.work_order
                INNER JOIN `tabMain Work Order` AS mwo
                    ON mwo.name = wo.reference_main_work_order
                INNER JOIN `tabWork Order Item Details` AS woid
                    ON woid.parent = wo.reference_main_work_order
            WHERE
                pl.name = %s
            LIMIT 1
        """.format(**{}), (pick_list), as_dict=True)

        if not details:
            raise Exception('Error in finding details.')

        items = frappe.db.sql("""
            SELECT
                item_code,
                item_name,
                qty,
                picked_qty,
                item_group,
                uom,
                warehouse
            FROM
                `tabPick List Item`
            WHERE
                parent = %s AND parentfield = 'locations'
        """.format(**{}), (pick_list), as_dict=True)

        details = details[0]
        details.picker_name = frappe.db.get_value(
            'User', details.picker, 'full_name')
        details.mwo_created_by_name = frappe.db.get_value(
            'User', details.mwo_created_by, 'full_name')
        details.items = items

        return format_result(
            result=details,
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
