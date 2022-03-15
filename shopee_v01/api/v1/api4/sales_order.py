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
    if data: data = data.get('data', [])
    else: return format_result(message='No data found', status_code=400, success=False, exception='No data found')
    
    result = []
    success_count, fail_count = 0, 0
    
    for record in list(data):
        res = {
            'sales_order': None,
            'sales_invoice': None,
            'delivery_note': None,
            'status': 'failed'
        }
        try:
            order_data = record.get('order_data', {})
            accounting_dimensions = record.get('accounting_dimensions', {})
            
            if not order_data.get("delivery_date"):
                order_data["delivery_date"] = today()
            if not order_data.get("external_so_number") or not  order_data.get("source_app_name"):
                raise Exception("Sales order Number and Source app name both are required")
            
            res['external_so_number'] = order_data.get('external_so_number')
            
            base = get_base_url(url=frappe.request.url)
        
            sales_order = create_and_submit_sales_order(
                base=base,
                order_data=order_data,
                submit=True
            )
            
            print(sales_order.text)
            
            if sales_order.status_code==200:
                sales_order = sales_order.json().get('data')
                so_name = sales_order.get("name")
                
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
                res['status'] = 'success'
                res['message'] = "Successfully created"
                success_count += 1
                result.append(res)
                
            else: raise Exception()
            
        except Exception as err:
            fail_count += 1
            res['message'] = str(err)
            result.append(res)
            
    return format_result(result={
            "success_count": success_count,
            "fail_count": fail_count,
            "record": result
        }, message="success", status_code=200)