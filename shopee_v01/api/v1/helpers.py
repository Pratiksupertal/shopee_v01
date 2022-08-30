from email.headerregistry import Address
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
from erpnext.selling.doctype.sales_order.sales_order import make_sales_invoice, make_delivery_note


import re


def cleanhtml(raw_html):
    if not raw_html:
        return raw_html
    if not type(raw_html) == str:
        return raw_html
    CLEANR = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')
    cleantext = re.sub(CLEANR, '', raw_html)
    return cleantext


def validate_data(data):
    if not data:
        return data
    if not len(data):
        return data
    try:
        return json.loads(data)
    except ValueError:
        return "Invalid JSON submitted"


def format_result(success=None, result=None, message=None, status_code=None, exception=None):
    if success is None:
        success = True if status_code in [None, 200, 201] and not exception else False
    if status_code is None:
        status_code = 200 if success and not exception else 400
    if message is None:
        message = exception if not message and exception else "success"
    if not success or status_code not in [200, 201]:
        if not exception:
            exception = message

    indicator = "green" if success else "red"
    raise_exception = 1 if exception else 0

    response = {}
    if isinstance(result, list):
        response["count"] = 0 if not result else len(result)

    response.update({
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
    })

    return response


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

        pick_list.item_location_map.setdefault(
            item_code,
            get_available_item_locations(
                item_code,
                from_warehouses,
                pick_list.item_count_map.get(item_code),
                pick_list.company
            )
        )

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
    from erpnext.stock.doctype.pick_list.pick_list import update_common_item_properties
    for location in pick_list.locations:
        target_warehouse = None
        if location.material_request_item:
            target_warehouse = frappe.get_value(
                'Material Request Item',
                location.material_request_item,
                'warehouse'
            )
        item = frappe._dict()
        update_common_item_properties(item, location)
        item.t_warehouse = target_warehouse
        stock_entry.append('items', item)
    return stock_entry


def update_stock_entry_based_on_sales_order(pick_list, stock_entry):
    from erpnext.stock.doctype.pick_list.pick_list import update_common_item_properties
    for location in pick_list.locations:
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
    pick_list = frappe.db.get_list(
        'Pick List',
        filters={
            "docstatus": 1,
            "purpose": ["in", ["Material Transfer", "Material Transfer for Manufecture", "Manufacture", "Material Issue"]]
        },
        fields=["name", "purpose", "parent_warehouse"]
    )

    pick_list_for_mtr = {}
    for item in pick_list:
        pick_list_id = item.get('name')
        if not pick_list_id:
            continue
        # if the pick list is in the stock entry, we have to filter them out
        if pick_list_id in stock_entry_pick_list:
            continue
        pick_list_for_mtr[pick_list_id] = {}
        pick_list_for_mtr[pick_list_id]["type"] = item.get("purpose")
        pick_list_for_mtr[pick_list_id]["parent_warehouse"] = item.get("parent_warehouse")
        pick_list_for_mtr[pick_list_id]["items"] = frappe.db.get_list(
            'Pick List Item',
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
    pick_list_items = frappe.db.get_list(
        'Pick List Item',
        filters={
            'sales_order': ['like', 'SAL-ORD-%'],
            'docstatus': 1
        },
        fields=[
            'parent',
            'sales_order',
            'item_code',
            'item_name',
            'warehouse',
            "uom",
            'qty'
        ]
    )
    pick_list_for_so = {}
    for item in pick_list_items:
        pick_list_id = item.get('parent')
        if not pick_list_id:
            continue
        # if the pick list is in the stock entry, we have to filter them out
        if pick_list_id in stock_entry_pick_list:
            continue
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
    item = frappe.db.get_list(
        'Pick List Item',
        filters={
            'parent': data.get("pick_list"),
            'item_code': data.get('item_code'),
            'warehouse': data.get('s_warehouse'),
            'parentfield': 'locations'
        },
        fields=['name', 'item_name', 'qty', 'picked_qty']
    )
    if len(item) < 1:
        raise Exception('Pick list, item code or warehouse invalid!')
    return item[0]


def create_new_stock_entry_for_single_item(data, item):
    picklist_details = frappe.db.get_value('Pick List', data.get('pick_list'), ['company', 'purpose', 'note'])

    new_doc_stock_entry = frappe.new_doc('Stock Entry')
    new_doc_stock_entry.company = picklist_details[0]
    new_doc_stock_entry.purpose = picklist_details[1]
    new_doc_stock_entry.remarks = picklist_details[2]

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


def pick_list_details_with_items(pick_list):
    """
    1. Pick List  Details (Company, Purpose)
    2. Pick List Items (paaarentfield: locations)
    3. Correct the picked qty
    """

    pick_list_details = frappe.db.get_value(
        'Pick List',
        pick_list,
        ['company', 'purpose', 'note'],
        as_dict=1
    )

    if not pick_list_details:
        raise Exception('Pick List not found.')

    pick_list_items = frappe.db.get_list(
        'Pick List Item',
        filters={
            'parent': pick_list,
            'parentfield': 'locations'
        },
        fields=[
            'name', 'item_code', 'item_name', 'qty', 'picked_qty'
        ]
    )

    return pick_list_details, pick_list_items


def check_any_item_picked(pick_list_items):
    for item in pick_list_items:
        corrected_pick_list = item['qty'] - item['picked_qty']
        if corrected_pick_list > 0.0:
            return True
    return False


def correct_picked_qty_for_submit_pick_list(pick_list_items):
    """Correct the picked_qty to (qty-picked_qty)"""
    for item in pick_list_items:
        frappe.db.set_value(
            'Pick List Item',
            item['name'],
            'picked_qty',
            item['qty'] - item['picked_qty']
        )


def update_endtime_and_submit_pick_list(pick_list):
    doc_pick_list = frappe.get_doc('Pick List', pick_list)
    doc_pick_list.end_time = frappe.utils.get_datetime()
    doc_pick_list.docstatus = 1
    """
    Most Imporant:
    Since ERP is not allowing partial pick item submission,
    we can not use - `doc_pick_list.submit()`
    If we use it, picked_qty will again be same as qty
    """
    doc_pick_list.save()


def create_and_submit_stock_entry_submit_picklist_and_create_stockentry(data, pick_list_details, pick_list_items):
    new_doc_stock_entry = frappe.new_doc('Stock Entry')
    new_doc_stock_entry.company = pick_list_details.get('company')
    new_doc_stock_entry.purpose = pick_list_details.get('purpose')
    new_doc_stock_entry.remarks = pick_list_details.get('note')

    new_doc_stock_entry.pick_list = data.get('pick_list')

    for item in pick_list_items:
        corrected_pick_list = item['qty'] - item['picked_qty']
        if corrected_pick_list <= 0.0:
            continue
        new_doc_stock_entry.append("items", {
            "item_code": item.get('item_code'),
            "item_name": item.get('item_name'),
            "t_warehouse": data.get("t_warehouse"),
            "s_warehouse": data.get("s_warehouse"),
            "qty": corrected_pick_list
        })
    if len(new_doc_stock_entry.get("items")) <= 0:
        raise Exception('No picked items found. Please, pick some items first.')
    new_doc_stock_entry.stock_entry_type = data.get("stock_entry_type")
    new_doc_stock_entry.save()
    new_doc_stock_entry.submit()
    return new_doc_stock_entry


def get_base_url(url):
    parts = urlparse(url)
    base = parts.scheme + '://' + parts.hostname + (':' + str(parts.port)) if parts.port != '' else ''
    return base


def check_delivery_note_status(pick_list):
    delivery_note = frappe.db.get_list(
        'Delivery Note',
        filters={
            'pick_list': pick_list
        },
        fields=['docstatus', 'owner']
    )
    # if delivery note not exist, return 9
    if not delivery_note:
        return 9, None
    creator_name = frappe.db.get_value('User', delivery_note[0].get('owner'), 'full_name')
    return delivery_note[0].get('docstatus'), creator_name


def get_item_bar_code(item_code):
    try:
        values = {'item_code': item_code}
        data = frappe.db.sql("""SELECT item_bar_code FROM `tabItem` WHERE item_code=%(item_code)s""", values=values)
        if data:
            return data[0][0]
        return None
    except Exception as e:
        print('Exception occured in fetching barcode\n------\n', str(e))
        return None


def create_and_save_customer(base, customer_data, submit=False):
    try:
        url = base + '/api/resource/Customer'
        customer_res = requests.post(url.replace("'", '"'), headers={
            "Authorization": frappe.request.headers["Authorization"]
        }, data=json.dumps(customer_data))
        if customer_res.status_code != 200:
            raise Exception()
        customer = customer_res.json().get("data")
        return customer
    except Exception as e:
        raise Exception(f'Problem in creating Customer. Reason: {str(e)}')


def create_and_submit_sales_order(order_data, submit=False):
    try:
        sales_order = frappe.new_doc("Sales Order")
        sales_order.customer = order_data.get("customer")
        sales_order.order_type = "Sales"
        sales_order.delivery_date = frappe.utils.getdate()
        sales_order.external_so_number = order_data.get("external_so_number")
        sales_order.source_app_name = order_data.get("source_app_name")
        sales_order.chain = order_data.get("chain")
        sales_order.store = order_data.get("store")
        sales_order.transaction_date = order_data.get("transaction_date")
        for item in order_data.get("items"):
            sales_order.append("items", {
                "item_code": item['item_code'],
                "qty": str(item['qty']),
                "rate": item['rate'],
                'warehouse': item['warehouse']
                })
        if 'taxes' in order_data:
            for tax in order_data.get("taxes"):
                sales_order.append("taxes", {
                    "charge_type": tax['charge_type'],
                    "account_head": tax['account_head'],
                    "tax_amount": tax['tax_amount'],
                    'description': tax['description']
                    })
        sales_order.save()
        sales_order.submit()
        return sales_order
    except Exception as e:
        raise Exception(f'Problem in creating sales order. Reason: {str(e)}')


def create_and_submit_sales_invoice_from_sales_order(
        source_name, accounting_dimensions, submit=False, transaction_date=None) -> any:
    try:
        sales_invoice_data = make_sales_invoice(source_name=source_name)
        new_sales_invoice = frappe.new_doc("Sales Invoice")
        new_sales_invoice = sales_invoice_data

        if transaction_date:
            sales_invoice_data.set_posting_time = 1
            sales_invoice_data.posting_date = transaction_date
        new_sales_invoice.update(accounting_dimensions)
        new_sales_invoice.save()
        if submit:
            new_sales_invoice.submit()

        return new_sales_invoice
    except Exception as e:
        raise Exception(f'Problem in creating sales invoice. Reason: {str(e)}')


def create_and_submit_delivery_note_from_sales_order(source_name, submit=False, transaction_date=None) -> any:
    try:
        dn_data = make_delivery_note(source_name=source_name)
        new_delivery_note = frappe.new_doc("Delivery Note")
        new_delivery_note = dn_data

        if transaction_date:
            dn_data.set_posting_time = 1
            dn_data.posting_date = transaction_date
        new_delivery_note.save()
        if submit:
            new_delivery_note.submit()

        return new_delivery_note
    except Exception as e:
        raise Exception(f'Problem in creating delivery note. Reason: {str(e)}')


def create_payment_for_sales_order_from_web(
        payment_data, sales_invoice, accounting_dimensions, submit=False, transaction_date=None):
    try:
        payment_entry = frappe.new_doc("Payment Entry")
        payment_entry.payment_type = "Receive"
        payment_entry.company = sales_invoice.company
        payment_entry.mode_of_payment = payment_data['mode_of_payment']
        payment_entry.posting_date = frappe.utils.getdate()
        payment_entry.party = payment_data['party']
        payment_entry.party_type = payment_data['party_type']
        payment_entry.paid_amount = payment_data['paid_amount']
        payment_entry.received_amount = payment_data['received_amount']
        payment_entry.paid_to = payment_data['paid_to']
        payment_entry.paid_from = payment_data['paid_from']
        payment_entry.paid_from_account_currency = payment_data['paid_from_account_currency']
        payment_entry.paid_to_account_currency = payment_data['paid_to_account_currency']
        payment_entry.reference_no = payment_data['reference_no']
        payment_entry.reference_date = payment_data['reference_date']

        payment_entry.append("references", {
            "parenttype": "Payment Entry",
            "reference_doctype": "Sales Invoice",
            "reference_name": sales_invoice.name,
            "due_date": None,
            "bill_no": None,
            "payment_term": None,
            "total_amount": sales_invoice.grand_total,
            "outstanding_amount": sales_invoice.grand_total,
            "allocated_amount": sales_invoice.grand_total,
            "exchange_rate": 0,
            "doctype": "Payment Entry Reference"
        })
        payment_entry.update(accounting_dimensions)

        if transaction_date:
            payment_entry.set_posting_time = 1
            payment_entry.posting_date = transaction_date
        payment_entry.save()
        if submit:
            payment_entry.submit()
        return payment_entry
    except Exception as e:
        raise Exception(f'Problem in creating payment entry. Reason: {str(e)}')


def auto_map_accounting_dimensions_fields(accounting_dimensions, order_data={}, add_region=False, add_brand=False):
    try:
        # auto map region from city by Territory Tree
        if add_region:
            if not accounting_dimensions.get('region'):
                accounting_dimensions['region'] = frappe.db.get_value('Territory', accounting_dimensions.get("city"), 'parent')
        # auto map brand name from item if all items are from same brand
        if add_brand:
            if not accounting_dimensions.get('brand'):
                items = order_data.get('items')
                print(items)
                if items:
                    first_item_code = items[0].get('item_code')
                    accounting_dimensions['brand'] = frappe.db.get_value('Item', first_item_code, 'brand')
        return accounting_dimensions
    except Exception:
        return accounting_dimensions


def get_coa_from_store(store):
    coa = frappe.db.get_value('COA Mapping Table', store, 'coa')
    if not coa:
        raise Exception('COA (Paid to) not found.')
    return coa


def handle_empty_error_message(response, keys, *args, **kwargs):
    for key in keys:
        if not response[key]:
            suggestion = 'Please, check the data you provided.'
            if key == 'order_data':
                suggestion = 'Please, check the order data.'
            elif key == 'delivery_note':
                suggestion = 'Please, check the availability of item of the specified warehouse.'
            elif key == 'sales_invoice':
                suggestion = 'Please, check the accounting dimensions information.'
            elif key == 'payment_entry':
                suggestion = 'Please, check the payment data.'
            return key.replace('_', ' ').title() + ' creation failed. ' + suggestion
    else:
        return 'Something went wrong. Please, check the data you provided.'


def validate_filter_field(filterfield, value, datatype=str):
    if not value:
        return None
    try:
        value = datatype(value[0])
        return value
    except Exception as err:
        raise Exception(f"{filterfield} datatype is not correct. {str(err)}")


def get_user_mapped_warehouses(user=frappe.session.user):
    user_warehouses = frappe.db.sql(
        "SELECT warehouse_id FROM `tabUser Warehouse Mapping` where user_id='{}'"
        .format(user))
    user_warehouses = [warehouse[0] for warehouse in user_warehouses]
    return user_warehouses


def submit_stock_entry_send_to_shop(stock_entry_doc):
    items = frappe.db.get_list('Stock Entry Detail', filters={'parent': stock_entry_doc.get("name")},
                               fields=['item_name', 'qty', 'basic_rate', 's_warehouse'])

    s_warehouse = None
    lists = []
    for item in items:
        current_item = {
            "product_name": item["item_name"],
            "variant_name": frappe.db.get_value('Item Variant Attribute', {'parent': item['item_name']},
                                                'attribute_value'),
            "quantity": item["qty"],
            "price": item["basic_rate"]
        }
        s_warehouse = item['s_warehouse']
        lists.append(current_item)

    """GET Material Request, Transaction Date."""
    pl_data = frappe.db.get_value(
        'Pick List', stock_entry_doc.get("pick_list"), ['material_request']
    )

    material_request = None
    if pl_data:
        material_request = pl_data

    if not material_request:
        raise Exception('No Material Request found associated with this stock entry')

    mr_data = frappe.db.get_value(
        'Material Request',
        material_request,
        ['name', 'transaction_date']
    )

    stock_entry_data = {
        "source_warehouse": s_warehouse,
        "destination_warehouse": frappe.db.get_value("Material Request Item", {'parent': mr_data[0]}, 'warehouse'),
        "transfer_date": mr_data[1],
        "external_number": stock_entry_doc.name,
        "material_request_number": mr_data[0],
        "lists": lists
    }

    return stock_entry_data


def create_new_stock_entry_from_outgoing_stock_entry(data):
    outgoing_stock_entry_doc = frappe.get_doc("Stock Entry", data.get("outgoing_stock_entry"))
    new_doc = frappe.new_doc('Stock Entry')
    new_doc.outgoing_stock_entry = data.get("outgoing_stock_entry")
    new_doc.stock_entry_type = data.get("stock_entry_type")
    new_doc.company = outgoing_stock_entry_doc.get("company")
    new_doc.pick_list = outgoing_stock_entry_doc.get("pick_list")
    new_doc.remarks = outgoing_stock_entry_doc.get("remarks")

    items = frappe.db.get_list('Stock Entry Detail', filters={'parent': outgoing_stock_entry_doc.get("name")},
                               fields=['item_code', 'item_group', 'qty', 't_warehouse'])
    total = 0
    if data.get("stock_entry_type") != 'Receive at Warehouse' and data.get("stock_entry_type") != 'Receive at Shop':
        for item in items:
            new_doc.append("items", {
                "item_code": item['item_code'],
                "s_warehouse": data.get("s_warehouse"),
                "t_warehouse": data.get("t_warehouse"),
                "qty": str(item['qty'])
            })
            total += item['qty']
    else:
        for item in items:
            new_doc.append("items", {
                "item_code": item['item_code'],
                "s_warehouse": item['t_warehouse'],
                "t_warehouse": data.get("t_warehouse"),
                "qty": str(item['qty'])
            })
            total += item['qty']
    new_doc.save()
    return new_doc
