import frappe
from frappe.model.document import Document

def validate(doc,method):
    sorted_location = []
    doc.sorted_locations = []
    sorted_location = sorted(doc.locations,key=lambda x:x.warehouse)
    for i in sorted_location:
        doc.append("sorted_locations", {
            "item_code":i.item_code,
            "item_name":i.item_name,
            "warehouse":i.warehouse,
            "qty":i.qty,
            "stock_qty":i.stock_qty
            })
