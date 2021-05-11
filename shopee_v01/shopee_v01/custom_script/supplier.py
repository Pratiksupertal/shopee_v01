from frappe.model.naming import make_autoname
import frappe
from frappe.model.document import Document
import json

@frappe.whitelist()
def available_credit(supplier):
    sql = "select sum(total) as total from `tabPurchase Order` where supplier = '{0}' and status in ('To Bill','To Receive and Bill') ".format(supplier)
    res = frappe.db.sql(sql);
    return res[0]
