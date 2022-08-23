from frappe.model.naming import make_autoname
import frappe
from frappe.model.document import Document
from frappe.utils import cstr, flt, getdate, new_line_sep, nowdate, add_days
from frappe.model.mapper import get_mapped_doc
import logging


@frappe.whitelist()
def size_filter2(item_code):
    doc1 = frappe.get_doc('Item', item_code)
    price_list = frappe.get_doc('Item Price',{"selling":1,"item_code":item_code})
    doc2 = frappe.get_doc('Finished901ItemQtySummary')
    doc2 = [x.available_items for x in doc2.total_item_count_in_warehouse if x.item_code == item_code]
    reserved_qty = get_value_of_actual_available_quantity(item_code)
    return doc1.invent_size_id,price_list.price_list_rate, doc2[0] if len(doc2) > 0 else '', reserved_qty

@frappe.whitelist()
def size_filter(item_code,qty):
    doc1 = frappe.get_doc('Item', item_code)
    price_list = frappe.get_doc('Item Price',{"selling":1,"item_code":item_code})
    doc2 = frappe.get_doc('Finished901ItemQtySummary')
    doc2 = [x.available_items for x in doc2.total_item_count_in_warehouse if x.item_code == item_code]
    #reserved_qty2 = get_reserved_qty2(item_code)+int(qty)+get_reserved_qty4(item_code)
    FORMAT = '%(asctime)s %(clientip)-15s %(user)-8s %(message)s'
    logging.basicConfig(format=FORMAT)
    logging.warning('Checking checking nilai Qty %s',qty)
    qty_MRI = get_value_of_quantity_of_Material_Request_Item(item_code)
    qty_SOI = get_value_of_quantity_of_Sales_Order_Item(item_code)

    #reserved_qty2 = get_value_of_actual_available_quantity(item_code) - 1
    FORMAT = '%(asctime)s %(clientip)-15s %(user)-8s %(message)s'
    logging.basicConfig(format=FORMAT)
    logging.warning('Checking checking nilai qtyMRI %s',str(qty_MRI))
    FORMAT = '%(asctime)s %(clientip)-15s %(user)-8s %(message)s'
    logging.basicConfig(format=FORMAT)
    logging.warning('Checking checking nilai qty_SOI %s',str(qty_SOI))
    reserved_qty2 = doc2[0] - qty_MRI - qty_SOI - 1 - get_reserved_qty4(item_code)
    return doc1.invent_size_id,price_list.price_list_rate, doc2[0] if len(doc2) > 0 else '', reserved_qty2

@frappe.whitelist()
def actual_qty_delivery_date(item_code,parent,actual_available_qty,qty):
    reserved_qty3 = 0
    doc1 = frappe.get_doc('Item', item_code)
    doc2 = frappe.get_doc('Finished901ItemQtySummary')
    doc2 = [x.available_items for x in doc2.total_item_count_in_warehouse if x.item_code == item_code]
    reserved_qty2 = int(qty)+get_reserved_qty4(item_code)+get_value_of_quantity_of_Material_Request_Item(item_code)+get_value_of_quantity_of_Sales_Order_Item(item_code)
    reserved_qty3 = reserved_qty3+doc2[0]-reserved_qty2

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

@frappe.whitelist()
def get_summary_sales_order(doc):
    return frappe.db.sql("""select parent,image,item_name,description,uom,sum(qty) quantity,rate,discount_amount,sum(amount) amount from `tabSales Order Item` where parent = %s group by parent,item_name""",(doc.name),as_dict=True)


def get_reserved_qty(item_code, warehouse="Delivery Area - ISS"):
    """warehouse is hard coded as per Mr. Albert's instructions"""
    reserved_qty = frappe.db.sql("""
		select
			sum(dnpi_qty * ((so_item_qty - so_item_delivered_qty) / so_item_qty))
		from
			(
				(select
					qty as dnpi_qty,
					(
						select qty from `tabSales Order Item`
						where name = dnpi.parent_detail_docname
						and (delivered_by_supplier is null or delivered_by_supplier = 0)
					) as so_item_qty,
					(
						select delivered_qty from `tabSales Order Item`
						where name = dnpi.parent_detail_docname
						and delivered_by_supplier = 0
					) as so_item_delivered_qty,
					parent, name
				from
				(
					select qty, parent_detail_docname, parent, name
					from `tabPacked Item` dnpi_in
					where item_code = %s and warehouse = %s
					and parenttype="Sales Order"
					and item_code != parent_item
					and exists (select * from `tabSales Order` so
					where name = dnpi_in.parent and docstatus = 1 and status != 'Closed')
				) dnpi)
			union
				(select stock_qty as dnpi_qty, qty as so_item_qty,
					delivered_qty as so_item_delivered_qty, parent, name
				from `tabSales Order Item` so_item
				where item_code = %s and warehouse = %s
				and (so_item.delivered_by_supplier is null or so_item.delivered_by_supplier = 0)
				and exists(select * from `tabSales Order` so
					where so.name = so_item.parent and so.docstatus = 1
					and so.status != 'Closed'))
			) tab
		where
			so_item_qty >= so_item_delivered_qty
	""", (item_code, warehouse, item_code, warehouse))
    return flt(reserved_qty[0][0]) if reserved_qty else 0

def get_reserved_qty2(item_code):
    """warehouse is hard coded as per Mr. Albert's instructions"""
    reserved_qty = frappe.db.sql("""
		select
			sum(reserved_qty) as reserved_qty
		from `tabBin` where item_code = %s and SUBSTRING(warehouse,1,3) =%s""", (item_code, '901'))
    return flt(reserved_qty[0][0]) if reserved_qty else 0

def get_reserved_qty3(item_code, parent, actual_available_qty,qty):
    """warehouse is hard coded as per Mr. Albert's instructions"""
    sql = "select actual_qty from `tabSales Order Item` where item_code = '{0}' and parent = '{1}' and actual_available_qty = {2}".format(item_code,parent,actual_available_qty)
    reserved_qty = frappe.db.sql(sql)
    return flt(reserved_qty[0][0]) if reserved_qty else 0

def get_reserved_qty4(item_code):
    """warehouse is hard coded as per Mr. Albert's instructions"""
    warehouse = "Delivery Area - ISS"
    sql = "select distinct b.reserved_qty FROM `tabItem` a LEFT JOIN `tabBin` b ON a.item_code = b.item_code LEFT JOIN `tabSales Order Item` c ON a.item_code = c.item_code LEFT JOIN `tabItem Price` d ON a.item_code = d.item_code where a.item_code = '{0}' and b.warehouse = '{1}'".format(item_code,warehouse)
    reserved_qty = frappe.db.sql(sql)
    return flt(reserved_qty[0][0]) if reserved_qty else 0

def get_value_of_actual_available_quantity(item_code):
    """warehouse is hard coded as per Mr. Albert's instructions"""
    warehouse = "Delivery Area - ISS"
    sql = "select actual_available_qty,schedule_date from `tabMaterial Request Item` where item_code = '{0}' order by creation desc limit 1".format(item_code)
    reserved_qty = frappe.db.sql(sql)
    FORMAT = '%(asctime)s %(clientip)-15s %(user)-8s %(message)s'
    logging.basicConfig(format=FORMAT)
    logging.warning('Checking for Query %s',sql)
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
    sql = "select sum(qty) qty from `tabMaterial Request Item` where item_code = '{0}' and substring(warehouse,1,3) = '{1}'".format(item_code,'901')
    reserved_qty = frappe.db.sql(sql)
    FORMAT = '%(asctime)s %(clientip)-15s %(user)-8s %(message)s'
    logging.basicConfig(format=FORMAT)
    logging.warning('Checking for Query %s',sql)
    return flt(reserved_qty[0][0]) if reserved_qty else 0

def get_value_of_quantity_of_Sales_Order_Item(item_code):
    """warehouse is hard coded as per Mr. Albert's instructions"""
    warehouse = "Delivery Area - ISS"
    sql = "select sum(qty) qty from `tabSales Order Item` where item_code = '{0}'".format(item_code)
    reserved_qty = frappe.db.sql(sql)
    FORMAT = '%(asctime)s %(clientip)-15s %(user)-8s %(message)s'
    logging.basicConfig(format=FORMAT)
    logging.warning('Checking for Query %s',sql)
    return flt(reserved_qty[0][0]) if reserved_qty else 0
