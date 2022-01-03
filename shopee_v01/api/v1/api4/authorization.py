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


@frappe.whitelist(allow_guest=True)
def login():
    data = validate_data(frappe.request.data)
    parts = urlparse(frappe.request.url)
    base = parts.scheme + '://' + parts.hostname + (':' + str(parts.port)) if parts.port != '' else ''

    url = base + '/api/method/login'
    res = requests.post(url.replace("'", '"'), data=data)
    if res.status_code != 200:
        return format_result(message='Login Failed', status_code=403, result='Entered credentials are invalid!')
    else:
        user_data = frappe.get_doc('User', {'email': data['usr']})
        url = base + '/api/method/frappe.core.doctype.user.user.generate_keys?user=' + user_data.name
        res_api_secret = requests.get(url.replace("'", '"'), cookies=res.cookies)
        api_secret = res_api_secret.json()
        try:
            warehouse_data = frappe.db.get_list('User Warehouse Mapping', filters={
                'user_id': user_data.email}, fields=['warehouse_id'])
            warehouse_id = warehouse_data[0].warehouse_id
        except:
            warehouse_id = None

        print(str(user_data.api_key + ':' + api_secret['message']['api_secret']))
        return format_result(message='Login Success', status_code=200, result={
            "id": str(user_data.idx),
            "username": str(user_data.username),
            "api_key": str(user_data.api_key + ':' + api_secret['message']['api_secret']),
            "warehouse_id": str(warehouse_id)
        })