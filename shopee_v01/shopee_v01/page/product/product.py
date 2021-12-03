from __future__ import unicode_literals
import frappe

@frappe.whitelist()
def product_list(item_code=None,item_group=None,division_group=None):
    print("========== product_list python ==========",item_code)
    item_data = {}
    item_list_raw = []
    # condition = " where 1=1 "
    filters = [
        ['docstatus', '<', '2']
    ]
    # item_list = frappe.get_list()
    if item_code:
        filters.append(['item_code', '=', item_code])
    if item_group:
        filters.append(['item_group','=',item_group])
    if division_group:
        filters.append(['division_group','=',division_group])
    print("---- filters : ",filters)
    fields = ['name as value','item_code','item_group','division_group','retail_group','size_group']
    item_list = frappe.get_list(doctype='Item', fields=fields, filters=filters, order_by='name')
    for row in item_list:
        item_list_raw.append([row.get('value'),row.get('item_code'),
        row.get('item_group'),row.get('division_group'),
        row.get('retail_group'),row.get('size_group')
        ])
    # item_list_raw.append()
    item_data["columns"]=["Item Name","Item Code","Item_group","Division Group","Retail Group","Size Group"]
    item_data["data"]=item_list_raw
    return item_data
