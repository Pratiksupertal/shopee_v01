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


def validate_data(data):
    if len(data) == 0 or data is None:
        return None
    try:
        data = json.loads(data)
        return data
    except ValueError:
        return "Invalid JSON submitted"


def format_result(success=None,result=None, message=None, status_code=None):
    return {
        "success": success,
        "message": message,
        "status_code": str(status_code),
        "data": result
    }


def get_last_parameter(url, link):
    param = unquote(urlparse(url).path)
    last = os.path.split(param)
    if link not in last[-1]:
        return last[-1]
    return None


def convert_to_pdf(template=None, invoice=None, weight=None, shipping=None, to_entity=None,
                   from_entity=None, address=None, address_company=None, product_list1=None,
                   delivery_type=None, b_code=None, owner=None):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    image = Image.open(dir_path + '/Tokopedia Label edit.jpg')
    draw = ImageDraw.Draw(image)
    color = 'rgb(0, 0, 0)'
    font = ImageFont.truetype(dir_path + '/OpenSans-Semibold.ttf', size=15)
    (x, y) = (320, 27)
    draw.text((x, y), template, fill=color, font=font)

    upc = barcode.get('upc', b_code, writer=barcode.writer.ImageWriter())
    img = upc.render()
    size = 280, 128
    image.paste(img.resize(size, Image.ANTIALIAS), (190, 67))

    font = ImageFont.truetype(dir_path + '/OpenSans-Semibold.ttf', size=12)

    (x, y) = (50, 70)
    draw.text((x, y), invoice, fill=color, font=font)

    (x, y) = (32, 162)
    draw.text((x, y), weight, fill=color, font=font)

    (x, y) = (118, 103)
    draw.text((x, y), delivery_type, fill=color, font=font)

    (x, y) = (116, 162)
    draw.text((x, y), shipping, fill=color, font=font)

    (x, y) = (32, 260)
    draw.text((x, y), to_entity, fill=color, font=font)

    (x, y) = (245, 260)
    draw.text((x, y), from_entity, fill=color, font=font)

    font = ImageFont.truetype(dir_path + '/OpenSans-Light.ttf', size=10)

    (x, y) = (32, 278)
    draw.text((x, y), address.replace('\n', '').replace('<br>', '\n'), fill=color, font=font)

    (x, y) = (245, 278)
    draw.text((x, y), address_company.replace('\n', '').replace('<br>', '\n'), fill=color, font=font)

    (x1, y1) = (32, 400)
    (x2, y2) = (420, 400)
    for i in product_list1:
        draw.text((x1, y1), i['item_name'], fill=color, font=font)
        draw.text((x2, y2), str(i['qty']) + ' Pcs', fill=color, font=font)
        (x1, y1), (x2, y2) = (x1, y1 + 15), (x2, y2 + 15)

    pdf_time = str(time.time())
    image.save(dir_path + '/output' + owner + pdf_time + '.pdf', resolution=500)
    with open(dir_path + '/output' + owner + pdf_time + '.pdf', "rb") as pdf_file:
        encoded_string = base64.b64encode(pdf_file.read())
    return encoded_string


def fill_barcode(item_code):
    doc = frappe.get_doc('Item', item_code)
    return str(doc.barcodes[0].barcode) if len(doc.barcodes) > 0 else ''