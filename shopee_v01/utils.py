import logging
import frappe
from frappe.utils import now

def schedular_log(msg):
    logger  = logging.getLogger()
    # logging.basicConfig(filename='example.log', encoding='UTF-8', level=logging.INFO)
    logging.basicConfig(handlers=[logging.FileHandler(filename="../logs/schedular_log.txt",
                                                 encoding='utf-8', mode='a+')],
                    format="%(asctime)s %(name)s:%(levelname)s:%(message)s",
                    datefmt="%F %A %T",
                    level=logging.INFO)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    logging.info(msg)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)

def data_migration_901_warehouse_summary():
    counter = 0
    warehouse_list = frappe.get_doc('Finished901ItemQtySummary')
    item_list = frappe.get_list("Total Item count in Warehouse","item_code")
    for i in item_list:
        print(i.item_code)
        if frappe.db.exists('Finished 901 Item Summary', i.item_code):
            continue
        else:
            counter += 1
            balance_qty = 0
            warehouse_tuple = [i.warehouse for i in warehouse_list.child_warehouse]
            warehouse_tuple = tuple(warehouse_tuple)
            for j in warehouse_list.child_warehouse:
                temp = frappe.db.sql("""select qty_after_transaction from `tabStock Ledger Entry`
                where item_code=%s and warehouse = %s and is_cancelled='No'
                order by posting_date desc, posting_time desc, creation desc
                limit 1""", (i.item_code, j.warehouse))
                temp = int(temp[0][0]) if len(temp)>0 else 0
                balance_qty = balance_qty + temp
                print(f'\nbalance_qty : {balance_qty} for item {i.item_code}\n')
            summary_doc = frappe.new_doc("Finished 901 Item Summary")
            summary_doc.item_code = i.item_code
            summary_doc.item_name = frappe.get_value("Item",i.item_code, "item_name")
            summary_doc.available_qty = balance_qty
            summary_doc.modified_time = now()
            summary_doc.save()
            comment = f'Data migration done for the Item : {i.item_code} with qty {balance_qty} '
            frappe.log_error(title="Data migration for 901 item summary Task", message=comment)
            print(comment)
            if counter >= 1000:
                break
