import frappe
from urllib.parse import urlparse, parse_qs

from shopee_v01.api.v1.helpers import *
from shopee_v01.api.v1.validations import *


@frappe.whitelist()
def filter_picklist():
    try:
        url = frappe.request.url
        docstatus = parse_qs(urlparse(url).query).get('docstatus')
        purpose = parse_qs(urlparse(url).query).get('purpose')
        if docstatus: docstatus = docstatus[0]
        if purpose: purpose = purpose[0]
        filtered_picklist = frappe.db.get_list('Pick List',
                filters={
                    'docstatus': docstatus,
                    'purpose': purpose
                },
                fields=['name', 'customer']
        )
        result = []
        for pl in filtered_picklist:
            items = frappe.db.get_list('Pick List Item',
                    filters={
                        'parent': pl.get("name"),
                        'parentfield': 'locations'
                    },
                    fields=['qty', 'picked_qty', 'sales_order']
                )
            sum_qty = sum([it.get('qty') if it.get('qty') not in ['', None] else 0 for it in items])
            sum_picked_qty = sum([it.get('picked_qty') if it.get('picked_qty') not in ['', None] else 0 for it in items])
            
            if len(items) < 1: continue
            
            result.append({
                "name": pl.get("name"),
                "customer": pl.get("customer"),
                "sales_order": items[0].get('sales_order'),
                "total_product": len(items),
                "total_qty": sum_qty,
                "total_qty_received": sum_qty-sum_picked_qty
            })
        return format_result(result=result, success=True, status_code=200, message='Data Found')
    except Exception as e:
        return format_result(result=None, success=False, status_code=400, message=str(e))


@frappe.whitelist()
def picklist_details_for_warehouse_app():
    try:
        pick_list = get_last_parameter(frappe.request.url, 'picklist_details_for_warehouse_app')
        
        print(pick_list, '\n\n\n')
        
        picklist_details = frappe.db.get_value('Pick List', pick_list, [
            'name', 'docstatus', 'purpose', 'customer', 'creation', 'modified'
        ], as_dict=1)
        
        if not picklist_details:
            raise Exception('Invalid pick list name')
        
        items = frappe.db.get_list('Pick List Item',
            filters={
                'parent': pick_list,
                'parentfield': 'locations'
            },
            fields=['item_code', 'item_name', 'warehouse', 'qty', 'picked_qty', 'uom', 'sales_order']
        )
        
        picklist_details.sales_order = items[0].sales_order
        
        so_details = frappe.db.get_value('Sales Order', picklist_details.sales_order, [
            'creation', 'delivery_date'
        ], as_dict=1)
        
        picklist_details.so_date = so_details.creation
        picklist_details.delivery_date = so_details.delivery_date
        
        for it in items:
            it.picked_qty = it.qty - it.picked_qty
            
        picklist_details.items = items        
        
        return format_result(result={
            'pick_list': picklist_details
        }, success=True, message='Data Created', status_code=200)
    except Exception as e:
        return format_result(result=None, success=False, status_code=400, message=str(e), exception=str(e))


@frappe.whitelist()
def save_picklist_and_create_stockentry():
    try:
        data = validate_data(frappe.request.data)
        data_validation_for_save_picklist_and_create_stockentry(data=data)
        print(data)
        
        """GET Pick List Item (sorted_locations) Details"""
        item = picklist_item(
            data=data
        )
        
        """Validate picked quantity, we are decreasing the value actually"""
        new_picked_qty = int(item.get('picked_qty')) - int(data.get('picked_qty'))
        if new_picked_qty < 0.0:
            raise Exception(f"Picked quantity can not be more than total quantity.")
        
        """Create stock entry"""
        stock_entry = create_new_stock_entry_for_single_item(
            data=data,
            item=item
        )
        
        """Update picklist item picked qty"""
        frappe.db.set_value('Pick List Item', item.get('name'), {
            'picked_qty': new_picked_qty
        })
        
        return format_result(result={'stock entry': stock_entry.name}, success=True, message='success', status_code=200)
    except Exception as e:
        return format_result(success=False, status_code=400, message=str(e), exception=str(e))
    

@frappe.whitelist()
def submit_picklist_and_create_stockentry():
    try:
        data = validate_data(frappe.request.data)
        data_validation_for_submit_picklist_and_create_stockentry(data=data)
        
        base = get_base_url(url=frappe.request.url)
        url = base + '/api/resource/Pick%20List/'+ data.get('pick_list')
        
        """GET Pick List Details"""
        
        picklist_details = picklist_details_for_submit_picklist_and_create_stockentry(url=url)
        
        """___ALL GOOD TO GO___"""
        
        """Create new stick entry, save and submit"""
        
        new_doc_stock_entry = create_and_submit_stock_entry_submit_picklist_and_create_stockentry(
            data=data,
            picklist_details=picklist_details
        )
        
        """Correct picked qty"""
        
        for item in picklist_details.get('locations'):
            picked_qty = item['qty'] - item['picked_qty']
            frappe.db.set_value('Pick List Item', item['name'], 'picked_qty', picked_qty)
        
        """Submit Pick List"""
        
        frappe.db.set_value('Pick List', picklist_details['name'], 'docstatus', 1)
        
        return format_result(result={'stock entry': new_doc_stock_entry.name,
                                 'items': new_doc_stock_entry.items
                                 }, success=True, message='Data Created', status_code=200)
    except Exception as e:
        return format_result(result=None, success=False, status_code=400, message=str(e), exception=str(e))


@frappe.whitelist()
def filter_stock_entry_for_warehouse_app():
    try:
        url = frappe.request.url
        stock_entry_type = parse_qs(urlparse(url).query).get('stock_entry_type')
        order_purpose = parse_qs(urlparse(url).query).get('order_purpose')
        if stock_entry_type is not None: stock_entry_type = stock_entry_type[0]
        if order_purpose is not None: order_purpose = order_purpose[0]

        """filter by
        1. stock entry type as per request
        2. not fully transferred (status in Draft or Goods In Transit)
        3. picklist be there
        """
        filtered_se = frappe.db.get_list('Stock Entry',
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
            if order_purpose == frappe.db.get_value('Pick List', se.get('pick_list'), 'purpose')
        ]

        """find and add other necessary fields"""
        for se in filtered_se:
            se['customer_name'] = frappe.db.get_value('Pick List', se.get('pick_list'), 'customer')
            items_pl = frappe.db.get_list('Pick List Item',
                    filters={
                        'parent': se.get("pick_list"),
                        'parentfield': 'locations'
                    },
                    fields=['sales_order', 'qty']
                )
            print(se, items_pl)
            if len(items_pl) < 1: continue
            se['sales_order'] = items_pl[0].get('sales_order')
            
            items_se = frappe.db.get_list('Stock Entry Detail',
                    filters={
                        'parent': se.get("name")
                    },
                    fields=['qty']
                )
            
            se['total_product'] = len(items_se)
            se['total qty'] = sum([ise.get('qty') for ise in items_se])

        return format_result(result=filtered_se, success=True, status_code=200, message='Data Found')
    except Exception as e:
        return format_result(result=None, success=False, status_code=400, message=str(e))


@frappe.whitelist()
def create_receive_at_warehouse():
    try:
        data = validate_data(frappe.request.data)
        data_validation_for_create_receive_at_warehouse(data=data)
        
        base = get_base_url(url=frappe.request.url)
        
        send_to_ste = base + '/api/method/erpnext.stock.doctype.stock_entry.stock_entry.make_stock_in_entry'
        stock_entry = requests.post(send_to_ste.replace("'", '"'), headers={
            "Authorization": frappe.request.headers["Authorization"]
        },data={"source_name": data.get("outgoing_stock_entry")})
        
        stock_entry_data = stock_entry.json().get("message")
        stock_entry_data["to_warehouse"] = data.get("t_warehouse")
        stock_entry_data["stock_entry_type"] = data.get("stock_entry_type")
        stock_entry_data["docstatus"] = 1
        
        receive_ste_url = base + '/api/resource/Stock%20Entry'
        receive_ste_url_api_response = requests.post(receive_ste_url.replace("'", '"'), headers={
            "Authorization": frappe.request.headers["Authorization"]
        },data=json.dumps(stock_entry_data))
        
        result = {
            "name": receive_ste_url_api_response.json().get("data").get("name")
        }
        return format_result(result=result, success=True, status_code=200, message='Received Warehouse Stock Entry is created')
    except Exception as e:
        return format_result(result=None, success=False, status_code=400, message=str(e), exception=str(e))


