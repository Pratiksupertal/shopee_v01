from frappe.model.naming import make_autoname
import frappe
from frappe.model.document import Document

def autoname(doc,method):
    if doc.is_new():
        po_type = doc.po_type
        if po_type:
            print(po_type[0])
            a = po_type.split(" ")
            print("---------------------------")
            doc.name = make_autoname(a[1][0]+"PO" + "-.#####")
        else:
            doc.name = make_autoname("PO" + "-.#####")
    #shopee_v01.shopee_v01.custom_script.purchase_order.test
    #shopee_v01/shopee_v01/custom_script/purchase_order.js



@frappe.whitelist()
def cara_packing(template_name):
    doc = frappe.get_doc('Cara Packing Template',template_name)
    template = doc.template_text
    return template
