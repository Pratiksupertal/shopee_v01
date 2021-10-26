from frappe.model.naming import make_autoname
import frappe
from frappe.model.document import Document
from frappe.utils import cstr, flt, getdate, new_line_sep, nowdate, add_days
from frappe.model.mapper import get_mapped_doc


@frappe.whitelist()
def make_stock_entry(source_name, target_doc=None):
    doclist = get_mapped_doc("Delivery Note", source_name, {
        "Delivery Note": {
            "doctype": "Stock Entry",},
        "Delivery Note Item": {
            "doctype": "Stock Entry Detail",
        }
    }, target_doc)

    return doclist
