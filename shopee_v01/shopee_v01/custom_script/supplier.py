from frappe.model.naming import make_autoname
import frappe
from frappe.model.document import Document
import json

@frappe.whitelist()
def available_credit(supplier):
    print("-------supplier doctype frappe call execcuted---------",supplier)
    # doc = frappe.get_doc('Purchase Order',{"supplier":supplier})
    # if(doc)
    sql = "select sum(total) as total from `tabPurchase Order` where supplier = '{0}' and status in ('To Bill','To Receive and Bill') ".format(supplier)
    res = frappe.db.sql(sql);
    # res = json.loads(res[0])
    print("========================================",type(res))

    print(res[0])
    return res[0]
