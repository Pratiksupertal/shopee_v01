import frappe
from frappe.utils import flt


@frappe.whitelist()
def size_filter(item_code=None):
    if not item_code:
        return None, 0, "N/A", "N/A"
    item_doc = frappe.get_doc('Item', item_code)
    price_list = frappe.get_doc('Item Price', {
        "selling": 1,
        "item_code": item_code
    })
    return item_doc.invent_size_id, price_list.price_list_rate, "N/A", "N/A"


@frappe.whitelist()
def actual_available_qty_schedule_date(item_code,qty):
    reserved_qty3 = 0
    doc1 = frappe.get_doc('Item', item_code)
    doc2 = frappe.get_doc('Finished901ItemQtySummary')
    doc2 = [x.available_items for x in doc2.total_item_count_in_warehouse if x.item_code == item_code]
    reserved_qty2 = int(qty)+get_reserved_qty4(item_code)+get_value_of_quantity_of_Material_Request_Item(item_code)+get_value_of_quantity_of_Sales_Order_Item(item_code)
    reserved_qty3 = reserved_qty3+doc2[0]-reserved_qty2
    return doc1.invent_size_id,reserved_qty3


def update_cancel_material_request(doc,action):
    for item in doc.items:
        sql = "update `tabMaterial Request Item` set actual_available_qty = actual_available_qty + qty, qty = 0 where name = '{0}'".format(item.name)
        query = frappe.db.sql(sql)
        frappe.db.commit()

def get_reserved_qty4(item_code):
    """warehouse is hard coded as per Mr. Albert's instructions"""
    warehouse = "Delivery Area - ISS"
    sql = "select distinct b.reserved_qty FROM `tabItem` a LEFT JOIN `tabBin` b ON a.item_code = b.item_code LEFT JOIN `tabSales Order Item` c ON a.item_code = c.item_code LEFT JOIN `tabItem Price` d ON a.item_code = d.item_code where a.item_code = '{0}' and b.warehouse = '{1}'".format(item_code,warehouse)
    reserved_qty = frappe.db.sql(sql)
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

def get_value_of_quantity_of_Material_Request_Item(item_code):
    """warehouse is hard coded as per Mr. Albert's instructions"""
    sql = "select sum(qty) qty from `tabMaterial Request Item` where item_code = '{0}'".format(item_code)
    reserved_qty = frappe.db.sql(sql)
    return flt(reserved_qty[0][0]) if reserved_qty else 0

def get_value_of_quantity_of_Sales_Order_Item(item_code):
    """warehouse is hard coded as per Mr. Albert's instructions"""
    sql = "select sum(qty) qty from `tabSales Order Item` where item_code = '{0}'".format(item_code)
    reserved_qty = frappe.db.sql(sql)
    return flt(reserved_qty[0][0]) if reserved_qty else 0

frappe.whitelist()
def get_material_request_sort(doc):
    return frappe.db.sql("""select item_code,item_group,qty,uom from `tabMaterial Request Item` where parent = %s order by item_code""",(doc.name),as_dict=True)

