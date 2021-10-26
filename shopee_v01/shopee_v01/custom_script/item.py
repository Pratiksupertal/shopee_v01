import frappe
from frappe.model.document import Document

def validate(doc,method):
    if(doc.__islocal):
        sql = "select barcode from `tabItem Barcode` order by creation desc limit 1".format(doc.item_code)
        pre_barcode = frappe.db.sql(sql,as_dict=True)
        barcode = int(pre_barcode[0].barcode)+1
        if len(pre_barcode)>0:
            doc.append("barcodes",{
            "barcode":str(barcode)
            })
        else:
            doc.append("barcodes",{
            "barcode":"1000001"
            })


@frappe.whitelist()
def categories(doctype,value,field):
    return frappe.db.get_value(doctype,value,field)

@frappe.whitelist()
def barcode(code):
    return str(code)
