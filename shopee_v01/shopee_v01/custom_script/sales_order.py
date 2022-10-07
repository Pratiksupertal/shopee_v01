from frappe.model.naming import make_autoname
import frappe
from frappe.model.document import Document
from frappe.utils import cstr, flt, getdate, new_line_sep, nowdate, add_days
from frappe.model.mapper import get_mapped_doc


@frappe.whitelist()
def size_filter(item_code):
    doc1 = frappe.get_doc('Item', item_code)
    price_list_rate = frappe.db.get_value('Item Price', {"selling": 1, "item_code": item_code}, 'price_list_rate')
    if price_list_rate is None:
        price_list_rate = frappe.db.get_value('Item', {'item_code': doc1.item_name}, 'price')
    doc2 = frappe.get_doc('Finished901ItemQtySummary')
    doc2 = [x.available_items for x in doc2.total_item_count_in_warehouse if x.item_code == item_code]
    size_id = frappe.db.get_value('Item Variant Attribute', {'parent': item_code}, 'attribute_value')
    reserved_qty = get_reserved_qty(item_code)
    return size_id, price_list_rate, doc2[0] if len(doc2) > 0 else '', reserved_qty


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
