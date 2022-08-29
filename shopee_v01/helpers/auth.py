import frappe
import requests
import json


def get_auth_token(config):
    try:
        url = config.base_url + 'auth'
        data = {
            "username": config.username,
            "password": config.get_password('password')
        }
        auth_res = requests.post(url.replace("'", '"'), data=data)
        auth_res_json = json.loads(auth_res.text)
        auth_token = "Bearer " + auth_res_json["data"]["token"]
        return auth_token
    except Exception:
        raise
        frappe.log_error(title="Update stock API Login part", message=frappe.get_traceback())
        frappe.msgprint(f'Problem in halosis update. {frappe.get_traceback()}')
