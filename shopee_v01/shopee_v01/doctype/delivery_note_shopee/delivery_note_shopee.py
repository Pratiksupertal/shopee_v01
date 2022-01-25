# -*- coding: utf-8 -*-
# Copyright (c) 2022, Pratik Mane and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json
from frappe.model.document import Document
from frappe.utils import flt, get_datetime, getdate, date_diff, cint, nowdate, get_link_to_form
# import frappe

class DeliveryNoteShopee(Document):
	pass

@frappe.whitelist()
def get_item_purchase_order(name):
    return frappe.db.sql("select item_code,item_name,qty,description,uom,stock_uom,rate,amount,conversion_factor from `tabPurchase Order Item` where parent = %s", (name), as_dict=True)

@frappe.whitelist()
def get_purchase_order(name):
    return frappe.db.get_all('Purchase Order', filters = {'name': name}, fields =['supplier','supplier_address','company','address_display','contact_person','total','net_total','base_total_taxes_and_charges','total_taxes_and_charges','grand_total','currency','conversion_rate','buying_price_list','price_list_currency','plc_conversion_rate','total_qty','total_net_weight','total','net_total','base_total','base_net_total','base_rounded_total','rounded_total','base_in_words','name'], as_list = False)

@frappe.whitelist()
def get_item_CMT(name):
    return frappe.db.sql("select bi.item_code,bi.item_name,woid.qty*bi.qty qty,bi.description,bi.uom,bi.stock_uom,bi.rate, woid.qty*bi.amount amount,bi.conversion_factor,bi.parent from `tabWork Order Item Details` woid left join `tabBOM Item` bi on bi.parent = woid.bom where woid.parent = %s", (name), as_dict=True)

@frappe.whitelist()
def get_item_CMT_Address_Supplier(name):
    return frappe.db.sql("select distinct mwo.supplier,po.supplier_address,po.company,po.address_display,po.contact_person,mwo.name from `tabMain Work Order` mwo left join `tabPurchase Order` po on mwo.supplier = po.supplier where mwo.name = %s", (name), as_dict=True)
