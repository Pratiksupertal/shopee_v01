import json
import frappe
import requests
from urllib.parse import urlparse
from frappe.utils import today

from shopee_v01.api.v1.helpers import *


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


def submit_and_sales_order_data_for_sales_order_from_web(base, res_api_response):
    sales_order_data = res_api_response.json().get("data")
    url = base + '/api/resource/Sales%20Order/'+sales_order_data['name']
    res_api_response = requests.post(url.replace("'", '"'), headers={
        "Authorization": frappe.request.headers["Authorization"]
    },data={ "run_method": "submit" })
    
    # res_api_response_final = requests.get(url.replace("'", '"'), headers={
    #     "Authorization": frappe.request.headers["Authorization"]
    # },data={})
    # sales_order_data = res_api_response_final.json().get("data")
    return sales_order_data


def submit_and_sales_invoice_data_for_sales_order_from_web(base, invoice_res_api_response):
    sales_invoice_data = invoice_res_api_response.json().get("message")
    invoice_url_2 = base + '/api/resource/Sales%20Invoice'
    invoice_res_api_response_2 = requests.post(invoice_url_2.replace("'", '"'), headers={
        "Authorization": frappe.request.headers["Authorization"]
    },data=json.dumps(sales_invoice_data))
    sales_invoice_data_2 = invoice_res_api_response_2.json()
    sales_invoice_data_2 = sales_invoice_data_2.get("data")
    
    invoice_url_3 = base + '/api/resource/Sales%20Invoice/'+sales_invoice_data_2.get('name')
    res_api_response = requests.post(invoice_url_3.replace("'", '"'), headers={
        "Authorization": frappe.request.headers["Authorization"]
    },data={ "run_method": "submit" })
    
    # res_api_response_final = requests.get(invoice_url_3.replace("'", '"'), headers={
    #     "Authorization": frappe.request.headers["Authorization"]
    # },data={})
    # sales_invoice_data_2 = res_api_response_final.json().get("data")
    return sales_invoice_data_2


def create_payment_for_sales_order_from_web(base, payment_data, sales_invoice_data_2):
    payment_url = base + '/api/resource/Payment%20Entry'
    payment_res_api_response = requests.post(payment_url.replace("'", '"'), headers={
        "Authorization": frappe.request.headers["Authorization"]
    },data=json.dumps({
        "paid_from": payment_data["paid_from"],
        "paid_to": payment_data["paid_to"],
        "paid_from_account_currency": payment_data["paid_from_account_currency"],
        "paid_to_account_currency": payment_data["paid_to_account_currency"],
        "paid_amount": payment_data["paid_amount"],
        "received_amount": payment_data["received_amount"],
        "party": payment_data.get("party"),
        "party_type": payment_data.get("party_type"),
        "reference_no": payment_data.get("reference_no"),
        "reference_date": payment_data.get("reference_date"),
        "references": [{
                "parenttype": "Payment Entry",
                "reference_doctype": "Sales Invoice",
                "reference_name": sales_invoice_data_2.get("name"),
                "due_date": None,
                "bill_no": None,
                "payment_term": None,
                "total_amount": sales_invoice_data_2.get("grand_total"),
                "outstanding_amount": sales_invoice_data_2.get("grand_total"),
                "allocated_amount": sales_invoice_data_2.get("grand_total"),
                "exchange_rate": 0,
                "doctype": "Payment Entry Reference"
        }]
    }))
    return payment_res_api_response


def submit_and_payment_data_for_sales_order_from_web(base, payment_res_api_response):
    payment_data = payment_res_api_response.json().get("data")
                            
    payment_url_2 = base + '/api/resource/Payment%20Entry/'+payment_data.get('name')
    res_api_response = requests.post(payment_url_2.replace("'", '"'), headers={
        "Authorization": frappe.request.headers["Authorization"]
    },data={ "run_method": "submit" })
    
    # res_api_response_final = requests.get(payment_url_2.replace("'", '"'), headers={
    #     "Authorization": frappe.request.headers["Authorization"]
    # },data={})
    # payment_data = res_api_response_final.json().get("data")
    return payment_data
   
    
@frappe.whitelist()
def create_sales_order_from_web():
    response = {}
    try:
        data = validate_data(frappe.request.data)
        print(data)
        order_data = data.get('order_data')
        payment_data = data.get('payment_data')
        
        data_validation_for_create_sales_order_web(order_data=order_data, payment_data=payment_data)
        
        parts = urlparse(frappe.request.url)
        base = parts.scheme + '://' + parts.hostname + (':' + str(parts.port)) if parts.port != '' else ''
        
        url = base + '/api/resource/Sales%20Order'
        res_api_response = requests.post(url.replace("'", '"'), headers={
            "Authorization": frappe.request.headers["Authorization"]
        },data=json.dumps(order_data))
        
        if res_api_response.status_code == 200:
            sales_order_data = submit_and_sales_order_data_for_sales_order_from_web(
                base=base,
                res_api_response=res_api_response
            )
            response['sales_order'] = sales_order_data.get("name")
            try:
                invoice_url = base + '/api/method/erpnext.selling.doctype.sales_order.sales_order.make_sales_invoice'
                invoice_res_api_response = requests.post(invoice_url.replace("'", '"'), headers={
                    "Authorization": frappe.request.headers["Authorization"]
                },data={"source_name": sales_order_data.get("name")})
                
                if invoice_res_api_response.status_code == 200:
                    sales_invoice_data_2 = submit_and_sales_invoice_data_for_sales_order_from_web(
                        base=base,
                        invoice_res_api_response=invoice_res_api_response
                    )
                    response['sales_invoice'] = sales_invoice_data_2.get("name")
                    try:
                        payment_res_api_response = create_payment_for_sales_order_from_web(
                            base=base,
                            payment_data=payment_data,
                            sales_invoice_data_2=sales_invoice_data_2
                        )
                        if payment_res_api_response.status_code == 200:
                            payment_data = submit_and_payment_data_for_sales_order_from_web(
                                base=base,
                                payment_res_api_response=payment_res_api_response
                            )
                            response['payment'] = payment_data.get("name")
                            return format_result(success="True", result=response, status_code=200)
                        else:
                            raise Exception(f"Please, provide valid payment information.") 
                    except Exception as e:
                        raise Exception(f"Error in stage #3 : Creating payment failed : {str(e)}")  
                else:
                    raise Exception(f"{str(invoice_res_api_response.text)}")
            except Exception as e:
                if str(e).find("stage #3") >= 0: raise Exception(str(e))
                raise Exception(f"Error in stage #2 : Creating sales invoice failed : {str(e)}")
        else:
            raise Exception(f"Error in stage #1 : Creating sales order failed : Please, provide valid order information.")
    except Exception as e:
        return format_result(success=False, result=response, message=str(e), status_code=400)
