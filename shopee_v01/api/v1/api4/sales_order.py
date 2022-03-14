import json
import frappe
import requests
from urllib.parse import urlparse
from frappe.utils import today

from shopee_v01.api.v1.helpers import *


@frappe.whitelist()
def create_sales_order():
    res = {}
    try:
        data = validate_data(frappe.request.data)
        order_data = data.get("order_data")
        accounting_dimensions = data.get("accounting_dimensions", {})
        
        if not order_data.get("delivery_date"):
            order_data["delivery_date"] = today()
        if not order_data.get("external_so_number") or not order_data.get("source_app_name"):
            raise Exception("Sales order Number and Source app name both are required")
        
        base = get_base_url(url=frappe.request.url)
        
        sales_order = create_and_submit_sales_order(
            base=base,
            order_data=order_data,
            submit=True
        )
        
        if sales_order.status_code==200:
            sales_order = sales_order.json().get('data')
            so_name = sales_order.get("name")
            print(so_name)
            
            res['sales_order'] = so_name
            
            sales_invoice = create_and_submit_sales_invoice_from_sales_order(
                base=base,
                source_name=so_name,
                accounting_dimensions=accounting_dimensions,
                submit=True
            )
            res['sales_invoice'] = sales_invoice.get('name')
            
            delivery_note = create_and_submit_delivery_note_from_sales_order(
                base=base,
                source_name=so_name,
                submit=True
            )
            res['delivery_note'] = delivery_note.get('name')
            
            return format_result(success=True, result=res)
        else: raise Exception()
    except Exception as e:
        return format_result(result=res, message=f'{str(e)}', status_code=400, success=False, exception=str(e))


@frappe.whitelist()
def create_sales_order_all():
    data = validate_data(frappe.request.data)
    result = []
    res = {}
    success_count, fail_count = 0, 0
    data=data.get("sales_order")
    for order in list(data):
        try:
            if not order.get("delivery_date"):
                order["delivery_date"] = today()
            if not order.get("external_so_number") or not  order.get("source_app_name"):
                raise Exception("Sales order Number and Source app name both are required")
            base = get_base_url(url=frappe.request.url)
            url = base + '/api/resource/Sales%20Order'
            order["docstatus"]=1
            res_api_response = requests.post(url.replace("'", '"'), headers={
                "Authorization": frappe.request.headers["Authorization"]
            },data=json.dumps(order))
            message = None
            if res_api_response.status_code==200:
                dn_data = res_api_response.json()
                dn_data = dn_data["data"]
                try:
                    dn_raw_data = base + '/api/method/erpnext.selling.doctype.sales_order.sales_order.make_delivery_note'
                    dn_res_api_response = requests.post(dn_raw_data.replace("'", '"'), headers={
                        "Authorization": frappe.request.headers["Authorization"]
                    },data={"source_name": dn_data.get("name")})
                    dn_raw = dn_res_api_response.json().get("message")
                    dn_raw['docstatus']=1
                    dn_url = base + '/api/resource/Delivery%20Note'
                    delivery_note_api_response = requests.post(dn_url.replace("'", '"'), headers={
                        "Authorization": frappe.request.headers["Authorization"]
                    },data=json.dumps(dn_raw))
                except Exception as e:
                    message="Delivery Note Failed"
                success_count += 1
                result.append({
                        "external_so_number": order.get("external_so_number"),
                        "sales_order": dn_data.get("name"),
                        "message": "success" if not message else message
                    })
            else:
                raise Exception('Invalid order data. Sales order creation failed.')
        except Exception as err:
            fail_count += 1
            result.append({
                "external_so_number": order.get("external_so_number"),
                "message": f"failed: {str(err)}"
            })
    return format_result(result={
            "success_count": success_count,
            "fail_count": fail_count,
            "sales_order": result
        }, message="success", status_code=200)