import json
import time
import frappe
import requests
from PIL import Image, ImageDraw, ImageFont
import base64
import os
import barcode
from urllib.parse import urlparse, unquote
from erpnext.stock.doctype.pick_list.pick_list import get_available_item_locations, get_items_with_location_and_quantity
from frappe import _


import re


def cleanhtml(raw_html):
    if not raw_html: return raw_html
    if not type(raw_html) == str: return raw_html
    CLEANR = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')
    cleantext = re.sub(CLEANR, '', raw_html)
    return cleantext


def validate_data(data):
    if not data: return data
    if not len(data): return data
    try:
        return json.loads(data)
    except ValueError:
        return "Invalid JSON submitted"


def format_result(success=None, result=None, message=None, status_code=None, exception=None):
    if success == None:
        success = True if status_code in [None, 200, 201] and not exception else False
    if status_code == None:
        status_code = 200 if success and not exception else 400
    if message == None:
        message = exception if not message and exception else "success"
    if not success or status_code not in [200, 201]:
        if not exception: exception = message
    
    indicator = "green" if success else "red"
    raise_exception = 1 if exception else 0
    
    return {
        "success": success,
        "message": cleanhtml(message),
        "status_code": str(status_code),
        "data": result,
        "_server_messages": [
            {
                "message": cleanhtml(exception),
                "indicator": indicator,
                "raise_exception": raise_exception
            }
        ]
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


def set_item_locations(pick_list, save=False):
    items = pick_list.aggregate_item_qty()
    pick_list.item_location_map = frappe._dict()

    from_warehouses = None
    if pick_list.parent_warehouse:
        from_warehouses = frappe.db.get_descendants('Warehouse', pick_list.parent_warehouse)

    # reset
    pick_list.delete_key('locations')
    for item_doc in items:
        item_code = item_doc.item_code

        pick_list.item_location_map.setdefault(item_code,
                                          get_available_item_locations(item_code, from_warehouses,
                                                                       pick_list.item_count_map.get(item_code),
                                                                       pick_list.company))

        locations = get_items_with_location_and_quantity(item_doc, pick_list.item_location_map)

        item_doc.idx = None
        item_doc.name = None

        for row in locations:
            row.update({
                'picked_qty': row.stock_qty
            })

            location = item_doc.as_dict()
            location.update(row)
            pick_list.append('locations', location)

    return pick_list


def update_stock_entry_based_on_material_request(pick_list, stock_entry):
    from  erpnext.stock.doctype.pick_list.pick_list import update_common_item_properties
    for location in pick_list.locations:
        target_warehouse = None
        if location.material_request_item:
            target_warehouse = frappe.get_value('Material Request Item',
				location.material_request_item, 'warehouse')
        item = frappe._dict()
        update_common_item_properties(item, location)
        item.t_warehouse = target_warehouse
        stock_entry.append('items', item)
    return stock_entry


def update_stock_entry_based_on_sales_order(pick_list, stock_entry):
    from  erpnext.stock.doctype.pick_list.pick_list import update_common_item_properties
    for location in pick_list.locations:
        target_warehouse = None
        item = frappe._dict()
        update_common_item_properties(item, location)
        item.t_warehouse = "Collecting Area Finish Good Out - ISS"
        stock_entry.append('items', item)
    return stock_entry


def pick_list_with_mtr(stock_entry_pick_list):
    """
    Filter by status - only Submitted PL allowed
    Filter by `material_request type` = [ Material Transfer | Manufacture | Material Issue ]
    Filter by Stock Entry - overlapped PL will be removed
    """
    pick_list = frappe.db.get_list('Pick List',
        filters={
            "docstatus": 1,
            "purpose": ["in", ["Material Transfer", "Material Transfer for Manufecture", "Manufacture", "Material Issue"]]
        },
        fields=["name", "purpose", "parent_warehouse"]
    )

    pick_list_for_mtr = {}
    for item in pick_list:
        pick_list_id = item.get('name')
        if not pick_list_id: continue
        # if the pick list is in the stock entry, we have to filter them out
        if pick_list_id in stock_entry_pick_list: continue
        pick_list_for_mtr[pick_list_id] = {}
        pick_list_for_mtr[pick_list_id]["type"] = item.get("purpose")
        pick_list_for_mtr[pick_list_id]["parent_warehouse"] = item.get("parent_warehouse")
        pick_list_for_mtr[pick_list_id]["items"] = frappe.db.get_list('Pick List Item',
            filters={
                "parent": pick_list_id
            },
            fields=["item_code", "item_name", "warehouse", "uom", "qty"]
        )
    return pick_list_for_mtr


def pick_list_with_so(stock_entry_pick_list):
    """
    For Sales Order
    """
    pick_list_items = frappe.db.get_list('Pick List Item',
             filters={
                'sales_order': ['like', 'SAL-ORD-%'],
                'docstatus': 1
             },
             fields=['parent', 'sales_order', 'item_code', 'item_name', 'warehouse', "uom", 'qty']
      )
    pick_list_for_so = {}
    for item in pick_list_items:
        pick_list_id = item.get('parent')
        if not pick_list_id: continue
        # if the pick list is in the stock entry, we have to filter them out
        if pick_list_id in stock_entry_pick_list: continue
        if pick_list_id not in pick_list_for_so:
            pick_list_for_so[pick_list_id] = {}
            pick_list_for_so[pick_list_id]["sales_order"] = item.get("sales_order")
            pick_list_for_so[pick_list_id]["items"] = []
        pick_list_for_so[pick_list_id]["items"].append({
            "item_code": item.get("item_code"),
            "item_name": item.get("item_name"),
            "warehouse": item.get("warehouse"),
            "uom": item.get("uom"),
            "qty": item.get("qty")
        })
    return pick_list_for_so


def picklist_item(data):
    item = frappe.db.get_list('Pick List Item',
                filters={
                    'parent': data.get("pick_list"),
                    'item_code': data.get('item_code'),
                    'warehouse': data.get('s_warehouse'),
                    'parentfield': 'locations'
                },
                fields=['name', 'item_name', 'qty', 'picked_qty']
            )
    if len(item) < 1: raise Exception('Pick list, item code or warehouse invalid!')
    return item[0]


def create_new_stock_entry_for_single_item(data, item):
    picklist_details = frappe.db.get_value('Pick List', data.get('pick_list'), ['company', 'purpose'])
    
    new_doc_stock_entry = frappe.new_doc('Stock Entry')
    new_doc_stock_entry.company = picklist_details[0]
    new_doc_stock_entry.purpose = picklist_details[1]
    
    new_doc_stock_entry.pick_list = data.get('pick_list')
    
    new_doc_stock_entry.append("items", {
        "item_code": data.get("item_code"),
        "item_name": item.get("item_name"),
        "t_warehouse": data.get("t_warehouse"),
        "s_warehouse": data.get("s_warehouse"),
        "qty": data.get("picked_qty")
    })
    new_doc_stock_entry.stock_entry_type = data.get("stock_entry_type")
    new_doc_stock_entry.save()
    new_doc_stock_entry.submit()
    return new_doc_stock_entry


def picklist_details_for_submit_picklist_and_create_stockentry(url):
    picklist_details = requests.get(url.replace("'", '"'), headers={
        "Authorization": frappe.request.headers["Authorization"]
    },data={})
    if picklist_details.status_code != 200:
        raise Exception("Picklist name is not found")
    return picklist_details.json().get("data")


def create_and_submit_stock_entry_submit_picklist_and_create_stockentry(data, picklist_details):
    new_doc_stock_entry = frappe.new_doc('Stock Entry')
    new_doc_stock_entry.company = picklist_details.get('company')
    new_doc_stock_entry.purpose = picklist_details.get('purpose')
    
    new_doc_stock_entry.pick_list = data.get('pick_list')
    
    for item in picklist_details.get('locations'):
        picked_qty = item['qty'] - item['picked_qty']
        if picked_qty <= 0.0: continue
        new_doc_stock_entry.append("items", {
            "item_code": item['item_code'],
            "item_name": item['item_name'],
            "t_warehouse": data.get("t_warehouse"),
            "s_warehouse": data.get("s_warehouse"),
            "qty": picked_qty
        })
    if len(new_doc_stock_entry.get("items")) <= 0:
        raise Exception('No picked items found. Can not create stock entry.')
    new_doc_stock_entry.stock_entry_type = data.get("stock_entry_type")
    new_doc_stock_entry.save()
    new_doc_stock_entry.submit()
    return new_doc_stock_entry


def get_base_url(url):
    parts = urlparse(url)
    base = parts.scheme + '://' + parts.hostname + (':' + str(parts.port)) if parts.port != '' else ''
    return base


def check_delivery_note_status(pick_list):
    delivery_note = frappe.db.get_list('Delivery Note',
                        filters={
                            'pick_list': pick_list
                        },
                        fields=['docstatus', 'owner']
                    )
    # if delivery note not exist, return 9
    if not delivery_note: return 9, None
    creator_name = frappe.db.get_value('User', delivery_note[0].get('owner'), 'full_name')
    return delivery_note[0].get('docstatus'), creator_name


def get_item_bar_code(item_code):
    try:
        values = {'item_code': item_code}
        data = frappe.db.sql("""SELECT item_bar_code FROM `tabItem` WHERE item_code=%(item_code)s""", values=values)
        if data: return data[0][0]
        return None
    except Exception as e:
        print('Exception occured in fetching barcode\n------\n', str(e))
        return None


def create_and_submit_sales_order(base, order_data, submit=False):
    try:
        url = base + '/api/resource/Sales%20Order'
        if submit: order_data['docstatus'] = 1
        sales_order = requests.post(url.replace("'", '"'), headers={
            "Authorization": frappe.request.headers["Authorization"]
        },data=json.dumps(order_data))
        return sales_order
    except Exception as e:
        raise Exception(f'Problem in creating sales order. Reason: {str(e)}')


def create_and_submit_sales_invoice_from_sales_order(base, source_name, accounting_dimensions, submit=False):
    try:
        invoice_url = base + '/api/method/erpnext.selling.doctype.sales_order.sales_order.make_sales_invoice'
        invoice_res_api_response = requests.post(invoice_url.replace("'", '"'), headers={
            "Authorization": frappe.request.headers["Authorization"]
        },data={"source_name": source_name})
        sales_invoice_data = invoice_res_api_response.json().get("message")
        
        print(sales_invoice_data)
        
        if submit: sales_invoice_data['docstatus'] = 1
        sales_invoice_data.update(accounting_dimensions)
        
        print(sales_invoice_data)
        
        invoice_url_2 = base + '/api/resource/Sales%20Invoice'
        invoice_res_api_response_2 = requests.post(invoice_url_2.replace("'", '"'), headers={
            "Authorization": frappe.request.headers["Authorization"]
        },data=json.dumps(sales_invoice_data))
        
        if invoice_res_api_response_2.status_code != 200:
            raise Exception('Please, provide valid information.')
        
        sales_invoice_data_2 = invoice_res_api_response_2.json().get("data")
        return sales_invoice_data_2
    except Exception as e:
        raise Exception(f'Problem in creating sales invoice. Reason: {str(e)}')


def create_and_submit_delivery_note_from_sales_order(base, source_name, submit=False):
    try:
        dn_url = base + '/api/method/erpnext.selling.doctype.sales_order.sales_order.make_delivery_note'
        dn_res_api_response = requests.post(dn_url.replace("'", '"'), headers={
            "Authorization": frappe.request.headers["Authorization"]
        },data={"source_name": source_name})
        dn_data = dn_res_api_response.json().get("message")
        if submit: dn_data['docstatus'] = 1
        dn_url_2 = base + '/api/resource/Delivery%20Note'
        dn_res_api_response_2 = requests.post(dn_url_2.replace("'", '"'), headers={
            "Authorization": frappe.request.headers["Authorization"]
        },data=json.dumps(dn_data))
        
        if dn_res_api_response_2.status_code != 200:
            raise Exception('Please, provide valid information.')
        
        dn_data_2 = dn_res_api_response_2.json().get("data")
        return dn_data_2
    except Exception as e:
        raise Exception(f'Problem in creating delivery note. Reason: {str(e)}')