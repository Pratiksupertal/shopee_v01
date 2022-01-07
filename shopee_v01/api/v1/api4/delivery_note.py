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
def sales_delivery_note():
    '''
    Create Pick List for given Sales Order
    '''
    data = validate_data(frappe.request.data)
    try:
        pick_list_sales = create_pick_list_from_sales_order(data['sales_order'])
        pick_list_sales.save()
        pick_list_sales.submit()
    except:
        return format_result(result="There was a problem creating the Pick List", message='Error', status_code=500)

    '''
    Create Delivery Note from Pick List
    '''
    new_delivery_note = create_delivery_note(pick_list_sales.name)
    new_delivery_note.save()
    new_delivery_note.submit()

    return format_result(result={'delivery note': new_delivery_note.name}, message='Data Created', status_code=200)
