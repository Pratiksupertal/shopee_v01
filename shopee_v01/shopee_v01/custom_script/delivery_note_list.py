from __future__ import unicode_literals
import frappe
import json
from frappe.utils import flt, get_datetime, getdate, date_diff, cint, nowdate, get_link_to_form
# import frappe

@frappe.whitelist()
def update_table_delivery_note():
    entries = get_data_sales_order()
    for d in entries:
        update_delivery_note(d.delivery_note,d.sales_order)

def get_data_sales_order():
    return frappe.db.sql("""select dni.against_sales_order as sales_order,dn.name as delivery_note from `tabDelivery Note Item` dni inner join `tabDelivery Note` dn on dni.parent = dn.name and dni.against_sales_order is not null and dn.sales_order is null union select pli.sales_order as sales_order,dn.name as delivery_note from `tabPick List Item` pli inner join `tabDelivery Note` dn on pli.parent = dn.pick_list where dn.sales_order is null and pli.sales_order is not null""", as_dict=True)

def update_delivery_note(delivery_note,sales_order):
    frappe.db.sql("""update `tabDelivery Note` set sales_order= %s where name = %s""", (sales_order,delivery_note), debug=True)
    frappe.db.commit()
