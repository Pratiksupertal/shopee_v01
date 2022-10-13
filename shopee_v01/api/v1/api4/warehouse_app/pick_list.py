import frappe
from urllib.parse import urlparse, parse_qs

from shopee_v01.api.v1.helpers import format_result
from shopee_v01.api.v1.helpers import get_last_parameter
from shopee_v01.api.v1.helpers import get_item_bar_code
from shopee_v01.api.v1.helpers import cleanhtml
from shopee_v01.api.v1.helpers import picklist_item
from shopee_v01.api.v1.helpers import create_new_stock_entry_for_single_item
from shopee_v01.api.v1.helpers import pick_list_details_with_items
from shopee_v01.api.v1.helpers import check_any_item_picked
from shopee_v01.api.v1.helpers import correct_picked_qty_for_submit_pick_list
from shopee_v01.api.v1.helpers import update_endtime_and_submit_pick_list
from shopee_v01.api.v1.helpers import create_and_submit_stock_entry_submit_picklist_and_create_stockentry

from shopee_v01.api.v1.validations import validate_data
from shopee_v01.api.v1.validations import data_validation_for_assign_picker
from shopee_v01.api.v1.validations import data_validation_for_save_picklist_and_create_stockentry
from shopee_v01.api.v1.validations import data_validation_for_submit_picklist_and_create_stockentry


@frappe.whitelist()
def filter_picklist():
    """Filter Pick List for Warehouse App

    Filter includes
        - docstatus (0/1/2)
        - purpose
        - source app name
        - chain
        - store
    """
    try:
        url = frappe.request.url
        docstatus = parse_qs(urlparse(url).query).get('docstatus')
        purpose = parse_qs(urlparse(url).query).get('purpose')
        source_app_name = parse_qs(urlparse(url).query).get('source_app_name')
        chain = parse_qs(urlparse(url).query).get('chain')
        store = parse_qs(urlparse(url).query).get('store')

        if docstatus:
            docstatus = docstatus[0]
        if purpose:
            purpose = purpose[0]
        if source_app_name:
            source_app_name = source_app_name[0]
        if chain:
            chain = chain[0]
        if store:
            store = store[0]

        filtered_picklist = frappe.db.get_list(
            'Pick List',
            filters={
                'docstatus': docstatus,
                'purpose': purpose
            },
            fields=['name', 'customer', 'picker', 'start_time']
        )
        result = []
        for pl in filtered_picklist:
            items = frappe.db.get_list(
                'Pick List Item',
                filters={
                    'parent': pl.get("name"),
                    'parentfield': 'locations'
                },
                fields=['qty', 'picked_qty', 'sales_order']
            )
            sum_qty = sum([it.get('qty') if it.get('qty') not in ['', None] else 0 for it in items])
            sum_picked_qty = sum([it.get('picked_qty') if it.get('picked_qty') not in ['', None] else 0 for it in items])

            if len(items) < 1:
                continue

            sales_order = items[0].get('sales_order')
            so_data = frappe.db.get_value(
                'Sales Order',
                sales_order,
                ['transaction_date', 'delivery_date', 'owner', 'source_app_name', 'chain', 'store', 'external_so_number']
            )

            if source_app_name:
                if so_data[3] != source_app_name:
                    continue

            if chain:
                if so_data[4] != chain:
                    continue

            if store:
                if so_data[5] != store:
                    continue

            result.append({
                "name": pl.get("name"),
                "customer": pl.get("customer"),
                "sales_order": sales_order,
                "transaction_date": so_data[0],
                "delivery_date": so_data[1],
                "total_product": len(items),
                "total_qty": sum_qty,
                "total_qty_received": sum_qty-sum_picked_qty,
                "so_created_by": frappe.db.get_value(
                    'User', so_data[2], 'full_name'
                ),
                "picker": pl.get('picker'),
                "picker_name": frappe.db.get_value(
                    'User',
                    pl.get('picker'),
                    'full_name'
                ),
                "pick_start_time": pl.get('start_time'),
                "external_so_number": so_data[6]
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
def picklist_details_for_warehouse_app():
    try:
        pick_list = get_last_parameter(
            url=frappe.request.url,
            link='picklist_details_for_warehouse_app'
        )

        picklist_details = frappe.db.get_value(
            'Pick List',
            pick_list,
            ['name', 'docstatus', 'purpose', 'customer', 'creation',
             'modified', 'picker', 'start_time', 'end_time'],
            as_dict=1
        )

        if not picklist_details:
            raise Exception('Invalid pick list name')

        items = frappe.db.get_list(
            'Pick List Item',
            filters={
                'parent': pick_list,
                'parentfield': 'locations'
            },
            fields=[
                'item_code', 'item_name', 'warehouse', 'qty', 'picked_qty',
                'uom', 'sales_order'
            ],
            order_by='warehouse'
        )

        picklist_details.sales_order = items[0].sales_order

        so_details = frappe.db.get_value(
            'Sales Order',
            picklist_details.sales_order,
            ['creation', 'delivery_date', 'owner', 'external_so_number'],
            as_dict=1
        )

        picklist_details.so_date = so_details.creation
        picklist_details.delivery_date = so_details.delivery_date
        picklist_details.external_so_number = so_details.external_so_number

        picklist_details.so_created_by = frappe.db.get_value(
            'User', so_details.owner, 'full_name'
        )

        picklist_details.picker_name = frappe.db.get_value(
            'User', picklist_details.picker, 'full_name'
        )

        for it in items:
            it.picked_qty = it.qty - it.picked_qty
            bar_code = get_item_bar_code(it.item_code)
            it["item_bar_code_value"] = None if not bar_code else cleanhtml(bar_code)
            it["item_bar_code"] = None if not bar_code else bar_code

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


@frappe.whitelist()
def assign_picker():
    try:
        data = validate_data(frappe.request.data)
        data_validation_for_assign_picker(data=data)

        """Update picklist picker and start time"""
        frappe.db.set_value(
            'Pick List',
            data.get('pick_list'),
            {
                'picker': frappe.session.user,
                'start_time': frappe.utils.get_datetime()
            }
        )

        return format_result(
            result='picker assigned',
            success=True,
            message='success',
            status_code=200
        )
    except Exception as e:
        return format_result(
            success=False,
            status_code=400,
            message=str(e),
            exception=str(e)
        )


@frappe.whitelist()
def save_picklist_and_create_stockentry():
    """
    @agenda
    - Update Pick List Item Quantity
    - Create a Stock Entry

    @lookup
    - Only one item can be updated at a time
    - Only assigned picker can pick the item
    """
    try:
        data = validate_data(frappe.request.data)
        data_validation_for_save_picklist_and_create_stockentry(data=data)

        """GET Pick List Item (sorted_locations) Details"""
        item = picklist_item(
            data=data
        )

        """Validate picked quantity, we are decreasing the value actually"""
        new_picked_qty = int(item.get('picked_qty')) - int(data.get('picked_qty'))
        if new_picked_qty < 0.0:
            raise Exception("Picked quantity can not be more than total quantity.")

        """Adding remarks to the Pick List."""
        picklist = frappe.get_doc("Pick List", data.get('pick_list'))
        picklist.note = data.get('remarks')
        picklist.save()

        """Create stock entry"""
        stock_entry = create_new_stock_entry_for_single_item(
            data=data,
            item=item
        )

        """Update picklist item picked qty"""
        frappe.db.set_value('Pick List Item', item.get('name'), {
            'picked_qty': new_picked_qty
        })

        return format_result(
            result={
                'stock entry': stock_entry.name
            },
            success=True,
            message='success',
            status_code=200
        )
    except Exception as e:
        return format_result(
            success=False,
            status_code=400,
            message=str(e),
            exception=str(e)
        )


@frappe.whitelist()
def submit_picklist_and_create_stockentry():
    """
    @agenda
    - Submit the Pick List
    - Create a Stock Entry Send to Warehouse

    @lookup
    - Only assigned picker can submit the pick list
    - At least one item has to be picked with some quantity
    - Partial picking allowed
    - Auto correct the picked qty again
    """
    try:
        data = validate_data(frappe.request.data)
        data_validation_for_submit_picklist_and_create_stockentry(data=data)

        """GET Pick List Details and Items"""
        pick_list_details, pick_list_items = pick_list_details_with_items(
            pick_list=data.get('pick_list')
        )

        """If any of the items not picked, do no proceed."""
        is_item_picked = check_any_item_picked(
            pick_list_items=pick_list_items
        )
        if not is_item_picked:
            raise Exception('No picked items found. Please, pick some items first.')

        """Correct picked qty"""
        correct_picked_qty_for_submit_pick_list(
            pick_list_items=pick_list_items
        )

        """Update end time picking and submit pick list"""
        update_endtime_and_submit_pick_list(
            pick_list=data.get('pick_list')
        )

        """If pick list is not submitted, do not create stock entry"""
        pick_list_status = frappe.db.get_value('Pick List', data.get('pick_list'), 'docstatus')
        if pick_list_status != 1:
            correct_picked_qty_for_submit_pick_list(
                pick_list_items=pick_list_items
            )
            raise Exception('Pick List submission failed. Can not create stock entry.')

        """Create new stick entry, save and submit"""
        new_doc_stock_entry = create_and_submit_stock_entry_submit_picklist_and_create_stockentry(
            data=data,
            pick_list_details=pick_list_details,
            pick_list_items=pick_list_items
        )

        return format_result(
            result={'stock entry': new_doc_stock_entry.name,
                    'items': new_doc_stock_entry.items
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
