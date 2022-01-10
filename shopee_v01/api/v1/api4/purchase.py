import frappe
import datetime as dt

from shopee_v01.api.v1.helpers import *


@frappe.whitelist()
def purchases():
    result = []

    each_data_list = list(map(lambda x: frappe.get_doc('Purchase Order', x),
                              [i['name'] for i in frappe.get_list('Purchase Order',filters={'docstatus':1})]))

    for each_data in each_data_list:
        temp_dict = {
            "id": each_data.name,
            "po_number": each_data.name,
            "po_date": each_data.creation,
            "supplier_id": each_data.supplier,
            "supplier_name": each_data.supplier_name,
            "total_amount": str(each_data.grand_total),
            "total_product": str(each_data.total_qty),
            "products": [{
                "id": str(i.idx),
                "purchase_id": i.parent,
                "product_id": i.item_code,
                "product_name": i.item_name,
                "product_code": i.item_code,
                "barcode": fill_barcode(i.item_code),
                "price": str(int(i.amount) if i.amount else ''),
                "warehouse":i.warehouse,
                "quantity": str(int(i.qty) if i.qty else ''),
                "unit_id": str(i.idx),
                "discount": str(int(i.discount_amount) if i.discount_amount else ''),
                "subtotal_amount": str(int(i.net_amount) if i.net_amount else '')
            } for i in each_data.items],
            "type": each_data.po_type,
            "rejected_by": each_data.modified_by if each_data.docstatus == 2 else None,
            "cancelled_by": each_data.modified_by if each_data.status == 2 else None,
            "supplier_is_taxable": None,
            "total_amount_excluding_tax": str(each_data.base_total),
            "tax_amount": str(each_data.total_taxes_and_charges),
            "delivery_contact_person": None,
            "supplier_email": None,
            "supplier_work_phone": None,
            "supplier_cell_phone": None,
            "expiration_date": each_data.schedule_date,
            "payment_due_date": None if each_data.payment_schedule is None or len(each_data.payment_schedule) == 0 else
            each_data.payment_schedule[
                0].due_date,
            "notes": each_data.remarks,
            "rejection_notes": each_data.remarks if each_data.docstatus == 2 else None,
            "cancellation_notes": each_data.remarks if each_data.status == 2 else None,
            "delivery_address": each_data.address_display
        }
        result.append(temp_dict)

    return format_result(message='Data found', result=result, status_code=200)



@frappe.whitelist()
def purchaseReceive():
    try:
        data = validate_data(frappe.request.data)
        today = dt.datetime.today()
        po_name = data['products'][0]['purchase_id']
        validate_po = frappe.db.get_list('Purchase Order',
        filters = {'name':po_name,'docstatus':1,'status':['not in',['Closed', 'On Hold']],'per_received':['<', 99.99] },
        fields = ['name']
        )
        if len(validate_po) < 1:
            msg = "Purchase Receipt is not created for Purchase order {0}".format(po_name)
            return format_result(success="False",status_code=500, message = msg, result={
            })
        else:
            new_doc = frappe.new_doc('Purchase Receipt')
            new_doc.posting_date = today.strftime("%Y-%m-%d")
            supplier = frappe.db.get_value("Purchase Order",{"name":po_name},"supplier")
            new_doc.supplier = supplier
            new_doc.supplier_travel_document_number = data['supplier_do_number']
            new_doc.set_warehouse = data['warehouse_id']
            for item in data['products']:
                new_doc.append("items", {
                    "item_code": item['purchase_product_id'],
                    "qty": item['quantity'],
                    "purchase_order":item['purchase_id']
                })
            new_doc.insert()
            new_doc.submit()
            return format_result(status_code=200, message='Purchase Receipt Created', result={
                "id": str(new_doc.name),
                "receive_number": new_doc.name,
                "supplier_do_number": new_doc.supplier_travel_document_number,
                "receive_date": new_doc.posting_date,
                "supplier_id": new_doc.supplier
            })
    except Exception as e:
        return format_result(success="False",status_code=500, message = "Purchase Receipt API Fail", result=e)