import frappe
from urllib.parse import urlparse, parse_qs

from shopee_v01.api.v1.helpers import format_result
from shopee_v01.api.v1.helpers import get_last_parameter
from shopee_v01.api.v1.helpers import get_item_bar_code
from shopee_v01.api.v1.helpers import cleanhtml


@frappe.whitelist()
def filter_picklist_from_material_request():
    """Filter Pick List for Warehouse App

    Filter includes
        - docstatus (0/1/2)
        - Stock Entry
    """
    try:
        url = frappe.request.url
        docstatus = parse_qs(urlparse(url).query).get('docstatus')
        material_request = parse_qs(urlparse(url).query).get('material_request')

        filters = {}

        if docstatus:
            docstatus = docstatus[0]
            filters['docstatus'] = docstatus
        if material_request:
            material_request = material_request[0]
            filters['material_request'] = material_request
        else:
            filters['material_request'] = ['like', '%-MR-%']

        filtered_picklist = frappe.db.get_list(
            'Pick List',
            filters=filters,
            fields=['name', 'customer', 'picker', 'start_time', 'material_request']
        )

        result = []
        for pl in filtered_picklist:
            items = frappe.db.get_list(
                'Pick List Item',
                filters={
                    'parent': pl.get("name"),
                    'parentfield': 'locations'
                },
                fields=['qty', 'picked_qty']
            )
            sum_qty = sum([it.get('qty') if it.get('qty') not in ['', None] else 0 for it in items])
            sum_picked_qty = sum([it.get('picked_qty') if it.get('picked_qty') not in ['', None] else 0 for it in items])

            if len(items) < 1:
                continue

            mr_data = frappe.db.get_value(
                'Material Request',
                pl.get('material_request'),
                ['transaction_date', 'schedule_date', 'owner']
            )
            if not mr_data:
                continue

            target_warehouse = frappe.db.get_list(
                'Material Request Item',
                filters={
                    'parent': material_request
                },
                fields=['warehouse'])

            result.append({
                "name": pl.get("name"),
                "material_request": pl.get('material_request'),
                "target_warehouse": target_warehouse[0]['warehouse'],
                "transaction_date": mr_data[0],
                "required_date": mr_data[1],
                "total_product": len(items),
                "total_qty": sum_qty,
                "total_qty_received": sum_qty-sum_picked_qty,
                "mr_created_by": frappe.db.get_value(
                    'User', mr_data[2], 'full_name'
                ),
                "picker": pl.get('picker'),
                "picker_name": frappe.db.get_value(
                    'User',
                    pl.get('picker'),
                    'full_name'
                ),
                "pick_start_time": pl.get('start_time'),
            })
        return format_result(
            result=result,
            success=True,
            status_code=200,
            message='Data Found'
        )
    except Exception as e:
        return format_result(
            result=None,
            success=False,
            status_code=400,
            message=str(e)
        )


@frappe.whitelist()
def picklist_details_for_material_request():
    try:
        pick_list = get_last_parameter(
            url=frappe.request.url,
            link='picklist_details_for_warehouse_app'
        )

        picklist_details = frappe.db.get_value(
            'Pick List',
            pick_list,
            ['name', 'material_request', 'docstatus', 'purpose', 'creation',
             'modified', 'picker', 'start_time', 'end_time'],
            as_dict=1
        )

        if not picklist_details:
            raise Exception('Invalid pick list name')

        mr_data = frappe.db.get_value(
            'Material Request',
            picklist_details.material_request,
            ['transaction_date', 'schedule_date', 'owner']
        )

        target_warehouse = frappe.db.get_list(
            'Material Request Item',
            filters={
                'parent': picklist_details.material_request
            },
            fields=['warehouse'])

        picklist_details.transaction_date = mr_data[0]
        picklist_details.required_date = mr_data[1]
        picklist_details.target_warehouse = target_warehouse[0]['warehouse']
        picklist_details.mr_created_by = frappe.db.get_value(
            'User', mr_data[2], 'full_name'
        )

        items = frappe.db.get_list(
            'Pick List Item',
            filters={
                'parent': pick_list,
                'parentfield': 'locations'
            },
            fields=[
                'item_code', 'item_name', 'warehouse', 'qty', 'picked_qty',
                'uom'
            ],
            order_by='warehouse'
        )

        picklist_details.picker_name = frappe.db.get_value(
            'User', picklist_details.picker, 'full_name'
        )

        for it in items:
            it.picked_qty = it.qty - it.picked_qty
            bar_code = get_item_bar_code(it.item_code)
            it["item_bar_code_value"] = None if not bar_code else cleanhtml(bar_code)

        picklist_details.items = items

        return format_result(
            result={
                'pick_list': picklist_details
            },
            success=True,
            message='Data Created',
            status_code=200
        )
    except Exception as e:
        return format_result(
            result=None,
            success=False,
            status_code=400,
            message=str(e),
            exception=str(e)
        )
