import frappe
from frappe.utils import now_datetime

from shopee_v01.api.v1.helpers import *


@frappe.whitelist()
def create_material_transfer_for_picklist():
    try:
        data = validate_data(frappe.request.data)
        pick_list = data.get("pick_list")
        picklist = frappe.get_doc("Pick List",pick_list)
        new_doc = frappe.new_doc('Stock Entry')
        new_doc.pick_list =pick_list
        new_doc.start_time = now_datetime()
        new_doc.end_time = now_datetime()
        new_doc.purpose = 'Material Transfer'
        new_doc.set_stock_entry_type()
        for item in picklist.locations:
            new_doc.append("items", {
                "item_code": item.item_code,
                "qty": item.qty,
                "s_warehouse":item.warehouse,
                "t_warehouse": data['t_warehouse']
            })

        new_doc.save()
        new_doc.submit()
        result = {
                    "Stock Entry":new_doc.name,
                    "Purpose":new_doc.purpose,
                    "Pick List":new_doc.pick_list
                }
        return format_result(result=result, success=True, status_code=200, message='Data Found')
    except Exception as e:
        return format_result(result=None, success=False, status_code=400, message=str(e))