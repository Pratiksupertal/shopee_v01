import frappe

from shopee_v01.api.v1.helpers import validate_data
from shopee_v01.api.v1.helpers import auto_map_accounting_dimensions_fields
from shopee_v01.api.v1.helpers import get_base_url
from shopee_v01.api.v1.helpers import create_and_save_customer
from shopee_v01.api.v1.helpers import create_and_submit_sales_order
from shopee_v01.api.v1.helpers import create_and_submit_sales_invoice_from_sales_order
from shopee_v01.api.v1.helpers import create_payment_for_sales_order_from_web
from shopee_v01.api.v1.helpers import format_result
from shopee_v01.api.v1.helpers import handle_empty_error_message
from shopee_v01.api.v1.validations import data_validation_for_create_sales_order_web


"""Sales Order Cycle

@agenda
1. Create Sales Order
2. Auto Create Sales Invoice from Sales Order
3. Auto Create Payment Entry from Sales Invoice

@lookup
- Sales Order will link Sales Invoice
- Sales Invoice will link Sales Order and Payment Entry

- Region name (in Accounting Dimensions) will be auto mapped
  and added from City name by Territory Tree
"""
@frappe.whitelist()
def create_sales_order_from_web():
    response = {
        'customer': None,
        'sales_order': None,
        'sales_invoice': None,
        'payment_entry': None
    }
    try:
        data = validate_data(frappe.request.data)
        customer_data = data.get('customer_data')
        order_data = data.get('order_data')
        accounting_dimensions = data.get("accounting_dimensions", {})
        payment_data = data.get('payment_data')

        data_validation_for_create_sales_order_web(
            order_data=order_data,
            payment_data=payment_data)

        """Auto Map accounting dimensions
        1. auto map region from city by Territory Tree
        """
        accounting_dimensions = auto_map_accounting_dimensions_fields(
            accounting_dimensions=accounting_dimensions,
            add_region=True
        )

        base = get_base_url(url=frappe.request.url)

        """step 1: create and save the customer"""
        customer = create_and_save_customer(
            base=base,
            customer_data=customer_data,
            submit=True
        )

        customer_name = customer.get("name")
        response['customer'] = customer_name
        order_data['customer'] = customer_name

        """step 2: create and submit sales order"""
        sales_order = create_and_submit_sales_order(
            base=base,
            order_data=order_data,
            submit=True
        )
        if sales_order.status_code != 200:
            raise Exception('Sales order not created. Please, provide valid data. ')

        sales_order = sales_order.json().get('data')
        so_name = sales_order.get("name")
        response['sales_order'] = so_name

        """step 3: create and submit sales invoice"""
        sales_invoice = create_and_submit_sales_invoice_from_sales_order(
            base=base,
            source_name=so_name,
            accounting_dimensions=accounting_dimensions,
            submit=True
        )
        response['sales_invoice'] = sales_invoice.get('name')

        """step 4: create and submit payment entry"""
        payment_entry = create_payment_for_sales_order_from_web(
            base=base,
            payment_data=payment_data,
            sales_invoice_data=sales_invoice,
            accounting_dimensions=accounting_dimensions,
            submit=True
        )
        response['payment_entry'] = payment_entry.get("name")

        return format_result(
            success="True",
            result=response,
            status_code=200)

    except Exception as err:
        if len(str(err)) < 2:
            err = handle_empty_error_message(
                response=response,
                keys=['customer', 'sales_order', 'sales_invoice', 'payment_entry']
            )
        return format_result(
            result=response,
            message=f'{str(err)}',
            status_code=400,
            success=False,
            exception=str(err)
        )
