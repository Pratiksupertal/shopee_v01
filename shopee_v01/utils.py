from __future__ import unicode_literals
import frappe
import logging

def schedular_log(msg):
	logger  = logging.getLogger()
	# logging.basicConfig(filename='example.log', encoding='UTF-8', level=logging.INFO)
	logging.basicConfig(handlers=[logging.FileHandler(filename="../logs/schedular_log.txt",
												 encoding='utf-8', mode='a+')],
					format="%(asctime)s %(name)s:%(levelname)s:%(message)s",
					datefmt="%F %A %T",
					level=logging.INFO)
	ch = logging.StreamHandler()
	ch.setLevel(logging.INFO)
	logging.info(msg)
	formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
	ch.setFormatter(formatter)

def get_permission_query_conditions_for_item(user):
	roles = frappe.get_roles(user)
	if (user != "Administrator") and ("ISS Follow Up Supervisor" in roles) or("ISS Follow Up Admin" in roles):
		item_groups = frappe.get_list("Item Group", filters={ "parent_item_group": "008 - Finish Good" },
		fields=["name"],
		distinct=True)
		final_item_group = [ '%s'%item_group.get("name") for item_group in item_groups ]
		final_item_group = tuple(final_item_group)
		return """(`tabItem`.item_group  in {0})""".format(final_item_group)
	elif (user != "Administrator") and ("ISS Purchasing Admin" in roles) or ("ISS Purchasing Manager" in roles):
		item_groups = frappe.get_list("Item Group", filters={ "parent_item_group":('in', ("001 - Raw Material","002 - Accessories"))},
		fields=["name"],
		distinct=True)
		final_item_group = [ '%s'%item_group.get("name") for item_group in item_groups ]
		final_item_group = tuple(final_item_group)
		return """(`tabItem`.item_group  in {0})""".format(final_item_group)
	elif (user != "Administrator") and ("ISS CEO" in roles) or ("ISS Accounting Supervisor" in roles):
		item_groups = frappe.get_list("Item Group", filters={ "parent_item_group":('in', ("001 - Raw Material","002 - Accessories", "008 - Finish Good"))},
		fields=["name"],
		distinct=True)
		final_item_group = [ '%s'%item_group.get("name") for item_group in item_groups ]
		final_item_group = tuple(final_item_group)
		return """(`tabItem`.item_group  in {0})""".format(final_item_group)

