from frappe.model.naming import make_autoname
import frappe, json
from frappe.model.document import Document
from frappe.utils import cstr, flt, getdate, new_line_sep, nowdate, add_days
from frappe.model.mapper import get_mapped_doc
from frappe.desk.notifications import get_notification_config
from frappe import _


def autoname(doc,method):
    if doc.is_new():
        po_type = doc.po_type
        potype_abbr = frappe.get_doc("PO Type", {"name": po_type})
        if po_type:
            doc.name = make_autoname(potype_abbr.abbreviation +".YYYY"+".MM."+ "-.####")
        else:
            doc.name = make_autoname("PO" +".YYYY.MM."+ "-.####")
    #shopee_v01.shopee_v01.custom_script.purchase_order.test
    #shopee_v01/shopee_v01/custom_script/purchase_order.js

@frappe.whitelist()
def warehouse_filter(supplier):
    doc = frappe.get_doc('Supplier',supplier)
    supplier_group = doc.supplier_group
    mapper = frappe.get_doc('Supplier Group  Warehouse Mapping')
    warehouse_list = []
    for row in mapper.warehouse_mapping:
        if row.supplier_id == supplier_group:
            warehouse_list.append(row.warehouse_id)

    # mapper = frappe.db.get_single_value("Supplier Group Warehouse Mapping","warehouse_mapping")
    return warehouse_list,supplier_group


@frappe.whitelist()
def cara_packing(template_name):
    doc = frappe.get_doc('Cara Packing Template',template_name)
    template = doc.template_text
    return template

@frappe.whitelist()
def size_filter(item_code):
    doc = frappe.get_doc('Item', item_code)
    return doc.invent_size_id


@frappe.whitelist()
def make_stock_entry(source_name, target_doc=None):

    doclist = get_mapped_doc("Purchase Order", source_name, {
        "Purchase Order": {
            "doctype": "Stock Entry",},
        "Purchase Order Item": {
            "doctype": "Stock Entry Detail",
        }
    }, target_doc)

    return doclist


@frappe.whitelist()
def make_stock_entry_material_request(source_name, target_doc=None):

    doclist = get_mapped_doc("Purchase Order", source_name, {
        "Purchase Order": {
            "doctype": "Material Request",},
        "Purchase Order Item": {
            "doctype": "Material Request Item",
        }
    }, target_doc)

    return doclist


@frappe.whitelist()
def create_pick_list(source_name, input_qty=0, total_qty=0):
    try:
        response = ""
        input_qty = int(input_qty)
        total_qty = int(total_qty)
        all_items = []
        purchase_order_doc = frappe.get_doc('Purchase Order', source_name)
        rows = purchase_order_doc.items
        for row in rows:
            all_items.append(row.item_name)
        max_qty = total_qty/len(all_items)
        if input_qty > max_qty:
            message = f"Pick List not created for purchase Order input quantity entered is greater than max quantity"
            return frappe.msgprint(message)
        picklist = generate_new_pick_list(all_items, purchase_order_doc, max_qty, input_qty)
        if picklist:
            response += f"<br>Pick List <strong><a href='{picklist.get_url()}'>{picklist.get('name')}</a></strong> is created for Purchase Order"
        if not input_qty:
            response += "Enter some integer input greater than 0 and less than or equal to Max Quantity."
        return frappe.msgprint(response)
    except Exception as e:
        purchase_order_doc = frappe.get_doc('Purchase Order', source_name)
        message = f"Pick List not created for Purchase Order - <strong>{purchase_order_doc.name}</strong>. Reason - {str(e)}"
        return frappe.msgprint(message)


def generate_new_pick_list(item_list, purchase_order_doc, max_qty, input_qty):
    if not item_list or not input_qty: return
    pick_list = frappe.new_doc('Pick List')
    pick_list.company = purchase_order_doc.company
    pick_list.purpose = "Material Transfer for Manufacture"
    pick_list.purchase_order = purchase_order_doc.name
    pick_list.for_qty = input_qty
    for item in item_list:
        row = pick_list.append('locations', {})
        row.item_code = item
        row.warehouse = "Stores - ISS"
        row.qty = input_qty
        row.stock_qty = input_qty
        row.picked_qty = input_qty
    pick_list.save()
    return pick_list

@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_user(doctype, txt, searchfield, start, page_len, filters):
    role = ""
    if filters and filters.get('role'):
        if len(filters.get('role'))>1:
            role = "and role in {0}".format(tuple(filters.get('role')))
        else:
            role = "and role = '{0}'".format(filters.get('role')[0])

    return frappe.db.sql("""select parent from `tabHas Role`
		where `parent` LIKE %(txt)s and parenttype='User' {role} ;"""
        .format(role=role), {
            'txt': '%' + txt + '%'
        })


@frappe.whitelist()
def get_first_name(doc):
    return frappe.db.get_list("Contact", {'name': ['like', '%-{0}'.format(doc.supplier)]}, ['first_name'])
