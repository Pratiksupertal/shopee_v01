from frappe.model.naming import make_autoname
import frappe
from frappe.model.document import Document
from frappe.utils import cstr, flt, getdate, new_line_sep, nowdate, add_days
from frappe.model.mapper import get_mapped_doc


@frappe.whitelist()
def make_stock_entry(source_name, target_doc=None):
    # def set_missing_values(target, source):
    #     target.date = source.posting_date

    print('---------------->> Stock entry called from Purchase Invoice -------')

    print(source_name, 'source--------------------<<')
    print(target_doc, 'target ---------------->>')

    doclist = get_mapped_doc("Purchase Invoice", source_name, {
        "Purchase Invoice": {
            "doctype": "Stock Entry",
        },
        "Purchase Invoice Item": {
            "doctype": "Stock Entry Detail",
        }
    }, target_doc)

    return doclist
