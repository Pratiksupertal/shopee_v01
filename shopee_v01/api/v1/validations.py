import frappe
import json
from frappe.utils import today


def validate_data(data):
    if not data:
        return data
    if not len(data):
        return data
    try:
        return json.loads(data)
    except ValueError:
        return "Invalid JSON submitted"

# it is created by pratik/Rakesh as sales order cycle doesn't have the customer data for validation
def data_validation_for_sales_order_cycle(order_data, payment_data):
    if not order_data.get("delivery_date"):
        raise Exception("Required data missing : Unable to proceed : Delivery date is required")
    if not order_data.get("items"):
        raise Exception("Required data missing : Unable to proceed : Items are required")
    if not order_data.get("store"):
        raise Exception("Required data missing : Unable to proceed : Store is required")
    if not order_data.get("external_so_number") or not order_data.get("source_app_name"):
        raise Exception("Required data missing : Unable to proceed : Sales order Number and Source app name both are required")
    if not payment_data.get("paid_from"):
        raise Exception("Required data missing : Unable to proceed : Paid from is required")
    if not payment_data.get("paid_from_account_currency"):
        raise Exception("Required data missing : Unable to proceed : Paid from account currency is required")
    if not payment_data.get("paid_to_account_currency"):
        raise Exception("Required data missing : Unable to proceed : Paid to account currency is required")
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

def data_validation_for_create_sales_order_web(customer_data, order_data, payment_data):
    if not customer_data.get('customer_name'):
        raise Exception('Customer name is required')
    if not customer_data.get('customer_type'):
        raise Exception('Customer type is required')
    if not customer_data.get('customer_group'):
        raise Exception('Customer group is required')
    if not customer_data.get('territory'):
        raise Exception('Customer territory is required')
    if not customer_data.get('email_id'):
        raise Exception('Customer email id is required')
    if not customer_data.get('mobile_no'):
        raise Exception('Customer mobile no is required')
    if not customer_data.get('address_type'):
        raise Exception('Customer address type is required')
    if not customer_data.get('address_line1'):
        raise Exception('Customer address line 1 is required')
    if not customer_data.get('city'):
        raise Exception('Customer city is required')
    if not customer_data.get('country'):
        raise Exception('Customer country is required')

    if not order_data.get("delivery_date"):
        raise Exception("Required data missing : Unable to proceed : Delivery date is required")
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
        raise Exception("Required data missing : Unable to proceed : Paid to account currency is required")
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
        if data.get("stock_entry_type") == "Receive at Shop":
            raise Exception('Received at Shop is already done for this Stock entry')
        else:
            raise Exception('Received at Warehouse is already done for this Stock entry')


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

    picker = frappe.db.get_value('Pick List', data.get("pick_list"), 'picker')
    if not frappe.session.user or not picker or frappe.session.user != picker:
        raise Exception("You are not authorized to do this.")


def data_validation_for_submit_picklist_and_create_stockentry(data):
    if not data.get("pick_list"):
        raise Exception("Required data missing : Pick List name is required")
    if not data.get("stock_entry_type"):
        raise Exception("Required data missing : Stock Entry Type is required")
    if not data.get("s_warehouse"):
        raise Exception("Required data missing : Source Warehouse is required")
    if not data.get("t_warehouse"):
        raise Exception("Required data missing : Target Warehouse is required")

    picker = frappe.db.get_value('Pick List', data.get("pick_list"), 'picker')
    print('\n\n\n', frappe.session.user, '\n\n\n', picker, '\n\n\n')
    if not frappe.session.user or not picker or frappe.session.user != picker:
        raise Exception("You are not authorized to do this.")


def data_validation_for_assign_picker(data):
    if not data.get("pick_list"):
        raise Exception("Required data missing : Pick List name is required")
    if not frappe.db.get_value('Pick List', data.get("pick_list"), 'name'):
        raise Exception("Incorrect Pick List")
    if frappe.db.get_value('Pick List', data.get("pick_list"), 'picker'):
        raise Exception("This picklist is already assigned to someone")


def data_validation_for_stock_entry_receive_at_warehouse(data):
    if not data.get("company"):
        raise Exception("Required data missing (Company is required)")
    if not data.get("send_to_warehouse_id"):
        raise Exception("Required data missing (Send to Warehouse id is required)")
    if not data.get("notes"):
        raise Exception("Required data missing (Notes are required)")
    if not data.get("items"):
        raise Exception("Required data missing (Items are required)")
    for item in data['items']:
        if not item.get("item_code"):
            raise Exception("Required data missing (Item code is required)")
        if not item.get("t_warehouse"):
            raise Exception("Required data missing (Target Warehouse is required)")
        if not item.get("qty"):
            raise Exception("Required data missing (Qty is required)")


def data_validation_for_stock_entry_send_to_shop(data):
    if not data.get("outgoing_stock_entry"):
        raise Exception("Required data missing : Outgoing Stock Entry name is required")
    if not data.get("stock_entry_type"):
        raise Exception("Required data missing : Stock Entry Type name is required")
    if not data.get("s_warehouse"):
        raise Exception("Required data missing : Source Warehouse is required")
    if not data.get("t_warehouse"):
        raise Exception("Required data missing : Target Warehouse is required")

    outgoing_stock_entry = frappe.get_list("Stock Entry", {"outgoing_stock_entry": data.get("outgoing_stock_entry")})
    if len(outgoing_stock_entry) > 0:
        raise Exception('Send to Shop is already done for this Stock entry')
