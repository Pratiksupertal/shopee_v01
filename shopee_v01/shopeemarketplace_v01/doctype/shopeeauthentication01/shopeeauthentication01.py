# -*- coding: utf-8 -*-
# Copyright (c) 2021, Pratik Mane and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
from frappe.model.document import Document
import frappe
from shopee_v01.shopeemarketplace_v01.utils import basic_auth, get_token
class ShopeeAuthentication01(Document):
	pass

@frappe.whitelist()
def get_code():
	url = basic_auth()
	return url

def new_key(key,value):
	print("----creating new key----",key,value)
	# auth = frappe.get_doc(doctype='ShopeeAuthorization', key=key)
	doc = frappe.get_doc("ShopeeAuthorization",{"key":key})
	print(doc.value)
	if doc.value:
		doc.value = value
		doc.save()
		frappe.db.commit()
		print("key value is available, updating current value")
	else:
		print("key value is not available. Creating new one")
		doc = frappe.new_doc('ShopeeAuthorization')
		doc.title = key
		doc.key = key
		doc.value = value
		doc.insert()
		frappe.db.commit()
	pass

@frappe.whitelist()
def generate_keyvalues(code):
	partner_id = 850230
	partner_key = "1c7032256d22adf8432cfb27ef94939158de64a2eee9aba935889afdcf5e85df"
	shop_id = 220288436
	# print("----generate keyvalues with code ",code)
	response= get_token(code, partner_id, partner_key,shop_id)
	print("---------------------------------------------")
	access_token = response.get("access_token")
	new_refresh_token = response.get("refresh_token")
	if access_token:
		new_key("access_token",access_token) #if access_token else pass
	if new_refresh_token:
		new_key("refresh_token",new_refresh_token) #if new_refresh_token else pass
	print("Access Token : ",access_token)
	print("Refresh Token : ",new_refresh_token)
