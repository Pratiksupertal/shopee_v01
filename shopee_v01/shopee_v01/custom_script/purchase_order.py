from frappe.model.naming import make_autoname
import frappe
from frappe.model.document import Document


def autoname(doc,method):
    if doc.is_new():
        po_type = doc.po_type
        if po_type:
            doc.name = make_autoname(po_type +".YYYY"+".MM."+ "-.####")
        else:
            doc.name = make_autoname("PO" +".YYYY.MM."+ "-.####")
    #shopee_v01.shopee_v01.custom_script.purchase_order.test
    #shopee_v01/shopee_v01/custom_script/purchase_order.js

@frappe.whitelist()
def warehouse_filter(supplier):
    print("---------------")


@frappe.whitelist()
def cara_packing(template_name):
    doc = frappe.get_doc('Cara Packing Template',template_name)
    template = doc.template_text
    return template
