import json

import frappe
import requests

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


def validate_data(req):
    if len(req) == 0 or req is None:
        return None
    try:
        data = json.loads(req)
        return data
    except ValueError:
        return "Invalid JSON submitted"


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


@frappe.whitelist()
def logout():
    global base
    base = frappe.request.url.rsplit('/', 3)[0]

    cookies = frappe.request.cookies
    if not cookies:
        raise requests.exceptions.BaseHTTPError
    res = requests.get(base + '/api/method/logout', cookies=cookies)
    return post_processing(res)


@frappe.whitelist()
def purchase_order_list():
    global base
    base = frappe.request.url.rsplit('/', 3)[0]
    print('reached ---------> ', base)
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
    base = frappe.request.url.rsplit('/', 3)[0]
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
    data = validate_data(frappe.request.data)
    cookies = frappe.request.cookies
    field = ["*"]
    return getDocument(data['id'], fields=field, cookies=cookies)


@frappe.whitelist()
def sales_order():
    global base
    base = frappe.request.url.rsplit('/', 3)[0]
    data = validate_data(frappe.request.data)
    cookies = frappe.request.cookies
    field = ["name", "customer_name", "delivery_date", "total_qty"]
    # field = ["*"]

    if "Invalid" in data:
        return "Invalid JSON body submitted."

    if len(data['id']) > 0:
        filters = [["Sales Order", "name", "=", data['id']]]
        result = getDocument('Sales Order', filters=filters, fields=field, cookies=cookies)
        print(type(result['data']))
        for i in result['data']:
            i.update({"delivery order id": ""})
        return result
    elif (data is None) or (len(data['id']) == 0):
        result = getDocument('Sales Order', fields=field, cookies=cookies)
        for i in result['data']:
            i.update({"delivery_order_id": ""})
        return result


@frappe.whitelist()
def product_sales_order():
    global base
    base = frappe.request.url.rsplit('/', 3)[0]
    data = validate_data(frappe.request.data)

    if "Invalid" in data:
        return "Invalid JSON body submitted."
    parent_id = data['parent_id']
    product_code = data['product_code']
    filters = {
            'parent': ['=', parent_id],
        }
    if len(product_code) != 0:
        filters.update({'item_code': product_code})

    check = frappe.db.get_list(
        'Sales Order Item',
        fields=["item_code", "qty"],
        filters=filters)
    for i in check:
        i.update({
            "lot_id":"",
            "storage_id":""
        })
    return check


@frappe.whitelist()
def product_purchase_order():
    global base
    base = frappe.request.url.rsplit('/', 3)[0]
    data = validate_data(frappe.request.data)
    if "Invalid" in data:
        return "Invalid JSON body submitted."

    parent_id = data['parent_id']
    product_code = data['product_code']
    filters = {
            'parent': ['=', parent_id],
        }
    if len(product_code) != 0:
        filters.update({'item_code': product_code})
    check = frappe.db.get_list(
        'Purchase Order Item',
        fields=["item_name", "qty", "item_code", ""],
        filters=filters)
    for i in check:
        i.update({
            "lot_id":"",
            "storage_id":""
        })
    return check
