from frappe.model.naming import parse_naming_series
import frappe
from frappe.model.document import Document


def autoname(doc,method):
    if doc.is_new():
        doc.name = make_autoname(doc.item_group_name+"-"+doc.item_group_description)

def make_autoname(key="", doctype="", doc=""):
	if key == "hash":
		return frappe.generate_hash(doctype, 10)

	parts = key.split('.')
	n = parse_naming_series(parts, doctype, doc)
	return n
