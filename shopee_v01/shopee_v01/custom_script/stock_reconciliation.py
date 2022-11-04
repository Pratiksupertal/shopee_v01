import frappe
from frappe import _
from frappe.utils import now

#Creating master to store updated item qty in Finished 901 Item Summary List
#On stock Reconciliation update event function is called
def update_warehouse_finished901_stock_rec(doc,method):
    # sr = "MAT-RECO-2022-00006"
    # doc = frappe.get_doc("Stock Reconciliation",sr)
    warehouse_tuple = []
    warehouse_list = frappe.get_doc('Finished901ItemQtySummary')
    for item in doc.items:
        if frappe.db.exists('Finished 901 Item Summary', item.item_code):
            warehouse_tuple = [i.warehouse for i in warehouse_list.child_warehouse if (i.warehouse == item.warehouse)]
            warehouse_tuple = tuple(warehouse_tuple)
            if len(warehouse_tuple) > 0:
                if warehouse_tuple[0] == item.warehouse:
                    qty = item.qty
                if qty != 0:
                    item_availability = frappe.get_doc("Finished 901 Item Summary",item.item_code)
                    balance_qty = recalculating_901(item)
                    pre_qty = item_availability.available_qty
                    item_availability.available_qty = pre_qty - item.current_qty + item.qty
                    item_availability.modified_time = now()
                    comment = "Stock Reconciliation ' {} ' is updated and qty before update is {}".format(frappe.bold(_(doc.name)),pre_qty)
                    item_availability.save()
                    item_availability.add_comment("Comment", comment)
                    print("\n\nfinished_901_summary is updated")

        else:
            balance_qty = 0
            balance_qty = recalculating_901(item)
            summary_doc = frappe.new_doc("Finished 901 Item Summary")
            summary_doc.item_code = item.item_code
            summary_doc.item_name =item.item_name
            summary_doc.available_qty = balance_qty
            summary_doc.modified_time = now()
            comment = "Stock Reconciliation ' {} ' updated item quantity.".format(frappe.bold(_(doc.name)))
            summary_doc.save()
            summary_doc.add_comment("Comment", comment)
    pass

#
def recalculating_901(item_obj):
    balance_qty = 0
    warehouse_list = frappe.get_doc('Finished901ItemQtySummary')
    warehouse_tuple = [i.warehouse for i in warehouse_list.child_warehouse if (i.warehouse == item_obj.warehouse)]
    warehouse_tuple = tuple(warehouse_tuple)
    for i in warehouse_list.child_warehouse:
        temp = frappe.db.sql("""select qty_after_transaction from `tabStock Ledger Entry`
        where item_code=%s and warehouse = %s and is_cancelled='No'
        order by posting_date desc, posting_time desc, creation desc
        limit 1""", (item_obj.item_code, i.warehouse))
        temp = int(temp[0][0]) if len(temp)>0 else 0
        balance_qty = balance_qty + temp
    return balance_qty

# Finished901ItemQtySummary Single doctype was updating with reconciled item quantity
#Note : Not using anymore
def update_finished_901_item_qty_summary_stock_rec(doc,method):
    """
    Update Finished901ItemQtySummary doctype when Stock Reconciliation document is submitted.
    """
    warehouse_tuple = []
    # doc = frappe.get_doc("Stock Reconciliation","MAT-RECO-2022-00001")
    warehouse_list = frappe.get_doc('Finished901ItemQtySummary')
    for item in doc.items:
        sql = "select item_code,available_items,warehouse from `tabTotal Item count in Warehouse` where item_code = '{0}'".format(item.item_code)
        item_availability = frappe.db.sql(sql)
        warehouse_tuple = [i.warehouse for i in warehouse_list.child_warehouse if (i.warehouse == item.warehouse)]
        warehouse_tuple = tuple(warehouse_tuple)
        if len(item_availability) > 0:
            if len(warehouse_tuple) > 0:
                if warehouse_tuple[0] == item.warehouse:
                    qty = item.qty
                if qty != 0:
                    sql = "update `tabTotal Item count in Warehouse` set available_items = {0},warehouse = '{1}',modified_time = now()  where item_code = '{2}';".format(qty,warehouse_tuple[0],item.item_code)
                    query = frappe.db.sql(sql,debug=True)
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
            sql = "insert into `tabTotal Item count in Warehouse` (name,idx,creation,modified,modified_time,modified_by,owner,parent,parentfield,parenttype,item_code,item_name,available_items,warehouse) values ('{0}',{4},now(),now(),now(),'{3}','{3}','Finished901ItemQtySummary','total_item_count_in_warehouse','Finished901ItemQtySummary','{0}','{5}',{1},'{2}')".format(item.item_code,balance_qty,item.warehouse,frappe.session.user,idx,item.item_name)
            query = frappe.db.sql(sql)
