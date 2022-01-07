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
def orders():
    each_data_list = list(map(lambda x: frappe.get_doc('Sales Order', x),
                              [i['name'] for i in frappe.get_list('Sales Order')]))
    result = []

    for each_data in each_data_list:
        sales_invoice_num = frappe.get_list('Sales Invoice Item', fields=['parent'],
                                            filters=[['sales_order', '=', each_data.name]])

        temp_dict = {
            "id": str(each_data.idx),
            "location_id": None,
            "location_name": None,
            "order_number": each_data.name,
            "order_date": each_data.creation,
            "original_order_id": each_data.name,
            "type": each_data.order_type,
            "status": each_data.delivery_status,
            "payment_type": each_data.currency,
            "customer_id": each_data.customer,
            "customer_name": each_data.contact_display,
            "total_product": each_data.total_qty,
            "total_amount_excluding_tax": each_data.net_total,
            "discount_amount": each_data.discount_amount,
            "tax_amount": each_data.total_taxes_and_charges,
            "total_amount": each_data.grand_total,
            "products": [{
                "id": str(j.idx),
                "order_id": j.parent,
                "product_id": j.item_code,
                "product_name": j.item_name,
                "product_code": j.item_code,
                "price": j.rate,
                "barcode": fill_barcode(j.item_code),
                "quantity": j.qty,
                "source_warehouse": j.warehouse,
                "unit_id": j.item_group,
                "discount": j.discount_amount,
                "subtotal_amount": j.base_net_amount,
                "product_condition_id": j.docstatus,
                "notes": None,
                # "isActive": None
            } for j in each_data.items],
            "notes": ('Sales Invoice: ' if len(sales_invoice_num) > 0 else '' ) +
                                                                          '\n-'.join(
                                                                            [i['parent'] for i in sales_invoice_num])
        }
        result.append(temp_dict)

    return format_result(result=result, status_code=200, message='Data Found')


@frappe.whitelist()
def deliveryOrders():
    each_data_list = list(map(lambda x: frappe.get_doc('Delivery Note', x),
                              [i['name'] for i in frappe.get_list('Delivery Note')]))
    result = []
    for each_data in each_data_list:

        try:
            warehouse_data = frappe.get_doc('Warehouse', each_data.set_warehouse).warehouse_name or None
        except:
            warehouse_data = None

        temp_dict = {
            "id": str(each_data.idx),
            "order_id": each_data.name,
            "warehouse_id": each_data.set_warehouse,
            "warehouse_name": warehouse_data,
            "order_number": each_data.name,
            "do_number": each_data.name,
            "order_date": each_data.creation,
            "customer_name": each_data.customer_name,
            "status": each_data.status,
            "delivery_date": each_data.lr_date,
            "pretax_amount": str(each_data.net_total),
            "tax_amount": str(each_data.total_taxes_and_charges),
            "discount_amount": str(each_data.discount_amount),
            "extra_discount_amount": str(each_data.additional_discount_percentage * each_data.net_total),
            "total_amount": str(each_data.grand_total),
            "products": [{
                "id": str(i.idx),
                "delivery_order_id": i.against_sales_order,
                "product_id": i.item_code,
                "product_name": i.item_name,
                "product_code": i.item_code,
                "price": str(i.price_list_rate),
                "barcode": fill_barcode(i.item_code),
                "quantity": str(i.qty),
                "unit_id": i.item_group,
                "discount": str(i.discount_amount),
                "subtotal_amount": str(i.amount),
                "notes": None
            } for i in each_data.items]
        }
        result.append(temp_dict)

    return format_result(result=result, message='Data Found', status_code=200)


@frappe.whitelist()
def deliveryOrder():
    data = validate_data(frappe.request.data)

    specific_part = get_last_parameter(frappe.request.url, 'deliveryOrder')

    if specific_part:
        delivery_order = frappe.get_doc('Delivery Note', specific_part)
        delivery_order.modified_by = data['update_user_id']
    else:
        delivery_order = frappe.new_doc('Delivery Note')
        delivery_order.customer = data['create_user_id']
        delivery_order.set_warehouse = data['warehouse_id']
        for item in data['products']:
            delivery_order.append("items", {
                "item_code": item['delivery_order_product_id'],
                "qty": str(item['quantity']),
                # "warehouse": data['warehouse_product_lot_id']
            })

    # delivery_order.docstatus = data['status']
    # delivery_order.modified = data['update_time']
    # delivery_order.modified_by = data['update_user_id']
    delivery_order.insert()

    return {
        "success": True,
        "message": "Data created",
        "status_code": 200,
        "data": [
            {
                "do_number": delivery_order.name
            }
        ]
    }