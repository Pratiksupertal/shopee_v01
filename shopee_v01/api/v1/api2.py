import json

import frappe
import requests

cookie = ''
base = 'http://localhost:8000'


@frappe.whitelist(allow_guest=True)
def login():
    # data = {
    #     "usr": "administrator",
    #     "pwd": "HaloRetail"
    # }
    try:
        data = json.loads(frappe.request.data)
    except ValueError:
        return "Invalid JSON submitted"
    res = requests.post(base + '/api/method/login', data)

    if res.status_code != 200:
        return {'message': 'Credentials invalid. Could not login.'}

    global cookie
    cookie = res.cookies

    return res.json()


def validate_data(req):
    try:
        data = json.loads(req)
        return data
    except ValueError:
        return "Invalid JSON submitted"


def getDocument(docType, filters=None, fields=None):
    if not cookie:
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

    res = requests.get(url.replace("'", '"'), cookies=cookie)

    if res.status_code != 200:
        return {'message': 'Error: Unable to retrieve requested item.'}

    print(res.status_code)
    return res.json()


@frappe.whitelist(allow_guest=True)
def logout():
    global cookie
    cookie = None


@frappe.whitelist(allow_guest=True)
def delivery_order_list():
    data = validate_data(frappe.request.data)
    # field = ["customer_name", "posting_date", "total_qty", "name"]
    field = ["*"]
    if "Invalid" in data:
        return "Item id parameter not found. Please enter ID and try again."

    if len(data['id']) > 0:
        filters = [["Delivery Note", "name", "=", data['id']]]
        return getDocument('Delivery Note', filters=filters, fields=field)
    elif len(data['id']) == 0:
        return getDocument('Delivery Note', fields=field)


@frappe.whitelist(allow_guest=True)
def product_list():
    data = validate_data(frappe.request.data)
    # field = ["item_code", "item_name", "total_projected_qty", "name"]
    field = ["*"]

    if "Invalid" in data:
        return "Item id parameter not found. Please enter ID and try again."

    if len(data['id']) > 0:
        filters = [["Item", "name", "=", data['id']]]
        return getDocument('Item', filters=filters, fields=field)
    elif len(data['id']) == 0:
        return getDocument('Item', fields=field)

