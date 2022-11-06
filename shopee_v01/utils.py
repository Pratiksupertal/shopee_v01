import logging
import frappe
from frappe.utils import now
import sys
import os
import csv

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
            summary_doc = frappe.new_doc("Finished 901 Item Summary")
            summary_doc.item_code = i.item_code
            summary_doc.item_name = frappe.get_value("Item",i.item_code, "item_name")
            summary_doc.available_qty = balance_qty
            summary_doc.modified_time = now()
            summary_doc.save()
            comment = f'Data migration done for the Item : {i.item_code} with qty {balance_qty} '
            print(comment)
            if counter >= 1000:
                break

#function to Add warehouse list to the 901 warehouse summary child warehouse table
@frappe.whitelist()
def add_warehouse(f_path=None):
    doc = frappe.get_single("Finished901ItemQtySummary")
    path = os.path.join(os.path.dirname(__file__), f_path)
    file = open(path, "r")
    csvreader = csv.reader(file)
    header = []
    rows = []
    header = next(csvreader)
    for row in csvreader:
        rows.append(row)
        doc.append("child_warehouse", {"warehouse": row[0]})
    file.close()
    doc.save()

#function to Remove warehouse list to the 901 warehouse summary child warehouse table
@frappe.whitelist()
def remove_warehouse(f_path=None):
    doc = frappe.get_single("Finished901ItemQtySummary")
    path = os.path.join(os.path.dirname(__file__), f_path)
    file = open(path, "r")
    csvreader = csv.reader(file)
    header = []
    rows = []
    header = next(csvreader)
    for row in csvreader:
        try:
            print("warehouse : ",row[0])
            warehouse_doc = frappe.get_doc("Child Warehouse",{"warehouse":row[0]})
            warehouse_doc.delete()
            print(f'Warehouse removed {row[0]}')
        except Exception as e:
            print(f'Exception Occured for {row[0]}')
            continue
    file.close()
    doc.save()
