// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Stock Sales Finish Good With Attribute Size"] = {
	"filters": [
	{
			fieldname: "warehouse_name",
			label: __("Warehouse"),
			fieldtype: "Link",
			options: "Warehouse",
			default: "All Warehouses - ISS"
		},
	]
};
