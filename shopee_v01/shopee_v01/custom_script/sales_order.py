import frappe


@frappe.whitelist()
def size_filter(item_code):
    doc1 = frappe.get_doc('Item', item_code)
    doc2 = frappe.get_doc('Item Counter')
    doc2 = [x.available_items for x in doc2.total_item_count_in_warehouse if x.item_code == item_code]
    return doc1.invent_size_id, doc2[0] if len(doc2) > 0 else ''
