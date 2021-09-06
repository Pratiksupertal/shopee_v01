
import frappe
from frappe.model.document import Document
# import time
# import json
# import hmac
# import hashlib
# import requests
from shopee_v01.shopeemarketplace_v01.utils import refresh_token

def refresh_acess_token():
    shop_id = 220288436
    partner_id = 850230
    partner_key = "1c7032256d22adf8432cfb27ef94939158de64a2eee9aba935889afdcf5e85df"
    # partner_key = bytes("1c7032256d22adf8432cfb27ef94939158de64a2eee9aba935889afdcf5e85df",'latin-1')
    doc = frappe.get_doc("ShopeeAuthorization",{"key":"refresh_token"})
    # refresh_token = "fd45d36cf7a65a3e0f432e1b2a35c1ff"
    old_refresh_token = doc.value
    at,refresh_token_new = refresh_token(shop_id, partner_id, partner_key, old_refresh_token)
    if refresh_token_new:
        doc.value = refresh_token_new
        doc.save()
        frappe.db.commit()

def access_token(shop_id,partner_id,partner_key,refresh_token):
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
    frappe.client.set_value("ShopeeAuthentication01", "ShopeeAuthentication01", "value", new_refresh_token)
    return access_token, new_refresh_token

def update_finished_901_item_qty_summary():
#    frappe.log('')
    warehouse_list = frappe.get_doc('Finished901ItemQtySummary')
    item_dict = {i.item_code : i.available_items for i in warehouse_list.total_item_count_in_warehouse}
    warehouse_tuple = [i.warehouse for i in warehouse_list.child_warehouse]
    for item in item_dict.keys():
        balance_qty = 0
        for i in range(len(warehouse_tuple)):
            temp = frappe.db.sql("""select qty_after_transaction from `tabStock Ledger Entry`
            where item_code=%s and warehouse = %s and is_cancelled='No'
            order by posting_date desc, posting_time desc, creation desc
            limit 1""", (item, warehouse_tuple[i]))
            temp = int(temp[0][0]) if len(temp)>0 else 0
            balance_qty = balance_qty + temp
        if int(balance_qty) != int(item_dict[item]):
            sql = "update `tabTotal Item count in Warehouse` set available_items ={0} ,modified_time = now()  where item_code = '{1}';".format(
                balance_qty, item)
            query = frappe.db.sql(sql,debug=True)
    pass
