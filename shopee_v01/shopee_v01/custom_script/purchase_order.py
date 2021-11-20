from frappe.model.naming import make_autoname
import frappe
from frappe.model.document import Document
from frappe.utils import cstr, flt, getdate, new_line_sep, nowdate, add_days
from frappe.model.mapper import get_mapped_doc


def autoname(doc,method):
    if doc.is_new():
        po_type = doc.po_type
        potype_abbr = frappe.get_doc("PO Type", {"name": po_type})
        if po_type:
            doc.name = make_autoname(potype_abbr.abbreviation +".YYYY"+".MM."+ "-.####")
        else:
            doc.name = make_autoname("PO" +".YYYY.MM."+ "-.####")
    #shopee_v01.shopee_v01.custom_script.purchase_order.test
    #shopee_v01/shopee_v01/custom_script/purchase_order.js

@frappe.whitelist()
def warehouse_filter(supplier):
    doc = frappe.get_doc('Supplier',supplier)
    supplier_group = doc.supplier_group
    mapper = frappe.get_doc('Supplier Group  Warehouse Mapping')
    warehouse_list = []
    for row in mapper.warehouse_mapping:
        if row.supplier_id == supplier_group:
            warehouse_list.append(row.warehouse_id)

    # mapper = frappe.db.get_single_value("Supplier Group Warehouse Mapping","warehouse_mapping")
    return warehouse_list,supplier_group


@frappe.whitelist()
def cara_packing(template_name):
    doc = frappe.get_doc('Cara Packing Template',template_name)
    template = doc.template_text
    return template

@frappe.whitelist()
def size_filter(item_code):
    doc = frappe.get_doc('Item', item_code)
    return doc.invent_size_id


@frappe.whitelist()
def make_stock_entry(source_name, target_doc=None):

    doclist = get_mapped_doc("Purchase Order", source_name, {
        "Purchase Order": {
            "doctype": "Stock Entry",},
        "Purchase Order Item": {
            "doctype": "Stock Entry Detail",
        }
    }, target_doc)

    return doclist


@frappe.whitelist()
def make_stock_entry_material_request(source_name, target_doc=None):

    doclist = get_mapped_doc("Purchase Order", source_name, {
        "Purchase Order": {
            "doctype": "Material Request",},
        "Purchase Order Item": {
            "doctype": "Material Request Item",
        }
    }, target_doc)

    return doclist

