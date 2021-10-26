import frappe
from frappe.model.mapper import get_mapped_doc
from frappe.model.document import Document
group_warehouse, node_warehouse = [],[]

def update_finished901itemsummary(doc,method):
    warehouse_tuple = []
    warehouse_list = frappe.get_doc('Finished901ItemQtySummary')
    for item in doc.items:
        sql = "select item_code,available_items,warehouse from `tabTotal Item count in Warehouse` where item_code = '{0}'".format(item.item_code)
        item_availability = frappe.db.sql(sql,debug=True)
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
                    query = frappe.db.sql(sql,debug=True)
        else:
            balance_qty = 0
            for i in warehouse_list.child_warehouse:
                temp = frappe.db.sql("""select qty_after_transaction from `tabStock Ledger Entry`
                where item_code=%s and warehouse = %s and is_cancelled='No'
                order by posting_date desc, posting_time desc, creation desc
                limit 1""", (item.item_code, i.warehouse),debug=True)
                temp = int(temp[0][0]) if len(temp)>0 else 0
                balance_qty = balance_qty + temp
            idx = frappe.db.sql("select idx from `tabTotal Item count in Warehouse` order by idx desc limit 1;",debug=True)
            idx = idx[0][0]+1 if idx else 1
            sql = "insert into `tabTotal Item count in Warehouse` (name,idx,creation,modified,modified_time,modified_by,owner,parent,parentfield,parenttype,item_code,item_name,available_items,warehouse) values ('{0}',{4},now(),now(),now(),'{3}','{3}','Finished901ItemQtySummary','total_item_count_in_warehouse','Finished901ItemQtySummary','{0}','{5}',{1},'{2}')".format(item.item_code,balance_qty,item.t_warehouse,frappe.session.user,idx,item.item_name)
            query = frappe.db.sql(sql,debug=True)


@frappe.whitelist()
def make_stock_entry(source_name, target_doc=None):
    doclist = get_mapped_doc("Stock Entry", source_name, {
        "Stock Entry": {
            "doctype": "Stock Entry",},
        "Stock Entry Detail": {
            "doctype": "Stock Entry Detail",
        }
    }, target_doc)

    return doclist
