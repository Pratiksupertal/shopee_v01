import json

import frappe
import requests
from PIL import Image, ImageDraw, ImageFont
import base64
import os
# import barcode


# base = 'http://localhost:8000'
base = ''


@frappe.whitelist(allow_guest=True)
def login():
    pass
    # try:
    #     data = json.loads(frappe.request.data)
    # except ValueError:
    #     return "Invalid JSON submitted"
    #
    # res = s.post(base + '/api/method/login', data)
    #
    # if res.status_code != 200:
    #     return {'message': 'Credentials invalid. Could not login.'}
    #
    # print(res.headers)
    # # print("json is,--->", res.json())
    # # print("cookie is,--->", res.cookies)
    # # d = {
    # #      "body": res.json(),
    # #      "cookies": res.cookies
    # #     }
    # return res.text


def getUrl(url):
    if url.startswith("http"):
        return url.rsplit('/', 3)[0]
    else:
        return url.rsplit('/')[0]


def validate_data(req):
    if len(req) == 0 or req is None:
        return None
    try:
        data = json.loads(req)
        return data
    except ValueError:
        return "Invalid JSON submitted"


def query_db(doctype, filters=None, fields=None):
    check = frappe.db.get_list(
        doctype,
        fields=fields,
        filters=filters)
    return check


def convert_to_pdf(template=None, invoice=None, weight=None, shipping=None, to_entity=None,
                   from_entity=None, address=None, address_company=None, product_list1=None,
                   delivery_type=None, b_code=None):
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

    # out = io.BytesIO()
    # image.save(out, format='pdf')
    # out1 = base64.base64encode(out)
    # print(out.getvalue().decode())

    image.save(dir_path + '/output.pdf', resolution=500)
    with open(dir_path + "/output.pdf", "rb") as pdf_file:
        encoded_string = base64.b64encode(pdf_file.read())

    return encoded_string

# import os
# with open(os.path.expanduser('test.pdf'), 'wb') as fout:
#      fout.write(base64.decodebytes(encoded_string))


def getDocument(docType, filters=None, fields=None, sql=None, cookies=None):
    global base
    if not cookies:
        return {'message': 'Credentials not identified. Please login first.'}

    url = base + '/api/resource/' + docType

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


def post_processing(res):
    if res.status_code != 200:
        raise requests.exceptions.HTTPError
    return res.json()


# import os
# with open(os.path.expanduser('test.pdf'), 'wb') as fout:
#      fout.write(base64.decodebytes(encoded_string))


@frappe.whitelist()
def logout():
    global base
    # base = frappe.request.url.rsplit('/', 3)[0]
    base = getUrl(frappe.request.url)

    cookies = frappe.request.cookies
    if not cookies:
        raise requests.exceptions.BaseHTTPError
    res = requests.get(base + '/api/method/logout', cookies=cookies)
    return post_processing(res)


@frappe.whitelist()
def purchase_order_list():
    global base
    # base = frappe.request.url.rsplit('/', 3)[0]
    base = getUrl(frappe.request.url)
    data = validate_data(frappe.request.data)
    cookies = frappe.request.cookies
    field = ["name", "supplier_name", "transaction_date", "total_qty", "supplier"]

    # field = ["*"]
    if "Invalid" in data:
        return "Invalid JSON body submitted"

    if len(data['id']) > 0:
        filters = [["Purchase Order", "name", "=", data['id']]]
        return getDocument('Purchase Order', filters=filters, fields=field, cookies=cookies)
    elif (data is None) or (len(data['id']) == 0):
        return getDocument('Purchase Order', fields=field, cookies=cookies)


@frappe.whitelist()
def product_list():
    global base
    # base = frappe.request.url.rsplit('/', 3)[0]
    base = getUrl(frappe.request.url)
    data = validate_data(frappe.request.data)
    cookies = frappe.request.cookies
    field = ["item_code", "item_name", "total_projected_qty", "name"]
    # field = ["*"]

    if "Invalid" in data:
        return "Invalid JSON body submitted."

    if len(data['id']) > 0:
        filters = [["Item", "name", "=", data['id']]]
        return getDocument('Item', filters=filters, fields=field, cookies=cookies)
    elif (data is None) or (len(data['id']) == 0):
        return getDocument('Item', fields=field, cookies=cookies)


@frappe.whitelist()
def testDoc():
    global base
    # base = frappe.request.url.rsplit('/', 3)[0]
    base = getUrl(frappe.request.url)
    data = validate_data(frappe.request.data)
    # cookies = frappe.request.cookies

    # data = validate_data(frappe.request.data)
    # field = ["*"]
    # cookies = frappe.request.cookies
    check = frappe.get_doc(
        'Sales Order',
        data['id']
    )
    return check

    # check = frappe.db.get_list(
    #     data['id'],
    #     fields=field
    # )
    # return check

    return getDocument(data['id'], fields=field, cookies=cookies)


@frappe.whitelist(allow_guest=True)
def test():
    return 'pong'


@frappe.whitelist()
def sales_order():
    global base
    base = getUrl(frappe.request.url)
    data = validate_data(frappe.request.data)
    cookies = frappe.request.cookies
    field = ["name", "customer_name", "delivery_date", "total_qty"]
    filters = None
    # field = ["*"]

    if "Invalid" in data:
        return "Invalid JSON body submitted."

    if len(data['id']) > 0:
        filters = [["Sales Order", "name", "=", data['id']]]

    result = getDocument('Sales Order', fields=field, cookies=cookies, filters=filters)

    for i in result['data']:
        i.update({"delivery_order_id": ""})

    return result


@frappe.whitelist()
def product_sales_order():
    data = validate_data(frappe.request.data)

    if "Invalid" in data:
        return "Invalid JSON body submitted."

    parent_id = data['parent_id']
    product_code = data['product_code']
    fields = ["item_code", "qty"]

    filters = {
        'parent': ['=', parent_id],
    }
    if len(product_code) != 0:
        filters.update({'item_code': product_code})

    check = query_db('Sales Order Item', fields=fields, filters=filters)

    # check = frappe.db.get_list(
    #     'Sales Order Item',
    #     fields=["item_code", "qty"],
    #     filters=filters)

    for i in check:
        i.update({
            "lot_id": "",
            "storage_id": ""
        })
    return check


@frappe.whitelist()
def product_purchase_order():
    data = validate_data(frappe.request.data)
    if "Invalid" in data:
        return "Invalid JSON body submitted."

    parent_id = data['parent_id']
    product_code = data['product_code']

    fields = ["item_name", "qty", "item_code", ""]
    filters = {
        'parent': ['=', parent_id],
    }
    if len(product_code) != 0:
        filters.update({'item_code': product_code})

    check = query_db('Purchase Order Item', fields=fields, filters=filters)

    for i in check:
        i.update({
            "lot_id": "",
            "storage_id": ""
        })

    return check


@frappe.whitelist()
def get_label():
    global base
    base = getUrl(frappe.request.url)
    data = validate_data(frappe.request.data)
    cookies = frappe.request.cookies
    fields = ['name', 'customer_name', 'company', 'address_display',
              'company_address_display', 'total_net_weight', 'payment_terms_template',
              'grand_total']
    filters = [["Sales Invoice", "name", "=", data['id']]]
    result = getDocument('Sales Invoice', fields=fields, cookies=cookies, filters=filters)

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
        product_list1=check, delivery_type='Regular \nShipping', b_code=str('123456789012')
    )

    # import os
    # with open(os.path.expanduser('/home/sid/PycharmProjects/supertal/mamba2/mamba-frappe-bench/apps/shopee_v01/shopee_v01/api/v1/test.pdf'), 'wb') as fout:
    #      fout.write(base64.decodebytes(pdf_binary))

    return {
        "pdf_bin": pdf_binary
    }
