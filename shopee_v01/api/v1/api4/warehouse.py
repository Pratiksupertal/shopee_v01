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
def warehouses():
    fields = [
        'idx',
        'warehouse_name',
        'name',
        'parent',
        'warehouse_type',
    ]

    warehouse_list = frappe.get_list('Warehouse', fields=fields)
    result = []

    for i in warehouse_list:
        warehouse_areas = frappe.get_list('Warehouse', fields=[
            "idx",
            "warehouse_id",
            "name",
            # "usage_type_id",
            # "description",
            "creation",
            "owner",
            "modified",
            "modified_by"
        ], filters={'parent_warehouse': i['name']})

        temp_dict = {
            "id": str(i['idx']),
            "name": i['warehouse_name'],
            "code": i['name'],
            "description": None,
            "areas": [{
                'id': j['idx'],
                'warehouse_id': j['warehouse_id'],
                'name': j['name'],
                'create_time': j['creation'],
                'update_time': j['modified'],
                'create_user_id': j['owner'],
                'update_user_id': j['modified_by'],
                'usage_type_id': None,
                'description': None
            } for j in warehouse_areas]
        }

        result.append(temp_dict)

    return format_result(result=result, status_code=200, message='Data Found')


@frappe.whitelist()
def warehouseAreas():
    fields = [
        "idx",
        "warehouse_name",
        "name",
        "parent",
        "warehouse_type",
    ]

    specific = {"parent_warehouse": ('!=', '')}

    specific_part = get_last_parameter(frappe.request.url, 'warehouseAreas')
    if specific_part:
        specific['name'] = specific_part

    warehouse_areas_list = frappe.get_list('Warehouse', fields=fields, filters=specific)
    result = []

    for i in warehouse_areas_list:
        temp_dict = {
            "id": str(i['idx']),
            "warehouse_id": i['name'],
            "usage_type_id": None,
            "name": i['warehouse_name'],
            "description": None,
            "storages": None
        }
        result.append(temp_dict)

    return format_result(result=result, status_code=200, message='Data Found')