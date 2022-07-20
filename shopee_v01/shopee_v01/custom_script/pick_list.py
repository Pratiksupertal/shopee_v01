import frappe
from frappe.model.document import Document

def validate(doc,method):
    sorted_location = []
    doc.sorted_locations = []
    sorted_location = sorted(doc.locations,key=lambda x:x.warehouse)
    for i in sorted_location:
        doc.append("sorted_locations", {
            "item_code":i.item_code,
            "item_name":i.item_name,
            "warehouse":i.warehouse,
            "qty":i.qty,
            "stock_qty":i.stock_qty
            })


@frappe.whitelist()
def get_pick_list_order(doc):
    return frappe.db.sql("""select distinct pli.parent as name,pick.customer as customer,pli.sales_order as sonumber,pli.warehouse,se.name as stock_entry,pli.item_code,convert(pli.qty,int) as qty,convert(pli.stock_qty,int) as stock_qty,convert(sed.qty,int) as picked_qty from `tabPick List Item` pli inner join `tabPick List` pick on pli.parent = pick.name inner join `tabStock Entry` se on pick.name = se.pick_list inner join `tabStock Entry Detail` sed on se.name = sed.parent where pli.item_code = sed.item_code and pli.sales_order is not null and pli.parent = %s and se.stock_entry_type=%s""",(doc.name,'Material Transfer'),as_dict=True)
