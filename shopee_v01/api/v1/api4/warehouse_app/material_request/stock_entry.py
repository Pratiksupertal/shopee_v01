import frappe
import json
import requests
from urllib.parse import urlparse, parse_qs

from shopee_v01.api.v1.helpers import format_result
from shopee_v01.api.v1.helpers import get_last_parameter
from shopee_v01.api.v1.helpers import get_base_url
from shopee_v01.api.v1.helpers import submit_stock_entry_send_to_shop
from shopee_v01.api.v1.helpers import create_new_stock_entry_from_outgoing_stock_entry
from shopee_v01.api.v1.validations import validate_data
from shopee_v01.api.v1.validations import data_validation_for_create_receive_at_warehouse
from shopee_v01.api.v1.validations import data_validation_for_stock_entry_send_to_shop


@frappe.whitelist()
def filter_stock_entry_for_material_request():
    """Filter Stock Entry

    Filter parameters includes
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
    """ This method displays the detailed view of fields and values of the Stock Entry."""
    try:
        stock_entry = get_last_parameter(frappe.request.url, 'stock_entry_details_for_material_request')
        stock_entry_doc = frappe.get_doc("Stock Entry", stock_entry)

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
            stock_entry_details['delivery_warehouse'] = frappe.db.get_value("Material Request Item",
                                                                            {'parent': mr_data[0]}, 'warehouse')
            stock_entry_details['material_request'] = mr_data[0]
            stock_entry_details['transaction_date'] = mr_data[1]
            stock_entry_details['required_date'] = mr_data[2]
            stock_entry_details['mr_created_by'] = frappe.db.get_value('User', mr_data[3], 'full_name')

        if stock_entry_doc.stock_entry_type == "Receive at Warehouse":
            stock_entry_details['received_by'] = frappe.db.get_value('User', stock_entry_doc.owner, 'full_name')
        elif stock_entry_doc.stock_entry_type == "Send to Shop":
            outgoing_se_owner = frappe.db.get_value('Stock Entry', stock_entry_doc.outgoing_stock_entry, ['owner'])
            stock_entry_details['received_by'] = frappe.db.get_value('User', outgoing_se_owner, 'full_name')
            stock_entry_details['packed_by'] = frappe.db.get_value('User', stock_entry_doc.owner, 'full_name')

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
    """This method creates Stock Entry with stock_entry_type => Receive at Warehouse as draft from
    Stock Entry with stock_entry_type => Send to Warehouse."""
    try:
        """Data validation segment."""
        data = validate_data(frappe.request.data)
        data_validation_for_create_receive_at_warehouse(data=data)

        if data.get("stock_entry_type") != "Receive at Warehouse":
            raise Exception("Stock Entry Type is not Receive at Warehouse.")
        outgoing_stock_entry_doc = frappe.get_doc("Stock Entry", data.get("outgoing_stock_entry"))
        if outgoing_stock_entry_doc.stock_entry_type != "Send to Warehouse":
            raise Exception("Outgoing Stock Entry Type is not Send to Warehouse.")

        """Create new Stock Entry with stock_entry_type => Receive at Warehouse as draft."""
        new_doc = create_new_stock_entry_from_outgoing_stock_entry(data)
        if not new_doc:
            raise Exception("Problem occurred in creating new Stock Entry.")

        result = {"stock_entry": new_doc.name, "stock_entry_type": new_doc.stock_entry_type}
        return format_result(
            result=result,
            success=True,
            status_code=200,
            message='Received at Warehouse Stock Entry is created'
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
    """This method first submits Stock Entry with stock_entry_type => Receive at Warehouse.
    Then it creates Stock Entry with stock_entry_type => Send to Shop as draft from
    Stock Entry with stock_entry_type => Receive at Warehouse."""
    try:
        """Data validation segment."""
        data = validate_data(frappe.request.data)
        data_validation_for_stock_entry_send_to_shop(data=data)

        if data.get("stock_entry_type") != "Send to Shop":
            raise Exception("Stock Entry Type is not Send to Shop.")
        outgoing_stock_entry_doc = frappe.get_doc("Stock Entry", data.get("outgoing_stock_entry"))
        if outgoing_stock_entry_doc.stock_entry_type != "Receive at Warehouse":
            raise Exception("Outgoing Stock Entry Type is not Receive at Warehouse.")

        """Submit outgoing_stock_entry segment."""
        outgoing_stock_entry_doc.submit()
        if outgoing_stock_entry_doc.docstatus != 1:
            raise Exception("Outgoing Stock Entry Receive at Warehouse not submitted.")
        frappe.db.set_value("Stock Entry", outgoing_stock_entry_doc.outgoing_stock_entry, 'per_transferred', 100)

        """Create new Stock Entry with stock_entry_type => Send to Shop as draft."""
        new_doc = create_new_stock_entry_from_outgoing_stock_entry(data)
        if not new_doc:
            raise Exception("Problem occurred in creating new Stock Entry.")
        stock_entry_data = {"stock_entry": new_doc.name, "stock_entry_type": new_doc.stock_entry_type}

        message = f"Receive at Warehouse Stock Entry [ {outgoing_stock_entry_doc.name} ] submitted," \
                  f" Send to Shop Stock Entry [ {new_doc.name} ] is created"

        return format_result(
            result=stock_entry_data,
            success=True,
            status_code=200,
            message=message
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
    """This method first submits Stock Entry with stock_entry_type => Send to Shop.
    Then it triggers trigger_send_to_shop_spg function which sends request at SPG end."""
    try:
        """Data validation segment."""
        data = validate_data(frappe.request.data)

        stock_entry_doc = frappe.get_doc("Stock Entry", data.get("stock_entry"))
        if not stock_entry_doc:
            pass
        if stock_entry_doc.stock_entry_type != "Send to Shop":
            raise Exception("Stock Entry Type is not Send to Shop.")
        if stock_entry_doc.docstatus == 1:
            raise Exception("Stock Entry already submitted.")

        """Submit Stock Entry segment."""
        stock_entry_doc.save()
        stock_entry_doc.submit()

        if stock_entry_doc.docstatus != 1:
            raise Exception("Outgoing Stock Entry Send to Shop not submitted.")

        """Trigger SPG API function segment."""
        stock_entry_data = submit_stock_entry_send_to_shop(stock_entry_doc)
        trigger_send_to_shop_spg(stock_entry_data)

        return format_result(
            result=stock_entry_data,
            success=True,
            status_code=200,
            message=f'Send to Shop Stock Entry [{stock_entry_doc.name}] is Submitted'
        )
    except Exception as e:
        return format_result(
            result=None,
            success=False,
            status_code=400,
            message=str(e),
            exception=str(e)
        )


def trigger_send_to_shop_spg(request_body):
    """This method triggers Send to Shop Stock Entry at SPG end when Stock Entry Send to Shop
    is submitted at ERP end. The prerequisite data for making API request is fetched from
    Warehouse App Settings."""
    import requests
    config = frappe.get_single("Warehouse App Settings")
    try:
        url = config.spg_base_url + 'request-token'
        data = {
            "username": config.username,
            "password": config.get_password('password')
        }
        auth_res = requests.post(url.replace("'", '"'), data=data)
        if auth_res.status_code not in [200, 201]:
            raise Exception()
        auth_res_json = auth_res.json()
        auth_token = auth_res_json.get('data').get("token")
    except Exception:
        frappe.log_error(title="Trigger Send to Shop API Login part", message=frappe.get_traceback())
        frappe.msgprint(f'Problem in Triggering API. {frappe.get_traceback()}')
        return

    if request_body.get('transfer_date'):
        request_body['transfer_date'] = request_body['transfer_date'].strftime("%Y-%m-%d")
    request = json.dumps(request_body).replace("'", '"')

    try:
        url = config.spg_base_url + 'transfer-request/external/create'
        response = requests.post(
            url.replace("'", '"'),
            headers={"Authorization": "Bearer " + auth_token},
            json=json.loads(request))
        frappe.log_error(title="Trigger Send to Shop API.", message=response.text)

        if response.status_code == 200:
            frappe.msgprint('API triggered. Please, check error log for more update.')
        else:
            frappe.msgprint(f'API trigger has failed for some reason! Please, check error log. {frappe.get_traceback()}')
    except Exception:
        frappe.log_error(title="API trigger Data part", message=frappe.get_traceback())
        frappe.msgprint(f'Problem in API trigger. {frappe.get_traceback()}')


@frappe.whitelist()
def create_receive_at_shop_for_material_request():
    """This method creates and submits Stock Entry with stock_entry_type => Receive at Shop from
    Stock Entry with stock_entry_type => Send to Shop."""
    try:
        """Data validation segment."""
        data = validate_data(frappe.request.data)
        data_validation_for_create_receive_at_warehouse(data=data)
        if data.get("stock_entry_type") != "Receive at Shop":
            raise Exception("Stock Entry Type is not Receive at Shop.")
        outgoing_stock_entry_doc = frappe.get_doc("Stock Entry", data.get("outgoing_stock_entry"))
        if outgoing_stock_entry_doc.stock_entry_type != "Send to Shop":
            raise Exception("Outgoing Stock Entry Type is not Send to Shop.")
        if outgoing_stock_entry_doc.docstatus != 1:
            raise Exception("Outgoing Stock Entry Send to Shop not submitted.")

        """Create new Stock Entry with stock_entry_type => Receive at Shop"""
        new_doc = create_new_stock_entry_from_outgoing_stock_entry(data)
        if not new_doc:
            raise Exception("Problem occurred in creating new Stock Entry.")

        """Submit Stock Entry segment."""
        frappe.db.set_value("Stock Entry", new_doc.name, 'docstatus', 1)
        frappe.db.set_value("Stock Entry", outgoing_stock_entry_doc.name, 'per_transferred', 100)

        "Material Request status change from pending to transferred."
        mr = frappe.db.get_value('Pick List', new_doc.get('pick_list'), 'material_request')
        frappe.db.set_value("Material Request", mr, 'per_ordered', 100)
        result = {"stock_entry": new_doc.name, "stock_entry_type": new_doc.stock_entry_type}
        return format_result(
            result=result,
            success=True,
            status_code=200,
            message='Received at Shop Stock Entry is created'
        )
    except Exception as e:
        return format_result(
            result=None,
            success=False,
            status_code=400,
            message=str(e),
            exception=str(e)
        )
