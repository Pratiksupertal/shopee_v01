import json
import frappe
import requests
from urllib.parse import urlparse

from shopee_v01.api.v1.helpers import *
from shopee_v01.api.v1.validations import *


def create_payment_for_sales_order_from_web(base, payment_data, sales_invoice_data, accounting_dimensions):
    try:
        payment_url = base + '/api/resource/Payment%20Entry'
        payment_data.update({
            "doctype": 1,
            "docstatus": 1,
            "references": [{
                    "parenttype": "Payment Entry",
                    "reference_doctype": "Sales Invoice",
                    "reference_name": sales_invoice_data.get("name"),
                    "due_date": None,
                    "bill_no": None,
                    "payment_term": None,
                    "total_amount": sales_invoice_data.get("grand_total"),
                    "outstanding_amount": sales_invoice_data.get("grand_total"),
                    "allocated_amount": sales_invoice_data.get("grand_total"),
                    "exchange_rate": 0,
                    "doctype": "Payment Entry Reference"
            }]
        })
        payment_data.update(accounting_dimensions)
        payment_res_api_response = requests.post(payment_url.replace("'", '"'), headers={
            "Authorization": frappe.request.headers["Authorization"]
        },data=json.dumps(payment_data))
        if payment_res_api_response.status_code != 200:
            raise Exception('Please, provide valid payment information.')
        return payment_res_api_response.json().get("data")
    except Exception as e:
        raise Exception(f'Problem in creating payment entry. Reason: {str(e)}')


@frappe.whitelist()
def create_sales_order_from_web():
    response = {
        'sales_order': None,
        'sales_invoice': None,
        'payment_entry': None
    }
    try:
        data = validate_data(frappe.request.data)
        order_data = data.get('order_data')
        accounting_dimensions = data.get("accounting_dimensions", {})
        payment_data = data.get('payment_data')
        
        if not accounting_dimensions.get('region'):
            accounting_dimensions['region'] = frappe.db.get_value('Territory', accounting_dimensions.get("city"), 'parent')

        data_validation_for_create_sales_order_web(order_data=order_data, payment_data=payment_data)

        base = get_base_url(url=frappe.request.url)
        
        sales_order = create_and_submit_sales_order(
            base=base,
            order_data=order_data,
            submit=True
        )
        
        if sales_order.status_code!=200:
            raise Exception('Sales order not created. Please, provide valid data. ')
            
        sales_order = sales_order.json().get('data')
        so_name = sales_order.get("name")
        print(so_name)
        
        response['sales_order'] = so_name
        
        sales_invoice = create_and_submit_sales_invoice_from_sales_order(
            base=base,
            source_name=so_name,
            accounting_dimensions=accounting_dimensions,
            submit=True
        )
        response['sales_invoice'] = sales_invoice.get('name')
        
        payment_entry = create_payment_for_sales_order_from_web(
            base=base,
            payment_data=payment_data,
            sales_invoice_data=sales_invoice,
            accounting_dimensions=accounting_dimensions
        )
        response['payment_entry'] = payment_entry.get("name")
        
        return format_result(success="True", result=response, status_code=200)
            
    except Exception as e:
        if len(str(e)) < 1:
            if not response['sales_order']: e = 'Sales Order creation failed.'
            elif not response['sales_invoice']: e = 'Sales Invoice creation failed.'
            elif not response['payment_entry']: e = 'Payment Entry creation failed.'
            else: e = 'Something went wrong.'
            e += ' Please, provide valid data.'
        return format_result(success=False, result=response, message=str(e), status_code=400)