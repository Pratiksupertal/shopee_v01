# -*- coding: utf-8 -*-
# Copyright (c) 2021, Pratik Mane and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import json

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, get_datetime, getdate, time_diff_in_hours, date_diff, cint, now, nowdate, get_link_to_form, time_diff
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
					supplied_qty = {}
					doc.total_supplied_amount = 0
					for i,val in enumerate(self.required_item):
						supplied_qty[val.item_code]= val.supplied_qty
					for d in supp_items:
						d.supplied_qty = supplied_qty[d.rm_item_code]
						d.reserve_warehouse = self.source_warehouse
						# d.supplied_qty_amount = d.supplied_qty * d.rate
						# d.rate = 5000
						# doc.total_supplied_amount = doc.total_supplied_amount + d.supplied_qty_amount
					# doc.total_supplied_amount_with_tax = doc.total_supplied_amount + (doc.total_supplied_amount * tax_template.taxes[0].rate/100)

				doc.save()
				doc.submit()
				# doc1 = frappe.get_doc("Purchase Order", doc.name)
				# doc1.title     # I not sure what to type here
				# doc1.grand_total = doc.grand_total - doc.total_supplied_amount_with_tax
				# doc1.rounded_total = doc1.grand_total
				# from frappe.utils import money_in_words
				# doc1.in_words = money_in_words(doc1.grand_total, "IDR")
				# doc1.save()

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


'''Fetching Data from Main Work Order'''
@frappe.whitelist()
def workorder_data(main_work_order):
	work_order = frappe.db.get_list('Work Order',
		filters={
			'reference_main_work_order': main_work_order
		},
	    fields=['name', 'qty']
	)
	return work_order


'''Creating pick for Main Work Order '''
def make_pick_list(work_order_id, qty):
	try:
		data_validation_for_creating_pick_list(work_order_id, qty)
		all_items = []
		raw_materials_items = []
		not_raw_materials_items = []
		work_order_doc = frappe.get_doc('Work Order', work_order_id)
		rows = work_order_doc.required_items
		for row in rows:
			all_items.append(row.item_name)
		for item in all_items:
			raw_mat_item = frappe.db.get_value('Item', filters={'name': ['=', item], 'item_group': ['=', 'Raw Material']})
			if raw_mat_item:
				raw_materials_items.append(raw_mat_item)
				continue
			acc_mat_item = frappe.db.get_value('Item', filters={'name': ['=', item], 'item_group': ['!=', 'Raw Material']})
			if acc_mat_item: not_raw_materials_items.append(acc_mat_item)

		picklist1 = generate_new_pick_list(raw_materials_items, work_order_doc)
		picklist2 = generate_new_pick_list(not_raw_materials_items, work_order_doc)
		response = f"For Work Order <strong><a href='{work_order_doc.get_url()}'>{work_order_doc.name}</a></strong>"
		if picklist1:
			response += f"<br>Pick List <strong><a href='{picklist1.get_url()}'>{picklist1.get('name')}</a></strong> is created for Raw Materials Items"
		if picklist2:
			response += f"<br>Pick List <strong><a href='{picklist2.get_url()}'>{picklist2.get('name')}</a></strong> is created for Accessories Items"
		return response + _("<br>")
	except Exception as e:
		work_order_doc = frappe.get_doc('Work Order', work_order_id)
		# return _("Pick List not created for Work Order - <strong>{0}</strong>. Reason - {1}").format(get_link_to_form("Pick List", picklist1), str(e))
		return f"Pick List not created for Work Order - <strong><a href='{work_order_doc.get_url()}'>{work_order_doc.name}</a></strong>. Reason - {str(e)}"

def generate_new_pick_list(item_list, work_order_doc):
	if not item_list: return
	pick_list = frappe.new_doc('Pick List')
	pick_list.company = work_order_doc.company
	pick_list.purpose = "Material Transfer for Manufacture"
	pick_list.work_order = work_order_doc.name
	pick_list.for_qty = work_order_doc.qty
	for item in item_list:
		row = pick_list.append('locations', {})
		row.item_code = item
		row.warehouse = "Stores - ISS"
		row.qty = work_order_doc.qty
		row.stock_qty = work_order_doc.qty
		row.picked_qty = work_order_doc.qty
	pick_list.save()
	return pick_list


'''For Mark check box selecting pick lists'''
@frappe.whitelist()
def pick_lists(work_order_list):
	work_order_list = json.loads(work_order_list)
	result = []
	for work_order in work_order_list:
		if "__checked" in work_order.keys():
			if work_order["__checked"]:
				res = make_pick_list(work_order_id=work_order["name"], qty=work_order["qty"])
				result.append(res)
	response_msg = "<br>".join(result)
	if len(response_msg) == 0:
		frappe.msgprint("Operation failed. No Work Order is selected.")
	else:
		frappe.msgprint(response_msg)


def data_validation_for_creating_pick_list(work_order, qty):
	max_finished_goods_qty = frappe.db.get_value('Work Order', work_order, 'qty')
	if qty != max_finished_goods_qty:
		raise Exception("Input quantity is not equal to the total quantity")


'''Fetching Job card Data'''
@frappe.whitelist()
def job_card_data(main_work_order):
	work_order_list = [work_order['name'] for work_order in workorder_data(main_work_order=main_work_order)]
	job_cards = frappe.db.get_list('Job Card',
		filters={
			"work_order": ["in", work_order_list],
			"job_started": ["=", 0]
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
			"job_started": ["=", 1]
		},
		fields=[
			'name', 'operation', 'work_order', 'for_quantity', "total_completed_qty", "status"
		],
		order_by='operation'
	)
	return job_cards


@frappe.whitelist()
def start_job_cards(job_card_list):
	response = []
	job_card_list = json.loads(job_card_list)
	new_jobs = [new_job for new_job in job_card_list if '__checked' in new_job]
	for job_card in new_jobs:
		if job_card['status'] == 'Completed':
			job_doc = frappe.get_doc('Job Card', job_card['name'])
			response.append(f"Job card <strong><a href='{job_doc.get_url()}'>{job_card['name']}</a> - [{job_card['job_card']}]</strong> already completed.<br>")
			continue
		job_doc = frappe.get_doc('Job Card', job_card['name'])
		row = job_doc.append('time_logs', {})
		row.from_time = get_datetime()
		row.completed_qty = 0
		job_doc.job_started = 1
		job_doc.started_time = row.from_time
		job_doc.status = "Work In Progress"
		if not frappe.flags.resume_job:
			job_doc.current_time = 0
		job_doc.save()
		response.append(f"Job card <strong><a href='{job_doc.get_url()}'>{job_card['name']}</a> - [{job_card['job_card']}]</strong> started.<br>")
	if len(response) == 0:
		frappe.msgprint("Operation failed. No Job Card is selected.")
	else:
		frappe.msgprint("<br>".join(response))


@frappe.whitelist()
def stop_job_cards(in_progress_job_card_list):
	new_jobs = []
	response = []
	in_progress_job_card_list = json.loads(in_progress_job_card_list)
	for new_job in in_progress_job_card_list:
		if '__checked' in new_job and new_job['status'] == "Work In Progress":
			new_jobs.append(new_job)
	for job_card in new_jobs:
		job_doc = frappe.get_doc('Job Card', job_card['name'])
		rows = job_doc.get('time_logs')
		print('\n', rows)

		# This is the last row of time logs
		row = rows[-1]
		print('\n', row)

		row.to_time = get_datetime()
		row.time_in_mins = time_diff_in_hours(row.to_time, job_doc.started_time) * 60
		job_doc.total_time_in_mins += row.time_in_mins
		if 'input_qty' not in job_card:
			response.append(f"Operation failed for Job card <strong><a href='{job_doc.get_url()}'>{job_card['name']}</a> - [{job_card['job_card']}]</strong>. No input quantity entered.<br>")
			continue

		if job_card['input_qty'] > 0:
			if job_card['total_completed_qty'] == 0 and job_card['input_qty'] <= job_card['qty']:
				row.completed_qty = job_card['input_qty']
				job_card['total_completed_qty'] = job_card['input_qty']
				job_doc.job_started = 0
				job_doc.started_time = ''
				if job_card['input_qty'] < job_card['qty']:
					job_doc.save()
					response.append(f"Job card <strong><a href='{job_doc.get_url()}'>{job_card['name']}</a> - [{job_card['job_card']}]</strong> stopped.<br>")
				else:
					job_doc.status = "Complete"
					job_doc.submit()
					response.append(f"Job card <strong><a href='{job_doc.get_url()}'>{job_card['name']}</a> - [{job_card['job_card']}]</strong> Completed.<br>")

			elif job_card['total_completed_qty'] != 0 and (job_card['total_completed_qty'] + job_card['input_qty']) <= job_card['qty']:
				row.completed_qty = job_card['input_qty']
				job_card['total_completed_qty'] += job_card['input_qty']
				job_doc.job_started = 0
				job_doc.started_time = ''
				if job_card['total_completed_qty'] < job_card['qty']:
					job_doc.save()
					response.append(f"Job card <strong><a href='{job_doc.get_url()}'>{job_card['name']}</a> - [{job_card['job_card']}]</strong> stopped.<br>")
				else:
					job_doc.status = "Complete"
					job_doc.submit()
					response.append(f"Job card <strong><a href='{job_doc.get_url()}'>{job_card['name']}</a> - [{job_card['job_card']}]</strong> completed.<br>")
			else:
				response.append(f"Operation failed for Job card <strong><a href='{job_doc.get_url()}'>{job_card['name']}</a> - [{job_card['job_card']}]</strong>. Enter a quantity less than or equal to the remaining quantity.<br>")
		else:
			response.append(f"Operation failed for Job card <strong><a href='{job_doc.get_url()}'>{job_card['name']}</a> - [{job_card['job_card']}]</strong>. Enter a quantity greater than 0.<br>")
	if len(response) == 0:
		frappe.msgprint("Operation failed. No Job Card is selected.")
	else:
		frappe.msgprint("<br>".join(response))
