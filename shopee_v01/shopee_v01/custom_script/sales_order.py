from frappe.model.naming import make_autoname
import frappe
from frappe.model.document import Document
from frappe.utils import cstr, flt, getdate, new_line_sep, nowdate, add_days
from frappe.model.mapper import get_mapped_doc


@frappe.whitelist()
def size_filter(item_code):
    doc1 = frappe.get_doc('Item', item_code)
    doc2 = frappe.get_doc('Finished901ItemQtySummary')
    doc2 = [x.available_items for x in doc2.total_item_count_in_warehouse if x.item_code == item_code]
    return doc1.invent_size_id, doc2[0] if len(doc2) > 0 else ''


@frappe.whitelist()
def make_stock_entry123(source_name, target_doc=None):
    print('---------------->> Stock entry called from Sales Order -------')

    def update_item(obj, target, source_parent):
        qty = flt(flt(obj.stock_qty) - flt(obj.ordered_qty)) / target.conversion_factor \
            if flt(obj.stock_qty) > flt(obj.ordered_qty) else 0
        target.qty = qty
        target.transfer_qty = qty * obj.conversion_factor
        target.conversion_factor = obj.conversion_factor

        if source_parent.material_request_type == "Material Transfer" or source_parent.material_request_type == "Customer Provided":
            target.t_warehouse = obj.warehouse
        else:
            target.s_warehouse = obj.warehouse

        if source_parent.material_request_type == "Customer Provided":
            target.allow_zero_valuation_rate = 1

    doclist = get_mapped_doc("Sales Order", source_name, {
        "Sales Order": {
            "doctype": "Stock Entry", },
        "Sales Order Item": {
            "doctype": "Stock Entry Detail",
        },
        "postprocess": update_item,
    }, target_doc)

    return doclist
