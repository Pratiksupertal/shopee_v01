import frappe
import requests
from urllib.parse import urlparse

from shopee_v01.api.v1.helpers import *


@frappe.whitelist(allow_guest=True)
def login():
    try:
        data = validate_data(frappe.request.data)
        base = get_base_url(url=frappe.request.url)

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