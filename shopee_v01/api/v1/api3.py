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
    # print(url)
    res = requests.post(url.replace("'", '"'), cookies=cookies, data=data)
    # print(res.raw)
    return post_processing(res)


def get_document(doctype, cookies, fields=None, filters=None):
    global base
    if not cookies:
        return {'message': 'Credentials not identified. Please login first.'}
    url = base + '/api/resource/' + doctype
    # print(url)
    if filters and fields:
        url += '?filters=' + str(filters)
        url += '&fields=' + str(fields)
    else:
        if fields:
            url += '?fields=' + str(fields)
        elif filters:
            url += '?filters=' + str(filters)
    # print(url)

    res = requests.get(url.replace("'", '"'), cookies=cookies)
    # print(res)
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
    # template = "Full Payment - COD"
    draw.text((x, y), template, fill=color, font=font)

    upc = barcode.get('upc', b_code, writer=barcode.writer.ImageWriter())
    img = upc.render()
    size = 280, 128
    image.paste(img.resize(size, Image.ANTIALIAS), (190, 67))

    font = ImageFont.truetype(dir_path + '/OpenSans-Semibold.ttf', size=12)

    (x, y) = (50, 70)
    # invoice = "Invoice"
    draw.text((x, y), invoice, fill=color, font=font)

    (x, y) = (32, 162)
    # weight = "weight"
    draw.text((x, y), weight, fill=color, font=font)

    (x, y) = (118, 103)
    # delivery_type = "Regular shipping"
    draw.text((x, y), delivery_type, fill=color, font=font)

    (x, y) = (116, 162)
    # shipping = "shipping"
    draw.text((x, y), shipping, fill=color, font=font)

    (x, y) = (32, 260)
    # to_entity = "to entity"
    draw.text((x, y), to_entity, fill=color, font=font)

    (x, y) = (245, 260)
    # from_entity = "from entity"
    draw.text((x, y), from_entity, fill=color, font=font)

    font = ImageFont.truetype(dir_path + '/OpenSans-Light.ttf', size=10)

    (x, y) = (32, 278)
    # address = "Jl. Customer 2 no 2<br>Bogor<br>\nJawa Barat<br>16000<br>Indonesia<br>\n"
    draw.text((x, y), address.replace('\n', '').replace('<br>', '\n'), fill=color, font=font)

    (x, y) = (245, 278)
    # address_company = "Jl. Customer 2 no 2<br>Bogor<br>\nJawa Barat<br>16000<br>Indonesia<br>\n"
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


@frappe.whitelist(allow_guest=True)
def test():
    cookies = get_request(frappe.request)
    return get_document('Purchase Order', cookies=cookies)


def format_result(result):
    return {
        "success": True,
        "message": "Login success",
        "status_code": 200,
        "data": result
    }


@frappe.whitelist()
def purchases():
    cookies = get_request(frappe.request)

    purchase_ids = get_document('Purchase Order', cookies=cookies)
    result = []

    for i in purchase_ids['data']:
        each_data = frappe.get_doc(
            'Purchase Order',
            i['name']
        )

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
            "payment_due_date": None if len(each_data.payment_schedule) == 0 else each_data.payment_schedule[
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

        # for j in warehouse_areas['data']:
        #
        #     j.update({
        #         "usage_type_id": None,
        #         "description": None
        #     })

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

    # import os
    # with open(os.path.expanduser('/home/sid/PycharmProjects/supertal/mamba2/mamba-frappe-bench/apps/shopee_v01/shopee_v01/api/v1/test.pdf'), 'wb') as fout:
    #      fout.write(base64.decodebytes(pdf_binary))

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
        # print(sales_invoice_num[0].parent)
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
    # if specific_part:
    #     specific += [["name", "=", specific_part]]

    # delivery_order = get_document('Delivery Note', filters=specific, cookies=cookies, fields=['*'])
    delivery_order = frappe.get_doc('Delivery Note', specific_part)
    # delivery_order.docstatus = data['status']
    delivery_order.modified = data['update_time']
    delivery_order.modified_by = data['update_user_id']
    delivery_order.insert()
    delivery_order.save()

    # print(delivery_order)
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


@frappe.whitelist()
def stockOpname():
    data = validate_data(frappe.request.data)

    # delivery_order = get_document('Delivery Note', filters=specific, cookies=cookies, fields=['*'])
    # stock_ledger = frappe.get_doc('Stock Ledger Entry', data['warehouse_stockopname_id'])
    # delivery_order.docstatus = data['status']
    stock_ledger = frappe.new_doc('Stock Ledger Entry')

    stock_ledger.modified = data['update_time']
    stock_ledger.modified_by = data['update_user_id']
    stock_ledger.insert()
    # delivery_order.save()

    # print(delivery_order)
    return {
        "success": True,
        "message": "Data created",
        "status_code": 200,
    }


@frappe.whitelist()
def stockTransfer():
    cookies = get_request(frappe.request)
    data = validate_data(frappe.request.data)
    stock_transfer = frappe.get_doc('Stock Entry')




@frappe.whitelist()
def purchaseReceive():
    cookies = get_request(frappe.request)
    data = validate_data(frappe.request.data)
    purchase_order_items = frappe.get_doc(
        'Purchase Order',
        data['purchase_id']
    ).items
    # print('-----------------1')
    purchase_receipt = frappe.new_doc(
        'Purchase Receipt'
    )
    # print('-----------------2')
    # pprint(dir(purchase_receipt))
    dic = {item.item_name: item for item in purchase_order_items}
    for i in data["products"]:
        # print(i)
        dic[i['name']].qty = i['qty']
        # print('-----------------yo')
        # purchase_receipt.items.append(dic[i['name']])
    # print('------------------------------3')
    purchase_receipt.insert()
    # print('-----------------4')

    return 'done'
    # temp_dict = {
    #     # "doctype" : "Purchase Order",
    #     "naming_series": "PUR-ORD-.YYYY.-",
    #     "supplier": "ALVINDO 2",
    #     "company": "ISS",
    #     "transaction_date": "2021-05-26",
    #     "currency": "IDR",
    #     "conversion_rate": "1.0",
    #     "items": [],
    #     "status": "0",
    #     "name": "BLDG202105-0008"
    # }
    # print('sent')

    # Approach - get_doc to create
    # doc = frappe.get_doc(temp_dict)
    # doc.insert()
    # doc.save()
    # print(res)
    # return 'done'

    # Approach - new_doc
    # doc = frappe.new_doc('Purchase Receipt')
    # print('--------------------------------')
    # doc.name = ''
    # doc.items = []
    # doc.supplier = 'Supplier 3 Raw'
    # doc.currency = 'USD'
    # print('--------------------->>>>>>>>>>>>>>')
    # res = doc.insert(
    #     ignore_permissions=True, # ignore write permissions during insert
    #     ignore_links=True, # ignore Link validation in the document
    #     ignore_if_duplicate=True, # dont insert if DuplicateEntryError is thrown
    #     ignore_mandatory=True # insert even if mandatory fields are not set
    # )
    # return doc.as_dict()

    # Approach - test get last doc
    # doc = frappe.get_last_doc('Purchase Receipt')
    # print(doc)
    # return doc.as_dict()

    # Approach - 4
    # return post_document('Purchase Order', cookies=cookies, data=temp_dict)
