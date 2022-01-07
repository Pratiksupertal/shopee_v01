import datetime
import json
import time
import frappe
import requests
from PIL import Image, ImageDraw, ImageFont
import base64
import os
import barcode
import traceback
from urllib.parse import urlparse, unquote, parse_qs
import datetime as dt
from frappe.utils import today
from erpnext.stock.doctype.pick_list.pick_list import create_stock_entry, create_delivery_note
from erpnext.stock.doctype.material_request.material_request import create_pick_list
from erpnext.selling.doctype.sales_order.sales_order import create_pick_list as create_pick_list_from_sales_order
from erpnext.stock.doctype.pick_list.pick_list import get_available_item_locations, get_items_with_location_and_quantity
from frappe import _

from shopee_v01.api.v1.helpers import *


@frappe.whitelist()
def stockOpname():
    data = validate_data(frappe.request.data)
    new_doc = frappe.new_doc('Stock Entry')
    new_doc.start_time = data['start_datetime']
    new_doc.end_time = data['end_datetime']
    new_doc._comments = data['notes']
    new_doc.modified_by = data['create_user_id']

    new_doc.purpose = 'Material Receipt'
    new_doc.set_stock_entry_type()
    for item in data['products']:
        new_doc.append("items", {
            "item_code": item['product_code'],
            "qty": item['quantity'],
            "t_warehouse": data['warehouse_stockopname_id']
        })

    new_doc.insert()

    return {
        "success": True,
        "message": "Data created",
        "status_code": 200,
    }


@frappe.whitelist()
def stockOpnames():
    fields = [
        'idx',
        'warehouse',
        'creation',
        '_comments',
        'posting_date',
        'posting_time',
        'modified_by'
    ]

    product_list = frappe.get_list('Stock Ledger Entry', fields=fields)

    result = []

    for i in product_list:
        temp_dict = {
            "id": str(i['idx']),
            "warehouse_id": i['warehouse'],
            "warehouse_area_id": None,
            "start_datetime": dt.datetime.combine(i['posting_date'],
                                                  (dt.datetime.min + i['posting_time']).time()
                                                  ),
            "end_datetime": None,
            "notes": i['_comments'],
            "create_user_id": i['modified_by'],
            "create_time": i['creation']
        }

        result.append(temp_dict)

    return format_result(result=result, status_code=200, message='Data Found')


@frappe.whitelist()
def stockTransfer():
    data = validate_data(frappe.request.data)
    new_doc = frappe.new_doc('Stock Entry')
    new_doc.purpose = 'Material Transfer'
    new_doc.company = data['company']
    new_doc._comments = data['notes']
    for item in data['items']:
        new_doc.append("items", {
            "item_code": item['item_code'],
            "t_warehouse": data['t_warehouse'],
            "s_warehouse": data['s_warehouse'],
            "qty": str(item['qty'])
        })
    new_doc.set_stock_entry_type()
    new_doc.insert()
    return {
        "success": True,
        "status_code": 200,
        "message": 'Data created',
        "data": {
            "transfer_number": new_doc.name
        },
    }


@frappe.whitelist()
def stockTransfers():
    each_data_list = list(map(lambda x: frappe.get_doc('Stock Entry', x),
                              [i['name'] for i in frappe.get_list('Stock Entry',
                                                                  filters={'purpose': 'Material Transfer'}
                                                                  )
                               ]))
    result = []

    for each_data in each_data_list:
        temp_dict = {
            "id": str(each_data.idx),
            "transfer_number": each_data.name,
            "transfer_date": each_data.posting_date,
            "status": str(each_data.docstatus),
            "from_warehouse_id": each_data.from_warehouse,
            "from_warehouse_area_id": None,
            "to_warehouse_id": each_data.to_warehouse,
            "to_warehouse_area_id": None,
            "start_datetime": None,
            "end_datetime": None,
            "notes": each_data.purpose,
            "create_user_id": each_data.modified_by,
            "create_time": each_data.creation,
            "products": [
                {
                    "id": str(i.idx),
                    "stock_transfer_id": i.name,
                    "product_id": i.item_code,
                    "product_name": i.item_name,
                    "product_code": i.item_name,
                    "barcode": fill_barcode(i.item_code),
                    "quantity": str(i.qty),
                    "warehouse_area_storage_id": None
                } for i in each_data.items
            ],
            "update_user_id": each_data.modified_by,
            "product_list": [i.item_name for i in each_data.items]
        }
        result.append(temp_dict)

    return format_result(result=result, message='Data Found', status_code=200)


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