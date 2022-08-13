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
            "label": _("CATEGORY"),
            "fieldname": "item_category",
            "fieldtype": "Data",
            "options": "",
            "width": 160
        },
		{
            "label": _("BRAND"),
            "fieldname": "brand",
            "fieldtype": "Data",
            "options": "",
            "width": 80
        },
		{
            "label": _("SUPPLIER"),
            "fieldname": "supplier",
            "fieldtype": "Data",
            "options": "",
            "width": 80
        },
		{
            "label": _("ITEM CODE"),
            "fieldname": "item_code",
            "fieldtype": "Data",
            "options": "",
            "width": 80
        },
		{
            "label": _("ITEM NAME"),
            "fieldname": "item_name",
            "fieldtype": "Data",
            "options": "",
            "width": 50
        },

		{
            "label": _("Ada Variasi?"),
            "fieldname": "ada_varasi",
            "fieldtype": "Data",
            "options": "",
            "width": 80
        },
        {
            "label": _("VARIANT"),
            "fieldname": "Variasi",
            "fieldtype": "Data",
            "options": "",
            "width": 80
        },
		{
            "label": _("Aktif"),
            "fieldname": "Aktif",
            "fieldtype": "Data",
            "options": "",
            "width": 120
        },
        {
            "label": _("PURCHASE PRICE"),
            "fieldname": "purchase_price",
            "fieldtype": "Data",
            "options": "",
            "width": 120
        },
		{
            "label": _("PRODUCT PRICE"),
            "fieldname": "valuation_rate",
            "fieldtype": "Data",
            "options": "",
            "width": 80
        },
		{
            "label": _("WEIGHT"),
            "fieldname": "weight_per_unit",
            "fieldtype": "Data",
            "options": "",
            "width": 100
        },
		{
            "label": _("STOCK"),
            "fieldname": "stock",
            "fieldtype": "Data",
            "options": "",
            "width": 50
        },
		{
            "label": _("Description"),
            "fieldname": "description",
            "fieldtype": "Data",
            "options": "",
            "width": 50
        },        
		{
            "label": _("VARIANT CODE"),
            "fieldname": "item_bar_code",
            "fieldtype": "Data",
            "options": "",
            "width": 50
        },
		{
            "label": _("Gambar 1"),
            "fieldname": "Gambar_1",
            "fieldtype": "Data",
            "options": "",
            "width": 80
        },
		{
            "label": _("Gambar 2"),
            "fieldname": "Gambar_2",
            "fieldtype": "Data",
            "options": "",
            "width": 80
        },
		{
            "label": _("Gambar 3"),
            "fieldname": "Gambar_3",
            "fieldtype": "Data",
            "options": "",
            "width": 80
        },
		{
            "label": _("Gambar 4"),
            "fieldname": "Gambar_4",
            "fieldtype": "Data",
            "options": "",
            "width": 80
        },
		{
            "label": _("Gambar 5"),
            "fieldname": "Gambar_5",
            "fieldtype": "Data",
            "options": "",
            "width": 80
        },
        {
            "label": _("SPECIAL PRICE"),
            "fieldname": "spl_price",
            "fieldtype": "Data",
            "options": "",
            "width": 80
        },
		{
            "label": _("START DATE SPECIAL PRICE"),
            "fieldname": "start_date_spl_price",
            "fieldtype": "Data",
            "options": "",
            "width": 80
        },
		{
            "label": _("END DATE SPECIAL PRICE"),
            "fieldname": "end_date_spl_price",
            "fieldtype": "Data",
            "options": "",
            "width": 80
        }                
    ]

    return columns

def get_entries(filters):
	entries = frappe.db.sql("""
	select i.item_category,i.brand,"", i.item_code, i.item_name, "YES", invent_size_id, "YES", "", valuation_rate, weight_per_unit, "", "", item_bar_code, 
        "",	"",	"",	"",	"", "" , "", "" from tabItem as i LEFT JOIN `tabBrand` as b on i.brand = b.brand ;
	""")
	return entries

def get_conditions(filters):
	conditions = ""
	return conditions
