import frappe
from frappe.utils import today

from shopee_v01.api.v1.helpers import validate_data
from shopee_v01.api.v1.helpers import auto_map_accounting_dimensions_fields
from shopee_v01.api.v1.helpers import get_base_url
from shopee_v01.api.v1.helpers import create_and_submit_sales_order
from shopee_v01.api.v1.helpers import create_and_submit_sales_invoice_from_sales_order
from shopee_v01.api.v1.helpers import create_and_submit_delivery_note_from_sales_order
from shopee_v01.api.v1.helpers import format_result


"""Sales Order SPG APP (Single)

Auto Create
    - Sales Order
    - Delivery Note
    - Sales Invoice
"""
@frappe.whitelist()
def create_sales_order():
    res = {
        'sales_order': None,
        'delivery_note': None,
        'sales_invoice': None
    }
    try:
        data = validate_data(frappe.request.data)
        order_data = data.get("order_data")
        accounting_dimensions = data.get("accounting_dimensions", {})

        """
        1. If Delivery Date is not given, will update TODAY as delivery date
        2. External SO Number and Source App Name fields mendatory
        """
        if not order_data.get("delivery_date"):
            order_data["delivery_date"] = today()
        if not order_data.get("external_so_number") or not order_data.get("source_app_name"):
            raise Exception("Sales order Number and Source app name both are required")

        """Auto Map accounting dimensions
        1. auto map region from city by Territory Tree
        2. auto map brand name from item if all items are from same brand
        """
        accounting_dimensions = auto_map_accounting_dimensions_fields(
            accounting_dimensions=accounting_dimensions,
            order_data=order_data,
            add_region=True,
            add_brand=True
        )

        base = get_base_url(url=frappe.request.url)

        """step 1: create and submit sales order"""
        sales_order = create_and_submit_sales_order(
            base=base,
            order_data=order_data,
            submit=True
        )

        if sales_order.status_code == 200:
            sales_order = sales_order.json().get('data')
            so_name = sales_order.get("name")
            print(so_name)

            res['sales_order'] = so_name

            """step 2: create and submit delivery note"""
            delivery_note = create_and_submit_delivery_note_from_sales_order(
                base=base,
                source_name=so_name,
                submit=True
            )
            res['delivery_note'] = delivery_note.get('name')

            """step 3: create and submit sales invoice"""
            sales_invoice = create_and_submit_sales_invoice_from_sales_order(
                base=base,
                source_name=so_name,
                accounting_dimensions=accounting_dimensions,
                submit=True
            )
            res['sales_invoice'] = sales_invoice.get('name')

            return format_result(success=True, result=res)
        else:
            raise Exception()
    except Exception as e:
        if len(str(e)) < 1:
            if not res['sales_order']:
                e = 'Sales Order creation failed.'
            elif not res['delivery_note']:
                e = 'Delivery Note creation failed.'
            elif not res['sales_invoice']:
                e = 'Sales Invoice creation failed.'
            else:
                e = 'Something went wrong.'
            e += ' Please, provide valid data.'
        return format_result(
            result=res,
            message=f'{str(e)}',
            status_code=400,
            success=False,
            exception=str(e)
        )


"""Sales Order SPG APP (Multiple)

Create Multiple Order at a time with Delivery Note and Sales Invoice

Auto Create
    - Sales Order
    - Delivery Note
    - Sales Invoice
"""
@frappe.whitelist()
def create_sales_order_all():
    data = validate_data(frappe.request.data)
    if data:
        data = data.get('data', [])
    else:
        return format_result(message='No data found', status_code=400, success=False, exception='No data found')

    result = []
    success_count, fail_count = 0, 0

    for record in list(data):
        res = {
            'sales_order': None,
            'delivery_note': None,
            'sales_invoice': None,
            'status': 'failed'
        }
        try:
            order_data = record.get('order_data', {})
            accounting_dimensions = record.get('accounting_dimensions', {})

            """
            1. If Delivery Date is not given, will update TODAY as delivery date
            2. External SO Number and Source App Name fields mendatory
            """
            if not order_data.get("delivery_date"):
                order_data["delivery_date"] = today()
            if not order_data.get("external_so_number") or not order_data.get("source_app_name"):
                raise Exception("Sales order Number and Source app name both are required")

            """Auto Map accounting dimensions
            1. auto map region from city by Territory Tree
            2. auto map brand name from item if all items are from same brand
            """
            accounting_dimensions = auto_map_accounting_dimensions_fields(
                accounting_dimensions=accounting_dimensions,
                order_data=order_data,
                add_region=True,
                add_brand=True
            )

            res['external_so_number'] = order_data.get('external_so_number')

            base = get_base_url(url=frappe.request.url)

            """step 1: create and submit sales order"""
            sales_order = create_and_submit_sales_order(
                base=base,
                order_data=order_data,
                submit=True
            )
            print(sales_order.text)

            if sales_order.status_code == 200:
                sales_order = sales_order.json().get('data')
                so_name = sales_order.get("name")
                res['sales_order'] = so_name

                """step 2: create and submit delivery note"""
                delivery_note = create_and_submit_delivery_note_from_sales_order(
                    base=base,
                    source_name=so_name,
                    submit=True
                )
                res['delivery_note'] = delivery_note.get('name')

                """step 3: create and submit sales invoice"""
                sales_invoice = create_and_submit_sales_invoice_from_sales_order(
                    base=base,
                    source_name=so_name,
                    accounting_dimensions=accounting_dimensions,
                    submit=True
                )
                res['sales_invoice'] = sales_invoice.get('name')

                res['status'] = 'success'
                res['message'] = "Successfully created"
                success_count += 1
                result.append(res)

            else:
                raise Exception()

        except Exception as err:
            if len(str(err)) < 1:
                if not res['sales_order']:
                    err = 'Sales Order creation failed.'
                elif not res['delivery_note']:
                    err = 'Delivery Note creation failed.'
                elif not res['sales_invoice']:
                    err = 'Sales Invoice creation failed.'
                else:
                    err = 'Something went wrong.'
                err += ' Please, provide valid data.'

            fail_count += 1
            res['message'] = str(err)
            result.append(res)

    message = 'success' if success_count > 0 else 'failed'
    return format_result(
        result={
            "success_count": success_count,
            "fail_count": fail_count,
            "record": result
        },
        message=message,
        status_code=200)
