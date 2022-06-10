import frappe, json
group_warehouse, node_warehouse = [], []

def update_finished901itemsummary(doc,method):
    warehouse_tuple = []
    warehouse_list = frappe.get_doc('Finished901ItemQtySummary')
    for item in doc.items:
        sql = "select item_code,available_items,warehouse from `tabTotal Item count in Warehouse` where item_code = '{0}'".format(item.item_code)
        item_availability = frappe.db.sql(sql)
        warehouse_tuple = [i.warehouse for i in warehouse_list.child_warehouse if (i.warehouse == item.t_warehouse or i.warehouse == item.s_warehouse)]
        warehouse_tuple = tuple(warehouse_tuple)
        if len(item_availability)>0 :
            # qty = item.qty if warehouse_tuple[0] == item.t_warehouse
            if len(warehouse_tuple)>0:
                if warehouse_tuple[0] == item.t_warehouse:
                    qty =  item.qty
                if warehouse_tuple[0] == item.s_warehouse:
                    qty = -item.qty
                if item.t_warehouse in warehouse_tuple and item.s_warehouse in warehouse_tuple:
                    qty = 0
                if qty != 0:
                    sql = "update `tabTotal Item count in Warehouse` set available_items = available_items + {0},warehouse = '{1}',modified_time = now()  where item_code = '{2}';".format(qty,warehouse_tuple[0],item.item_code)
                    query = frappe.db.sql(sql)
        else:
            balance_qty = 0
            for i in warehouse_list.child_warehouse:
                temp = frappe.db.sql("""select qty_after_transaction from `tabStock Ledger Entry`
                where item_code=%s and warehouse = %s and is_cancelled='No'
                order by posting_date desc, posting_time desc, creation desc
                limit 1""", (item.item_code, i.warehouse))
                temp = int(temp[0][0]) if len(temp)>0 else 0
                balance_qty = balance_qty + temp
            idx = frappe.db.sql("select idx from `tabTotal Item count in Warehouse` order by idx desc limit 1;")
            idx = idx[0][0]+1 if idx else 1
            sql = "insert into `tabTotal Item count in Warehouse` (name,idx,creation,modified,modified_time,modified_by,owner,parent,parentfield,parenttype,item_code,item_name,available_items,warehouse) values ('{0}',{4},now(),now(),now(),'{3}','{3}','Finished901ItemQtySummary','total_item_count_in_warehouse','Finished901ItemQtySummary','{0}','{5}',{1},'{2}')".format(item.item_code,balance_qty,item.t_warehouse,frappe.session.user,idx,item.item_name)
            query = frappe.db.sql(sql)


def submit(doc, method):
    update_stock_to_halosis(doc=doc)

def update_stock_to_halosis(doc):
    import requests
    # Comparing the parent warehouse
    config = frappe.get_single("Online Warehouse Configuration")
    frappe.msgprint('Updating to Halosis. Please, check error log for more update.')
    for item in doc.items:
        request_body = {
            "item_code": item.item_code,
            "brand": frappe.db.get_value("Item", item.item_code, "brand"),
            "qty": int(item.qty),
            "type": "in" if (parent_warehouse(item.t_warehouse)) else ("out" if (parent_warehouse(item.s_warehouse)) else "")
        }
        print(request_body)
        if (request_body["type"] in ["in", "out"]):
            try:
                url = config.base_url + 'auth'
                data = {
                    "username": config.username,
                    "password": config.get_password('password')
                }
                auth_res = requests.post(url.replace("'", '"'), data=data)
                auth_res_json = json.loads(auth_res.text)
                print(auth_res_json)
            except Exception:
                raise
                frappe.log_error(title="Update stock API Login part", message=frappe.get_traceback())
                frappe.msgprint(f'Problem in halosis update. {frappe.get_traceback()}')
            auth_token = "Bearer " + auth_res_json["data"]["token"]
            try:
                url = config.base_url + 'update-stock'
                response = requests.post(
                    url.replace("'", '"'),
                    data=request_body,
                    headers={"Authorization": auth_token},)
                print(response.text)
                frappe.log_error(title="Update stock API update stock part", message=response.text)
                frappe.msgprint(f'{response.text}')
            except Exception:
                raise
                frappe.log_error(title="Update stock API Data part", message=frappe.get_traceback())
                frappe.msgprint(f'Problem in halosis update. {frappe.get_traceback()}')

def parent_warehouse(warehouse):
    config = frappe.get_single("Online Warehouse Configuration")
    warehouse_list = [i.warehouse for i in config.online_warehouse]
    a = frappe.db.get_value("Warehouse", warehouse, "parent")
    if not a:
        return False
    elif a in warehouse_list:
        # parent matched
        return True
    else:
        parent_warehouse(a)
        return True
