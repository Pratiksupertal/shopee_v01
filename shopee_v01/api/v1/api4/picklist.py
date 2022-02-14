import frappe
from frappe import _

from shopee_v01.api.v1.helpers import *


@frappe.whitelist()
def pickList():
    submitted_pick_list = frappe.db.get_list('Pick List',
             filters={
                 'docstatus': 1
             },

             fields=['name']
      )
    stock_entry_pick_list = frappe.db.get_list('Stock Entry',
            filters={
                'pick_list': ['like', '%PICK%']
            },
            fields=['pick_list']
      )
    submitted_pick_list = [order.get('name') for order in submitted_pick_list]
    stock_entry_pick_list = [order.get('pick_list') for order in stock_entry_pick_list]
    result = [order for order in submitted_pick_list if order not in stock_entry_pick_list]
    return format_result(result=result, status_code=200, message='Data Found')


@frappe.whitelist()
def submit_picklist():
    data = validate_data(frappe.request.data)
    try:
        pick_list = frappe.get_doc('Pick List',data['picklist'])
        if pick_list.docstatus == 0 :
            pick_list.submit()
    except Exception as e:
        frappe.log_error(title="submit_picklist API",message =frappe.get_traceback())
        return format_result(success="False",status_code=500, message = "PickList is not Submitted")
    from  erpnext.stock.doctype.pick_list.pick_list import validate_item_locations
    validate_item_locations(pick_list)
    if frappe.db.exists('Stock Entry', {'pick_list': data['picklist'],'docstatus' :1 }):
        return format_result(success="False",status_code=500, message = "Stock Entry has been already created against this Pick List")
    stock_entry = frappe.new_doc('Stock Entry')
    stock_entry.pick_list = pick_list.get('name')
    stock_entry.purpose = pick_list.get('purpose') if pick_list.get('purpose') !="Delivery" else ""
    stock_entry.set_stock_entry_type()
    if pick_list.get('material_request'):
        stock_entry = update_stock_entry_based_on_material_request(pick_list, stock_entry)
    else:
        return format_result(success="False",status_code=500, message = "Stock Entry has been already created against this Pick List")
        return frappe.msgprint(_('Stock Entry for Sales Order linked Pick List cant be done'))
    stock_entry.set_incoming_rate()
    stock_entry.set_actual_qty()
    stock_entry.calculate_rate_and_amount(update_finished_item_rate=False)
    stock_entry.save()
    stock_entry.submit()
    return format_result(result={
            "stock_entry": stock_entry.name,
            "picklist": stock_entry.pick_list
        }, message="success", status_code=200)


@frappe.whitelist()
def pick_list_with_mtr_and_so():
    stock_entry_pick_list = frappe.db.get_list('Stock Entry',
            filters={
                'pick_list': ['like', '%PICK%']
            },
            fields=['pick_list']
      )
    stock_entry_pick_list = list(map(lambda order: order.get('pick_list'), list(stock_entry_pick_list)))

    pick_list_for_mtr = pick_list_with_mtr(stock_entry_pick_list)
    pick_list_for_so = pick_list_with_so(stock_entry_pick_list)
    return format_result(result={
        "pick_list_for_mtr": pick_list_for_mtr,
        "pick_list_for_so": pick_list_for_so
    }, status_code=200, message='Data Found')