import json
import frappe
import requests
from urllib.parse import urlparse
from frappe.utils import today

from shopee_v01.api.v1.helpers import *


@frappe.whitelist()
def create_sales_order():
    try:
        res = {}
        order=validate_data(frappe.request.data)
        if not order.get("delivery_date"):
            order["delivery_date"] = today()

        if not order.get("delivery_date"):
            order["delivery_date"] = today()

        if not order.get("external_so_number") or not order.get("source_app_name"):
            raise Exception("Sales order Number and Source app name both are required")
        parts = urlparse(frappe.request.url)
        base = parts.scheme + '://' + parts.hostname + (':' + str(parts.port)) if parts.port != '' else ''
        url = base + '/api/resource/Sales%20Order'
        res_api_response = requests.post(url.replace("'", '"'), headers={
            "Authorization": frappe.request.headers["Authorization"]
        },data=json.dumps(order))
        if res_api_response.status_code==200:
            dn_data = res_api_response.json()
            dn_data = dn_data["data"]
            url = base + '/api/resource/Sales%20Order/'+dn_data['name']
            res_api_response = requests.post(url.replace("'", '"'), headers={
                "Authorization": frappe.request.headers["Authorization"]
            },data={ "run_method": "submit" })
            res['sales_order']=dn_data
            dn_json = {}
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
                res['delivery_note']= delivery_note_api_response.json().get("data").get("name")
            except Exception as e:
                return format_result(success="False",result="Delivery Note Failed",message=str(e))
            return format_result(success="True",result=res)
        return format_result(result="There was a problem creating the Sales Order", message="Error", status_code=res_api_response.status_code)
    except Exception as e:
        return format_result(result="Sales Order not created", message=str(e),status_code=400)


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
            url = base + '/api/resource/Sales%20Order'
            order["docstatus"]=1
            res_api_response = requests.post(url.replace("'", '"'), headers={
                "Authorization": frappe.request.headers["Authorization"]
            },data=json.dumps(order))
            if res_api_response.status_code==200:
                dn_data = res_api_response.json()
                dn_data = dn_data["data"]
                dn_json = {}
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
                    # return True
                except Exception as e:
                    return format_result(success="False",result="Delivery Note Failed",message = e)
            success_count += 1
            result.append({
                    "external_so_number": order.get("external_so_number"),
                    "message": "success"
                })


        except Exception as err:
            print("\n\n",str(err),"\n\n")
            fail_count += 1
            result.append({
                "external_so_number": order.get("external_so_number"),
                "message": "failed"
            })
    return format_result(result={
            "success_count": success_count,
            "fail_count": fail_count,
            "sales_order": result
        }, message="success", status_code=200)