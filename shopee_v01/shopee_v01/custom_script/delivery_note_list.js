frappe.listview_settings['Delivery Note'] = {
  add_fields: ["sales_order","customer", "customer_name", "base_grand_total", "per_installed", "per_billed",
   "transporter_name", "grand_total", "is_return", "status", "currency"],
  onload(listview) {
      frappe.call({
				method: "shopee_v01.shopee_v01.custom_script.delivery_note_list.update_table_delivery_note",
				args: {
					name: ""
				}
			});
  },

}
