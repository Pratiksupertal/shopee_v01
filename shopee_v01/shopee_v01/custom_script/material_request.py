from frappe.model.naming import make_autoname
import frappe
from frappe.model.document import Document
from frappe.utils import cstr, flt, getdate, new_line_sep, nowdate, add_days
from frappe.model.mapper import get_mapped_doc


frappe.whitelist()
def get_material_request_sort(doc):
    return frappe.db.sql("""select item_code,item_group,qty,uom from `tabMaterial Request Item` where parent = %s order by item_code""",(doc.name),as_dict=True)
