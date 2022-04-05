import frappe

from shopee_v01.api.v1.helpers import format_result


@frappe.whitelist()
def source_app_name_list():
    try:
        apps = frappe.db.sql("""SELECT name FROM `tabSource App Name`""")
        result = list(map(lambda app: app[0], apps))
        return format_result(result=result, success=True, status_code=200, message='Data Found')
    except Exception as e:
        return format_result(result=None, success=False, status_code=400, message=str(e))


@frappe.whitelist()
def chain_list():
    try:
        apps = frappe.db.sql("""SELECT name FROM `tabChain`""")
        result = list(map(lambda app: app[0], apps))
        return format_result(result=result, success=True, status_code=200, message='Data Found')
    except Exception as e:
        return format_result(result=None, success=False, status_code=400, message=str(e))


@frappe.whitelist()
def store_list():
    try:
        apps = frappe.db.sql("""SELECT name FROM `tabStore`""")
        result = list(map(lambda app: app[0], apps))
        return format_result(result=result, success=True, status_code=200, message='Data Found')
    except Exception as e:
        return format_result(result=None, success=False, status_code=400, message=str(e))
