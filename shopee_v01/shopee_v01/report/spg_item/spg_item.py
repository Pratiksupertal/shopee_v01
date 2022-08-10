# Copyright (c) 2013, Pratik Mane and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
from frappe import msgprint, _
import frappe

def execute(filters=None):
	columns, data = [], []
	columns = get_columns(filters)
	data = get_entries(filters)
	print("===columns======",columns)
	print("\n==data=====",data)
	return columns, data

def get_columns(filters):

    columns =[
        {
            "label": _("Item Name"),
            "fieldname": "item_name",
            "fieldtype": "Data",
            "options": "",
            "width": 160
        },
		{
            "label": _("Product Code"),
            "fieldname": "item_code",
            "fieldtype": "Data",
            "options": "",
            "width": 80
        },
		{
            "label": _("Product Image"),
            "fieldname": "upload",
            "fieldtype": "Data",
            "options": "",
            "width": 80
        },
		{
            "label": _("UoM"),
            "fieldname": "stock_uom",
            "fieldtype": "Data",
            "options": "",
            "width": 80
        },
		{
            "label": _("Brand Code"),
            "fieldname": "brand",
            "fieldtype": "Data",
            "options": "",
            "width": 50
        },
		{
            "label": _("Brand"),
            "fieldname": "brand",
            "fieldtype": "Data",
            "options": "",
            "width": 80
        },
		{
            "label": _("Division Group"),
            "fieldname": "division_group",
            "fieldtype": "Data",
            "options": "",
            "width": 80
        },
		{
            "label": _("Division Group Description"),
            "fieldname": "division_group_description",
            "fieldtype": "Data",
            "options": "",
            "width": 120
        },
		{
            "label": _("Selling Rate"),
            "fieldname": "valuation_rate",
            "fieldtype": "Data",
            "options": "",
            "width": 80
        },
		{
            "label": _("Barcode"),
            "fieldname": "item_bar_code",
            "fieldtype": "Data",
            "options": "",
            "width": 100
        },
		{
            "label": _("Size Group"),
            "fieldname": "size_group",
            "fieldtype": "Data",
            "options": "",
            "width": 50
        },
		{
            "label": _("Attribute Size"),
            "fieldname": "invent_size_id",
            "fieldtype": "Data",
            "options": "",
            "width": 50
        },
		{
            "label": _("Selling Rate"),
            "fieldname": "valuation_rate",
            "fieldtype": "Data",
            "options": "",
            "width": 80
        },
		{
            "label": _("Status Code"),
            "fieldname": "status_code",
            "fieldtype": "Data",
            "options": "",
            "width": 80
        },
    ]

    return columns

def get_entries(filters):
	conditions = get_conditions(filters)
	print("====== conditions ======")
	entries = frappe.db.sql("""
	select item_name,item_code,'',stock_uom,'',brand,division_group,division_group_description, valuation_rate,item_bar_code, size_group, invent_size_id, valuation_rate,status_code from tabItem
	""")
	return entries

def get_conditions(filters):
	print("====filters \n=======")
	conditions = ""
	if filters.get("item_name"):
		conditions += " and b.item_name = '{0}'".format(filters.get("item_name"))
	if filters.get("city"):
		conditions += " and ad.city = '{0}'".format(filters.get("city"))
	if filters.get("state"):
		conditions += " and ad.state = '{0}'".format(filters.get("state"))
	return conditions
