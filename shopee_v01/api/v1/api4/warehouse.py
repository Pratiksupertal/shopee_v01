import frappe

from shopee_v01.api.v1.helpers import format_result
from shopee_v01.api.v1.helpers import get_last_parameter
from shopee_v01.api.v1.helpers import get_user_mapped_warehouses


@frappe.whitelist()
def warehouses():
    """
    Using in Mobile App (flow: login -> Receiving -> PO -> Supplier DO -> Target warehouse)
    There will show all the warehouse mapped with logged in user (Warehouse and User Mapping)
    """
    user_warehouses = get_user_mapped_warehouses()
    warehouse_areas = frappe.get_list(
        'Warehouse',
        fields=[
            "idx",
            "name",
            "warehouse_id",
            "creation",
            "owner",
            "modified",
            "modified_by",
            "parent"
        ],
        filters={
            "name": ["in", user_warehouses]
        }
    )
    return format_result(
        result=warehouse_areas,
        status_code=200,
        message='Data Found'
    )


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

    return format_result(
        result=result,
        status_code=200,
        message='Data Found'
    )
