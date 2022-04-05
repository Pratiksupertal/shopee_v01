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
def filter_stock_entry_for_warehouse_app():
    """Filter Stock Entry

    Filter includes
        - stock entry type
        - order purpose
    """
    try:
        url = frappe.request.url
        stock_entry_type = parse_qs(urlparse(url).query).get('stock_entry_type')
        order_purpose = parse_qs(urlparse(url).query).get('order_purpose')
        if stock_entry_type is not None:
            stock_entry_type = stock_entry_type[0]
        if order_purpose is not None:
            order_purpose = order_purpose[0]

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

        """filter by
        4. order purpose as per request
        """
        filtered_se = [se for se in filtered_se
                       if order_purpose == frappe.db.get_value(
                           'Pick List', se.get('pick_list'), 'purpose')]

        """find and add other necessary fields"""
        for se in filtered_se:
            pl_data = frappe.db.get_value(
                'Pick List', se.get('pick_list'), ['customer', 'picker']
            )
            se['customer_name'] = pl_data[0]
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
                fields=['sales_order', 'qty']
            )
            if len(items_pl) < 1:
                continue
            sales_order = items_pl[0].get('sales_order')
            se['sales_order'] = sales_order

            so_data = frappe.db.get_value(
                'Sales Order', sales_order, ['transaction_date', 'delivery_date', 'owner']
            )
            if so_data:
                se['transaction_date'] = so_data[0]
                se['delivery_date'] = so_data[1]
                se['so_created_by'] = frappe.db.get_value('User', so_data[2], 'full_name')

            items_se = frappe.db.get_list(
                'Stock Entry Detail',
                filters={
                    'parent': se.get("name")
                },
                fields=['qty']
            )
            se['total_product'] = len(items_se)
            se['total qty'] = sum([ise.get('qty') for ise in items_se])

        return format_result(
            result=filtered_se,
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
def create_receive_at_warehouse():
    try:
        data = validate_data(frappe.request.data)
        data_validation_for_create_receive_at_warehouse(data=data)

        base = get_base_url(url=frappe.request.url)

        send_to_ste = base + '/api/method/erpnext.stock.doctype.stock_entry.stock_entry.make_stock_in_entry'
        stock_entry = requests.post(
            send_to_ste.replace("'", '"'),
            headers={
                "Authorization": frappe.request.headers["Authorization"]
            },
            data={"source_name": data.get("outgoing_stock_entry")}
        )

        stock_entry_data = stock_entry.json().get("message")
        stock_entry_data["to_warehouse"] = data.get("t_warehouse")
        stock_entry_data["stock_entry_type"] = data.get("stock_entry_type")
        stock_entry_data["docstatus"] = 1

        receive_ste_url = base + '/api/resource/Stock%20Entry'
        receive_ste_url_api_response = requests.post(
            receive_ste_url.replace("'", '"'),
            headers={
                "Authorization": frappe.request.headers["Authorization"]
            },
            data=json.dumps(stock_entry_data)
        )
        result = {
            "name": receive_ste_url_api_response.json().get("data").get("name")
        }
        return format_result(
            result=result,
            success=True,
            status_code=200,
            message='Received Warehouse Stock Entry is created'
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

        """GET Sales Order, Transaction Date, Delivery Date"""
        pick_list_items = frappe.db.get_list(
            'Pick List Item',
            filters={
                'parent': stock_entry_details.get('pick_list'),
                'parentfield': 'locations'
            },
            fields=['sales_order']
        )
        if pick_list_items:
            sales_order = pick_list_items[0].sales_order

        if not sales_order:
            raise Exception('No sales order found associated with this stock entry')

        stock_entry_details.sales_order = sales_order

        so_date_data = frappe.db.get_value(
            'Sales Order',
            sales_order,
            ['customer', 'customer_name', 'customer_address', 'transaction_date', 'delivery_date']
        )
        if so_date_data:
            stock_entry_details.customer = so_date_data[0]
            stock_entry_details.customer_name = so_date_data[1]
            stock_entry_details.customer_address = frappe.db.get_value(
                'Address',
                so_date_data[2],
                ['name', 'address_type', 'address_line1', 'address_line2',
                 'city', 'state', 'country', 'pincode', 'email_id', 'phone', 'fax'],
                as_dict=1
            )
            stock_entry_details.transaction_date = so_date_data[3]
            stock_entry_details.delivery_date = so_date_data[4]

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
def filter_receive_at_warehouse_for_packing_area():
    """Filter Stock Entry Receive at Warehouse

    Filter includes
        - stock entry type (receive at warehouse)
        - order purpose
        - docstatus (0/1/2)
        - has delivery note (yes/no)
        - delivery_note_status (0/1/2)
    """
    try:
        url = frappe.request.url
        stock_entry_type = parse_qs(urlparse(url).query).get('stock_entry_type')
        order_purpose = parse_qs(urlparse(url).query).get('order_purpose')
        docstatus = parse_qs(urlparse(url).query).get('docstatus')
        has_delivery_note = parse_qs(urlparse(url).query).get('has_delivery_note')
        delivery_note_status = parse_qs(urlparse(url).query).get('delivery_note_status')

        if stock_entry_type is None:
            raise Exception('Stock entry type is required')
        if order_purpose is None:
            raise Exception('Order purpose is required')
        if docstatus is None:
            raise Exception('Docstatus is required')
        if has_delivery_note:
            if has_delivery_note[0] in ["yes", "Yes", "YES"] and delivery_note_status is None:
                raise Exception('Delivery note status is required')

        stock_entry_type = stock_entry_type[0]
        order_purpose = order_purpose[0]
        docstatus = docstatus[0]
        if has_delivery_note is not None:
            has_delivery_note = has_delivery_note[0]
        if delivery_note_status is not None:
            delivery_note_status = delivery_note_status[0]

        """filter by
        1. stock entry type = as per request (Receive at Warehouse)
        2. SO purpose = as per request (Delivery)
        3. Received at Warehouse type must be submitted
        4. Stock Entry has Picklist

        4. delivery note action
        if has_delivery_note is no, picklist has no delivery note
        if has_delivery_note is yes, picklist delivery note docstatus == delivery_note_status
        """
        filtered_se = frappe.db.get_list(
            'Stock Entry',
            filters={
                'stock_entry_type': stock_entry_type,
                'docstatus': docstatus,
                'pick_list': ('not in', (None, ''))
            },
            fields=['name', 'pick_list', 'outgoing_stock_entry']
        )

        final_filtered_se = []

        """final filter, find and add other necessary fields"""
        for se in filtered_se:
            if order_purpose != frappe.db.get_value('Pick List', se.get('pick_list'), 'purpose'):
                continue
            dn_status, packer_name = check_delivery_note_status(se.get('pick_list'))

            if has_delivery_note in ["no", "No", "NO"]:
                if dn_status in [0, 1]:  # delivery note not exist, or not in draft or submitted
                    continue
            if has_delivery_note in ["yes", "Yes", "YES"]:
                if dn_status != int(delivery_note_status):
                    continue

            picklist_data = frappe.db.get_value('Pick List', se.get('pick_list'), ['customer', 'picker'])
            se['customer_name'] = picklist_data[0]
            se['picker'] = picklist_data[1]
            se['picker_name'] = frappe.db.get_value('User', picklist_data[1], 'full_name')
            received_by = frappe.db.get_value('Stock Entry', se['outgoing_stock_entry'], 'owner')
            if received_by:
                se['received_by'] = frappe.db.get_value(
                    'User', received_by, 'full_name'
                )

            items_pl = frappe.db.get_list(
                'Pick List Item',
                filters={
                    'parent': se.get("pick_list"),
                    'parentfield': 'locations'
                },
                fields=['sales_order', 'qty']
            )
            if len(items_pl) < 1:
                continue
            sales_order = items_pl[0].get('sales_order')
            se['sales_order'] = sales_order

            so_date_data = frappe.db.get_value('Sales Order', sales_order, ['transaction_date', 'delivery_date', 'owner'])
            if so_date_data:
                se['transaction_date'] = so_date_data[0]
                se['delivery_date'] = so_date_data[1]
                se['so_created_by'] = frappe.db.get_value('User', so_date_data[2], 'full_name')

            items_se = frappe.db.get_list(
                'Stock Entry Detail',
                filters={
                    'parent': se.get("name")
                },
                fields=['qty']
            )

            se['total_product'] = len(items_se)
            se['total qty'] = sum([ise.get('qty') for ise in items_se])
            if has_delivery_note in ["yes", "Yes", "YES"]:
                se['packer_name'] = packer_name
            final_filtered_se.append(se)
        return format_result(
            result=final_filtered_se,
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
