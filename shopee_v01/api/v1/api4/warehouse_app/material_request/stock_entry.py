import frappe
import json
import requests
from urllib.parse import urlparse, parse_qs

from shopee_v01.api.v1.helpers import format_result
from shopee_v01.api.v1.helpers import get_last_parameter
from shopee_v01.api.v1.helpers import get_base_url
from shopee_v01.api.v1.validations import validate_data
from shopee_v01.api.v1.validations import data_validation_for_create_receive_at_warehouse
from shopee_v01.api.v1.validations import data_validation_for_stock_entry_send_to_shop


@frappe.whitelist()
def filter_stock_entry_for_material_request():
    """Filter Stock Entry

    Filter includes
        - docstatus (0/1/2)
        - stock entry type
        - Pick List
    """
    try:
        url = frappe.request.url
        docstatus = parse_qs(urlparse(url).query).get('docstatus')
        pick_list = parse_qs(urlparse(url).query).get('pick_list')
        stock_entry_type = parse_qs(urlparse(url).query).get('stock_entry_type')

        filters = {}

        if docstatus:
            docstatus = docstatus[0]
            filters['docstatus'] = docstatus
        if pick_list:
            pick_list = pick_list[0]
        if stock_entry_type is not None:
            stock_entry_type = stock_entry_type[0]
            filters['stock_entry_type'] = stock_entry_type

        filters['per_transferred'] = ('!=', int(100))
        filters['pick_list'] = ('not in', (None, ''))

        """filter by
        1. docstatus
        2. stock entry type as per request
        3. not fully transferred (status in Draft or Goods In Transit)
        4. picklist be there
        """
        filtered_se = frappe.db.get_list(
            'Stock Entry',
            filters=filters,
            fields=['name', 'pick_list']
        )

        result_se = []

        """find and add other necessary fields"""
        for se in filtered_se:
            pl_data = frappe.db.get_value(
                'Pick List', se.get('pick_list'), ['customer', 'picker', 'material_request', 'name']
            )

            if pick_list is not None:
                if pl_data[3] != pick_list:
                    continue

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

            warehouses = frappe.db.get_list(
                'Stock Entry Detail',
                filters={
                    'parent': se.get('name')
                },
                fields=['t_warehouse', 's_warehouse'])
            se['source_warehouse'] = warehouses[0]['s_warehouse']
            se['target_warehouse'] = warehouses[0]['t_warehouse']

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
def stock_entry_details_for_material_request():
    try:
        stock_entry = get_last_parameter(frappe.request.url, 'stock_entry_details_for_material_request')

        """GET Stock Entry Details"""

        stock_entry_details = frappe.db.get_value(
            'Stock Entry',
            stock_entry,
            ['name', 'docstatus', 'stock_entry_type', 'creation', 'modified', 'pick_list', 'outgoing_stock_entry'],
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
        stock_entry_details['total_product'] = len(items)
        stock_entry_details['total qty'] = sum([ise.get('qty') for ise in items])
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


@frappe.whitelist()
def create_receive_at_warehouse_for_material_request():
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

        if stock_entry.status_code != 200:
            raise Exception('Please, check the outgoing stock entry status.')

        stock_entry_data = stock_entry.json().get("message")
        stock_entry_data["to_warehouse"] = data.get("t_warehouse")
        stock_entry_data["stock_entry_type"] = data.get("stock_entry_type")
        stock_entry_data["docstatus"] = 0

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
def create_send_to_shop_for_material_request():
    try:
        data = validate_data(frappe.request.data)
        data_validation_for_stock_entry_send_to_shop(data=data)

        if data.get("stock_entry_type") != "Send to Shop":
            raise Exception("Stock Entry Type is not Send to Shop.")
        outgoing_stock_entry_doc = frappe.get_doc("Stock Entry", data.get("outgoing_stock_entry"))
        if outgoing_stock_entry_doc.stock_entry_type != "Receive at Warehouse":
            raise Exception("Outgoing Stock Entry Type is not Receive at Warehouse.")

        outgoing_stock_entry_doc.save()
        outgoing_stock_entry_doc.submit()
        if outgoing_stock_entry_doc.docstatus != 1:
            raise Exception("Outgoing Stock Entry Receive at Warehouse not submitted.")

        new_doc = frappe.new_doc('Stock Entry')
        new_doc.outgoing_stock_entry = data.get("outgoing_stock_entry")
        new_doc.stock_entry_type = data.get("stock_entry_type")
        new_doc.company = outgoing_stock_entry_doc.get("company")
        new_doc.pick_list = outgoing_stock_entry_doc.get("pick_list")
        new_doc.remarks = outgoing_stock_entry_doc.get("remarks")

        items = frappe.db.get_list('Stock Entry Detail', filters={'parent': outgoing_stock_entry_doc.get("name")},
                                   fields=['item_code', 'item_group', 'qty'])
        total = 0
        for item in items:
            new_doc.append("items", {
                "item_code": item['item_code'],
                "t_warehouse": data.get("t_warehouse"),
                "s_warehouse": data.get("s_warehouse"),
                "qty": str(item['qty'])
                })
            total += item['qty']
        new_doc.save()

        stock_entry_data = {"Receive at Warehouse Stock Entry submitted": outgoing_stock_entry_doc.name,
                            "Send to Shop Stock Entry created": new_doc.name}

        return format_result(
            result=stock_entry_data,
            success=True,
            status_code=200,
            message='Receive at Warehouse Stock Entry submitted, Send to Shop Stock Entry is created'
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
def submit_send_to_shop_for_material_request():
    try:
        data = validate_data(frappe.request.data)

        stock_entry_doc = frappe.get_doc("Stock Entry", data.get("stock_entry"))
        if not stock_entry_doc:
            pass
        if stock_entry_doc.stock_entry_type != "Send to Shop":
            raise Exception("Stock Entry Type is not Send to Shop.")

        stock_entry_doc.save()
        stock_entry_doc.submit()

        if stock_entry_doc.docstatus != 1:
            raise Exception("Outgoing Stock Entry Send to Shop not submitted.")

        items = frappe.db.get_list('Stock Entry Detail', filters={'parent': stock_entry_doc.get("name")},
                                   fields=['item_code', 'item_name', 'item_group', 'qty', 'basic_rate', 's_warehouse',
                                           't_warehouse'])

        total = 0
        s_warehouse, t_warehouse = None, None
        for item in items:
            item['attribute_value'] = frappe.db.get_value('Item Variant Attribute', {'parent': item['item_name']}, 'attribute_value')
            item['invent_size_id'] = frappe.db.get_value('Item', {'name': item['item_name']}, 'invent_size_id')
            s_warehouse = item['s_warehouse']
            t_warehouse = item['t_warehouse']
            total += item['qty']

        stock_entry_data = {}
        stock_entry_data["name"] = stock_entry_doc.name
        stock_entry_data["s_warehouse"] = s_warehouse
        stock_entry_data["t_warehouse"] = t_warehouse
        stock_entry_data["stock_entry_type"] = stock_entry_doc.get("stock_entry_type")
        stock_entry_data["outgoing_stock_entry"] = stock_entry_doc.get("outgoing_stock_entry")
        stock_entry_data["pick_list"] = stock_entry_doc.get("pick_list")
        stock_entry_data["company"] = stock_entry_doc.get("company")

        """GET Material Request, Transaction Date, Required Date, Material Request created by"""
        pl_data = frappe.db.get_value(
            'Pick List', stock_entry_doc.get("pick_list"), ['customer', 'picker', 'material_request']
        )

        material_request = None
        if pl_data:
            stock_entry_data["picker"] = pl_data[1]
            stock_entry_data["picker_name"] = frappe.db.get_value('User', pl_data[1], 'full_name')
            material_request = pl_data[2]

        if not material_request:
            raise Exception('No Material Request found associated with this stock entry')

        stock_entry_data["material_request"] = material_request

        mr_data = frappe.db.get_value(
            'Material Request',
            material_request,
            ['name', 'transaction_date', 'schedule_date', 'owner']
        )
        if mr_data:
            stock_entry_data['delivery_warehouse'] = frappe.db.get_value("Material Request Item", {'parent': mr_data[0]}
                                                                         , 'warehouse')
            stock_entry_data['material_request'] = mr_data[0]
            stock_entry_data['transaction_date'] = mr_data[1]
            stock_entry_data['required_date'] = mr_data[2]
            stock_entry_data['mr_created_by'] = frappe.db.get_value('User', mr_data[3], 'full_name')
        stock_entry_data['items'] = items

        return format_result(
            result=stock_entry_data,
            success=True,
            status_code=200,
            message='Send to Shop Stock Entry is Submitted'
        )
    except Exception as e:
        return format_result(
            result=None,
            success=False,
            status_code=400,
            message=str(e),
            exception=str(e)
        )
