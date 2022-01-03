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
def get_label():
    data = validate_data(frappe.request.data)
    fields = ['name', 'customer_name', 'company', 'address_display',
              'company_address_display', 'total_net_weight', 'payment_terms_template',
              'grand_total', 'owner']
    filters = {"name": data['id']}
    result = frappe.get_list('Sales Invoice', fields=fields, filters=filters)

    filters = {
        'parent': data['id']
    }

    fields = ["item_name", "qty"]
    check = frappe.get_list(
        'Sales Invoice Item',
        fields=fields,
        filters=filters)
    info_retrieved = result[0]

    pdf_binary = convert_to_pdf(
        template=str(info_retrieved['payment_terms_template']), invoice=str(info_retrieved['name']),
        weight=str(info_retrieved['total_net_weight']), shipping=str(info_retrieved['grand_total']),
        to_entity=str(info_retrieved['customer_name']), from_entity=str(info_retrieved['company']),
        address=str(info_retrieved['address_display']), address_company=str(info_retrieved['company_address_display']),
        product_list1=check, delivery_type='Regular \nShipping', b_code=str('123456789012'),
        owner=str(info_retrieved['owner'])
    )

    return {
        "pdf_bin": str(pdf_binary)
    }