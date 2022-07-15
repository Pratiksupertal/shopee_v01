import frappe
import json
import requests
from urllib.parse import urlparse, parse_qs

from shopee_v01.api.v1.helpers import format_result
from shopee_v01.api.v1.helpers import get_base_url
from shopee_v01.api.v1.helpers import get_last_parameter
from shopee_v01.api.v1.helpers import check_delivery_note_status
from shopee_v01.api.v1.validations import validate_data
from shopee_v01.api.v1.validations import data_validation_for_create_receive_at_warehouse


@frappe.whitelist()
def filter_stock_entry_for_material_request():
    """Filter Stock Entry

    Filter includes
        - stock entry type
    """
    try:
        url = frappe.request.url
        stock_entry_type = parse_qs(urlparse(url).query).get('stock_entry_type')
        if stock_entry_type is not None:
            stock_entry_type = stock_entry_type[0]

        """filter by
        1. stock entry type as per request
        2. not fully transferred (status in Draft or Goods In Transit)
        3. picklist be there
        """
        filtered_se = frappe.db.get_list(
            'Stock Entry',
            filters={
                'stock_entry_type': stock_entry_type,
                'per_transferred': ('!=', int(100)),
                'pick_list': ('not in', (None, ''))
            },
            fields=['name', 'pick_list']
        )

        result_se = []

        """find and add other necessary fields"""
        for se in filtered_se:
            pl_data = frappe.db.get_value(
                'Pick List', se.get('pick_list'), ['customer', 'picker', 'material_request']
            )

            if pl_data[2]:
                mr_data = frappe.db.get_value(
                    'Material Request',
                    pl_data[2],
                    ['name', 'transaction_date', 'schedule_date', 'owner']
                )
                if mr_data:
                    se['material_request'] = mr_data[0]
                    se['transaction_date'] = mr_data[1]
                    se['required_date'] = mr_data[2]
                    se['mr_created_by'] = frappe.db.get_value('User', mr_data[3], 'full_name')
                else:
                    continue
            else:
                continue

            se['picker'] = pl_data[1]
            se['picker_name'] = frappe.db.get_value(
                'User', pl_data[1], 'full_name'
            )

            items_pl = frappe.db.get_list(
                'Pick List Item',
                filters={
                    'parent': se.get("pick_list"),
                    'parentfield': 'locations'
                },
                fields=['qty']
            )

            target_warehouse = frappe.db.get_list(
                'Stock Entry Detail',
                filters={
                    'parent': se.get('name')
                },
                fields=['t_warehouse'])
            se['target_warehouse'] = target_warehouse[0]['t_warehouse']

            if len(items_pl) < 1:
                continue

            items_se = frappe.db.get_list(
                'Stock Entry Detail',
                filters={
                    'parent': se.get("name")
                },
                fields=['qty']
            )
            se['total_product'] = len(items_se)
            se['total qty'] = sum([ise.get('qty') for ise in items_se])
            result_se.append(se)

        return format_result(
            result=result_se,
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
def stock_entry_details_for_warehouse_app():
    try:
        stock_entry = get_last_parameter(frappe.request.url, 'stock_entry_details_for_warehouse_app')

        """GET Stock Entry Details"""

        stock_entry_details = frappe.db.get_value(
            'Stock Entry',
            stock_entry,
            ['name', 'docstatus', 'purpose', 'creation', 'modified', 'pick_list'],
            as_dict=1
        )

        if not stock_entry_details:
            raise Exception('Invalid stock entry name')

        """GET Material Request, Transaction Date, Required Date, Material Request created by"""
        pl_data = frappe.db.get_value(
            'Pick List', stock_entry_details.get('pick_list'), ['customer', 'picker', 'material_request']
        )

        material_request = None
        if pl_data:
            material_request = pl_data[2]

        if not material_request:
            raise Exception('No Material Request found associated with this stock entry')

        stock_entry_details.material_request = material_request

        mr_data = frappe.db.get_value(
            'Material Request',
            material_request,
            ['name', 'transaction_date', 'schedule_date', 'owner']
        )
        if mr_data:
            stock_entry_details['material_request'] = mr_data[0]
            stock_entry_details['transaction_date'] = mr_data[1]
            stock_entry_details['required_date'] = mr_data[2]
            stock_entry_details['mr_created_by'] = frappe.db.get_value('User', mr_data[3], 'full_name')

        """GET ITEMS"""
        items = frappe.db.get_list(
            'Stock Entry Detail',
            filters={
                'parent': stock_entry
            },
            fields=[
                'item_code', 'item_name', 'qty', 'transfer_qty', 'uom', 's_warehouse', 't_warehouse'
            ]
        )
        stock_entry_details.items = items
        return format_result(
            result=stock_entry_details,
            success=True,
            message='Data Found',
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
