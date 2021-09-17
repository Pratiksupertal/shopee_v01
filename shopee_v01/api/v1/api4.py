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
from erpnext.stock.doctype.pick_list.pick_list import create_stock_entry
from erpnext.stock.doctype.material_request.material_request import create_pick_list


def validate_data(data):
    if len(data) == 0 or data is None:
        return None
    try:
        data = json.loads(data)
        return data
    except ValueError:
        return "Invalid JSON submitted"


def format_result(result=None, message=None, status_code=None):
    return {
        "success": True,
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

        return format_result(message='Login Success', status_code=200, result={
            "id": str(user_data.idx),
            "username": str(user_data.username),
            "api_key": str(user_data.api_key + ':' + api_secret['message']['api_secret']),
            "warehouse_id": str(warehouse_id)
        })


@frappe.whitelist()
def purchases():
    result = []

    each_data_list = list(map(lambda x: frappe.get_doc('Purchase Order', x),
                              [i['name'] for i in frappe.get_list('Purchase Order')]))

    for each_data in each_data_list:
        temp_dict = {
            "id": str(each_data.idx),
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
                "price": str(int(i.amount) if i.amount else ''),
                "quantity": str(int(i.qty) if i.qty else ''),
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
    data = validate_data(frappe.request.data)

    today = dt.datetime.today()

    new_doc = frappe.new_doc('Purchase Receipt')
    new_doc.posting_date = today.strftime("%Y-%m-%d")
    new_doc.supplier = data['supplier_do_number']
    new_doc.set_warehouse = data['warehouse_id']
    new_doc.modified_by = data['create_user_id']

    for item in data['products']:
        new_doc.append("items", {
            "item_code": item['purchase_product_id'],
            "qty": item['quantity'],
            "purchase_order": data['purchase_id']
        })

    new_doc.insert()

    return format_result(status_code=200, message='Data Created', result={
        "id": str(new_doc.name),
        "receive_number": new_doc.name,
        "supplier_do_number": new_doc.supplier,
        "receive_date": new_doc.posting_date,
        "supplier_id": new_doc.supplier
    })


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

    return format_result(result)


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
                "quantity": j.qty,
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
                    "quantity": str(i.qty),
                    "warehouse_area_storage_id": None
                } for i in each_data.items
            ],
            "update_user_id": each_data.modified_by,
            "product_list": [i.item_name for i in each_data.items]
        }
        result.append(temp_dict)

    return format_result(result=result, message='Data Found', status_code=200)


@frappe.whitelist()
def material_stock_entry():
    '''
    Processing Material Request
    '''
    data = validate_data(frappe.request.data)
    new_doc_material_request = frappe.new_doc('Material Request')
    new_doc_material_request.material_request_type = "Material Transfer"
    for item in data['items']:
        new_doc_material_request.append("items", {
            "item_code": item['item_code'],
            "qty": item["qty"],
            "uom": item["uom"],
            "conversion_factor": item["conversion_factor"],
            "schedule_date": item['scheduled_date'] or today(),
            "warehouse": item['target_warehouse'],
        })
    new_doc_material_request.save()
    new_doc_material_request.submit()

    '''
    Generating Pick List from Material Request
    '''
    new_doc_pick_list = create_pick_list(new_doc_material_request.name)
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
    new_doc_stock_entry.submit()

    return format_result(result=new_doc_stock_entry.name, message='Data Created', status_code=200)
