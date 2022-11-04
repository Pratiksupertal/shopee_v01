import frappe
from frappe.model.document import Document


def validate(doc,method):
    # short_list = sorted(doc.items,key=lambda x:x.item_code)
    # for i in short_list:
    #     doc.append("consolidated_items", {
    #         "item_code":i.item_code,
    #         "item_name":i.item_name,
    #         "qty":i.qty,
    #         })
    item_dict = {}
    doc.consolidated_items = []
    for item in doc.items:
        if item.item_code not in item_dict:
            item_dict[item.item_code] = {
                                         "description": item.description,
                                         "qty": int(item.qty),
                                         "uom": item.uom,
                                         "image": item.image,
                                         "discount_amount": int(item.discount_amount),
                                         "rate": item.rate,
                                         "amount": int(item.amount),
                                         "cost_center": item.cost_center,
                                         "income_account": item.income_account,
                                         "base_amount": item.base_amount,
                                         "base_rate": item.base_rate,
                                         "conversion_factor": item.conversion_factor,
                                         "item_name": item.item_name
                                         }
        else:
            item_dict[item.item_code] = {
                                         "description": item.description,
                                         "qty": item.qty + item_dict[item.item_code]["qty"],
                                         "uom": item.uom,
                                         "image": item.image,
                                         "discount_amount": item.discount_amount + item_dict[item.item_code]["discount_amount"],
                                         "rate": item.rate,
                                         "amount": item.amount + item_dict[item.item_code]["amount"],
                                         "cost_center": item.cost_center,
                                         "income_account": item.income_account,
                                         "base_amount": item.base_amount,
                                         "base_rate": item.base_rate,
                                         "conversion_factor": item.conversion_factor,
                                         "item_name": item.item_name
                                    }

    for k, v in item_dict.items():
        doc.append("consolidated_items", {
            "item_code": k,
            "description": v['description'],
            "qty": v['qty'],
             "uom": v['uom'],
             "image": v['image'],
             "discount_amount": v['discount_amount'],
             "rate": v['rate'],
             "amount": v['amount'],
             "cost_center": v['cost_center'],
             "income_account": v['income_account'],
             "base_amount": v['base_amount'],
             "base_rate": v['base_rate'],
             "conversion_factor": v['conversion_factor'],
             "item_name": v['item_name']
        })

    print(item_dict)
    print(doc.consolidated_items)


@frappe.whitelist()
def get_summary_sales_invoice(doc):
    return frappe.db.sql("""select a.parent,a.item_name,a.description,a.uom,sum(a.qty) quantity,a.rate,a.discount_amount,sum(a.amount) amount from
                            (select sii.parent,sii.item_name,sii.description,sii.uom,sii.qty,sii.discount_amount,sii.amount,soi.basic_rate rate  from `tabSales Invoice Item` sii
                            left join `tabSales Order Item` soi on sii.sales_order = soi.parent and sii.item_code = soi.item_code where sii.parent = %s) a group by a.parent,a.item_name,a.rate""",(doc.name),as_dict=True)

def make_customer_gl_entry(doc, method):
    gle_list = frappe.db.get_list('GL Entry', filters={'voucher_no': doc.name}, fields=['name'])
    for gle in gle_list:
        gle_doc = frappe.get_doc("GL Entry", gle)
        frappe.db.set_value('GL Entry', gle, 'department_category', doc.department_category, update_modified=False)
