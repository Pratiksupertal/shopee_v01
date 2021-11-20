from __future__ import unicode_literals
from frappe import _
import frappe

def get_data():
	return [
		{
			"label": _("Custom App"),
			"icon": "fa fa-star",
			"items": [
				{
					"type": "doctype",
					"name": "Main Work Order",
					"description": _("Orders released for production."),
					"onboard": 1,
					"dependencies": ["Item", "BOM"]
				}
			]
		},
		{
			"label": _("Dashboard Accounting Receivable"),
			"icon": "fa fa-star",
			"items": [
				{
					"type": "report",
					"is_query_report": True,
					"name": "Account Receivable",
					"route": "#query-report/Accounts%20Receivable",
					"description": _("Accounts Receivable"),
					"doctype": "Sales Invoice",
					"onboard": 1,
					"dependencies": ["Sales Invoice"]
				},
				{
					"type": "report",
					"name": "Ordered Items To Be Billed",
					"is_query_report": True,
					"doctype": "Sales Invoice"
				},
				{
					"type": "report",
					"name": "Delivered Items To Be Billed",
					"is_query_report": True,
					"doctype": "Sales Invoice"
				}
			]
		},
		{
			"label": _("Dashboard Accounting Payable"),
			"icon": "fa fa-star",
			"items": [
				{
					"type": "report",
					"name": "Accounts Payable",
					"doctype": "Purchase Invoice",
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "Purchase Order Items To Be Billed",
					"is_query_report": True,
					"doctype": "Purchase Invoice"
				},
				{
					"type": "report",
					"name": "Received Items To Be Billed",
					"is_query_report": True,
					"doctype": "Purchase Invoice"
				},
			]
		},
		{
			"label": _("Dashboard Warehouse"),
			"icon": "fa fa-star",
			"items": [
				{
					"type": "report",
					"is_query_report": True,
					"name": "Ordered Items To Be Delivered",
					"doctype": "Delivery Note"
				},
				{
					"type": "report",
					"is_query_report": True,
					"name": "Purchase Order Items To Be Received",
					"doctype": "Purchase Receipt"
				},
				{
					"type": "report",
					"is_query_report": True,
					"name": "Batch-Wise Balance History",
					"doctype": "Batch"
				},
				{
					"type": "page",
					"name": "stock-balance",
					"label": _("Stock Summary"),
					"dependencies": ["Item"],
				}
			]
		}
        ]
