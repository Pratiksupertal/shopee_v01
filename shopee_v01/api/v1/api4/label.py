import frappe

from shopee_v01.api.v1.helpers import *


@frappe.whitelist()
def get_label():
    data = validate_data(frappe.request.data)
    fields = ['name', 'customer_name', 'company', 'address_display',
              'company_address_display', 'total_net_weight', 'payment_terms_template',
              'grand_total', 'owner']
    filters = {"name": data['id']}
    result = frappe.get_list('Sales Invoice', fields=fields, filters=filters)

    filters = {
        'parent': data['id']
    }

    fields = ["item_name", "qty"]
    check = frappe.get_list(
        'Sales Invoice Item',
        fields=fields,
        filters=filters)
    info_retrieved = result[0]

    pdf_binary = convert_to_pdf(
        template=str(info_retrieved['payment_terms_template']), invoice=str(info_retrieved['name']),
        weight=str(info_retrieved['total_net_weight']), shipping=str(info_retrieved['grand_total']),
        to_entity=str(info_retrieved['customer_name']), from_entity=str(info_retrieved['company']),
        address=str(info_retrieved['address_display']), address_company=str(info_retrieved['company_address_display']),
        product_list1=check, delivery_type='Regular \nShipping', b_code=str('123456789012'),
        owner=str(info_retrieved['owner'])
    )

    return {
        "pdf_bin": str(pdf_binary)
    }