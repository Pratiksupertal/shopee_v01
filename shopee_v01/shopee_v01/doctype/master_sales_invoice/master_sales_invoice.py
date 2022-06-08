"""
# flake8: noqa: files that contain this line are skipped from flake8 warnings
# pylint: skip-file: files that contain this line are skipped from pylint warnings
"""

# flake8: noqa
# pylint: skip-file

from __future__ import unicode_literals

import frappe, json
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, nowdate, getdate

from six import string_types


class MasterSalesInvoice(Document):
    pass


@frappe.whitelist()
def get_outstanding_reference_documents(args):
	if isinstance(args, string_types):
		args = json.loads(args)
  
	condition = ""
  
	# Add customer condition
	if args.get("customer"):
		condition += " and customer='%s'" % args.get("customer")

	# Add source app name condition
	if args.get("source_app_name"):
		condition += " and source_app_name='%s'" % args.get("source_app_name")
	# Add store condition
	if args.get("store"):
		condition += " and store='%s'" % args.get("store")

	# Add department category condition
	if args.get("department_category"):
		count = 0
		list_args = args.get("department_category").split(",")
		condition += f" and (department_category="
		for category in list_args:
			category = category.strip()
			if count == 0:
				condition += f"'{category}'"
				count += 1
			else:
				condition += f" OR department_category='{category}'"
		condition += ")"

	date_fields_dict = {
		'posting_date': ['from_posting_date', 'to_posting_date'],
		'due_date': ['from_due_date', 'to_due_date']
	}

	for fieldname, date_fields in date_fields_dict.items():
		if args.get(date_fields[0]) and args.get(date_fields[1]):
			condition += " and {0} between '{1}' and '{2}'".format(fieldname,
				args.get(date_fields[0]), args.get(date_fields[1]))

	if args.get("company"):
		condition += " and company = {0}".format(frappe.db.escape(args.get("company")))

	invoice_list = frappe.db.sql("""
		select
			name AS voucher_no,
   			'Sales Invoice' AS voucher_type,
      		posting_date,
        	due_date,
			rounded_total AS invoice_amount,
			outstanding_amount,
			currency,
			total_qty
		from
			`tabSales Invoice`
		where
			docstatus = 1
			{condition}
		order by posting_date, name""".format(
			condition=condition or ""
		), {}, as_dict=True)

	if not invoice_list:
		frappe.msgprint(("No outstanding invoices found.").format())
  
	outstanding_invoices = []
	pe_map = frappe._dict()
	precision = frappe.get_precision("Sales Invoice", "outstanding_amount") or 2
	for d in invoice_list:
		sales_invoice_doc = frappe.get_doc("Sales Invoice", d.voucher_no)
		if sales_invoice_doc.get('status') not in ['Unpaid', 'Overdue', 'Unpaid and Discounted', 'Overdue and Discounted', 'Return']:
			continue
		outstanding_amount = flt(d.outstanding_amount, precision)
		payment_amount = flt(d.invoice_amount - outstanding_amount, precision)
		if outstanding_amount > 0.5 / (10**precision) and d.voucher_no:
			outstanding_invoices.append(
				frappe._dict({
					'voucher_no': d.voucher_no,
					'voucher_type': d.voucher_type,
					'posting_date': d.posting_date,
					'invoice_amount': flt(d.invoice_amount),
					'payment_amount': flt(payment_amount),
					'outstanding_amount': flt(outstanding_amount),
					'due_date': d.due_date,
					'currency': d.currency,
					'qty': d.total_qty
				})
			)

	outstanding_invoices = sorted(outstanding_invoices, key=lambda k: k['due_date'] or getdate(nowdate()))
	return outstanding_invoices
