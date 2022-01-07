import datetime
import json
import time
import frappe
import requests
from PIL import Image, ImageDraw, ImageFont
import base64
import os
import barcode
import traceback
from urllib.parse import urlparse, unquote, parse_qs
import datetime as dt
from frappe.utils import today
from erpnext.stock.doctype.pick_list.pick_list import create_stock_entry, create_delivery_note
from erpnext.stock.doctype.material_request.material_request import create_pick_list
from erpnext.selling.doctype.sales_order.sales_order import create_pick_list as create_pick_list_from_sales_order
from erpnext.stock.doctype.pick_list.pick_list import get_available_item_locations, get_items_with_location_and_quantity
from frappe import _

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
                delivery_note = frappe.new_doc("Delivery Note")
                delivery_note.customer = dn_data["customer"]
                for item in dn_data['items']:
                    delivery_note.append("items", {
                        "item_code": item['item_code'],
                        "qty": str(item['qty']),
                        "warehouse": item['warehouse'],
                        "rate":item['rate']
                        # "against_sales_order":item['parent']
                    })
                delivery_note.save()
                delivery_note.submit()
                res['delivery_note']= delivery_note.name
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
            new_so = frappe.new_doc("Sales Order")
            new_so.customer = order.get("customer")
            new_so.delivery_date = order.get("delivery_date")
            item_dict = {}
            for item in order.get("items"):
                new_so.append("items",{
                    "description":item['description'],
                    "item_code":item['item_code'],
                    "qty":item['qty'],
                    "rate":item['rate'],
                    "warehouse":item['warehouse']
                })
            new_so.save()
            new_so.submit()
            frappe.db.commit()
            res["sales_order"]= new_so.name
            try:
                delivery_note = frappe.new_doc("Delivery Note")
                delivery_note.customer = order.get("customer")
                for item in order.get("items"):
                    delivery_note.append("items", {
                        "item_code": item['item_code'],
                        "qty": str(item['qty']),
                        "warehouse": item['warehouse'],
                        # "against_sales_order":item['parent']
                    })
                delivery_note.save()
                delivery_note.submit()
                # res['delivery_note']= delivery_note.name
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