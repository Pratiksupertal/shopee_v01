import frappe
from frappe.model.document import Document
from frappe.utils import cstr, flt, getdate, new_line_sep, nowdate, add_days
from frappe.model.mapper import get_mapped_doc


@frappe.whitelist()
def make_stock_entry(source_name, target_doc=None):

    print('---------------->> Stock entry called from Material request -------')

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

    def set_missing_values(source, target):
        target.purpose = source.material_request_type
        if source.job_card:
            target.purpose = 'Material Transfer for Manufacture'

        if source.material_request_type == "Customer Provided":
            target.purpose = "Material Receipt"

        target.run_method("calculate_rate_and_amount")
        target.set_stock_entry_type()
        target.set_job_card_data()

    doclist = get_mapped_doc("Material Request", source_name, {
        "Material Request": {
            "doctype": "Stock Entry",
            "validation": {
                "docstatus": ["=", 1],
                "material_request_type": ["in", ["Material Transfer", "Material Issue", "Customer Provided"]]
            }
        },
        "Material Request Item": {
            "doctype": "Stock Entry Detail",
            "field_map": {
                "name": "material_request_item",
                "parent": "material_request",
                "uom": "stock_uom"
            },
            "postprocess": update_item,
            "condition": lambda doc: doc.ordered_qty < doc.stock_qty
        }
    }, target_doc, set_missing_values)

    return doclist
