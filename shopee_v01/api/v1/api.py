import json

import frappe
import requests

cookie = ''
base = 'http://localhost:8000'


@frappe.whitelist(allow_guest=True)
def ping():
    r = json.loads(frappe.request.data) if len(frappe.request.data) > 0 else 'nothing'
    return r


@frappe.whitelist(allow_guest=True)
def login():
    data = {
        "usr": "administrator",
        "pwd": "HaloRetail"
    }
    # try:
    #     data = json.loads(frappe.request.data)
    # except ValueError:
    #     return "Invalid JSON submitted"
    res = requests.post(base + '/api/method/login', data)

    if res.status_code != 200:
        return {'message': 'Credentials invalid. Could not login.'}

    global cookie
    cookie = res.cookies

    return res.json()


def getDocument(docType, filters=None, fields=None):
    if not cookie:
        return {'message': 'Credentials not identified. Please login first.'}

    url = base + '/api/resource/' + docType

    if fields:
        url += '?fields=' + str(fields).replace("'", '"')
    if filters:
        url += '?filters=' + str(filters).replace("'", '"')

    res = requests.get(url, cookies=cookie)
    print(res.json())
    if res.status_code != 200:
        return {'message': 'Error: Unable to retrieve requested item.'}
    return res.json()


@frappe.whitelist(allow_guest=True)
def logout():
    global cookie
    cookie = None


@frappe.whitelist(allow_guest=True)
def warehouse_list():
    return getDocument('Warehouse')


@frappe.whitelist(allow_guest=True)
def warehouse_area_list():
    field = ["warehouse_name", "pin", "city", "state", "address_line_1", "address_line_2"]
    return getDocument('Warehouse', fields=field)


@frappe.whitelist(allow_guest=True)
def warehouse_area_by_id():
    login()
    data = {
        "id":"Finished Goods - II"
    }
    # try:
    #     data = json.loads(frappe.request.data)
    # except ValueError:
    #     return "Invalid JSON submitted"
    field = ["warehouse_name", "pin", "city", "state", "address_line_1", "address_line_2"]
    if data['id']:
        filters = [["Warehouse", "warehouse_name", "=", data['id']]]
        return getDocument('Warehouse', filters=filters, fields=field)
    else:
        return "Warehouse id parameter not found. Please enter ID and try again."


@frappe.whitelist(allow_guest=True)
def sales_order():
    return getDocument('Sales Order')


@frappe.whitelist(allow_guest=True)
def purchase_order():
    return getDocument('Purchase Order')


@frappe.whitelist(allow_guest=True)
def item_list():
    return getDocument('Item')


@frappe.whitelist(allow_guest=True)
def item_detail_list():
    field = ["*"]
    return getDocument('Item', fields=field)
