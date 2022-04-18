import frappe

from shopee_v01.api.v1.helpers import format_result
from shopee_v01.api.v1.helpers import get_last_parameter


@frappe.whitelist()
def warehouses():
    fields = [
        'idx',
        'warehouse_name',
        'name',
        'parent',
        'warehouse_type',
    ]

    warehouse_list = frappe.get_list('Warehouse', fields=fields)
    result = []

    user = frappe.session.user
    user_warehouses = frappe.db.sql(
        "SELECT warehouse_id FROM `tabUser Warehouse Mapping` where user_id='{}'"
        .format(user))
    user_warehouses = [warehouse[0] for warehouse in user_warehouses]
    print(user_warehouses)

    for i in warehouse_list:
        warehouse_areas = frappe.get_list('Warehouse', fields=[
            "idx",
            "warehouse_id",
            "name",
            # "usage_type_id",
            # "description",
            "creation",
            "owner",
            "modified",
            "modified_by"
        ], filters={'parent_warehouse': i['name']})

        temp_dict = {
            "id": str(i['idx']),
            "name": i['warehouse_name'],
            "code": i['name'],
            "description": None,
            "areas": [{
                'id': j['idx'],
                'warehouse_id': j['warehouse_id'],
                'name': j['name'],
                'create_time': j['creation'],
                'update_time': j['modified'],
                'create_user_id': j['owner'],
                'update_user_id': j['modified_by'],
                'usage_type_id': None,
                'description': None
            } for j in warehouse_areas if j['name'] in user_warehouses]
        }

        if len(temp_dict.get('areas', [])):
            result.append(temp_dict)

    return format_result(result=result, status_code=200, message='Data Found')


@frappe.whitelist()
def warehouseAreas():
    fields = [
        "idx",
        "warehouse_name",
        "name",
        "parent",
        "warehouse_type",
    ]

    specific = {"parent_warehouse": ('!=', '')}

    specific_part = get_last_parameter(frappe.request.url, 'warehouseAreas')
    if specific_part:
        specific['name'] = specific_part

    warehouse_areas_list = frappe.get_list('Warehouse', fields=fields, filters=specific)
    result = []

    for i in warehouse_areas_list:
        temp_dict = {
            "id": str(i['idx']),
            "warehouse_id": i['name'],
            "usage_type_id": None,
            "name": i['warehouse_name'],
            "description": None,
            "storages": None
        }
        result.append(temp_dict)

    return format_result(result=result, status_code=200, message='Data Found')
