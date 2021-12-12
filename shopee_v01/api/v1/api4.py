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

        print(str(user_data.api_key + ':' + api_secret['message']['api_secret']))
        return format_result(message='Login Success', status_code=200, result={
            "id": str(user_data.idx),
            "username": str(user_data.username),
            "api_key": str(user_data.api_key + ':' + api_secret['message']['api_secret']),
            "warehouse_id": str(warehouse_id)
        })


def fill_barcode(item_code):
    doc = frappe.get_doc('Item', item_code)
    return str(doc.barcodes[0].barcode) if len(doc.barcodes) > 0 else ''


@frappe.whitelist()
def purchases():
    result = []

    each_data_list = list(map(lambda x: frappe.get_doc('Purchase Order', x),
                              [i['name'] for i in frappe.get_list('Purchase Order')]))

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
    data = validate_data(frappe.request.data)
    today = dt.datetime.today()
    new_doc = frappe.new_doc('Purchase Receipt')
    new_doc.posting_date = today.strftime("%Y-%m-%d")
    po_name = data['products'][0]['purchase_id']
    supplier = frappe.db.get_value("Purchase Order",{"name":po_name},"Supplier")
    new_doc.supplier = supplier
    new_doc.supplier_travel_document_number = data['supplier_do_number']
    new_doc.set_warehouse = data['warehouse_id']
    for item in data['products']:
        new_doc.append("items", {
            "item_code": item['purchase_product_id'],
            "qty": item['quantity'],
            "purchase_order":item['purchase_id']
        })
    new_doc.insert()
    return format_result(status_code=200, message='Purchase Receipt Created', result={
        "id": str(new_doc.name),
        "receive_number": new_doc.name,
        "supplier_do_number": new_doc.supplier_travel_document_number,
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


@frappe.whitelist()
def create_sales_order():
    order=validate_data(frappe.request.data)
    if not order.get("delivery_date"):
        order["delivery_date"]=today()

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
        return format_result(res_api_response.json())
    return format_result(result="There was a problem creating the Sales Order", message="Error", status_code=res_api_response.status_code)


@frappe.whitelist()
def create_sales_order_all():
    data = validate_data(frappe.request.data)
    result = []
    success_count, fail_count = 0, 0
    data=data.get("sales_order")
    for order in list(data):
        try:
            if not order.get("delivery_date"):
                order["delivery_date"] = today()
            if not order.get("external_so_number") or not  order.get("source_app_name"):
                raise Exception("Sales order Number and Source app name both are required")
            parts = urlparse(frappe.request.url)
            base = parts.scheme + '://' + parts.hostname + (':' + str(parts.port)) if parts.port != '' else ''
            url = base + '/api/resource/Sales%20Order'
            res_api_response = requests.post(url.replace("'", '"'), headers={
                "Authorization": frappe.request.headers["Authorization"]
            }, data=json.dumps(order))
            if res_api_response.status_code == 200:
                success_count += 1
                result.append({
                    "external_so_number": order.get("external_so_number"),
                    "message": "success"
                })
            else:
                print("\n\n",res_api_response.text,"\n\n")
                fail_count += 1
                result.append({
                    "external_so_number": order.get("external_so_number"),
                    "message": "failed"
                })
        except Exception as err:
            print("\n\n",str(err),"\n\n")
            fail_count += 1
            result.append({
                "external_so_number": order.get("external_so_number"),
                "message": "failed"
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
        item.t_warehouse = "Collecting Area Finish Good Out - ISS"
        stock_entry.append('items', item)
    return stock_entry


@frappe.whitelist()
def submit_picklist():
    data = validate_data(frappe.request.data)
    pick_list = frappe.get_doc('Pick List',data['picklist'])
    pick_list.submit()
    from  erpnext.stock.doctype.pick_list.pick_list import validate_item_locations
    from  erpnext.stock.doctype.pick_list.pick_list import update_stock_entry_items_with_no_reference
    validate_item_locations(pick_list)
    if frappe.db.exists('Stock Entry', {'pick_list': data['picklist'],'docstatus' :1 }):
        return frappe.msgprint(_('Stock Entry has been already created against this Pick List'))
    stock_entry = frappe.new_doc('Stock Entry')
    stock_entry.pick_list = pick_list.get('name')
    stock_entry.purpose = pick_list.get('purpose')
    stock_entry.set_stock_entry_type()
    if pick_list.get('material_request'):
        stock_entry = update_stock_entry_based_on_material_request(pick_list, stock_entry)
    else:
        stock_entry = update_stock_entry_items_with_no_reference(pick_list, stock_entry)
    stock_entry.set_incoming_rate()
    stock_entry.set_actual_qty()
    stock_entry.calculate_rate_and_amount(update_finished_item_rate=False)
    stock_entry.save()
    stock_entry.submit()
    return format_result(result={
            "stock_entry": stock_entry.name,
            "picklist": stock_entry.pick_list
        }, message="success", status_code=200)
    return stock_entry


@frappe.whitelist()
def update_current_stock():
    data = validate_data(frappe.request.data)
    doc = frappe.get_doc("Pick List",data['picklist'])
    doc.set_item_locations(save=True)
    return format_result(message="success", status_code=200)


def pick_list_with_mtr():
    """
    Filter by `material_request type` = [ Material Transfer | Manufacture | Material Issue ]
    """
    material_request_list = frappe.db.sql(
        "select name, purpose, for_qty from `tabPick List` where purpose like '%Material Transfer%' or purpose like '%Manufacture%' or purpose like '%Material Issue%';"
        )
    result = {}
    for item in material_request_list:
        pick_list_id = item[0]
        result[pick_list_id] = {
            "type": item[1],
            "qty": item[2]
        }
    return result
    

def pick_list_with_so():
    """
    For Sales Order
    """
    pick_list_items = frappe.db.get_list('Pick List Item',
             filters={
                'sales_order': ['like', 'SAL-ORD-%']
             },
             fields=['parent', 'sales_order', 'item_code', 'warehouse', 'qty']
      )
    pick_list_for_so = {}
    for item in pick_list_items:
        pick_list_id = item.get('parent')
        if not pick_list_id: continue
        if pick_list_id not in pick_list_for_so:
            pick_list_for_so[pick_list_id] = {}
            pick_list_for_so[pick_list_id]["sales_order"] = item.get("sales_order")
            pick_list_for_so[pick_list_id]["items"] = []
        pick_list_for_so[pick_list_id]["items"].append({
            "item_code": item.get("item_code"),
            "warehouse": item.get("warehouse"),
            "qty": item.get("qty")
        })
    return pick_list_for_so


@frappe.whitelist()
def pick_list_with_mtr_and_so():
    pick_list_for_mtr = pick_list_with_mtr()
    pick_list_for_so = pick_list_with_so()
    return format_result(result={
        "pick_list_for_mtr": pick_list_for_mtr,
        "pick_list_for_so": pick_list_for_so
    }, status_code=200, message='Data Found')