# -*- coding: utf-8 -*-
# Copyright (c) 2022, Pratik Mane and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json
from frappe.model.document import Document
from frappe.utils import flt, get_datetime, getdate, date_diff, cint, nowdate, get_link_to_form
# import frappe

@frappe.whitelist()
def get_sales_order(doc):
    return frappe.db.sql("select distinct a.sales_order from (select parent delivery_note,against_sales_order sales_order from `tabDelivery Note Item` where against_sales_order is not null and parent =%s union select dn.name delivery_note,pli.sales_order sales_order from `tabPick List Item` pli inner join `tabPick List` pl on pli.parent = pl.name inner join `tabDelivery Note` dn on dn.pick_list = pl.name where pli.sales_order is not null and dn.name = %s) a",(doc.name,doc.name),as_dict=True)

def get_delivery_note(doc):
    return frappe.db.sql("select item_code,item_name,qty,weight_per_unit,uom from `tabDelivery Note Item` where parent = %s order by item_code ",(doc.name),as_dict=True)
