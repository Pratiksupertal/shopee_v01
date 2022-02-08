# -*- coding: utf-8 -*-
# Copyright (c) 2021, Pratik Mane and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import json

import frappe
from frappe.model.document import Document
from frappe.utils import flt, get_datetime, getdate, date_diff, cint, now, nowdate, get_link_to_form
from erpnext.manufacturing.doctype.bom.bom import validate_bom_no, get_bom_items_as_dict
from erpnext.stock.utils import get_bin, validate_warehouse_company, get_latest_stock_qty
from frappe.model.naming import make_autoname
from frappe.model.mapper import get_mapped_doc

from urllib.parse import urlparse


class MainWorkOrder(Document):
	#For main work order Art no is Doctype ART No
	def autoname(self):
		if self.is_new():
			bom_no = [row.bom for row in self.work_order_item_detail ]
			bom_data = frappe.get_doc("BOM",bom_no[0])
			item = frappe.get_doc("Item", {"item_name": bom_data.item_name})
			if item.item_category:
				item_category = item.item_category
				item_category = item_category.split("-")
				supplier_id = frappe.db.get_value('Supplier',self.supplier, 'supplier_id')
				if not supplier_id:
					raise Exception("Supplier ID not available for this supplier")
				name = item_category[0] + "/.###"+"/."+supplier_id+"/.YYYY"
				self.name = make_autoname(item_category[0]+"./." + ".###."+"./."+supplier_id+"./.YYYY")
	#For main work order Art no is Item code
	def autonameCommented(self):
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
		supplier = frappe.get_doc('Supplier', self.supplier)
		for row in self.work_order_item_detail:
			with_operation = frappe.db.get_value("BOM",row.bom,"with_operations")
			if(self.is_external and with_operation ==0):
				doc = frappe.new_doc("Purchase Order")
				doc.supplier = self.supplier
				doc.tax_category = supplier.tax_category
				doc.schedule_date = self.expected_finish_date
				doc.is_subcontracted = "Yes"
				doc.supplier_warehouse = self.supplier_warehouse
				doc.po_type = "FACTORY"
				item = frappe.db.get_value("BOM",row.bom,"item")
				doc.append("items", {
					"item_code": item ,
					"warehouse": self.supplier_warehouse,
					"qty": row.qty,
					"rate": self.manufacturing_rate,
					"schedule_date": self.expected_finish_date,
					"bom":row.bom
				})
				doc.reference_main_work_order = self.name
				tax_category = frappe.get_value("Supplier",doc.supplier,"tax_category")
				taxes_and_charges = frappe.get_doc('Purchase Taxes and Charges Template',{"tax_category":tax_category})
				tax_template = frappe.get_doc('Purchase Taxes and Charges Template', taxes_and_charges.name)
				doc.append("taxes",{
					"category" : "Total",
					"add_deduct_tax":"Add",
					"charge_type":tax_template.taxes[0].charge_type,
					# "charge_type":"On Net Total",
					"account_head":tax_template.taxes[0].account_head,
					# "account_head":"VAT - ISS",
					"rate": tax_template.taxes[0].rate,
					# "rate": 10.00,
					"description":tax_template.taxes[0].description
					# "description":"VAT - ISS"
				})
				doc.save()
				# setting up reserve_warehouse in purchase order
				if doc.is_subcontracted == "Yes":
					doc.reserve_warehouse = self.source_warehouse
					supp_items = doc.get("supplied_items")
					for d in supp_items:
						d.reserve_warehouse = self.source_warehouse
				doc.save()
				doc.submit()



	def on_submit(self):
		# External production will create new purchase order.
		for row in self.work_order_item_detail:
			with_operation = frappe.db.get_value("BOM",row.bom,"with_operations")
			# Internal production will create new work order.
			if(self.is_external!=1 and with_operation ==1):
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
				doc.production_item = bom_data.item
				if bom_data.with_operations:
					for op_row in bom_data.operations:
						print(op_row.operation)
					sql = "select operation, description, workstation, idx,'Pending' as status,base_hour_rate as hour_rate, time_in_mins, parent as bom, batch_size from `tabBOM Operation` where parent = '{0}' order by idx".format(row.bom)
					operations = frappe.db.sql(sql, as_dict=1)

					doc.set('operations', operations)
				doc.reference_main_work_order = self.name
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



@frappe.whitelist()
def workorder_data(main_work_order):
	print(main_work_order)
	work_order = frappe.db.get_list('Work Order',
		filters={
			'reference_main_work_order': main_work_order
		},
	    fields=['name', 'qty']
	)
	print(work_order)
	return work_order

'''Creating pick for Main Work Order '''


def create_pick_list(source_name, target_doc=None, for_qty=None):
	for_qty = for_qty or json.loads(target_doc).get('for_qty')
	max_finished_goods_qty = frappe.db.get_value('Work Order', source_name, 'qty')
	def update_item_quantity(source, target, source_parent):
		pending_to_issue = flt(source.required_qty) - flt(source.transferred_qty)
		desire_to_transfer = flt(source.required_qty) / max_finished_goods_qty * flt(for_qty)
		qty = 0
		if desire_to_transfer <= pending_to_issue:
			qty = desire_to_transfer
		elif pending_to_issue > 0:
			qty = pending_to_issue
		if qty:
			target.qty = qty
			target.stock_qty = qty
			target.uom = frappe.get_value('Item', source.item_code, 'stock_uom')
			target.stock_uom = target.uom
			target.conversion_factor = 1
		else:
			target.delete()
	doc = get_mapped_doc('Work Order', source_name, {
		'Work Order': {
			'doctype': 'Pick List',
			'validation': {
				'docstatus': ['=', 1]
			}
		},
		'Work Order Item': {
			'doctype': 'Pick List Item',
			'postprocess': update_item_quantity,
			'condition': lambda doc: abs(doc.transferred_qty) < abs(doc.required_qty)
		},
	}, target_doc)
	doc.for_qty = for_qty
	#doc.purpose = "Material Transfer"
	doc.set_item_locations()
	return doc


def make_pick_list(work_order_id, qty):
	try:
		import requests
		data_validation_for_creating_pick_list(work_order_id, qty)
		data = create_pick_list(
			source_name=work_order_id,
			for_qty=qty
		)

		pick_list = frappe.new_doc('Pick List')
		pick_list = data
		pick_list.save()
		pick_list_id = pick_list.get('name')
		return f"Work Order {work_order_id}: Pick List {pick_list_id} created"
	except Exception as e:
		return f"Pick List not created for Work Order - {work_order_id}. Reason - {e}"


@frappe.whitelist()
def pick_lists(work_order_list):
	work_order_list = json.loads(work_order_list)
	print(work_order_list)
	result = []
	for work_order in work_order_list:
		if "__checked" in work_order.keys():
			if work_order["__checked"]:
				res = make_pick_list(work_order_id=work_order["name"], qty=work_order["qty"])
				result.append(res)
	response_msg = "<br>".join(result)
	print(response_msg)
	return response_msg		


def data_validation_for_creating_pick_list(work_order, qty):
	print("This is data validation function")
	pick_list = frappe.db.sql("select * from `tabPick List` where work_order = %s", work_order)
	if pick_list:
		raise Exception("Pick List already created for the work order")

	max_finished_goods_qty = frappe.db.get_value('Work Order', work_order, 'qty')
	if qty != max_finished_goods_qty:
		raise Exception("Input quantity is not equal to the total quantity")


@frappe.whitelist()
def job_card_data(main_work_order):
	work_order_list = [work_order['name'] for work_order in workorder_data(main_work_order=main_work_order)]
	job_cards = frappe.db.get_list('Job Card',
		filters={
			"work_order": ["in", work_order_list],
			"status": ["in", ["Open", "Completed"]]
		},
		fields=[
			'name', 'operation', 'work_order', 'for_quantity', "total_completed_qty", "status"
		],
		order_by='operation'
	)
	return job_cards


@frappe.whitelist()
def in_progress_job_card_data(main_work_order):
	work_order_list = [work_order['name'] for work_order in workorder_data(main_work_order=main_work_order)]
	job_cards = frappe.db.get_list('Job Card',
		filters={
			"work_order": ["in", work_order_list],
			"status": "Work In Progress"
		},
		fields=[
			'name', 'operation', 'work_order', 'for_quantity', "total_completed_qty", "status"
		],
		order_by='operation'
	)

	return job_cards


@frappe.whitelist()
def start_job_cards(job_card_list):
	from datetime import datetime
	new_jobs = []
	job_card_list = json.loads(job_card_list)
	print(job_card_list)
	print(type(job_card_list))
	for new_job in job_card_list:
		if '__checked' in new_job:
			new_jobs.append(new_job)
	job_card_name_list = [job_card['name'] for job_card in new_jobs]
	print(job_card_name_list)
	job_cards = frappe.db.get_list('Job Card', filters={'name': ['in', job_card_name_list], 'status': 'Open'})
	print(job_cards)
	for job_card in job_cards:
		job_doc = frappe.get_doc('Job Card', job_card.name)
		row = job_doc.append('time_logs', {})
		row.from_time = now()
		row.completed_qty = 0
		job_doc.job_started = 1
		job_doc.started_time = row.from_time
		job_doc.status = "Work In Progress"
		if not frappe.flags.resume_job:
			job_doc.current_time = 0

		job_doc.save()




