# Copyright (c) 2013, Pratik Mane and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
from frappe import msgprint, _
import frappe

def execute(filters=None):
	columns, data = [], []
	columns = get_columns(filters)
	data = get_entries(filters)
	return columns, data

def get_columns(filters):

    columns =[
        {
            "label": _("Product Name"),
            "fieldname": "item_name",
            "fieldtype": "Data",
            "options": "",
            "width": 160
        },
		{
            "label": _("Product Code"),
            "fieldname": "product_code",
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
            "label": _("Unit"),
            "fieldname": "stock_uom",
            "fieldtype": "Data",
            "options": "",
            "width": 80
        },
		{
            "label": _("Brand Code"),
            "fieldname": "brand_code",
            "fieldtype": "Data",
            "options": "",
            "width": 50
        },
		{
            "label": _("Brand Name"),
            "fieldname": "brand",
            "fieldtype": "Data",
            "options": "",
            "width": 80
        },
		{
            "label": _("Division Code"),
            "fieldname": "division_group",
            "fieldtype": "Data",
            "options": "",
            "width": 80
        },
		{
            "label": _("Division"),
            "fieldname": "division_group_description",
            "fieldtype": "Data",
            "options": "",
            "width": 120
        },
		{
            "label": _("Product Price"),
            "fieldname": "valuation_rate",
            "fieldtype": "Data",
            "options": "",
            "width": 80
        },
		{
            "label": _("Varient Code"),
            "fieldname": "item_bar_code",
            "fieldtype": "Data",
            "options": "",
            "width": 100
        },
		{
            "label": _("Varient Size Group"),
            "fieldname": "size_group",
            "fieldtype": "Data",
            "options": "",
            "width": 50
        },
		{
            "label": _("Varient"),
            "fieldname": "invent_size_id",
            "fieldtype": "Data",
            "options": "",
            "width": 50
        },
		{
            "label": _("Varient Price"),
            "fieldname": "valuation_rate",
            "fieldtype": "Data",
            "options": "",
            "width": 80
        },
		{
            "label": _("Product Status"),
            "fieldname": "status_code",
            "fieldtype": "Data",
            "options": "",
            "width": 80
        },
    ]

    return columns

def get_entries(filters):
	entries = frappe.db.sql("""
	select item_name,product_code,upload,stock_uom,b.brand_code,i.brand,division_group,division_group_description, valuation_rate,item_bar_code, size_group, invent_size_id, valuation_rate,status_code from tabItem as i LEFT JOIN `tabBrand` as b on i.brand = b.brand ;
	""")
	return entries

def get_conditions(filters):
	conditions = ""
	return conditions
