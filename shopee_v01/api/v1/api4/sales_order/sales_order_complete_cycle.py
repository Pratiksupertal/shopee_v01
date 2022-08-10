import frappe

from shopee_v01.api.v1.helpers import get_base_url
from shopee_v01.api.v1.helpers import create_and_submit_sales_order
from shopee_v01.api.v1.helpers import create_and_submit_delivery_note_from_sales_order
from shopee_v01.api.v1.helpers import create_and_submit_sales_invoice_from_sales_order
from shopee_v01.api.v1.helpers import create_payment_for_sales_order_from_web
from shopee_v01.api.v1.helpers import format_result
from shopee_v01.api.v1.helpers import handle_empty_error_message
from shopee_v01.api.v1.helpers import auto_map_accounting_dimensions_fields
from shopee_v01.api.v1.helpers import get_coa_from_store

from shopee_v01.api.v1.validations import validate_data
from shopee_v01.api.v1.validations import data_validation_for_sales_order_cycle


"""Sales Order Cycle

@agenda
1. Create Sales Order
2. Auto Create Delivery Note from Sales Order
3. Auto Create Sales Invoice from Sales Order
4. Auto Create Payment Entry from Sales Invoice

@lookup
- Sales Order will link Sales Invoice and Delivery Note
- Delivery Note will link Sales Order
- Sales Invoice will link Sales Order and Payment Entry

- Region name (in Accounting Dimensions) will be auto mapped
  and added from City name by Territory Tree
"""
@frappe.whitelist()
def sales_order_cycle():
    response = {
        'sales_order': None,
        'delivery_note': None,
        'sales_invoice': None,
        'payment_entry': None
    }
    try:
        data = validate_data(frappe.request.data)
        order_data = data.get('order_data')
        accounting_dimensions = data.get("accounting_dimensions", {})
        payment_data = data.get('payment_data')

        """Auto Map accounting dimensions
        1. auto map region from city by Territory Tree
        """
        accounting_dimensions = auto_map_accounting_dimensions_fields(
            accounting_dimensions=accounting_dimensions,
            add_region=True
        )

        data_validation_for_sales_order_cycle(
            order_data=order_data,
            payment_data=payment_data)

        """Auto map paid to with store by Chart of Account Configuration"""
        payment_data['paid_to'] = get_coa_from_store(store=order_data.get('store'))

        base = get_base_url(url=frappe.request.url)

        """step 1: create and submit sales order"""
        sales_order = create_and_submit_sales_order(
            base=base,
            order_data=order_data,
            submit=True
        )

        if sales_order.status_code != 200:
            raise Exception('Sales order not created. Please, provide valid data.')

        sales_order = sales_order.json().get('data')
        so_name = sales_order.get("name")
        response['sales_order'] = so_name

        """step 2: create and submit delivery_note"""
        delivery_note = create_and_submit_delivery_note_from_sales_order(
            base=base,
            source_name=so_name,
            submit=True,
            transaction_date=order_data.get('transaction_date')
        )
        response['delivery_note'] = delivery_note.get('name')

        """step 3: create and submit sales invoice"""
        sales_invoice = create_and_submit_sales_invoice_from_sales_order(
            base=base,
            source_name=so_name,
            accounting_dimensions=accounting_dimensions,
            submit=True,
            transaction_date=order_data.get('transaction_date')
        )
        response['sales_invoice'] = sales_invoice.get('name')

        """step 4: create and submit payment entry"""
        payment_entry = create_payment_for_sales_order_from_web(
            base=base,
            payment_data=payment_data,
            sales_invoice_data=sales_invoice,
            accounting_dimensions=accounting_dimensions,
            submit=True,
            transaction_date=order_data.get('transaction_date')
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
                keys=['sales_order', 'delivery_note', 'sales_invoice', 'payment_entry']
            )
        return format_result(
            result=response,
            message=f'{str(err)}',
            status_code=400,
            success=False,
            exception=str(err)
        )


"""Sales Order Cycle Bulk

@agenda
Multple Sales Order Cycle at a time

@flow
1. Create Sales Order
2. Auto Create Delivery Note from Sales Order
3. Auto Create Sales Invoice from Sales Order
4. Auto Create Payment Entry from Sales Invoice

@lookup
- Sales Order will link Sales Invoice and Delivery Note
- Delivery Note will link Sales Order
- Sales Invoice will link Sales Order and Payment Entry

- Region name (in Accounting Dimensions) will be auto mapped
  and added from City name by Territory Tree
"""
@frappe.whitelist()
def sales_order_cycle_bulk():
    data = validate_data(frappe.request.data)
    if data:
        data = data.get('data', [])
    else:
        return format_result(message='No data found', status_code=400, success=False, exception='No data found')

    result = []
    success_count, fail_count = 0, 0

    for record in list(data):
        response = {
            'sales_order': None,
            'delivery_note': None,
            'sales_invoice': None,
            'payment_entry': None,
            'status': 'failed'
        }
        try:
            order_data = record.get('order_data', {})
            accounting_dimensions = record.get("accounting_dimensions", {})
            payment_data = record.get('payment_data', {})

            """Auto Map accounting dimensions
            1. auto map region from city by Territory Tree
            """
            accounting_dimensions = auto_map_accounting_dimensions_fields(
                accounting_dimensions=accounting_dimensions,
                add_region=True
            )

            data_validation_for_sales_order_cycle(
                order_data=order_data,
                payment_data=payment_data)

            """Auto map paid to with store by Chart of Account Configuration"""
            payment_data['paid_to'] = get_coa_from_store(store=order_data.get('store'))

            base = get_base_url(url=frappe.request.url)

            """step 1: create and submit sales order"""
            sales_order = create_and_submit_sales_order(
                base=base,
                order_data=order_data,
                submit=True
            )

            if sales_order.status_code != 200:
                raise Exception('Sales order not created. Please, provide valid data.')

            sales_order = sales_order.json().get('data')
            so_name = sales_order.get("name")
            response['sales_order'] = so_name

            """step 2: create and submit delivery_note"""
            delivery_note = create_and_submit_delivery_note_from_sales_order(
                base=base,
                source_name=so_name,
                submit=True,
                transaction_date=order_data.get('transaction_date')
            )
            response['delivery_note'] = delivery_note.get('name')

            """step 3: create and submit sales invoice"""
            sales_invoice = create_and_submit_sales_invoice_from_sales_order(
                base=base,
                source_name=so_name,
                accounting_dimensions=accounting_dimensions,
                submit=True,
                transaction_date=order_data.get('transaction_date')
            )
            response['sales_invoice'] = sales_invoice.get('name')

            """step 4: create and submit payment entry"""
            payment_entry = create_payment_for_sales_order_from_web(
                base=base,
                payment_data=payment_data,
                sales_invoice_data=sales_invoice,
                accounting_dimensions=accounting_dimensions,
                submit=True,
                transaction_date=order_data.get('transaction_date')
            )
            response['payment_entry'] = payment_entry.get("name")

            response['status'] = 'success'
            response['message'] = "Successfully created"
            success_count += 1
            result.append(response)

        except Exception as err:
            if len(str(err)) < 2:
                err = handle_empty_error_message(
                    response=response,
                    keys=['sales_order', 'delivery_note', 'sales_invoice', 'payment_entry']
                )
            fail_count += 1
            response['message'] = str(err)
            result.append(response)

    message = 'success' if success_count > 0 else 'failed'
    success = True if success_count > 0 else False
    return format_result(
        result={
            "success_count": success_count,
            "fail_count": fail_count,
            "record": result
        },
        message=message,
        success=success,
        status_code=200
    )
