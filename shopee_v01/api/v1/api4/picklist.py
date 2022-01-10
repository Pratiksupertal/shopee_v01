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


def update_stock_entry_based_on_material_request(pick_list, stock_entry):
    from  erpnext.stock.doctype.pick_list.pick_list import update_common_item_properties
    for location in pick_list.locations:
        target_warehouse = None
        if location.material_request_item:
            target_warehouse = frappe.get_value('Material Request Item',
				location.material_request_item, 'warehouse')
        item = frappe._dict()
        update_common_item_properties(item, location)
        item.t_warehouse = target_warehouse
        stock_entry.append('items', item)
    return stock_entry


def update_stock_entry_based_on_sales_order(pick_list, stock_entry):
    from  erpnext.stock.doctype.pick_list.pick_list import update_common_item_properties
    for location in pick_list.locations:
        target_warehouse = None
        item = frappe._dict()
        update_common_item_properties(item, location)
        item.t_warehouse = "Collecting Area Finish Good Out - ISS"
        stock_entry.append('items', item)
    return stock_entry


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
    

def pick_list_with_mtr(stock_entry_pick_list):
    """
    Filter by status - only Submitted PL allowed
    Filter by `material_request type` = [ Material Transfer | Manufacture | Material Issue ]
    Filter by Stock Entry - overlapped PL will be removed
    """
    pick_list = frappe.db.get_list('Pick List',
        filters={
            "docstatus": 1,
            "purpose": ["in", ["Material Transfer", "Material Transfer for Manufecture", "Manufacture", "Material Issue"]]
        },
        fields=["name", "purpose", "parent_warehouse"]
    )

    pick_list_for_mtr = {}
    for item in pick_list:
        pick_list_id = item.get('name')
        if not pick_list_id: continue
        # if the pick list is in the stock entry, we have to filter them out
        if pick_list_id in stock_entry_pick_list: continue
        pick_list_for_mtr[pick_list_id] = {}
        pick_list_for_mtr[pick_list_id]["type"] = item.get("purpose")
        pick_list_for_mtr[pick_list_id]["parent_warehouse"] = item.get("parent_warehouse")
        pick_list_for_mtr[pick_list_id]["items"] = frappe.db.get_list('Pick List Item',
            filters={
                "parent": pick_list_id
            },
            fields=["item_code", "item_name", "warehouse", "uom", "qty"]
        )
    return pick_list_for_mtr


def pick_list_with_so(stock_entry_pick_list):
    """
    For Sales Order
    """
    pick_list_items = frappe.db.get_list('Pick List Item',
             filters={
                'sales_order': ['like', 'SAL-ORD-%'],
                'docstatus': 1
             },
             fields=['parent', 'sales_order', 'item_code', 'item_name', 'warehouse', "uom", 'qty']
      )
    pick_list_for_so = {}
    for item in pick_list_items:
        pick_list_id = item.get('parent')
        if not pick_list_id: continue
        # if the pick list is in the stock entry, we have to filter them out
        if pick_list_id in stock_entry_pick_list: continue
        if pick_list_id not in pick_list_for_so:
            pick_list_for_so[pick_list_id] = {}
            pick_list_for_so[pick_list_id]["sales_order"] = item.get("sales_order")
            pick_list_for_so[pick_list_id]["items"] = []
        pick_list_for_so[pick_list_id]["items"].append({
            "item_code": item.get("item_code"),
            "item_name": item.get("item_name"),
            "warehouse": item.get("warehouse"),
            "uom": item.get("uom"),
            "qty": item.get("qty")
        })
    return pick_list_for_so


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