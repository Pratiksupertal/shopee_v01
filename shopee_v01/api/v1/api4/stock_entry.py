import frappe
from frappe.utils import today
from erpnext.stock.doctype.pick_list.pick_list import create_stock_entry, create_delivery_note
from erpnext.stock.doctype.material_request.material_request import create_pick_list
from erpnext.stock.doctype.pick_list.pick_list import get_available_item_locations, get_items_with_location_and_quantity

from shopee_v01.api.v1.helpers import *


def set_item_locations(pick_list, save=False):
    items = pick_list.aggregate_item_qty()
    pick_list.item_location_map = frappe._dict()

    from_warehouses = None
    if pick_list.parent_warehouse:
        from_warehouses = frappe.db.get_descendants('Warehouse', pick_list.parent_warehouse)

    # reset
    pick_list.delete_key('locations')
    for item_doc in items:
        item_code = item_doc.item_code

        pick_list.item_location_map.setdefault(item_code,
                                          get_available_item_locations(item_code, from_warehouses,
                                                                       pick_list.item_count_map.get(item_code),
                                                                       pick_list.company))

        locations = get_items_with_location_and_quantity(item_doc, pick_list.item_location_map)

        item_doc.idx = None
        item_doc.name = None

        for row in locations:
            row.update({
                'picked_qty': row.stock_qty
            })

            location = item_doc.as_dict()
            location.update(row)
            pick_list.append('locations', location)

    return pick_list


@frappe.whitelist()
def material_stock_entry():
    '''
    Processing Material Request
    '''
    data = validate_data(frappe.request.data)
    new_doc_material_request = frappe.new_doc('Material Request')
    new_doc_material_request.material_request_type = "Material Transfer"

    if 'get_items_doc' in data:
        for num in data['get_items_doc_no']:
            source_doc = frappe.get_doc(data['get_items_doc'], num)
            for item in source_doc.items:
                new_doc_material_request.append("items", {
                    "item_code": item.item_code,
                    "qty": item.qty,
                    # "uom": item["uom"],
                    # "conversion_factor": item["conversion_factor"],
                    "schedule_date": data['schedule_date'] or today(),
                    "warehouse": source_doc.set_warehouse,
                })
    else:
        for item in data["items"]:
            new_doc_material_request.append("items", {
                "item_code": item['item_code'],
                "qty": item["qty"],
                "uom": item["uom"],
                "conversion_factor": item["conversion_factor"],
                "schedule_date": item['schedule_date'] or today(),
                "warehouse": item['target_warehouse'],
            })
    new_doc_material_request.save()
    new_doc_material_request.submit()

    '''
    Generating Pick List from Material Request
    '''
    new_doc_pick_list = create_pick_list(new_doc_material_request.name)
    new_doc_pick_list.parent_warehouse = data['parent_warehouse']
    new_doc_pick_list = set_item_locations(new_doc_pick_list)
    new_doc_pick_list.save()
    new_doc_pick_list.submit()

    '''
    Generating Stock Entry from Pick List
    '''
    stock_entry_dict = create_stock_entry(new_doc_pick_list.as_json())
    new_doc_stock_entry = frappe.new_doc('Stock Entry')
    new_doc_stock_entry.company = stock_entry_dict['company']
    new_doc_stock_entry.purpose = stock_entry_dict['purpose']
    for item in stock_entry_dict['items']:
        new_doc_stock_entry.append("items", {
            "item_code": item['item_code'],
            "t_warehouse": item['t_warehouse'],
            "s_warehouse": item['s_warehouse'],
            "qty": item['qty'],
            "basic_rate": item['basic_rate'],
            "cost_center": item['cost_center']
        })
    new_doc_stock_entry.stock_entry_type = stock_entry_dict["stock_entry_type"]

    new_doc_stock_entry.save()
    # new_doc_stock_entry.submit()

    return format_result(result={'stock entry': new_doc_stock_entry.name,
                                 'items': new_doc_stock_entry.items
                                 }, message='Data Created', status_code=200)
    

@frappe.whitelist()
def stock_entry():
    data = validate_data(frappe.request.data)
    new_doc = frappe.new_doc('Stock Entry')
    new_doc.start_time = data['start_datetime']
    new_doc.end_time = data['end_datetime']
    new_doc._comments = data['notes']

    new_doc.purpose = data['purpose']
    new_doc.set_stock_entry_type()

    if data['purpose'] not in ['Material Receipt']:
        for doc in data['get_item_doc_id']:
            item_list = frappe.get_doc(data['get_items_from'], doc)
            for item in item_list.items:
                new_doc.append("items", {
                    "item_code": item.item_code,
                    "qty": item.qty,
                    "t_warehouse": data['target_warehouse_stockopname_id'],
                    "s_warehouse": data['source_warehouse_stockopname_id']
                })
    else:
        for doc in data['get_item_doc_id']:
            item_list = frappe.get_doc(data['get_items_from'], doc)
            for item in item_list.items:
                new_doc.append("items", {
                    "item_code": item.item_code,
                    "qty": item.qty,
                    "t_warehouse": data['target_warehouse_stockopname_id'],
                })

    new_doc.insert()

    return format_result(result=new_doc.name, status_code=200, message='Data Created')


@frappe.whitelist()
def submit_stock_entry():
    data = validate_data(frappe.request.data)
    stock_entry_doc = frappe.get_doc('Stock Entry', data['id'])
    if 'add_items' in data:
        for item in data['add_items']:
            stock_entry_doc.append("items", {
                "item_code": item['item_id'],
                "qty": item['qty'],
                "t_warehouse": item['target_warehouse_id'],
                "s_warehouse": item['source_warehouse_id'],
            })

    if 'edit_items' in data:
        for item in data['edit_items']:
            for se_item in stock_entry_doc.items:
                if se_item.item_code == item['item_id']:
                    se_item.qty = item['qty']
                    se_item.t_warehouse = item['target_warehouse_id']
                    se_item.s_warehouse = item['source_warehouse_id']

    stock_entry_doc.save()
    stock_entry_doc.submit()

    return format_result(result={'stock entry': stock_entry_doc.name,
                                 'items': stock_entry_doc.items
                                 }, message='Data Created', status_code=200)


@frappe.whitelist()
def stock_entry_send_to_warehouse():
    try:
        data = validate_data(frappe.request.data)
        new_doc = frappe.new_doc('Stock Entry')
        new_doc.purpose = 'Send To Warehouse'
        new_doc.company = data['company']
        new_doc._comments = data['notes']
        for item in data['items']:
            new_doc.append("items", {
                "item_code": item['item_code'],
                "t_warehouse": 'Virtual Transit - ISS',
                "s_warehouse": item['s_warehouse'],
                "qty": str(item['qty'])
            })
        new_doc.set_stock_entry_type()
        new_doc.insert()
        new_doc.submit()
        return {
            "success": True,
            "status_code": 200,
            "message": 'Data created',
            "data": {
                "transfer_number": new_doc.name,
                "items": new_doc.items
            },
        }
    except Exception as e:
        return format_result(success = "False",message='Stock Entry is not created', status_code=500)

@frappe.whitelist()
def get_stock_entry_send_to_warehouse():
    each_data_list = list(map(lambda x: frappe.get_doc('Stock Entry', x),
                              [i['name'] for i in frappe.get_list('Stock Entry',
                                                                  filters={'purpose': 'Send To Warehouse',
                                                                           'docstatus': 1}
                                                                  )
                               ]))

    return format_result(result=each_data_list, message='Data Found', status_code=200)


@frappe.whitelist()
def stock_entry_receive_at_warehouse():
    try:
        data = validate_data(frappe.request.data)
        new_doc = frappe.new_doc('Stock Entry')
        new_doc.purpose = 'Receive at Warehouse'
        new_doc.company = data['company']
        new_doc.outgoing_stock_entry = data['send_to_warehouse_id']
        new_doc._comments = data['notes']
        for item in data['items']:
            new_doc.append("items", {
                "item_code": item['item_code'],
                "t_warehouse": item['t_warehouse'],
                "s_warehouse": item['s_warehouse'],
                "qty": int(item['qty'])
            })
        new_doc.set_stock_entry_type()
        new_doc.insert()
        new_doc.submit()
        return {
            "success": True,
            "status_code": 200,
            "message": 'Data created',
            "data": {
                "transfer_number": new_doc.name,
                "items": new_doc.items
            },
        }
    except Exception as e:
        return format_result(success="False",message='Stock Entry is not created', status_code=500)
