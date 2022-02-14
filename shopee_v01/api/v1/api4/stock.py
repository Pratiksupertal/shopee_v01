import frappe
import datetime as dt

from shopee_v01.api.v1.helpers import *


@frappe.whitelist()
def stockOpname():
    data = validate_data(frappe.request.data)
    new_doc = frappe.new_doc('Stock Entry')
    new_doc.start_time = data['start_datetime']
    new_doc.end_time = data['end_datetime']
    new_doc._comments = data['notes']
    new_doc.modified_by = data['create_user_id']

    new_doc.purpose = 'Material Receipt'
    new_doc.set_stock_entry_type()
    for item in data['products']:
        new_doc.append("items", {
            "item_code": item['product_code'],
            "qty": item['quantity'],
            "t_warehouse": data['warehouse_stockopname_id']
        })

    new_doc.insert()

    return {
        "success": True,
        "message": "Data created",
        "status_code": 200,
    }


@frappe.whitelist()
def stockOpnames():
    fields = [
        'idx',
        'warehouse',
        'creation',
        '_comments',
        'posting_date',
        'posting_time',
        'modified_by'
    ]

    product_list = frappe.get_list('Stock Ledger Entry', fields=fields)

    result = []

    for i in product_list:
        temp_dict = {
            "id": str(i['idx']),
            "warehouse_id": i['warehouse'],
            "warehouse_area_id": None,
            "start_datetime": dt.datetime.combine(i['posting_date'],
                                                  (dt.datetime.min + i['posting_time']).time()
                                                  ),
            "end_datetime": None,
            "notes": i['_comments'],
            "create_user_id": i['modified_by'],
            "create_time": i['creation']
        }

        result.append(temp_dict)

    return format_result(result=result, status_code=200, message='Data Found')


@frappe.whitelist()
def update_current_stock():
    try:
        data = validate_data(frappe.request.data)
        doc = frappe.get_doc("Pick List",data['picklist'])
        doc.set_item_locations(save=True)
        return format_result(message="success", status_code=200)
    except Exception as e:
        frappe.log_error(title="update_current_stock API",message =frappe.get_traceback())
        return e