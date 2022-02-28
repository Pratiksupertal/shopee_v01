// Copyright (c) 2016, Pratik Mane and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Kartu Stock"] = {
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
