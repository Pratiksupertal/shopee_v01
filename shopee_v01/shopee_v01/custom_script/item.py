import frappe
from frappe.model.document import Document



@frappe.whitelist()
def categories(doctype,value,field):
    return frappe.db.get_value(doctype,value,field)
