from frappe.model.naming import make_autoname
import frappe
from frappe.model.document import Document
from frappe.utils import cstr, flt, getdate, new_line_sep, nowdate, add_days
from frappe.model.mapper import get_mapped_doc
import logging


@frappe.whitelist()
def size_filter(item_code="x"):
    if item_code == 'x':
        item_codex = "CTS.222.C3039.39"
        doc1 = frappe.get_doc('Item', item_codex)
        price_list = frappe.get_doc('Item Price',{"selling":1,"item_code":item_codex})
        doc2 = frappe.get_doc('Finished901ItemQtySummary')
        doc2 = [x.available_items for x in doc2.total_item_count_in_warehouse if x.item_code == item_codex]
        #reserved_qty2 = get_reserved_qty2(item_code)+int(qty)+get_reserved_qty4(item_code)
        qty_MRI = get_value_of_quantity_of_Material_Request_Item(item_code)
        qty_SOI = get_value_of_quantity_of_Sales_Order_Item(item_code)
        #reserved_qty2 = get_value_of_actual_available_quantity(item_code) - 1
        reserved_qty2 = doc2[0] - qty_MRI - qty_SOI - 1 - get_reserved_qty4(item_code)
        return doc1.invent_size_id,price_list.price_list_rate,'', reserved_qty2
    else:
        doc1 = frappe.get_doc('Item', item_code)
        price_list = frappe.get_doc('Item Price',{"selling":1,"item_code":item_code})
        doc2 = frappe.get_doc('Finished901ItemQtySummary')
        doc2 = [x.available_items for x in doc2.total_item_count_in_warehouse if x.item_code == item_code]
        #reserved_qty2 = get_reserved_qty2(item_code)+int(qty)+get_reserved_qty4(item_code)
        qty_MRI = get_value_of_quantity_of_Material_Request_Item(item_code)
        qty_SOI = get_value_of_quantity_of_Sales_Order_Item(item_code)
        #reserved_qty2 = get_value_of_actual_available_quantity(item_code) - 1
        reserved_qty2 = doc2[0] - qty_MRI - qty_SOI - 1 - get_reserved_qty4(item_code)
        return doc1.invent_size_id,price_list.price_list_rate, doc2[0] if len(doc2) > 0 else '', reserved_qty2

@frappe.whitelist()
def actual_qty_delivery_date(item_code,qty):
    reserved_qty3 = 0
    doc1 = frappe.get_doc('Item', item_code)
    doc2 = frappe.get_doc('Finished901ItemQtySummary')
    doc2 = [x.available_items for x in doc2.total_item_count_in_warehouse if x.item_code == item_code]
    reserved_qty2 = int(qty)+get_reserved_qty4(item_code)+get_value_of_quantity_of_Material_Request_Item(item_code)+get_value_of_quantity_of_Sales_Order_Item(item_code)
    reserved_qty3 = reserved_qty3+doc2[0]-reserved_qty2

    return doc1.invent_size_id,reserved_qty3

@frappe.whitelist()
def get_summary_sales_order(doc):
    return frappe.db.sql("""select parent,image,item_name,description,uom,sum(qty) quantity,rate,discount_amount,sum(amount) amount from `tabSales Order Item` where parent = %s group by parent,item_name""",(doc.name),as_dict=True)


def get_reserved_qty4(item_code):
    """warehouse is hard coded as per Mr. Albert's instructions"""
    warehouse = "Delivery Area - ISS"
    sql = "select distinct b.reserved_qty FROM `tabItem` a LEFT JOIN `tabBin` b ON a.item_code = b.item_code LEFT JOIN `tabSales Order Item` c ON a.item_code = c.item_code LEFT JOIN `tabItem Price` d ON a.item_code = d.item_code where a.item_code = '{0}' and b.warehouse = '{1}'".format(item_code,warehouse)
    reserved_qty = frappe.db.sql(sql)
    return flt(reserved_qty[0][0]) if reserved_qty else 0

def cancel_update(doc,method):
    """Material Request belongs to Finished warehouse then item count will be reversed."""
    update_cancel_material_request(doc,action="cancel")

def update_cancel_material_request(doc,action):
    for item in doc.items:
        sql = "update `tabSales Order Item` set actual_available_qty = actual_available_qty + qty, qty = 0 where name = '{0}'".format(item.name)
        query = frappe.db.sql(sql)
        frappe.db.commit()

def get_value_of_quantity_of_Material_Request_Item(item_code):
    """warehouse is hard coded as per Mr. Albert's instructions"""
    warehouse = "Delivery Area - ISS"
    sql = "select sum(qty) qty from `tabMaterial Request Item` where item_code = '{0}'".format(item_code)
    reserved_qty = frappe.db.sql(sql)
    return flt(reserved_qty[0][0]) if reserved_qty else 0

def get_value_of_quantity_of_Sales_Order_Item(item_code):
    """warehouse is hard coded as per Mr. Albert's instructions"""
    warehouse = "Delivery Area - ISS"
    sql = "select sum(qty) qty from `tabSales Order Item` where item_code = '{0}'".format(item_code)
    reserved_qty = frappe.db.sql(sql)
    return flt(reserved_qty[0][0]) if reserved_qty else 0
