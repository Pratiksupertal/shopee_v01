import frappe

from shopee_v01.api.v1.helpers import *


@frappe.whitelist()
def stockTransfer():
    data = validate_data(frappe.request.data)
    new_doc = frappe.new_doc('Stock Entry')
    new_doc.purpose = 'Material Transfer'
    new_doc.company = data['company']
    new_doc._comments = data['notes']
    for item in data['items']:
        new_doc.append("items", {
            "item_code": item['item_code'],
            "t_warehouse": data['t_warehouse'],
            "s_warehouse": data['s_warehouse'],
            "qty": str(item['qty'])
        })
    new_doc.set_stock_entry_type()
    new_doc.insert()
    return {
        "success": True,
        "status_code": 200,
        "message": 'Data created',
        "data": {
            "transfer_number": new_doc.name
        },
    }


@frappe.whitelist()
def stockTransfers():
    each_data_list = list(map(lambda x: frappe.get_doc('Stock Entry', x),
                              [i['name'] for i in frappe.get_list('Stock Entry',
                                                                  filters={'purpose': 'Material Transfer'}
                                                                  )
                               ]))
    result = []

    for each_data in each_data_list:
        temp_dict = {
            "id": str(each_data.idx),
            "transfer_number": each_data.name,
            "transfer_date": each_data.posting_date,
            "status": str(each_data.docstatus),
            "from_warehouse_id": each_data.from_warehouse,
            "from_warehouse_area_id": None,
            "to_warehouse_id": each_data.to_warehouse,
            "to_warehouse_area_id": None,
            "start_datetime": None,
            "end_datetime": None,
            "notes": each_data.purpose,
            "create_user_id": each_data.modified_by,
            "create_time": each_data.creation,
            "products": [
                {
                    "id": str(i.idx),
                    "stock_transfer_id": i.name,
                    "product_id": i.item_code,
                    "product_name": i.item_name,
                    "product_code": i.item_name,
                    "barcode": fill_barcode(i.item_code),
                    "quantity": str(i.qty),
                    "warehouse_area_storage_id": None
                } for i in each_data.items
            ],
            "update_user_id": each_data.modified_by,
            "product_list": [i.item_name for i in each_data.items]
        }
        result.append(temp_dict)

    return format_result(result=result, message='Data Found', status_code=200)
