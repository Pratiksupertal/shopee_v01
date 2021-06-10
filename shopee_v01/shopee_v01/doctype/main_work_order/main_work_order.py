# -*- coding: utf-8 -*-
# Copyright (c) 2021, Pratik Mane and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import flt, get_datetime, getdate, date_diff, cint, nowdate, get_link_to_form
from erpnext.manufacturing.doctype.bom.bom import validate_bom_no, get_bom_items_as_dict
from erpnext.stock.utils import get_bin, validate_warehouse_company, get_latest_stock_qty

class MainWorkOrder(Document):
	def on_submit(self):
		for row in self.work_order_item_detail:
			doc = frappe.new_doc('Work Order')
			print(row)
			# continue
			doc.production_item = row.art_no
			doc.qty = row.qty
			doc.spk_date = self.spk_date
			doc.wip_warehouse = self.wip_warehouse
			doc.fg_warehouse = self.fg_warehouse
			doc.scrap_warehouse = self.scrap_warehouse
			doc.bom_no = row.bom
			doc.reference_main_work_order = self.name
			doc.save(ignore_permissions=True)
			frappe.db.commit()
			doc.submit()
		# self.docstatus=1

	def on_cancel(self):
		work_order = frappe.get_doc('Work Order', {"reference_main_work_order": self.name })
		print(work_order.name)
		print(work_order.docstatus)
		if work_order.docstatus == 1:
			msg = "Please cancel the Work Order linked with this Main Work Order {0}".format(work_order.name)
			frappe.msgprint(msg)
			work_order.docstatus = 2
			work_order.status = "Cancelled"
		# work_order.save(ignore_permissions=True)
		self.docstatus = 2
		self.status = "Cancelled"



		pass

	def fetch_required_item(self):
		print(self.bom)
		bom = frappe.get_doc("BOM",self.bom)
		bom_data = {}
		for row in bom.items:
			bom_data["item_code"] = row.item_code
			bom_data["qty"] = row.qty
			bom_data["uom"] = row.uom
			print(row.item_code,row.qty,row.uom)
		print("fetch required item function called")
		return bom_data
