import frappe
import traceback
from urllib.parse import urlparse, parse_qs

from shopee_v01.api.v1.helpers import *


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