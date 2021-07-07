# -*- coding: utf-8 -*-
# Copyright (c) 2021, Pratik Mane and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import flt, get_datetime, getdate, date_diff, cint, nowdate, get_link_to_form
from erpnext.manufacturing.doctype.bom.bom import validate_bom_no, get_bom_items_as_dict
from erpnext.stock.utils import get_bin, validate_warehouse_company, get_latest_stock_qty
from frappe.model.naming import make_autoname

class MainWorkOrder(Document):
	def autoname(self):
		if self.is_new():
			item_name = [row.art_no for row in self.work_order_item_detail ]
			item = frappe.get_doc("Item", {"name": item_name[0]})
			if item.item_category:
				item_category = item.item_category
				item_category = item_category.split("-")
				supplier_id = frappe.db.get_value('Supplier',self.supplier, 'supplier_id')
				name = item_category[0] + "/.###"+"/."+supplier_id+"/.YYYY"
				self.name = make_autoname(item_category[0]+"./." + ".###."+"./."+supplier_id+"./.YYYY")

	def before_submit(self):
		self.submitted_by = frappe.session.user


	def on_submit(self):
		for row in self.work_order_item_detail:
			doc = frappe.new_doc('Work Order')
			# doc.production_item = row.art_no
			doc.qty = row.qty

			doc.spk_date = self.spk_date
			doc.wip_warehouse = self.wip_warehouse
			doc.fg_warehouse = self.fg_warehouse
			doc.scrap_warehouse = self.scrap_warehouse
			doc.bom_no = row.bom
			doc.company = self.company
			bom_data = frappe.get_doc("BOM",row.bom)
			doc.production_item = bom_data.item_name
			if bom_data.with_operations:
				for op_row in bom_data.operations:
					print(op_row.operation)
				sql = "select operation, description, workstation, idx,'Pending' as status,base_hour_rate as hour_rate, time_in_mins, parent as bom, batch_size from `tabBOM Operation` where parent = '{0}' order by idx".format(row.bom)
				operations = frappe.db.sql(sql, as_dict=1)

				doc.set('operations', operations)
			doc.expected_delivery_date = self.expected_finish_date
			doc.save(ignore_permissions=True)
			frappe.db.commit()
			doc.submit()
		# self.save()
		# self.docstatus=1


	def fetch_required_item(self,bom):
		bom = frappe.get_doc("BOM",bom)
		bom_data = {}
		item_list = []
		for row in bom.items:
			print("Item :",row.item_code)
			item_list.append(row.item_code)
		bom_data["item_code"] = item_list
		return bom_data
