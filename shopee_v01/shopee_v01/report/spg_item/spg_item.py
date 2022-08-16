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
            "label": _("SrNo."),
            "fieldname": "srno",
            "fieldtype": "Data",
            "options": "",
            "width": 60
        },
		{
            "label": _("PRODUCT_NAME"),
            "fieldname": "item_name",
            "fieldtype": "Data",
            "options": "",
            "width": 160
        },
		{
            "label": _("PRODUCT_CODE"),
            "fieldname": "product_code",
            "fieldtype": "Data",
            "options": "",
            "width": 80
        },
		{
            "label": _("PRODUCT_IMAGE"),
            "fieldname": "image",
            "fieldtype": "Data",
            "options": "",
            "width": 80
        },
		{
            "label": _("UNIT"),
            "fieldname": "stock_uom",
            "fieldtype": "Data",
            "options": "",
            "width": 80
        },
		{
            "label": _("BRAND_CODE"),
            "fieldname": "brand_code",
            "fieldtype": "Data",
            "options": "",
            "width": 50
        },
		{
            "label": _("BRAND_NAME"),
            "fieldname": "brand",
            "fieldtype": "Data",
            "options": "",
            "width": 80
        },
		{
            "label": _("DIVISION_CODE"),
            "fieldname": "division_group",
            "fieldtype": "Data",
            "options": "",
            "width": 80
        },
		{
            "label": _("DIVISION"),
            "fieldname": "division_group_description",
            "fieldtype": "Data",
            "options": "",
            "width": 120
        },
		{
            "label": _("PRODUCT_PRICE"),
            "fieldname": "valuation_rate",
            "fieldtype": "Data",
            "options": "",
            "width": 80
        },
		{
            "label": _("VARIANT_CODE"),
            "fieldname": "item_bar_code",
            "fieldtype": "Data",
            "options": "",
            "width": 100
        },
		{
            "label": _("VARIANT_GROUP_SIZE"),
            "fieldname": "size_group",
            "fieldtype": "Data",
            "options": "",
            "width": 50
        },
		{
            "label": _("VARIANT"),
            "fieldname": "invent_size_id",
            "fieldtype": "Data",
            "options": "",
            "width": 50
        },
		{
            "label": _("VARIANT_PRICE"),
            "fieldname": "valuation_rate",
            "fieldtype": "Data",
            "options": "",
            "width": 80
        },
		{
            "label": _("PRODUCT_STATUS"),
            "fieldname": "status_code",
            "fieldtype": "Data",
            "options": "",
            "width": 80
        },
    ]

    return columns

def get_entries(filters):
	entries = frappe.db.sql("""
	select ROW_NUMBER()  OVER (ORDER BY  item_name) As SrNo ,item_name,product_code,image,stock_uom,b.brand_code,i.brand,division_group,division_group_description, valuation_rate,item_bar_code, size_group, invent_size_id, valuation_rate,status_code from tabItem as i LEFT JOIN `tabBrand` as b on i.brand = b.brand ;
	""")
	return entries

def get_conditions(filters):
	conditions = ""
	return conditions
