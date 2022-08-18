from frappe.model.naming import make_autoname
import frappe
from frappe.model.document import Document
from frappe.utils import cstr, flt, getdate, new_line_sep, nowdate, add_days
from frappe.model.mapper import get_mapped_doc
from frappe.utils import flt
import logging


@frappe.whitelist()
def size_filter(item_code,warehouse,qty):
    doc1 = frappe.get_doc('Item', item_code)
    price_list = frappe.get_doc('Item Price',{"selling":1,"item_code":item_code})
    doc2 = frappe.get_doc('Finished901ItemQtySummary')
    doc2 = [x.available_items for x in doc2.total_item_count_in_warehouse if x.item_code == item_code]
    reserved_qty2 = get_reserved_qty2(item_code,warehouse)+int(qty)+get_reserved_qty4(item_code)
    return doc1.invent_size_id,price_list.price_list_rate, doc2[0] if len(doc2) > 0 else '', reserved_qty2

@frappe.whitelist()
def actual_available_qty_schedule_date(item_code,warehouse,schedule_date,actual_available_qty,qty):
    reserved_qty3 = 0
    reserved_qty2 = get_reserved_qty2(item_code,warehouse)+int(qty)
    doc1 = frappe.get_doc('Item', item_code)
    if (get_reserved_qty3(item_code,warehouse,schedule_date,actual_available_qty,qty) > 0):
        reserved_qty3 = reserved_qty3 + int(actual_available_qty) - int(qty) + get_reserved_qty4(item_code)

    else:
        doc2 = frappe.get_doc('Finished901ItemQtySummary')
        doc2 = [x.available_items for x in doc2.total_item_count_in_warehouse if x.item_code == item_code]
        reserved_qty3 = doc2[0] - reserved_qty2

    return doc1.invent_size_id,reserved_qty3


@frappe.whitelist()
def make_stock_entry(source_name, target_doc=None):

    doclist = get_mapped_doc("Sales Order", source_name, {
        "Sales Order": {
            "doctype": "Stock Entry", },
        "Sales Order Item": {
            "doctype": "Stock Entry Detail",
        },
    }, target_doc)

    return doclist

def update_cancel_material_request(doc,action):
    for item in doc.items:
        sql = "update `tabMaterial Request Item` set actual_available_qty = actual_available_qty + qty where name = '{0}'".format(item.name)
        query = frappe.db.sql(sql)
        frappe.db.commit()


@frappe.whitelist()
def get_summary_sales_order(doc):
    return frappe.db.sql("""select parent,image,item_name,description,uom,sum(qty) quantity,rate,discount_amount,sum(amount) amount from `tabSales Order Item` where parent = %s group by parent,item_name""",(doc.name),as_dict=True)

def get_reserved_qty2(item_code, warehouse):
    """warehouse is hard coded as per Mr. Albert's instructions"""
    reserved_qty = frappe.db.sql("""
		select
			sum(reserved_qty) as reserved_qty
		from `tabBin` where item_code = %s and SUBSTRING(warehouse,1,3) =%s""", (item_code, '901'))
    return flt(reserved_qty[0][0]) if reserved_qty else 0

def get_reserved_qty3(item_code, warehouse, schedule_date, actual_available_qty,qty):
    """warehouse is hard coded as per Mr. Albert's instructions"""
    sql = "select actual_available_qty from `tabMaterial Request Item` where item_code = '{0}' and warehouse = '{1}' and schedule_date = '{2}' and actual_available_qty = {3}".format(item_code,warehouse,schedule_date,actual_available_qty)
    reserved_qty = frappe.db.sql(sql)
    FORMAT = '%(asctime)s %(clientip)-15s %(user)-8s %(message)s'
    logging.basicConfig(format=FORMAT)
    logging.warning('Checking for Query %s',sql)
    return flt(reserved_qty[0][0]) if reserved_qty else 0

def get_reserved_qty4(item_code):
    """warehouse is hard coded as per Mr. Albert's instructions"""
    sql = "select b.reserved_qty FROM `tabItem` a LEFT JOIN `tabBin` b ON a.item_code = b.item_code LEFT JOIN `tabSales Order Item` c ON a.item_code = c.item_code LEFT JOIN `tabItem Price` d ON a.item_code = d.item_code where a.item_code = '{0}'".format(item_code)
    reserved_qty = frappe.db.sql(sql)
    FORMAT = '%(asctime)s %(clientip)-15s %(user)-8s %(message)s'
    logging.basicConfig(format=FORMAT)
    logging.warning('Checking for Query %s',sql)
    return flt(reserved_qty[0][0]) if reserved_qty else 0

def cancel_update(doc,method):
    """Material Request belongs to Finished warehouse then item count will be reversed."""
    update_cancel_material_request(doc,action="cancel")

def submit_material_request(doc,method):
    """Material Request belongs to Finished warehouse then item count will be reversed."""
    for item in doc.items:
        sql = "update `tabMaterial Request Item` set actual_available_qty = actual_available_qty - qty + 1 where name = '{0}'".format(item.name)
        query = frappe.db.sql(sql)
        frappe.db.commit()
