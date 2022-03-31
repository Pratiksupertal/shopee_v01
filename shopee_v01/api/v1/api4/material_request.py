import frappe

from shopee_v01.api.v1.helpers import format_result


@frappe.whitelist()
def material_requests():
    each_data_list = list(map(lambda x: frappe.get_doc('Material Request', x),
                              [i['name'] for i in frappe.get_list('Material Request')]))
    return format_result(result=each_data_list, status_code=200, message='Data Found')
