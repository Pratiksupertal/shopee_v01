import frappe
from frappe.utils import today
from frappe import _


def data_validation_for_create_sales_order_web(order_data, payment_data):
    if not order_data.get("delivery_date"):
        order_data["delivery_date"] = today()
    if not order_data.get("delivery_date"):
        order_data["delivery_date"] = today()
    if not order_data.get("items"):
        raise Exception("Required data missing : Unable to proceed : Items are required")
    if not order_data.get("external_so_number") or not order_data.get("source_app_name"):
        raise Exception("Required data missing : Unable to proceed : Sales order Number and Source app name both are required")

    if not payment_data.get("paid_from"):
        raise Exception("Required data missing : Unable to proceed : Paid from is required")
    if not payment_data.get("paid_to"):
        raise Exception("Required data missing : Unable to proceed : Paid to is required")
    if not payment_data.get("paid_from_account_currency"):
        raise Exception("Required data missing : Unable to proceed : Paid from account currency is required")
    if not payment_data.get("paid_to_account_currency"):
        raise Exception("Required data missing : Unable to proceed : Paid to accountcurrency is required")
    if not payment_data.get("paid_amount"):
        raise Exception("Required data missing : Unable to proceed : Paid amount is required")
    if not payment_data.get("received_amount"):
        raise Exception("Required data missing : Unable to proceed : Received amount is required")
    if not payment_data.get("reference_no"):
        raise Exception("Required data missing : Unable to proceed : Reference no is required")
    if not payment_data.get("reference_date"):
        raise Exception("Required data missing : Unable to proceed : Reference date is required")
    if not payment_data.get("mode_of_payment"):
        raise Exception("Required data missing : Unable to proceed : Payment Mode is required")


def data_validation_for_create_receive_at_warehouse(data):
    if not data.get("outgoing_stock_entry"):
        raise Exception("Required data missing : Outgoing Stock Entry name is required")
    if not data.get("stock_entry_type"):
        raise Exception("Required data missing : Stock Entry Type name is required")
    if not data.get("t_warehouse"):
        raise Exception("Required data missing : Target Warehouse is required")
    
    outgoing_stock_entry = frappe.get_list("Stock Entry", {"outgoing_stock_entry": data.get("outgoing_stock_entry")})
    if len(outgoing_stock_entry) > 0:
        raise Exception('Received at warehouse is already done for this Stock entry')


def data_validation_for_save_picklist_and_create_stockentry(data):
    if not data.get("pick_list"):
        raise Exception("Required data missing : Pick List name is required")
    if not data.get("item_code"):
        raise Exception("Required data missing : Item code is required")
    if not data.get("picked_qty"):
        raise Exception("Required data missing : Picked quantity is required")
    if not data.get("s_warehouse"):
        raise Exception("Required data missing : Source Warehouse is required")
    if not data.get("t_warehouse"):
        raise Exception("Required data missing : Target Warehouse is required")
    if not data.get("stock_entry_type"):
        raise Exception("Required data missing : Stock entry type is required")


def data_validation_for_submit_picklist_and_create_stockentry(data):
    if not data.get("pick_list"):
        raise Exception("Required data missing : Pick List name is required")
    if not data.get("stock_entry_type"):
        raise Exception("Required data missing : Stock Entry Type is required")
    if not data.get("s_warehouse"):
        raise Exception("Required data missing : Source Warehouse is required")
    if not data.get("t_warehouse"):
        raise Exception("Required data missing : Target Warehouse is required")


def data_validation_for_assign_picker(data):
    if not data.get("pick_list"):
        raise Exception("Required data missing : Pick List name is required")
    if not data.get("picker"):
        raise Exception("Required data missing : Picker is required")
    if not data.get("start_time"):
        raise Exception("Required data missing : Start Time is required")
    if not frappe.db.get_value('Pick List', data.get("pick_list"), 'name'):
        raise Exception("Incorrect Pick List")
    if not frappe.db.get_value('User', data.get("picker"), 'name'):
        raise Exception("Incorrect Picker")
    if frappe.db.get_value('Pick List', data.get("pick_list"), 'picker'):
        raise Exception("This picklist is already assigned to someone")