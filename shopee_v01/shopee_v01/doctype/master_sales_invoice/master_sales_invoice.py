"""
# flake8: noqa: files that contain this line are skipped from flake8 warnings
# pylint: skip-file: files that contain this line are skipped from pylint warnings
"""

# flake8: noqa
# pylint: skip-file

from __future__ import unicode_literals
from frappe.model.document import Document

import frappe, json
from frappe.utils import nowdate, getdate
from erpnext.accounts.utils import get_outstanding_invoices, get_account_currency
from erpnext.setup.utils import get_exchange_rate
from erpnext.controllers.accounts_controller import AccountsController, get_supplier_block_status

from six import string_types
from erpnext.accounts.doctype.payment_entry.payment_entry import get_negative_outstanding_invoices, get_orders_to_be_billed


class MasterSalesInvoice(Document):
	pass


@frappe.whitelist()
def get_outstanding_reference_documents(args):
	print('\n\n\n\n\n\n\nget_outstanding_reference_documents\n\n\n\n\n\n\n')
	if isinstance(args, string_types):
		args = json.loads(args)

	if args.get('party_type') == 'Member':
		return

	# confirm that Supplier is not blocked
	if args.get('party_type') == 'Supplier':
		supplier_status = get_supplier_block_status(args['party'])
		if supplier_status['on_hold']:
			if supplier_status['hold_type'] == 'All':
				return []
			elif supplier_status['hold_type'] == 'Payments':
				if not supplier_status['release_date'] or getdate(nowdate()) <= supplier_status['release_date']:
					return []

	party_account_currency = get_account_currency(args.get("party_account"))
	company_currency = frappe.get_cached_value('Company',  args.get("company"),  "default_currency")

	# Get negative outstanding sales /purchase invoices
	negative_outstanding_invoices = []
	if args.get("party_type") not in ["Student", "Employee"] and not args.get("voucher_no"):
		negative_outstanding_invoices = get_negative_outstanding_invoices(args.get("party_type"), args.get("party"),
			args.get("party_account"), args.get("company"), party_account_currency, company_currency)

	# Get positive outstanding sales /purchase invoices/ Fees
	condition = ""
	if args.get("voucher_type") and args.get("voucher_no"):
		condition = " and voucher_type={0} and voucher_no={1}"\
			.format(frappe.db.escape(args["voucher_type"]), frappe.db.escape(args["voucher_no"]))

	# Add cost center condition
	if args.get("cost_center"):
		condition += " and cost_center='%s'" % args.get("cost_center")

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

	outstanding_invoices = get_outstanding_invoices(args.get("party_type"), args.get("party"),
		args.get("party_account"), filters=args, condition=condition)

	for d in outstanding_invoices:
		d["exchange_rate"] = 1
		if party_account_currency != company_currency:
			if d.voucher_type in ("Sales Invoice", "Purchase Invoice", "Expense Claim"):
				d["exchange_rate"] = frappe.db.get_value(d.voucher_type, d.voucher_no, "conversion_rate")
			elif d.voucher_type == "Journal Entry":
				d["exchange_rate"] = get_exchange_rate(
					party_account_currency,	company_currency, d.posting_date
				)
		if d.voucher_type in ("Purchase Invoice"):
			d["bill_no"] = frappe.db.get_value(d.voucher_type, d.voucher_no, "bill_no")

	# Get all SO / PO which are not fully billed or aginst which full advance not paid
	orders_to_be_billed = []
	if (args.get("party_type") != "Student"):
		orders_to_be_billed =  get_orders_to_be_billed(args.get("posting_date"),args.get("party_type"),
			args.get("party"), args.get("company"), party_account_currency, company_currency, filters=args)

	data = negative_outstanding_invoices + outstanding_invoices + orders_to_be_billed

	if not data:
		frappe.msgprint(("No outstanding invoices found for the {0} {1} which qualify the filters you have specified.")
			.format(args.get("party_type").lower(), frappe.bold(args.get("party"))))

	total_invoice_amount = 0
	total_outstanding_amount = 0

	for current_data in data:
		total_invoice_amount += current_data['invoice_amount']
		total_outstanding_amount += current_data['outstanding_amount']
	if args.get('additional_view') == 1:
		new_data = [{'voucher_no': None, 'voucher_type': 'Sales Invoice', 'posting_date': None,
						'invoice_amount': total_invoice_amount, 'payment_amount': 0,'outstanding_amount': total_outstanding_amount,
						'due_date': None, 'currency': 'IDR', 'exchange_rate': 1}]
		return new_data
	return data
