import frappe

from shopee_v01.api.v1.helpers import format_result
from shopee_v01.api.v1.validations import validate_data


"""
@note After creating the delivery note from a picklist,
        the stock entry that associated with it -
        will go to Finished List from packing area
"""
@frappe.whitelist()
def create_delivery_note_from_pick_list():
    try:
        data = validate_data(frappe.request.data)
        pick_list_name = data.get('pick_list')
        if not pick_list_name:
            raise Exception('Pick List name required')

        pick_list_data = frappe.db.get_value(
            'Pick List',
            pick_list_name,
            ['name', 'customer', 'company']
        )
        if not pick_list_data[0]:
            raise Exception('Pick List name is not valid')

        pick_list_items = frappe.db.get_list(
            'Pick List Item',
            filters={
                'parent': pick_list_name,
                'parentfield': 'locations'
            },
            fields=['item_code', 'item_name', 'qty', 'uom', 'warehouse']
        )

        delivery_note = frappe.new_doc('Delivery Note')
        delivery_note.customer = pick_list_data[1]
        delivery_note.company = pick_list_data[2]
        delivery_note.pick_list = pick_list_name
        for item in pick_list_items:
            delivery_note.append("items", item)
        delivery_note.insert()
        return format_result(
            result=delivery_note,
            success=True,
            message='Delivery Note successfully created',
            status_code=200
        )
    except Exception as e:
        return format_result(
            success=False,
            status_code=400,
            message=str(e),
            exception=str(e)
        )
