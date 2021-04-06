import frappe
from frappe.model.document import Document

@frappe.whitelist()
def cara_packing(template_name):
    doc = frappe.get_doc('Cara Packing Template',template_name)
    template = doc.template_text
    return template
