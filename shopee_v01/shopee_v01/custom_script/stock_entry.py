import frappe
import requests
import json

from shopee_v01.helpers.auth import get_auth_token


group_warehouse, node_warehouse = [], []

def update_finished901itemsummary(doc,action):
    warehouse_tuple = []
    warehouse_list = frappe.get_doc('Finished901ItemQtySummary')
    for item in doc.items:
        sql = "select item_code,available_items,warehouse from `tabTotal Item count in Warehouse` where item_code = '{0}'".format(item.item_code)
        item_availability = frappe.db.sql(sql)
        warehouse_tuple = [i.warehouse for i in warehouse_list.child_warehouse if (i.warehouse == item.t_warehouse or i.warehouse == item.s_warehouse)]
        warehouse_tuple = tuple(warehouse_tuple)
        if len(item_availability) > 0:
            if len(warehouse_tuple) > 0:
                if warehouse_tuple[0] == item.t_warehouse:
                    qty = item.qty if action == "update" else -item.qty
                if warehouse_tuple[0] == item.s_warehouse:
                    qty = -item.qty if action == "cancel" else item.qty
                if item.t_warehouse in warehouse_tuple and item.s_warehouse in warehouse_tuple:
                    qty = 0
                if qty != 0:
                    sql = "update `tabTotal Item count in Warehouse` set available_items = available_items + {0},warehouse = '{1}',modified_time = now()  where item_code = '{2}';".format(qty,warehouse_tuple[0],item.item_code)
                    query = frappe.db.sql(sql)
        else:
            balance_qty = 0
            for i in warehouse_list.child_warehouse:
                temp = frappe.db.sql("""select qty_after_transaction from `tabStock Ledger Entry`
                where item_code=%s and warehouse = %s and is_cancelled='No'
                order by posting_date desc, posting_time desc, creation desc
                limit 1""", (item.item_code, i.warehouse))
                temp = int(temp[0][0]) if len(temp)>0 else 0
                balance_qty = balance_qty + temp
            idx = frappe.db.sql("select idx from `tabTotal Item count in Warehouse` order by idx desc limit 1;")
            idx = idx[0][0]+1 if idx else 1
            sql = "insert into `tabTotal Item count in Warehouse` (name,idx,creation,modified,modified_time,modified_by,owner,parent,parentfield,parenttype,item_code,item_name,available_items,warehouse) values ('{0}',{4},now(),now(),now(),'{3}','{3}','Finished901ItemQtySummary','total_item_count_in_warehouse','Finished901ItemQtySummary','{0}','{5}',{1},'{2}')".format(item.item_code,balance_qty,item.t_warehouse,frappe.session.user,idx,item.item_name)
            query = frappe.db.sql(sql)

def finished901ItemQtySummary(doc,method):
    """Stock Entry Items belongs to Finished warehouse then item count will be updated."""
    update_finished901itemsummary(doc,action="update")

def cancel_update(doc,method):
    """Stock Entry Items belongs to Finished warehouse then item count will be reversed."""
    update_finished901itemsummary(doc,action="cancel")

def submit(doc, method):
    update_stock_to_halosis(doc=doc)


def is_type_adjustment(pick_list):
    """
    Handling case for warehouse app
    If any stock entry has pick list and this pick pick list has sales order from `E-Commerce`
    Then, the halosis stock update type will be `adjustmennnt`

    Return True if type `adjustment`, False otherwise
    """
    if not pick_list:
        return False
    try:
        pick_list_details = frappe.get_doc('Pick List', pick_list)
        if pick_list_details:
            locations = pick_list_details.locations
            if locations:
                sales_order = locations[0].sales_order
                if sales_order:
                    source_app_name = frappe.db.get_value("Sales Order", sales_order, "source_app_name")
                    if source_app_name:
                        return source_app_name.lower() in ["ecommerce", "e-commerce"]
        return False
    except Exception:
        return False


def get_stock_update_type(adjustment_type, item):
    config = frappe.get_single("Online Warehouse Configuration")
    warehouse_list = [i.warehouse for i in config.online_warehouse]
    in_type = parent_warehouse(item.t_warehouse, warehouse_list)
    out_type = parent_warehouse(item.s_warehouse, warehouse_list)
    if adjustment_type and in_type:
        return "adjustment", "plus"
    elif adjustment_type and out_type:
        return "adjustment", "minus"
    elif in_type:
        return "in", "plus"
    elif out_type:
        return "out", "minus"
    return None, None


def get_qty(type, cal_type, item):
    try:
        if type in ["in", "out"]:
            return int(item.qty)

        # Next, handle adjustment type
        warehouse = item.t_warehouse if cal_type == "plus" else item.s_warehouse
        actual_qty = frappe.db.get_list('Bin', fields=['actual_qty'], filters={
            'item_code': item.item_code,
            'warehouse': warehouse}, as_list=True)[0][0]
        return actual_qty
    except Exception:
        raise
        frappe.log_error(title="Update stock API Data part", message=frappe.get_traceback())
        frappe.msgprint(f'Something went wrong! {frappe.get_traceback()}')


def update_stock_to_halosis(doc):
    request = []
    config = frappe.get_single("Online Warehouse Configuration")

    adjustment_type = is_type_adjustment(doc.pick_list)

    for item in doc.items:
        brand = frappe.db.get_value("Item", item.item_code, "brand")
        vendors_list = [data.vendor_id for data in config.brand_vendor_mapping if data.brand == brand]
        type, cal_type = get_stock_update_type(adjustment_type, item)
        if not type:
            continue

        request_body = {
            "item_code": item.item_code,
            "brand": brand,
            "vendor_id": vendors_list,
            "qty": get_qty(type, cal_type, item),
            "type": type
        }
        request.append(request_body)

    if request:
        try:
            request = json.dumps(request).replace("'", '"')
            url = config.base_url + 'update-stock'
            response = requests.post(
                url.replace("'", '"'),
                json=json.loads(request),
                headers={"Authorization": get_auth_token(config)},)
            frappe.log_error(title="Update stock API update stock part", message=response.text)
            if response.status_code == 200:
                frappe.msgprint('Updating to Halosis. Please, check error log for more update.')
            else:
                frappe.msgprint(f'Stock updation to halosis is failed for some reasons! Please, check error log. {frappe.get_traceback()}')
        except Exception:
            raise
            frappe.log_error(title="Update stock API Data part", message=frappe.get_traceback())
            frappe.msgprint(f'Problem in halosis update. {frappe.get_traceback()}')


def parent_warehouse(warehouse, warehouse_list):
    base_parent = [frappe.db.get_value("Warehouse", warehouse, "parent") for warehouse in warehouse_list]
    a = frappe.db.get_value("Warehouse", warehouse, "parent")
    if not a:
        return False
    elif a in warehouse_list:  # parent matched
        return True
    elif a in base_parent:
        return False
    else:
        b = parent_warehouse(a, warehouse_list)
        return b
