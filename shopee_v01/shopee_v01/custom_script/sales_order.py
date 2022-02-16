from frappe.model.naming import make_autoname
import frappe
from frappe.model.document import Document
from frappe.utils import cstr, flt, getdate, new_line_sep, nowdate, add_days
from frappe.model.mapper import get_mapped_doc


@frappe.whitelist()
def size_filter(item_code):
    doc1 = frappe.get_doc('Item', item_code)
    price_list = frappe.get_doc('Item Price',{"selling":1,"item_code":item_code})
    doc2 = frappe.get_doc('Finished901ItemQtySummary')
    doc2 = [x.available_items for x in doc2.total_item_count_in_warehouse if x.item_code == item_code]
    return doc1.invent_size_id,price_list.price_list_rate, doc2[0] if len(doc2) > 0 else ''


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
