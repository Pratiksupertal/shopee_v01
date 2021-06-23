import json
import time
from pprint import pprint
import io
import frappe
import requests
from PIL import Image, ImageDraw, ImageFont
import base64
import os
import barcode
from urllib.parse import urlparse
import datetime as dt

base = ''


@frappe.whitelist(allow_guest=True)
def ping():
    return 'pong'


def authorize_request(header):
    print(header)


def get_request(request):
    global base
    parts = urlparse(request.url)
    base = parts.scheme + '://' + parts.hostname + (':' + str(parts.port)) if parts.port != '' else ''
    cookies = request.cookies
    return cookies


def validate_data(data):
    if len(data) == 0 or data is None:
        return None
    try:
        data = json.loads(data)
        return data
    except ValueError:
        return "Invalid JSON submitted"


def query_db(doctype, filters=None, fields=None):
    check = frappe.db.get_list(
        doctype,
        fields=fields,
        filters=filters)
    return check


def post_processing(res):
    if res.status_code != 200:
        raise requests.exceptions.HTTPError
    return res.json()


def post_document(doctype, cookies, data):
    global base
    if not cookies:
        return {'message': 'Credentials not identified. Please login first.'}
    url = base + '/api/resource/' + doctype
    res = requests.post(url.replace("'", '"'), cookies=cookies, data=data)
    return post_processing(res)


def get_document(doctype, cookies, fields=None, filters=None):
    global base
    if not cookies:
        return {'message': 'Credentials not identified. Please login first.'}
    url = base + '/api/resource/' + doctype
    if filters and fields:
        url += '?filters=' + str(filters)
        url += '&fields=' + str(fields)
    else:
        if fields:
            url += '?fields=' + str(fields)
        elif filters:
            url += '?filters=' + str(filters)

    res = requests.get(url.replace("'", '"'), cookies=cookies)
    return post_processing(res)


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


def format_result(result):
    return {
        "success": True,
        "message": "Login success",
        "status_code": 200,
        "data": result
    }


@frappe.whitelist(allow_guest=True)
def login():
    data = validate_data(frappe.request.data)
    cookies = get_request(frappe.request)
    global base
    url = base + '/api/method/login'

    res = requests.post(url.replace("'", '"'), data=data)
    response = post_processing(res)
    api_id = res.headers.get('Set-Cookie')
    return format_result([
        {
            "id": "",
            "username": response['full_name'],
            "api_key": api_id[api_id.index('=')+1:api_id.index(';')],
            "warehouse_id": ""
        }
    ])


@frappe.whitelist()
def purchases():
    # purchase_ids = query_db('Purchase Order', fields=['*'])
    cookies = get_request(frappe.request)
    result = []
    each_data_list = list(map(lambda x: frappe.get_doc('Purchase Order', x),
                              [i['name'] for i in frappe.get_list('Purchase Order')]))
    for each_data in each_data_list:
        temp_dict = {
            "id": each_data.idx,
            "po_number": each_data.name,
            "po_date": each_data.creation,
            "supplier_id": each_data.supplier,
            "supplier_name": each_data.supplier_name,
            "total_amount": each_data.grand_total,
            "total_product": each_data.total_qty,
            "products": [{
                "id": i.idx,
                "purchase_id": i.parent,
                "product_id": i.item_code,
                "product_name": i.item_name,
                "product_code": i.item_code,
                "price": i.amount,
                "quantity": i.qty,
                "unit_id": i.idx,
                "discount": i.discount_amount,
                "subtotal_amount": i.net_amount
            } for i in each_data.items],
            "type": each_data.po_type,
            "rejected_by": each_data.modified_by if each_data.docstatus == 2 else None,
            "cancelled_by": each_data.modified_by if each_data.status == 2 else None,
            "supplier_is_taxable": None,
            "total_amount_excluding_tax": each_data.base_total,
            "tax_amount": each_data.total_taxes_and_charges,
            "delivery_contact_person": None,
            "supplier_email": None,
            "supplier_work_phone": None,
            "supplier_cell_phone": None,
            "expiration_date": each_data.schedule_date,
            "payment_due_date": None if each_data.payment_schedule is None or len(each_data.payment_schedule) == 0 else each_data.payment_schedule[
                0].due_date,
            "notes": each_data.remarks,
            "rejection_notes": each_data.remarks if each_data.docstatus == 2 else None,
            "cancellation_notes": each_data.remarks if each_data.status == 2 else None,
            "delivery_address": each_data.address_display
        }
        result.append(temp_dict)

    return format_result(result)


@frappe.whitelist()
def products():
    cookies = get_request(frappe.request)
    fields = [
        'idx',
        'item_name',
        'item_code',
        'item_group',
        'weightage',
        'description'
    ]

    parts = urlparse(frappe.request.url)
    specific = parts.path.split('/')[-1] if parts.path.split('/')[-1].find('shopee_v01.api.v1.api3.') == -1 else None
    if specific:
        specific = [["item_code", "=", specific]]

    product_list = get_document('Item', fields=fields, cookies=cookies, filters=specific)
    result = []

    for i in product_list['data']:
        temp_dict = {
            "id": i['idx'],
            "name": i['item_name'],
            "code": i['item_code'],
            "category_id": i['item_group'],
            "unit_id": None,
            "weight": i['weightage'],
            "is_taxable": None,
            "description": i['description']
        }

        result.append(temp_dict)

    return format_result(result)


@frappe.whitelist()
def warehouse():
    cookies = get_request(frappe.request)
    fields = [
        'idx',
        'warehouse_name',
        'name',
        'parent',
        'warehouse_type',
    ]

    warehouse_list = get_document('Warehouse', cookies=cookies, fields=fields)
    result = []

    for i in warehouse_list['data']:
        warehouse_areas = get_document('Warehouse', cookies=cookies, fields=[
            "idx",
            "warehouse_id",
            "name",
            # "usage_type_id",
            # "description",
            "creation",
            "owner",
            "modified",
            "modified_by"
        ], filters=[["parent_warehouse", "=", i['name']]])

        temp_dict = {
            "id": i['idx'],
            "name": i['warehouse_name'],
            "code": i['name'],
            "is_headquarter": "1" if i['parent'] is None else "0",
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
            } for j in warehouse_areas['data']],
            "is_store": i['warehouse_type'],
            "default_customer_id": None
        }

        result.append(temp_dict)

    return format_result(result)


@frappe.whitelist()
def warehouseAreas():
    cookies = get_request(frappe.request)
    fields = [
        "idx",
        "warehouse_name",
        "name",
        "parent",
        "warehouse_type",
    ]

    specific = [["parent_warehouse", "!=", ""]]

    parts = urlparse(frappe.request.url)
    specific_part = parts.path.split('/')[-1] if parts.path.split('/')[-1].find(
        'shopee_v01.api.v1.api3') == -1 else None
    if specific_part:
        specific += [["name", "=", specific_part]]

    warehouse_areas_list = get_document('Warehouse', fields=fields, cookies=cookies, filters=specific)
    result = []

    for i in warehouse_areas_list['data']:
        temp_dict = {
            "id": i['idx'],
            "warehouse_id": i['name'],
            "usage_type_id": None,
            "name": i['warehouse_name'],
            "description": None,
            "storages": None
        }
        result.append(temp_dict)

    return format_result(result)


@frappe.whitelist()
def get_label():
    data = validate_data(frappe.request.data)
    cookies = get_request(frappe.request)
    fields = ['name', 'customer_name', 'company', 'address_display',
              'company_address_display', 'total_net_weight', 'payment_terms_template',
              'grand_total', 'owner']
    filters = [["Sales Invoice", "name", "=", data['id']]]
    result = get_document('Sales Invoice', fields=fields, cookies=cookies, filters=filters)

    filters = {
        'parent': ['=', data['id']]
    }

    fields = ["item_name", "qty"]
    check = query_db('Sales Invoice Item', fields=fields, filters=filters)
    info_retrieved = result['data'][0]

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


@frappe.whitelist()
def orders():
    cookies = get_request(frappe.request)

    sales_order_ids = get_document('Sales Order', cookies=cookies)
    result = []

    for i in sales_order_ids['data']:
        each_data = frappe.get_doc(
            'Sales Order',
            i['name']
        )
        sales_invoice_num = frappe.get_list('Sales Invoice Item', fields=['parent'],
                                              filters=[['sales_order', '=', i['name']]])
        temp_dict = {
            "id": each_data.idx,
            "location_id": None,
            "location_name": None,
            "order_number": each_data.name,
            "order_date": each_data.creation,
            "original_order_id": each_data.name,
            "type": each_data.order_type,
            "status": each_data.delivery_status,
            "payment_type": each_data.currency,
            "customer_id": each_data.customer,
            "customer_name": each_data.contact_display,
            "total_product": each_data.total_qty,
            "total_amount_excluding_tax": each_data.net_total,
            "discount_amount": each_data.discount_amount,
            "tax_amount": each_data.total_taxes_and_charges,
            "total_amount": each_data.grand_total,
            "products": [{
                "id": j.idx,
                "order_id": j.parent,
                "product_id": j.item_code,
                "product_name": j.item_name,
                "product_code": j.item_code,
                "price": j.rate,
                "quantity": j.qty,
                "unit_id": j.item_group,
                "discount": j.discount_amount,
                "subtotal_amount": j.base_net_amount,
                "product_condition_id": j.docstatus,
                "notes": None,
                # "isActive": None
            } for j in each_data.items],
            "notes": 'Sales Invoice: ' + '\n-'.join([i['parent'] for i in sales_invoice_num])
        }
        result.append(temp_dict)

    return format_result(result)


@frappe.whitelist()
def deliveryOrders():
    cookies = get_request(frappe.request)

    delivery_order_ids = get_document('Delivery Note', cookies=cookies)
    result = []

    for i in delivery_order_ids['data']:
        each_data = frappe.get_doc(
            'Delivery Note',
            i['name']
        )

        warehouse_data = get_document('Warehouse', cookies=cookies, fields=['warehouse_name'], filters=[['name', '=', each_data.set_warehouse]]) if each_data.set_warehouse is not None else None
        warehouse_data = warehouse_data['data'][0]['warehouse_name'] if warehouse_data is not None and len(warehouse_data['data']) > 0 else None

        temp_dict = {
            "id": each_data.idx,
            "order_id": each_data.name,
            "warehouse_id": each_data.set_warehouse,
            "warehouse_name": warehouse_data,
            "order_number": each_data.name,
            "do_number": each_data.name,
            "order_date": each_data.creation,
            "customer_name": each_data.customer_name,
            "status": each_data.status,
            "delivery_date": each_data.lr_date,
            "pretax_amount": each_data.net_total,
            "tax_amount": each_data.total_taxes_and_charges,
            "discount_amount": each_data.discount_amount,
            "extra_discount_amount": each_data.additional_discount_percentage * each_data.net_total,
            "total_amount": each_data.grand_total,
            "products": [{
                "id": i.idx,
                "delivery_order_id": i.against_sales_order,
                "product_id": i.item_code,
                "product_name": i.item_name,
                "product_code": i.item_code,
                "price": i.price_list_rate,
                "quantity": i.qty,
                "unit_id": i.item_group,
                "discount": i.discount_amount,
                "subtotal_amount": i.amount,
                "notes": None
            } for i in each_data.items]
        }
        result.append(temp_dict)

    return format_result(result)


@frappe.whitelist()
def purchaseReceive():
    cookies = get_request(frappe.request)
    data = validate_data(frappe.request.data)

    today = dt.datetime.today()

    new_doc = frappe.new_doc('Purchase Receipt')
    new_doc.posting_date = today.strftime("%Y-%m-%d")
    new_doc.supplier = data['supplier_do_number']
    new_doc.set_warehouse = data['warehouse_id']
    new_doc.modified_by = data['create_user_id']

    for item in data['products']:
        new_doc.append("items", {
            "item_code" : item['purchase_product_id'],
            "qty" : item['quantity'],
            "purchase_order" : data['purchase_id']
        })

    new_doc.insert()

    return format_result({
        "id": new_doc.name,
        "receive_number": new_doc.name,
        "supplier_do_number": new_doc.supplier,
        "receive_date": new_doc.posting_date,
        "supplier_id": new_doc.supplier
    })


@frappe.whitelist()
def stockTransfers():
    cookies = get_request(frappe.request)

    stock_entry_ids = get_document('Stock Entry', cookies=cookies)
    result = []

    for i in stock_entry_ids['data']:
        each_data = frappe.get_doc(
            'Stock Entry',
            i['name']
        )
        temp_dict = {
            "id": each_data.idx,
            "transfer_number": each_data.name,
            "transfer_date": each_data.posting_date,
            "status": each_data.docstatus,
            "from_warehouse_id": each_data.from_warehouse,
            "from_warehouse_area_id": None,
            "to_warehouse_id": each_data.to_warehouse,
            "to_warehouse_area_id": None,
            "start_datetime": None,
            "end_datetime": None,
            "notes": each_data.purpose,
            "create_user_id": each_data.modified_by,
            "create_time": each_data.creation,
            "products": [
                {
                    "id": i.idx,
                    "stock_transfer_id": i.name,
                    "product_id": i.item_code,
                    "product_name": i.item_name,
                    "product_code": i.item_name,
                    "quantity": i.qty,
                    "warehouse_area_storage_id": None
                } for i in each_data.items
            ],
            "update_user_id": each_data.modified_by,
            "product_list": [i.item_name for i in each_data.items]
        }
        result.append(temp_dict)

    return format_result(result)


@frappe.whitelist()
def stockTransfer():
    cookies = get_request(frappe.request)
    data = validate_data(frappe.request.data)
    new_doc = frappe.new_doc('Stock Entry')
    new_doc.purpose = 'Material Transfer'
    new_doc.company = data['company']
    new_doc._comments = data['notes']
    for item in data['items']:
        new_doc.append("items", {
            "item_code": item['item_code'],
            "t_warehouse": data['t_warehouse'],
            "s_warehouse": data['s_warehouse'],
            "qty": item['qty']
        })
    new_doc.set_stock_entry_type()
    new_doc.insert()
    return {
        "success": True,
        "status_code": 200,
        "message": 'Data created',
        "data": {
            "transfer_number": new_doc.name
        },
    }


@frappe.whitelist()
def stockOpname():
    cookies = get_request(frappe.request)
    data = validate_data(frappe.request.data)
    new_doc = frappe.new_doc('Stock Entry')
    new_doc.start_time = data['start_datetime']
    new_doc.end_time = data['end_datetime']
    new_doc._comments = data['notes']
    new_doc.modified_by = data['create_user_id']

    new_doc.purpose = 'Material Receipt'
    new_doc.set_stock_entry_type()
    for item in data['products']:
        new_doc.append("items", {
            "item_code" : item['product_code'],
            "qty" : item['quantity'],
            "t_warehouse" : data['warehouse_stockopname_id']
        })

    new_doc.insert()

    return {
       "success": True,
       "message": "Data created",
       "status_code": 200,
    }


@frappe.whitelist()
def stockOpnames():
    cookies = get_request(frappe.request)
    data = validate_data(frappe.request.data)
    fields = [
        'idx',
        'warehouse',
        'creation',
        '_comments',
        'posting_date',
        'posting_time',
        'modified_by'
    ]

    product_list = get_document('Stock Ledger Entry', fields=fields, cookies=cookies)

    result = []

    for i in product_list['data']:
        temp_dict = {
            "id": i['idx'],
            "warehouse_id": i['warehouse'],
            "warehouse_area_id": None,
            "start_datetime": dt.datetime.combine(dt.datetime.strptime(i['posting_date'], '%Y-%m-%d').date(),
                                                  dt.datetime.strptime(i['posting_time'], '%H:%M:%S.%f').time()),
            "end_datetime": None,
            "notes": i['_comments'],
            "create_user_id": i['modified_by'],
            "create_time": i['creation']
        }

        result.append(temp_dict)

    return format_result(result)


@frappe.whitelist()
def deliveryOrder():
    cookies = get_request(frappe.request)
    data = validate_data(frappe.request.data)

    # specific = []

    parts = urlparse(frappe.request.url)
    specific_part = parts.path.split('/')[-1] if parts.path.split('/')[-1].find(
        'shopee_v01.api.v1.api3') == -1 else None

    if specific_part:
        delivery_order = frappe.get_doc('Delivery Note', specific_part)
        delivery_order.modified_by = data['update_user_id']
    else:
        delivery_order = frappe.new_doc('Delivery Note')
        delivery_order.customer = data['create_user_id']
        delivery_order.set_warehouse = data['warehouse_id']
        for item in data['products']:
            delivery_order.append("items", {
                "item_code": item['delivery_order_product_id'],
                "qty": item['quantity'],
                # "warehouse": data['warehouse_product_lot_id']
            })

    # delivery_order.docstatus = data['status']
    # delivery_order.modified = data['update_time']
    # delivery_order.modified_by = data['update_user_id']
    delivery_order.insert()

    return {
        "success": True,
        "message": "Data created",
        "status_code": 200,
        "data": [
            {
                "do_number": delivery_order.name
            }
        ]
    }
