import frappe


@frappe.whitelist()
def size_filter(item_code):
    doc = frappe.get_doc('Item', item_code)
    return doc.invent_size_id
