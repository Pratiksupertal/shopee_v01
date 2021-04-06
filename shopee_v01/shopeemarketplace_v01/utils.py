
import frappe
from frappe.model.document import Document
import time
import json
import hmac
import hashlib
import requests

def basic_auth():
    timest = int(time.time())
    host = "https://partner.uat.shopeemobile.com"
    path = "/api/v2/shop/auth_partner"
    redirect_url = "https://dev.mamba-erp.com"
    partner_id = 850230
    partner_key = bytes("1c7032256d22adf8432cfb27ef94939158de64a2eee9aba935889afdcf5e85df",'latin-1')
    base_string = "%s%s%s"%(partner_id,path,timest)
    sign = hmac.new(partner_key,base_string.encode('utf-8'),hashlib.sha256).hexdigest()
    url = host + path + "?partner_id=%s&timestamp=%s&sign=%s&redirect=%s"%(partner_id,timest,sign,redirect_url)
    return url

def get_token(code, partner_id, partner_key,shop_id):
	timest = int(time.time())
	body = {"code":code, "shop_id":shop_id,"partner_id":partner_id}
	host = "https://partner.uat.shopeemobile.com"
	path = "/api/v2/auth/token/get"
	partner_key = bytes(partner_key,'latin-1')
	base_string = "%s%s%s"%(partner_id,path,timest)
	sign = hmac.new(partner_key,base_string.encode('utf-8'),hashlib.sha256).hexdigest()
	url = host + path + "?partner_id=%s&timestamp=%s&sign=%s"%(partner_id,timest,sign)
	headers = {"Content-Type":"application/json"}
	resp = requests.post(url, json=body, headers=headers)
	return json.loads(resp.content)
	#access_token = ret.get("access_token")
	#new_refresh_token = ret.get("refresh_token")
	#return access_token,new_refresh_token
def refresh_token(shop_id,partner_id,partner_key,refresh_token):
    timest = int(time.time())
    host = "https://partner.uat.shopeemobile.com"
    path = "/api/v2/auth/access_token/get"
    body = {"shop_id":shop_id, "refresh_token":refresh_token,"partner_id":partner_id}
    base_string = "%s%s%s"%(partner_id,path,timest)
    sign = hmac.new(str.encode(partner_key),base_string.encode('utf-8'),hashlib.sha256).hexdigest()
    url  = host + path + "?partner_id=%s&timestamp=%s&sign=%s"%(partner_id,timest,sign)
    headers = {"Content-Type":"application/json"}
    resp = requests.post(url,json=body, headers=headers )
    ret = json.loads(resp.content)
    access_token = ret.get("access_token")
    new_refresh_token = ret.get("refresh_token")
    return access_token, new_refresh_token
