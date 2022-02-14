import datetime
from distutils.log import error
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
from frappe.utils import now_datetime
parts = urlparse(frappe.request.url)
base = parts.scheme + '://' + parts.hostname + (':' + str(parts.port)) if parts.port != '' else ''

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


@frappe.whitelist(allow_guest=True)
def login():
    try:
        data = validate_data(frappe.request.data)
        parts = urlparse(frappe.request.url)
        base = parts.scheme + '://' + parts.hostname + (':' + str(parts.port)) if parts.port != '' else ''

        url = base + '/api/method/login'
        res = requests.post(url.replace("'", '"'), data=data)
        if res.status_code != 200:
            raise Exception('Entered credentials are invalid!')
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
    except Exception as e:
        return format_result(status_code=403, message=f'Login Failed. {str(e)}', exception=str(e))


def fill_barcode(item_code):
    doc = frappe.get_doc('Item', item_code)
    return str(doc.barcodes[0].barcode) if len(doc.barcodes) > 0 else ''


@frappe.whitelist()
def purchases():
    result = []

    each_data_list = list(map(lambda x: frappe.get_doc('Purchase Order', x),
                              [i['name'] for i in frappe.get_list('Purchase Order',filters={'docstatus':1})]))

    for each_data in each_data_list:
        temp_dict = {
            "id": each_data.name,
            "po_number": each_data.name,
            "po_date": each_data.creation,
            "supplier_id": each_data.supplier,
            "supplier_name": each_data.supplier_name,
            "total_amount": str(each_data.grand_total),
            "total_product": str(each_data.total_qty),
            "products": [{
                "id": str(i.idx),
                "purchase_id": i.parent,
                "product_id": i.item_code,
                "product_name": i.item_name,
                "product_code": i.item_code,
                "barcode": fill_barcode(i.item_code),
                "price": str(int(i.amount) if i.amount else ''),
                "warehouse":i.warehouse,
                "quantity": int(i.qty) if i.qty else 0,
                "received_qty": int(i.received_qty) if i.received_qty else 0,
                "unit_id": str(i.idx),
                "discount": str(int(i.discount_amount) if i.discount_amount else ''),
                "subtotal_amount": str(int(i.net_amount) if i.net_amount else '')
            } for i in each_data.items],
            "type": each_data.po_type,
            "rejected_by": each_data.modified_by if each_data.docstatus == 2 else None,
            "cancelled_by": each_data.modified_by if each_data.status == 2 else None,
            "supplier_is_taxable": None,
            "total_amount_excluding_tax": str(each_data.base_total),
            "tax_amount": str(each_data.total_taxes_and_charges),
            "delivery_contact_person": None,
            "supplier_email": None,
            "supplier_work_phone": None,
            "supplier_cell_phone": None,
            "expiration_date": each_data.schedule_date,
            "payment_due_date": None if each_data.payment_schedule is None or len(each_data.payment_schedule) == 0 else
            each_data.payment_schedule[
                0].due_date,
            "notes": each_data.remarks,
            "rejection_notes": each_data.remarks if each_data.docstatus == 2 else None,
            "cancellation_notes": each_data.remarks if each_data.status == 2 else None,
            "delivery_address": each_data.address_display
        }
        result.append(temp_dict)

    return format_result(message='Data found', result=result, status_code=200)


@frappe.whitelist()
def products():
    fields = [
        'idx',
        'item_name',
        'item_code',
        'item_group',
        'weightage',
        'description'
    ]

    specific = get_last_parameter(frappe.request.url, 'products')

    if specific:
        specific = {'item_code': specific}

    data_list = frappe.get_list('Item', fields=fields, filters=specific)

    try:
        query_limit = int(parse_qs(urlparse(frappe.request.url).query)['limit'][0])
        query_page = int(parse_qs(urlparse(frappe.request.url).query)['page'][0])
        each_data_list_length = len(data_list)
        each_data_list = data_list[min(each_data_list_length, query_page * query_limit) : min(each_data_list_length, (query_page + 1) * query_limit)]
    except:
        traceback.print_exc()
        each_data_list = data_list
        query_limit = len(data_list)
        query_page = 0


    result = []

    for i in each_data_list:
        temp_dict = {
            "id": str(i['idx']),
            "name": i['item_name'],
            "code": i['item_code'],
            "category_id": i['item_group'],
            "barcode": fill_barcode(i['item_code']),
            "unit_id": None,
            "weight": str(i['weightage']),
            "is_taxable": None,
            "description": i['description']
        }

        result.append(temp_dict)

    return format_result(result=result, status_code=200, message={
        'Total records': len(data_list),
        'Limit': query_limit,
        'Page': query_page
    })


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


@frappe.whitelist()
def purchaseReceive():
    try:
        data = validate_data(frappe.request.data)
        today = dt.datetime.today()
        po_name = data['products'][0]['purchase_id']
        validate_po = frappe.db.get_list('Purchase Order',
        filters = {'name':po_name,'docstatus':1,'status':['not in',['Closed', 'On Hold']],'per_received':['<', 99.99] },
        fields = ['name']
        )
        if len(validate_po) < 1:
            msg = "Purchase Receipt is not created for Purchase order {0}".format(po_name)
            return format_result(success="False",status_code=500, message = msg, result={
            })
        else:
            new_doc = frappe.new_doc('Purchase Receipt')
            new_doc.posting_date = today.strftime("%Y-%m-%d")
            supplier = frappe.db.get_value("Purchase Order",{"name":po_name},"supplier")
            new_doc.supplier = supplier
            new_doc.supplier_travel_document_number = data['supplier_do_number']
            new_doc.set_warehouse = data['warehouse_id']
            for item in data['products']:
                new_doc.append("items", {
                    "item_code": item['purchase_product_id'],
                    "qty": item['quantity'],
                    "purchase_order":item['purchase_id']
                })
                """Adding receive_qty"""
                purchase_order_item = frappe.db.get_list('Purchase Order Item',
                                       filters = {
                                           'parent': item['purchase_id'],
                                           'item_code': item['purchase_product_id'],
                                       },
                                       fields=['name', 'received_qty']
                                       )
                if len(purchase_order_item)==1:
                    purchase_order_item=purchase_order_item[0]
                    frappe.db.set_value('Purchase Order Item', purchase_order_item.get('name'), {
                        'received_qty': (int(purchase_order_item.get('received_qty')) if purchase_order_item.get(
                            'received_qty') else 0.0) + int(item['quantity'])
                    })
                else:
                    print(purchase_order_item, item['purchase_id'], item['purchase_product_id'])

            new_doc.insert()
            new_doc.submit()

            return format_result(status_code=200, message='Purchase Receipt Created', result={
                "id": str(new_doc.name),
                "receive_number": new_doc.name,
                "supplier_do_number": new_doc.supplier_travel_document_number,
                "receive_date": new_doc.posting_date,
                "supplier_id": new_doc.supplier
            })
    except Exception as e:
        return format_result(success="False",status_code=500, message = "Purchase Receipt API Fail", result=e)

@frappe.whitelist()
def stockOpname():
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
            "item_code": item['product_code'],
            "qty": item['quantity'],
            "t_warehouse": data['warehouse_stockopname_id']
        })

    new_doc.insert()

    return {
        "success": True,
        "message": "Data created",
        "status_code": 200,
    }


@frappe.whitelist()
def stockOpnames():
    fields = [
        'idx',
        'warehouse',
        'creation',
        '_comments',
        'posting_date',
        'posting_time',
        'modified_by'
    ]

    product_list = frappe.get_list('Stock Ledger Entry', fields=fields)

    result = []

    for i in product_list:
        temp_dict = {
            "id": str(i['idx']),
            "warehouse_id": i['warehouse'],
            "warehouse_area_id": None,
            "start_datetime": dt.datetime.combine(i['posting_date'],
                                                  (dt.datetime.min + i['posting_time']).time()
                                                  ),
            "end_datetime": None,
            "notes": i['_comments'],
            "create_user_id": i['modified_by'],
            "create_time": i['creation']
        }

        result.append(temp_dict)

    return format_result(result=result, status_code=200, message='Data Found')


@frappe.whitelist()
def orders():
    each_data_list = list(map(lambda x: frappe.get_doc('Sales Order', x),
                              [i['name'] for i in frappe.get_list('Sales Order')]))
    result = []

    for each_data in each_data_list:
        sales_invoice_num = frappe.get_list('Sales Invoice Item', fields=['parent'],
                                            filters=[['sales_order', '=', each_data.name]])

        temp_dict = {
            "id": str(each_data.idx),
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
                "id": str(j.idx),
                "order_id": j.parent,
                "product_id": j.item_code,
                "product_name": j.item_name,
                "product_code": j.item_code,
                "price": j.rate,
                "barcode": fill_barcode(j.item_code),
                "quantity": j.qty,
                "source_warehouse": j.warehouse,
                "unit_id": j.item_group,
                "discount": j.discount_amount,
                "subtotal_amount": j.base_net_amount,
                "product_condition_id": j.docstatus,
                "notes": None,
                # "isActive": None
            } for j in each_data.items],
            "notes": ('Sales Invoice: ' if len(sales_invoice_num) > 0 else '' ) +
                                                                          '\n-'.join(
                                                                            [i['parent'] for i in sales_invoice_num])
        }
        result.append(temp_dict)

    return format_result(result=result, status_code=200, message='Data Found')


@frappe.whitelist()
def deliveryOrders():
    each_data_list = list(map(lambda x: frappe.get_doc('Delivery Note', x),
                              [i['name'] for i in frappe.get_list('Delivery Note')]))
    result = []
    for each_data in each_data_list:

        try:
            warehouse_data = frappe.get_doc('Warehouse', each_data.set_warehouse).warehouse_name or None
        except:
            warehouse_data = None

        temp_dict = {
            "id": str(each_data.idx),
            "order_id": each_data.name,
            "warehouse_id": each_data.set_warehouse,
            "warehouse_name": warehouse_data,
            "order_number": each_data.name,
            "do_number": each_data.name,
            "order_date": each_data.creation,
            "customer_name": each_data.customer_name,
            "status": each_data.status,
            "delivery_date": each_data.lr_date,
            "pretax_amount": str(each_data.net_total),
            "tax_amount": str(each_data.total_taxes_and_charges),
            "discount_amount": str(each_data.discount_amount),
            "extra_discount_amount": str(each_data.additional_discount_percentage * each_data.net_total),
            "total_amount": str(each_data.grand_total),
            "products": [{
                "id": str(i.idx),
                "delivery_order_id": i.against_sales_order,
                "product_id": i.item_code,
                "product_name": i.item_name,
                "product_code": i.item_code,
                "price": str(i.price_list_rate),
                "barcode": fill_barcode(i.item_code),
                "quantity": str(i.qty),
                "unit_id": i.item_group,
                "discount": str(i.discount_amount),
                "subtotal_amount": str(i.amount),
                "notes": None
            } for i in each_data.items]
        }
        result.append(temp_dict)

    return format_result(result=result, message='Data Found', status_code=200)


@frappe.whitelist()
def deliveryOrder():
    data = validate_data(frappe.request.data)

    specific_part = get_last_parameter(frappe.request.url, 'deliveryOrder')

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
                "qty": str(item['quantity']),
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


@frappe.whitelist()
def stockTransfer():
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
            "qty": str(item['qty'])
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
def stockTransfers():
    each_data_list = list(map(lambda x: frappe.get_doc('Stock Entry', x),
                              [i['name'] for i in frappe.get_list('Stock Entry',
                                                                  filters={'purpose': 'Material Transfer'}
                                                                  )
                               ]))
    result = []

    for each_data in each_data_list:
        temp_dict = {
            "id": str(each_data.idx),
            "transfer_number": each_data.name,
            "transfer_date": each_data.posting_date,
            "status": str(each_data.docstatus),
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
                    "id": str(i.idx),
                    "stock_transfer_id": i.name,
                    "product_id": i.item_code,
                    "product_name": i.item_name,
                    "product_code": i.item_name,
                    "barcode": fill_barcode(i.item_code),
                    "quantity": str(i.qty),
                    "warehouse_area_storage_id": None
                } for i in each_data.items
            ],
            "update_user_id": each_data.modified_by,
            "product_list": [i.item_name for i in each_data.items]
        }
        result.append(temp_dict)

    return format_result(result=result, message='Data Found', status_code=200)


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


@frappe.whitelist()
def material_stock_entry():
    '''
    Processing Material Request
    '''
    data = validate_data(frappe.request.data)
    new_doc_material_request = frappe.new_doc('Material Request')
    new_doc_material_request.material_request_type = "Material Transfer"

    if 'get_items_doc' in data:
        for num in data['get_items_doc_no']:
            source_doc = frappe.get_doc(data['get_items_doc'], num)
            for item in source_doc.items:
                new_doc_material_request.append("items", {
                    "item_code": item.item_code,
                    "qty": item.qty,
                    # "uom": item["uom"],
                    # "conversion_factor": item["conversion_factor"],
                    "schedule_date": data['schedule_date'] or today(),
                    "warehouse": source_doc.set_warehouse,
                })
    else:
        for item in data["items"]:
            new_doc_material_request.append("items", {
                "item_code": item['item_code'],
                "qty": item["qty"],
                "uom": item["uom"],
                "conversion_factor": item["conversion_factor"],
                "schedule_date": item['schedule_date'] or today(),
                "warehouse": item['target_warehouse'],
            })
    new_doc_material_request.save()
    new_doc_material_request.submit()

    '''
    Generating Pick List from Material Request
    '''
    new_doc_pick_list = create_pick_list(new_doc_material_request.name)
    new_doc_pick_list.parent_warehouse = data['parent_warehouse']
    new_doc_pick_list = set_item_locations(new_doc_pick_list)
    new_doc_pick_list.save()
    new_doc_pick_list.submit()

    '''
    Generating Stock Entry from Pick List
    '''
    stock_entry_dict = create_stock_entry(new_doc_pick_list.as_json())
    new_doc_stock_entry = frappe.new_doc('Stock Entry')
    new_doc_stock_entry.company = stock_entry_dict['company']
    new_doc_stock_entry.purpose = stock_entry_dict['purpose']
    for item in stock_entry_dict['items']:
        new_doc_stock_entry.append("items", {
            "item_code": item['item_code'],
            "t_warehouse": item['t_warehouse'],
            "s_warehouse": item['s_warehouse'],
            "qty": item['qty'],
            "basic_rate": item['basic_rate'],
            "cost_center": item['cost_center']
        })
    new_doc_stock_entry.stock_entry_type = stock_entry_dict["stock_entry_type"]

    new_doc_stock_entry.save()
    # new_doc_stock_entry.submit()

    return format_result(result={'stock entry': new_doc_stock_entry.name,
                                 'items': new_doc_stock_entry.items
                                 }, message='Data Created', status_code=200)


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


@frappe.whitelist()
def material_requests():
    each_data_list = list(map(lambda x: frappe.get_doc('Material Request', x),
                              [i['name'] for i in frappe.get_list('Material Request')]))
    return format_result(result=each_data_list, status_code=200, message='Data Found')


@frappe.whitelist()
def stock_entry():
    data = validate_data(frappe.request.data)
    new_doc = frappe.new_doc('Stock Entry')
    new_doc.start_time = data['start_datetime']
    new_doc.end_time = data['end_datetime']
    new_doc._comments = data['notes']

    new_doc.purpose = data['purpose']
    new_doc.set_stock_entry_type()

    if data['purpose'] not in ['Material Receipt']:
        for doc in data['get_item_doc_id']:
            item_list = frappe.get_doc(data['get_items_from'], doc)
            for item in item_list.items:
                new_doc.append("items", {
                    "item_code": item.item_code,
                    "qty": item.qty,
                    "t_warehouse": data['target_warehouse_stockopname_id'],
                    "s_warehouse": data['source_warehouse_stockopname_id']
                })
    else:
        for doc in data['get_item_doc_id']:
            item_list = frappe.get_doc(data['get_items_from'], doc)
            for item in item_list.items:
                new_doc.append("items", {
                    "item_code": item.item_code,
                    "qty": item.qty,
                    "t_warehouse": data['target_warehouse_stockopname_id'],
                })

    new_doc.insert()

    return format_result(result=new_doc.name, status_code=200, message='Data Created')


@frappe.whitelist()
def submit_stock_entry():
    data = validate_data(frappe.request.data)
    stock_entry_doc = frappe.get_doc('Stock Entry', data['id'])
    if 'add_items' in data:
        for item in data['add_items']:
            stock_entry_doc.append("items", {
                "item_code": item['item_id'],
                "qty": item['qty'],
                "t_warehouse": item['target_warehouse_id'],
                "s_warehouse": item['source_warehouse_id'],
            })

    if 'edit_items' in data:
        for item in data['edit_items']:
            for se_item in stock_entry_doc.items:
                if se_item.item_code == item['item_id']:
                    se_item.qty = item['qty']
                    se_item.t_warehouse = item['target_warehouse_id']
                    se_item.s_warehouse = item['source_warehouse_id']

    stock_entry_doc.save()
    stock_entry_doc.submit()

    return format_result(result={'stock entry': stock_entry_doc.name,
                                 'items': stock_entry_doc.items
                                 }, message='Data Created', status_code=200)


@frappe.whitelist()
def stock_entry_send_to_warehouse():
    try:
        data = validate_data(frappe.request.data)
        new_doc = frappe.new_doc('Stock Entry')
        new_doc.purpose = 'Send To Warehouse'
        new_doc.company = data['company']
        new_doc._comments = data['notes']
        for item in data['items']:
            new_doc.append("items", {
                "item_code": item['item_code'],
                "t_warehouse": 'Virtual Transit - ISS',
                "s_warehouse": item['s_warehouse'],
                "qty": str(item['qty'])
            })
        new_doc.set_stock_entry_type()
        new_doc.insert()
        new_doc.submit()
        return {
            "success": True,
            "status_code": 200,
            "message": 'Data created',
            "data": {
                "transfer_number": new_doc.name,
                "items": new_doc.items
            },
        }
    except Exception as e:
        return format_result(success = "False",message='Stock Entry is not created', status_code=500, exception=str(e))

@frappe.whitelist()
def get_stock_entry_send_to_warehouse():
    each_data_list = list(map(lambda x: frappe.get_doc('Stock Entry', x),
                              [i['name'] for i in frappe.get_list('Stock Entry',
                                                                  filters={'purpose': 'Send To Warehouse',
                                                                           'docstatus': 1}
                                                                  )
                               ]))

    return format_result(result=each_data_list, message='Data Found', status_code=200)


@frappe.whitelist()
def stock_entry_receive_at_warehouse():
    try:
        data = validate_data(frappe.request.data)
        new_doc = frappe.new_doc('Stock Entry')
        new_doc.purpose = 'Receive at Warehouse'
        new_doc.company = data['company']
        new_doc.outgoing_stock_entry = data['send_to_warehouse_id']
        new_doc._comments = data['notes']
        for item in data['items']:
            new_doc.append("items", {
                "item_code": item['item_code'],
                "t_warehouse": item['t_warehouse'],
                "s_warehouse": item['s_warehouse'],
                "qty": int(item['qty'])
            })
        new_doc.set_stock_entry_type()
        new_doc.insert()
        new_doc.submit()
        return {
            "success": True,
            "status_code": 200,
            "message": 'Data created',
            "data": {
                "transfer_number": new_doc.name,
                "items": new_doc.items
            },
        }
    except Exception as e:
        return format_result(success="False",message='Stock Entry is not created', status_code=500)


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
                dn_raw_data = base + '/api/method/erpnext.selling.doctype.sales_order.sales_order.make_delivery_note'
                dn_res_api_response = requests.post(dn_raw_data.replace("'", '"'), headers={
                    "Authorization": frappe.request.headers["Authorization"]
                },data={"source_name": dn_data.get("name")})
                dn_raw = dn_res_api_response.json().get("message")
                dn_raw['docstatus']=1
                dn_url = base + '/api/resource/Delivery%20Note'
                delivery_note_api_response = requests.post(dn_url.replace("'", '"'), headers={
                    "Authorization": frappe.request.headers["Authorization"]
                },data=json.dumps(dn_raw))
                res['delivery_note']= delivery_note_api_response.json().get("data").get("name")
            except Exception as e:
                raise Exception('Delivery note failed')
            return format_result(success=True, result=res)
        raise Exception('There was a problem creating the Sales Order')
    except Exception as e:
        return format_result(result=res, message=f'{str(e)}', status_code=400, success=False, exception=str(e))


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
            url = base + '/api/resource/Sales%20Order'
            order["docstatus"]=1
            res_api_response = requests.post(url.replace("'", '"'), headers={
                "Authorization": frappe.request.headers["Authorization"]
            },data=json.dumps(order))
            message = None
            if res_api_response.status_code==200:
                dn_data = res_api_response.json()
                dn_data = dn_data["data"]
                try:
                    dn_raw_data = base + '/api/method/erpnext.selling.doctype.sales_order.sales_order.make_delivery_note'
                    dn_res_api_response = requests.post(dn_raw_data.replace("'", '"'), headers={
                        "Authorization": frappe.request.headers["Authorization"]
                    },data={"source_name": dn_data.get("name")})
                    dn_raw = dn_res_api_response.json().get("message")
                    dn_raw['docstatus']=1
                    dn_url = base + '/api/resource/Delivery%20Note'
                    delivery_note_api_response = requests.post(dn_url.replace("'", '"'), headers={
                        "Authorization": frappe.request.headers["Authorization"]
                    },data=json.dumps(dn_raw))
                except Exception as e:
                    message="Delivery Note Failed"
                success_count += 1
                result.append({
                        "external_so_number": order.get("external_so_number"),
                        "sales_order": dn_data.get("name"),
                        "message": "success" if not message else message
                    })
            else:
                raise Exception('Invalid order data. Sales order creation failed.')
        except Exception as err:
            fail_count += 1
            result.append({
                "external_so_number": order.get("external_so_number"),
                "message": f"failed: {str(err)}"
            })
    return format_result(result={
            "success_count": success_count,
            "fail_count": fail_count,
            "sales_order": result
        }, message="success", status_code=200)



@frappe.whitelist()
def pickList():
    submitted_pick_list = frappe.db.get_list('Pick List',
             filters={
                 'docstatus': 1
             },

             fields=['name']
      )
    stock_entry_pick_list = frappe.db.get_list('Stock Entry',
            filters={
                'pick_list': ['like', '%PICK%']
            },
            fields=['pick_list']
      )
    submitted_pick_list = [order.get('name') for order in submitted_pick_list]
    stock_entry_pick_list = [order.get('pick_list') for order in stock_entry_pick_list]
    result = [order for order in submitted_pick_list if order not in stock_entry_pick_list]
    return format_result(result=result, status_code=200, message='Data Found')

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

@frappe.whitelist()
def submit_picklist():
    data = validate_data(frappe.request.data)
    try:
        pick_list = frappe.get_doc('Pick List',data['picklist'])
        if pick_list.docstatus == 0 :
            pick_list.submit()
    except Exception as e:
        frappe.log_error(title="submit_picklist API",message =frappe.get_traceback())
        return format_result(success="False",status_code=500, message = "PickList is not Submitted")
    from  erpnext.stock.doctype.pick_list.pick_list import validate_item_locations
    validate_item_locations(pick_list)
    if frappe.db.exists('Stock Entry', {'pick_list': data['picklist'],'docstatus' :1 }):
        return format_result(success="False",status_code=500, message = "Stock Entry has been already created against this Pick List")
    stock_entry = frappe.new_doc('Stock Entry')
    stock_entry.pick_list = pick_list.get('name')
    stock_entry.purpose = pick_list.get('purpose') if pick_list.get('purpose') !="Delivery" else ""
    stock_entry.set_stock_entry_type()
    if pick_list.get('material_request'):
        stock_entry = update_stock_entry_based_on_material_request(pick_list, stock_entry)
    else:
        return format_result(success="False",status_code=500, message = "Stock Entry has been already created against this Pick List")
        return frappe.msgprint(_('Stock Entry for Sales Order linked Pick List cant be done'))
    stock_entry.set_incoming_rate()
    stock_entry.set_actual_qty()
    stock_entry.calculate_rate_and_amount(update_finished_item_rate=False)
    stock_entry.save()
    stock_entry.submit()
    return format_result(result={
            "stock_entry": stock_entry.name,
            "picklist": stock_entry.pick_list
        }, message="success", status_code=200)

@frappe.whitelist()
def update_current_stock():
    try:
        data = validate_data(frappe.request.data)
        doc = frappe.get_doc("Pick List",data['picklist'])
        doc.set_item_locations(save=True)
        return format_result(message="success", status_code=200)
    except Exception as e:
        frappe.log_error(title="update_current_stock API",message =frappe.get_traceback())
        return e

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


@frappe.whitelist()
def pick_list_with_mtr_and_so():
    stock_entry_pick_list = frappe.db.get_list('Stock Entry',
            filters={
                'pick_list': ['like', '%PICK%']
            },
            fields=['pick_list']
      )
    stock_entry_pick_list = list(map(lambda order: order.get('pick_list'), list(stock_entry_pick_list)))

    pick_list_for_mtr = pick_list_with_mtr(stock_entry_pick_list)
    pick_list_for_so = pick_list_with_so(stock_entry_pick_list)
    return format_result(result={
        "pick_list_for_mtr": pick_list_for_mtr,
        "pick_list_for_so": pick_list_for_so
    }, status_code=200, message='Data Found')


def data_validation_for_create_sales_order_web(order_data, payment_data):
    if not order_data.get("delivery_date"):
        order_data["delivery_date"] = today()
    if not order_data.get("delivery_date"):
        order_data["delivery_date"] = today()
    if not order_data.get("items"):
        raise Exception("Required data missing : Unable to proceed : Items are required")
    if not order_data.get("external_so_number") or not order_data.get("source_app_name"):
        raise Exception("Required data missing : Unable to proceed : Sales order Number and Source app name both are required")

    if not payment_data.get("paid_from"):
        raise Exception("Required data missing : Unable to proceed : Paid from is required")
    if not payment_data.get("paid_to"):
        raise Exception("Required data missing : Unable to proceed : Paid to is required")
    if not payment_data.get("paid_from_account_currency"):
        raise Exception("Required data missing : Unable to proceed : Paid from account currency is required")
    if not payment_data.get("paid_to_account_currency"):
        raise Exception("Required data missing : Unable to proceed : Paid to accountcurrency is required")
    if not payment_data.get("paid_amount"):
        raise Exception("Required data missing : Unable to proceed : Paid amount is required")
    if not payment_data.get("received_amount"):
        raise Exception("Required data missing : Unable to proceed : Received amount is required")
    if not payment_data.get("reference_no"):
        raise Exception("Required data missing : Unable to proceed : Reference no is required")
    if not payment_data.get("reference_date"):
        raise Exception("Required data missing : Unable to proceed : Reference date is required")
    if not payment_data.get("mode_of_payment"):
        raise Exception("Required data missing : Unable to proceed : Payment Mode is required")


def submit_and_sales_order_data_for_sales_order_from_web(base, res_api_response):
    sales_order_data = res_api_response.json().get("data")
    url = base + '/api/resource/Sales%20Order/'+sales_order_data['name']
    res_api_response = requests.post(url.replace("'", '"'), headers={
        "Authorization": frappe.request.headers["Authorization"]
    },data={ "run_method": "submit" })

    # res_api_response_final = requests.get(url.replace("'", '"'), headers={
    #     "Authorization": frappe.request.headers["Authorization"]
    # },data={})
    # sales_order_data = res_api_response_final.json().get("data")
    return sales_order_data


def submit_and_sales_invoice_data_for_sales_order_from_web(base, invoice_res_api_response):
    sales_invoice_data = invoice_res_api_response.json().get("message")
    invoice_url_2 = base + '/api/resource/Sales%20Invoice'
    invoice_res_api_response_2 = requests.post(invoice_url_2.replace("'", '"'), headers={
        "Authorization": frappe.request.headers["Authorization"]
    },data=json.dumps(sales_invoice_data))
    sales_invoice_data_2 = invoice_res_api_response_2.json()
    sales_invoice_data_2 = sales_invoice_data_2.get("data")

    invoice_url_3 = base + '/api/resource/Sales%20Invoice/'+sales_invoice_data_2.get('name')
    res_api_response = requests.post(invoice_url_3.replace("'", '"'), headers={
        "Authorization": frappe.request.headers["Authorization"]
    },data={ "run_method": "submit" })

    # res_api_response_final = requests.get(invoice_url_3.replace("'", '"'), headers={
    #     "Authorization": frappe.request.headers["Authorization"]
    # },data={})
    # sales_invoice_data_2 = res_api_response_final.json().get("data")
    return sales_invoice_data_2


def create_payment_for_sales_order_from_web(base, payment_data, sales_invoice_data_2):
    payment_url = base + '/api/resource/Payment%20Entry'
    payment_data_final = {
        "paid_from": payment_data["paid_from"],
        "paid_to": payment_data["paid_to"],
        "paid_from_account_currency": payment_data["paid_from_account_currency"],
        "paid_to_account_currency": payment_data["paid_to_account_currency"],
        "paid_amount": payment_data["paid_amount"],
        "received_amount": payment_data["received_amount"],
        "party": payment_data.get("party"),
        "party_type": payment_data.get("party_type"),
        "reference_no": payment_data.get("reference_no"),
        "reference_date": payment_data.get("reference_date"),
        "mode_of_payment": payment_data.get("mode_of_payment"),
        "references": [{
                "parenttype": "Payment Entry",
                "reference_doctype": "Sales Invoice",
                "reference_name": sales_invoice_data_2.get("name"),
                "due_date": None,
                "bill_no": None,
                "payment_term": None,
                "total_amount": sales_invoice_data_2.get("grand_total"),
                "outstanding_amount": sales_invoice_data_2.get("grand_total"),
                "allocated_amount": sales_invoice_data_2.get("grand_total"),
                "exchange_rate": 0,
                "doctype": "Payment Entry Reference"
        }]
    }
    if payment_data.get("payment_type"):
        payment_data_final["payment_type"] = payment_data.get("payment_type")
    payment_res_api_response = requests.post(payment_url.replace("'", '"'), headers={
        "Authorization": frappe.request.headers["Authorization"]
    },data=json.dumps(payment_data_final))
    return payment_res_api_response


def submit_and_payment_data_for_sales_order_from_web(base, payment_res_api_response):
    payment_data = payment_res_api_response.json().get("data")

    payment_url_2 = base + '/api/resource/Payment%20Entry/'+payment_data.get('name')
    res_api_response = requests.post(payment_url_2.replace("'", '"'), headers={
        "Authorization": frappe.request.headers["Authorization"]
    },data={ "run_method": "submit" })

    # res_api_response_final = requests.get(payment_url_2.replace("'", '"'), headers={
    #     "Authorization": frappe.request.headers["Authorization"]
    # },data={})
    # payment_data = res_api_response_final.json().get("data")
    return payment_data


@frappe.whitelist()
def create_sales_order_from_web():
    response = {}
    try:
        data = validate_data(frappe.request.data)
        print(data)
        order_data = data.get('order_data')
        payment_data = data.get('payment_data')

        data_validation_for_create_sales_order_web(order_data=order_data, payment_data=payment_data)

        parts = urlparse(frappe.request.url)
        base = parts.scheme + '://' + parts.hostname + (':' + str(parts.port)) if parts.port != '' else ''

        url = base + '/api/resource/Sales%20Order'
        res_api_response = requests.post(url.replace("'", '"'), headers={
            "Authorization": frappe.request.headers["Authorization"]
        },data=json.dumps(order_data))

        if res_api_response.status_code == 200:
            sales_order_data = submit_and_sales_order_data_for_sales_order_from_web(
                base=base,
                res_api_response=res_api_response
            )
            response['sales_order'] = sales_order_data.get("name")
            try:
                invoice_url = base + '/api/method/erpnext.selling.doctype.sales_order.sales_order.make_sales_invoice'
                invoice_res_api_response = requests.post(invoice_url.replace("'", '"'), headers={
                    "Authorization": frappe.request.headers["Authorization"]
                },data={"source_name": sales_order_data.get("name")})

                if invoice_res_api_response.status_code == 200:
                    sales_invoice_data_2 = submit_and_sales_invoice_data_for_sales_order_from_web(
                        base=base,
                        invoice_res_api_response=invoice_res_api_response
                    )
                    response['sales_invoice'] = sales_invoice_data_2.get("name")
                    try:
                        payment_res_api_response = create_payment_for_sales_order_from_web(
                            base=base,
                            payment_data=payment_data,
                            sales_invoice_data_2=sales_invoice_data_2
                        )
                        if payment_res_api_response.status_code == 200:
                            payment_data = submit_and_payment_data_for_sales_order_from_web(
                                base=base,
                                payment_res_api_response=payment_res_api_response
                            )
                            response['payment'] = payment_data.get("name")
                            return format_result(success="True", result=response, status_code=200)
                        else:
                            raise Exception(f"Please, provide valid payment information.")
                    except Exception as e:
                        raise Exception(f"Error in stage #3 : Creating payment failed : {str(e)}")
                else:
                    raise Exception(f"{str(invoice_res_api_response.text)}")
            except Exception as e:
                if str(e).find("stage #3") >= 0: raise Exception(str(e))
                raise Exception(f"Error in stage #2 : Creating sales invoice failed : {str(e)}")
        else:
            raise Exception(f"Error in stage #1 : Creating sales order failed : Please, provide valid order information.")
    except Exception as e:
        return format_result(success=False, result=response, message=str(e), status_code=400)


@frappe.whitelist()
def filter_picklist():
    try:
        url = frappe.request.url
        docstatus = parse_qs(urlparse(url).query).get('docstatus')
        purpose = parse_qs(urlparse(url).query).get('purpose')
        if docstatus: docstatus = docstatus[0]
        if purpose: purpose = purpose[0]
        filtered_picklist = frappe.db.get_list('Pick List',
                filters={
                    'docstatus': docstatus,
                    'purpose': purpose
                },
                fields=['name', 'customer']
        )
        result = []
        for pl in filtered_picklist:
            items = frappe.db.get_list('Pick List Item',
                    filters={
                        'parent': pl.get("name"),
                        'parentfield': 'locations'
                    },
                    fields=['qty', 'picked_qty', 'sales_order']
                )
            sum_qty = sum([it.get('qty') if it.get('qty') not in ['', None] else 0 for it in items])
            sum_picked_qty = sum([it.get('picked_qty') if it.get('picked_qty') not in ['', None] else 0 for it in items])
            
            if len(items) < 1: continue
            
            sales_order = items[0].get('sales_order')
            so_date_data = frappe.db.get_value('Sales Order', sales_order, ['transaction_date', 'delivery_date'])
            
            result.append({
                "name": pl.get("name"),
                "customer": pl.get("customer"),
                "sales_order": sales_order,
                "transaction_date": so_date_data[0],
                "delivery_date": so_date_data[1],
                "total_product": len(items),
                "total_qty": sum_qty,
                "total_qty_received": sum_qty-sum_picked_qty
            })
        return format_result(result=result, success=True, status_code=200, message='Data Found')
    except Exception as e:
        return format_result(result=None, success=False, status_code=400, message=str(e))


@frappe.whitelist()
def filter_stock_entry_for_warehouse_app():
    try:
        url = frappe.request.url
        stock_entry_type = parse_qs(urlparse(url).query).get('stock_entry_type')
        order_purpose = parse_qs(urlparse(url).query).get('order_purpose')
        if stock_entry_type is not None: stock_entry_type = stock_entry_type[0]
        if order_purpose is not None: order_purpose = order_purpose[0]

        """filter by
        1. stock entry type as per request
        2. not fully transferred (status in Draft or Goods In Transit)
        3. picklist be there
        """
        filtered_se = frappe.db.get_list('Stock Entry',
                filters={
                    'stock_entry_type': stock_entry_type,
                    'per_transferred': ('!=', int(100)),
                    'pick_list': ('not in', (None, ''))
                },
                fields=['name', 'pick_list']
        )

        """filter by
        4. order purpose as per request
        """
        filtered_se = [se for se in filtered_se
            if order_purpose == frappe.db.get_value('Pick List', se.get('pick_list'), 'purpose')
        ]

        """find and add other necessary fields"""
        for se in filtered_se:
            se['customer_name'] = frappe.db.get_value('Pick List', se.get('pick_list'), 'customer')
            items_pl = frappe.db.get_list('Pick List Item',
                    filters={
                        'parent': se.get("pick_list"),
                        'parentfield': 'locations'
                    },
                    fields=['sales_order', 'qty']
                )
            if len(items_pl) < 1: continue
            sales_order = items_pl[0].get('sales_order')
            se['sales_order'] = sales_order
            
            so_date_data = frappe.db.get_value('Sales Order', sales_order, ['transaction_date', 'delivery_date'])
            if so_date_data:
                se['transaction_date'] = so_date_data[0]
                se['delivery_date'] = so_date_data[1]
            
            items_se = frappe.db.get_list('Stock Entry Detail',
                    filters={
                        'parent': se.get("name")
                    },
                    fields=['qty']
                )
            
            se['total_product'] = len(items_se)
            se['total qty'] = sum([ise.get('qty') for ise in items_se])

        return format_result(result=filtered_se, success=True, status_code=200, message='Data Found')
    except Exception as e:
        return format_result(result=None, success=False, status_code=400, message=str(e))


def data_validation_for_create_receive_at_warehouse(data):
    if not data.get("outgoing_stock_entry"):
        raise Exception("Required data missing : Outgoing Stock Entry name is required")
    if not data.get("stock_entry_type"):
        raise Exception("Required data missing : Stock Entry Type name is required")
    if not data.get("t_warehouse"):
        raise Exception("Required data missing : Target Warehouse is required")
    
    outgoing_stock_entry = frappe.get_list("Stock Entry", {"outgoing_stock_entry": data.get("outgoing_stock_entry")})
    if len(outgoing_stock_entry) > 0:
        raise Exception('Received at warehouse is already done for this Stock entry')


@frappe.whitelist()
def create_receive_at_warehouse():
    try:
        data = validate_data(frappe.request.data)
        data_validation_for_create_receive_at_warehouse(data=data)
        
        send_to_ste = base + '/api/method/erpnext.stock.doctype.stock_entry.stock_entry.make_stock_in_entry'
        stock_entry = requests.post(send_to_ste.replace("'", '"'), headers={
            "Authorization": frappe.request.headers["Authorization"]
        },data={"source_name": data.get("outgoing_stock_entry")})
        
        stock_entry_data = stock_entry.json().get("message")
        stock_entry_data["to_warehouse"] = data.get("t_warehouse")
        stock_entry_data["stock_entry_type"] = data.get("stock_entry_type")
        stock_entry_data["docstatus"] = 1
        
        receive_ste_url = base + '/api/resource/Stock%20Entry'
        receive_ste_url_api_response = requests.post(receive_ste_url.replace("'", '"'), headers={
            "Authorization": frappe.request.headers["Authorization"]
        },data=json.dumps(stock_entry_data))
        
        result = {
            "name": receive_ste_url_api_response.json().get("data").get("name")
        }
        return format_result(result=result, success=True, status_code=200, message='Received Warehouse Stock Entry is created')
    except Exception as e:
        return format_result(result=None, success=False, status_code=400, message=str(e), exception=str(e))
    

@frappe.whitelist()
def create_material_transfer_for_picklist():
    try:
        data = validate_data(frappe.request.data)
        pick_list = data.get("pick_list")
        picklist = frappe.get_doc("Pick List",pick_list)
        new_doc = frappe.new_doc('Stock Entry')
        new_doc.pick_list =pick_list
        new_doc.start_time = now_datetime()
        new_doc.end_time = now_datetime()
        new_doc.purpose = 'Material Transfer'
        new_doc.set_stock_entry_type()
        for item in picklist.locations:
            new_doc.append("items", {
                "item_code": item.item_code,
                "qty": item.qty,
                "s_warehouse":item.warehouse,
                "t_warehouse": data['t_warehouse']
            })

        new_doc.save()
        new_doc.submit()
        result = {
                    "Stock Entry":new_doc.name,
                    "Purpose":new_doc.purpose,
                    "Pick List":new_doc.pick_list
                }
        return format_result(result=result, success=True, status_code=200, message='Data Found')
    except Exception as e:
        return format_result(result=None, success=False, status_code=400, message=str(e))


def data_validation_for_save_picklist_and_create_stockentry(data):
    if not data.get("pick_list"):
        raise Exception("Required data missing : Pick List name is required")
    if not data.get("item_code"):
        raise Exception("Required data missing : Item code is required")
    if not data.get("picked_qty"):
        raise Exception("Required data missing : Picked quantity is required")
    if not data.get("s_warehouse"):
        raise Exception("Required data missing : Source Warehouse is required")
    if not data.get("t_warehouse"):
        raise Exception("Required data missing : Target Warehouse is required")
    if not data.get("stock_entry_type"):
        raise Exception("Required data missing : Stock entry type is required")


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


@frappe.whitelist()
def save_picklist_and_create_stockentry():
    try:
        data = validate_data(frappe.request.data)
        data_validation_for_save_picklist_and_create_stockentry(data=data)
        print(data)
        
        """GET Pick List Item (sorted_locations) Details"""
        item = picklist_item(
            data=data
        )
        
        """Validate picked quantity, we are decreasing the value actually"""
        new_picked_qty = int(item.get('picked_qty')) - int(data.get('picked_qty'))
        if new_picked_qty < 0.0:
            raise Exception(f"Picked quantity can not be more than total quantity.")
        
        """Create stock entry"""
        stock_entry = create_new_stock_entry_for_single_item(
            data=data,
            item=item
        )
        
        """Update picklist item picked qty"""
        frappe.db.set_value('Pick List Item', item.get('name'), {
            'picked_qty': new_picked_qty
        })
        
        return format_result(result={'stock entry': stock_entry.name}, success=True, message='success', status_code=200)
    except Exception as e:
        return format_result(success=False, status_code=400, message=str(e), exception=str(e))


def data_validation_for_submit_picklist_and_create_stockentry(data):
    if not data.get("pick_list"):
        raise Exception("Required data missing : Pick List name is required")
    if not data.get("stock_entry_type"):
        raise Exception("Required data missing : Stock Entry Type is required")
    if not data.get("s_warehouse"):
        raise Exception("Required data missing : Source Warehouse is required")
    if not data.get("t_warehouse"):
        raise Exception("Required data missing : Target Warehouse is required")


def picklist_details_for_submit_picklist_and_create_stockentry(url):
    picklist_details = requests.get(url.replace("'", '"'), headers={
        "Authorization": frappe.request.headers["Authorization"]
    },data={})
    if picklist_details.status_code != 200:
        raise Exception("Picklist name is not found")
    return picklist_details.json().get("data")


# def validation_to_proceed_for_submit_picklist_and_create_stockentry(data, picklist_details):
#     if picklist_details.get("docstatus") != 0:
#             raise Exception(f"Unable to proceed with this picklist : Pick List - {data.get('pick_list')} already submitted or cancelled")
#     for item in picklist_details.get('sorted_locations'):
#         if item['qty'] > item['picked_qty']:
#             raise Exception(f"Unable to proceed : {item['item_name']} is not fully transferred. Total qty to transfer is {item['qty']}. Transferred qty is {item['picked_qty']}.")


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


@frappe.whitelist()
def submit_picklist_and_create_stockentry():
    try:
        data = validate_data(frappe.request.data)
        data_validation_for_submit_picklist_and_create_stockentry(data=data)
        
        parts = urlparse(frappe.request.url)
        base = parts.scheme + '://' + parts.hostname + (':' + str(parts.port)) if parts.port != '' else ''
        url = base + '/api/resource/Pick%20List/'+ data.get('pick_list')
        
        """GET Pick List Details"""
        
        picklist_details = picklist_details_for_submit_picklist_and_create_stockentry(url=url)
        
        # """Check is all item picked and all good to go"""
        
        # validation_to_proceed_for_submit_picklist_and_create_stockentry(
        #     data=data,
        #     picklist_details=picklist_details
        # )
        
        """___ALL GOOD TO GO___"""
        
        """Create new stick entry, save and submit"""
        
        new_doc_stock_entry = create_and_submit_stock_entry_submit_picklist_and_create_stockentry(
            data=data,
            picklist_details=picklist_details
        )
        
        """Correct picked qty"""
        
        for item in picklist_details.get('locations'):
            picked_qty = item['qty'] - item['picked_qty']
            frappe.db.set_value('Pick List Item', item['name'], 'picked_qty', picked_qty)
        
        """Submit Pick List"""
        
        frappe.db.set_value('Pick List', picklist_details['name'], 'docstatus', 1)
        
        return format_result(result={'stock entry': new_doc_stock_entry.name,
                                 'items': new_doc_stock_entry.items
                                 }, success=True, message='Data Created', status_code=200)
    except Exception as e:
        return format_result(result=None, success=False, status_code=400, message=str(e), exception=str(e))
    
    
@frappe.whitelist()
def picklist_details_for_warehouse_app():
    try:
        pick_list = get_last_parameter(frappe.request.url, 'picklist_details_for_warehouse_app')
        
        print(pick_list, '\n\n\n')
        
        picklist_details = frappe.db.get_value('Pick List', pick_list, [
            'name', 'docstatus', 'purpose', 'customer', 'creation', 'modified'
        ], as_dict=1)
        
        if not picklist_details:
            raise Exception('Invalid pick list name')
        
        items = frappe.db.get_list('Pick List Item',
            filters={
                'parent': pick_list,
                'parentfield': 'locations'
            },
            fields=[
                'item_code', 'item_name', 'warehouse', 'qty', 'picked_qty', 'uom', 'sales_order'
            ],
            order_by='warehouse'
        )
        
        picklist_details.sales_order = items[0].sales_order
        
        so_details = frappe.db.get_value('Sales Order', picklist_details.sales_order, [
            'creation', 'delivery_date'
        ], as_dict=1)
        
        picklist_details.so_date = so_details.creation
        picklist_details.delivery_date = so_details.delivery_date
        
        for it in items:
            it.picked_qty = it.qty - it.picked_qty
            
        picklist_details.items = items        
        
        return format_result(result={
            'pick_list': picklist_details
        }, success=True, message='Data Created', status_code=200)
    except Exception as e:
        return format_result(result=None, success=False, status_code=400, message=str(e), exception=str(e))
    

def check_delivery_note_is_exist(pick_list):
    delivery_note = frappe.db.get_list('Delivery Note',
                        filters={
                            'pick_list': pick_list
                        },
                        fields=['docstatus']
                    )
    if not delivery_note: return False
    for dn in delivery_note:
        if dn.get('docstatus') in [0, 1, "0", "1"]:
            return True
    return False


@frappe.whitelist()
def filter_receive_at_warehouse_for_packing_area():
    try:
        url = frappe.request.url
        stock_entry_type = parse_qs(urlparse(url).query).get('stock_entry_type')
        order_purpose = parse_qs(urlparse(url).query).get('order_purpose')
        docstatus = parse_qs(urlparse(url).query).get('docstatus')
        has_delivery_note = parse_qs(urlparse(url).query).get('has_delivery_note')
        if stock_entry_type is not None: stock_entry_type = stock_entry_type[0]
        if order_purpose is not None: order_purpose = order_purpose[0]
        if docstatus is not None: docstatus = docstatus[0]
        if has_delivery_note is not None: has_delivery_note = has_delivery_note[0]
        

        """filter by
        1. stock entry type = as per request (Receive at Warehouse)
        2. SO purpose = as per request (Delivery)
        3. Received at Warehouse type must be submitted
        4. if Stock Entry has Picklist and the Picklist has Delivery Note then we need to remove from the list
        """
        filtered_se = frappe.db.get_list('Stock Entry',
                filters={
                    'stock_entry_type': stock_entry_type,
                    'docstatus': docstatus,
                    'pick_list': ('not in', (None, ''))
                },
                fields=['name', 'pick_list']
        )
        
        final_filtered_se = []

        """final filter, find and add other necessary fields"""
        for se in filtered_se:
            if order_purpose != frappe.db.get_value('Pick List', se.get('pick_list'), 'purpose'):
                continue
            if has_delivery_note in ["no"]:
                if check_delivery_note_is_exist(se.get('pick_list')):
                    continue
            
            se['customer_name'] = frappe.db.get_value('Pick List', se.get('pick_list'), 'customer')
            items_pl = frappe.db.get_list('Pick List Item',
                    filters={
                        'parent': se.get("pick_list"),
                        'parentfield': 'locations'
                    },
                    fields=['sales_order', 'qty']
                )
            if len(items_pl) < 1: continue
            sales_order = items_pl[0].get('sales_order')
            se['sales_order'] = sales_order

            so_date_data = frappe.db.get_value('Sales Order', sales_order, ['transaction_date', 'delivery_date'])
            if so_date_data:
                se['transaction_date'] = so_date_data[0]
                se['delivery_date'] = so_date_data[1]
            
            items_se = frappe.db.get_list('Stock Entry Detail',
                    filters={
                        'parent': se.get("name")
                    },
                    fields=['qty']
                )
            
            se['total_product'] = len(items_se)
            se['total qty'] = sum([ise.get('qty') for ise in items_se])
            final_filtered_se.append(se)

        return format_result(result=final_filtered_se, success=True, status_code=200, message='Data Found')
    except Exception as e:
        return format_result(result=None, success=False, status_code=400, message=str(e))

    
@frappe.whitelist()
def stock_entry_details_for_warehouse_app():
    try:
        stock_entry = get_last_parameter(frappe.request.url, 'stock_entry_details_for_warehouse_app')
        
        """GET Stock Entry Details"""
        
        stock_entry_details = frappe.db.get_value('Stock Entry', stock_entry, [
            'name', 'docstatus', 'purpose', 'creation', 'modified', 'pick_list'
        ], as_dict=1)
        
        if not stock_entry_details:
            raise Exception('Invalid stock entry name')
        
        """GET Sales Order, Transaction Date, Delivery Date"""
        
        pick_list_items = frappe.db.get_list('Pick List Item',
            filters={
                'parent': stock_entry_details.get('pick_list'),
                'parentfield': 'locations'
            },
            fields=['sales_order']
        )
        if pick_list_items: sales_order = pick_list_items[0].sales_order
        stock_entry_details.sales_order = sales_order
        
        so_date_data = frappe.db.get_value('Sales Order', sales_order, [ 'customer', 'customer_name', 'customer_address', 'transaction_date', 'delivery_date'])
        if so_date_data:
            stock_entry_details.customer = so_date_data[0]
            stock_entry_details.customer_name = so_date_data[1]
            stock_entry_details.customer_address = so_date_data[2]
            stock_entry_details.transaction_date = so_date_data[3]
            stock_entry_details.delivery_date = so_date_data[4]
            
        """GET ITEMS"""
        
        items = frappe.db.get_list('Stock Entry Detail',
            filters={
                'parent': stock_entry
            },
            fields=[
                'item_code', 'item_name', 'qty', 'transfer_qty', 'uom', 's_warehouse', 't_warehouse'
            ]
        )   
        stock_entry_details.items = items        
        
        return format_result(result=stock_entry_details, success=True, message='Data Created', status_code=200)
    except Exception as e:
        return format_result(result=None, success=False, status_code=400, message=str(e), exception=str(e))
    

@frappe.whitelist()
def create_delivery_note_from_pick_list():
    try:
        data = validate_data(frappe.request.data)
        pick_list_name = data.get('pick_list')
        if not pick_list_name:
            raise Exception('Pick List name required')
        
        pick_list_data = frappe.db.get_value('Pick List',
                            pick_list_name,
                            ['name', 'customer', 'company']
                        )
        if not pick_list_data[0]:
            raise Exception('Pick List name is not valid')
        
        pick_list_items = frappe.db.get_list('Pick List Item',
                        filters={
                            'parent': pick_list_name,
                            'parentfield': 'locations'
                        },
                        fields=['item_code', 'item_name', 'qty', 'uom', 'warehouse']
                    )
        print(pick_list_items)
        
        delivery_note = frappe.new_doc('Delivery Note')
        delivery_note.customer = pick_list_data[1]
        delivery_note.company = pick_list_data[2]
        delivery_note.pick_list = pick_list_name
        for item in pick_list_items:
            print(item)
            delivery_note.append("items", item)
        delivery_note.insert()        
        return format_result(result=delivery_note, success=True, message='Delivery Note successfully created', status_code=200)
    except Exception as e:
        return format_result(success=False, status_code=400, message=str(e), exception=str(e))
