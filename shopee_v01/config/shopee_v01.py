from __future__ import unicode_literals
from frappe import _
import frappe

def get_data():
	return [
		{
			"label": _("Shopee V01"),
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
		}
        ]
