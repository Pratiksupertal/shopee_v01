from __future__ import unicode_literals
import frappe

@frappe.whitelist()
def product_list(item_code=None):
    print("product list function is called")
    item_data = {}
    item_list_raw = []
    # item_list = frappe.get_list()
    if item_code:
        filters = [
    		['docstatus', '<', '2'],
    		['item_code', '=', item_code]
    	]
    else:
        filters = [
    		['docstatus', '<', '2']
    	]
    fields = ['name as value','item_code','item_group','division_group','retail_group','size_group']
    item_list = frappe.get_list(doctype='Item', fields=fields, filters=filters, order_by='name')
    print("=======================================================")
    print(item_list)
    for row in item_list:
        item_list_raw.append([row.get('value'),row.get('item_code'),
        row.get('item_group'),row.get('division_group'),
        row.get('retail_group'),row.get('size_group')
        ])
    print("==================================")
    print(item_list_raw)
    # item_list_raw.append()

    return item_list_raw

@frappe.whitelist()
def test():
    print("--------- testing 1234 -----------------")
