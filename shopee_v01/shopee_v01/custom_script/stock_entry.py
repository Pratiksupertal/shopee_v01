import frappe
from frappe.model.document import Document
group_warehouse, node_warehouse = [],[]

def update_item_qty(doc,method):
    warehouse_tuple = []
    warehouse_list = frappe.get_doc('Item Counter')
    for item in doc.items:
        warehouse_tuple = [i.warehouse for i in warehouse_list.child_warehouse]
        warehouse_tuple = tuple(warehouse_tuple)
        balance_qty = 0
        for i in warehouse_list.child_warehouse:
            temp = frappe.db.sql("""select qty_after_transaction from `tabStock Ledger Entry`
            where item_code=%s and warehouse = %s and is_cancelled='No'
            order by posting_date desc, posting_time desc, creation desc
            limit 1""", (item.item_code, i.warehouse),debug=True)
            temp = int(temp[0][0]) if len(temp)>0 else 0
            balance_qty = balance_qty + temp
        try:
            sql = "select item_code,available_items,warehouse from `tabTotal Item count in Warehouse` where item_code = '{0}'".format(item.item_code)
            query = frappe.db.sql(sql,debug=True)
            if len(query)>0:
                sql = "update `tabTotal Item count in Warehouse` set item_code = '{0}' ,available_items = {1},warehouse='{2}' where item_code = '{0}' ".format(item.item_code,balance_qty+item.qty,item.t_warehouse)
                query = frappe.db.sql(sql,debug=True)
            else:
                idx = frappe.db.sql("select idx from `tabTotal Item count in Warehouse` order by idx desc limit 1;",debug=True)
                idx = idx[0][0]+1
                sql = "insert into `tabTotal Item count in Warehouse` (name,idx,creation,modified,modified_by,owner,parent,parentfield,parenttype,item_code,available_items,warehouse) values ('{0}',{4},now(),now(),'{3}','{3}','Item Counter','total_item_count_in_warehouse','Item Counter','{0}',{1},'{2}')".format(item.item_code,balance_qty,item.t_warehouse,frappe.session.user,idx)
                query = frappe.db.sql(sql,debug=True)

        except:
            print("xxxxxxxxxxxxxxxx Update query failed xxxxxxxxxxxxxxxxxxxxxxxxx")
        # if query:
        #     print("------- final output -----------")
        #     print(query)
        # else:
        #     print("---- item is not available -----")

    pass
# Recursively update warehouse in specified Parent warehouse
def fetch_warehouse_list(doc,method):
    tems_details = frappe.db.get_single_value('Item Counter', 'total_item_count_in_warehouse')
    parent = frappe.db.get_single_value('Item Counter','reference_warehouse')
    # group warehouse list
    sql1 = "select name from tabWarehouse where parent_warehouse = '{0}' and is_group = 1".format(parent)
    first_child = frappe.db.sql(sql1)
    node_warehouse =  test1(first_child)
    child_warehouse = [i for i in node_warehouse if len(i)>0]
    # child_warehouse = [i[0] for i in child_warehouse]
    return child_warehouse

def test1(first_child):
    warehouse_output = {}
    for i in first_child:
        second = query(i[0])
        group_warehouse.append(second["first_child"])
        node_warehouse.append(second["first_child_node"])
        if second["first_child"] :
            for i in second["first_child"]:
                if len(i)>0:
                    warehouse_output = query(i[0])
                # warehouse_output = query(i[0]) if len(i)>1 else
                    group_warehouse.append(warehouse_output["first_child"])
                    node_warehouse.append(warehouse_output["first_child_node"])
                    if len(warehouse_output["first_child"])>0:
                        test1(warehouse_output["first_child"])
                    else:
                        print("===Final output====================================================")
                        print(group_warehouse)
                        print(node_warehouse)
                        print()
    return node_warehouse
def query(first_child):
    print("----- inside query -------",first_child)
    temp_dict = {}
    first_child = "".join(first_child)
    print("".join(first_child))
    sql2 = "select name from tabWarehouse where parent_warehouse = '{0}' and is_group = 0".format(first_child)
    temp_dict["first_child_node"] = frappe.db.sql(sql2,debug=True)

    # for i in first_child:
    sql1 = "select name from tabWarehouse where parent_warehouse = '{0}' and is_group = 1".format(first_child)
    temp_dict["first_child"] = frappe.db.sql(sql1,debug=True)
    return temp_dict
    # second = query(i[0])
    #     print(i)
        # print("-------- LOOP -------")
        # print(first_child)
