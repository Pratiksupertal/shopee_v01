import frappe

def get_po_dashboard_data(data):
    for x in data['transactions']:
        if (x['label'] == 'Sub-contracting'):
            x["items"].append("Pick List")
    return data