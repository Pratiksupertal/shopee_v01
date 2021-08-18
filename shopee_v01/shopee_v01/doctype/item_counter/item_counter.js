// Copyright (c) 2021, Pratik Mane and contributors
// For license information, please see license.txt

frappe.ui.form.on('Item Counter', {
	// refresh: function(frm) {

	// }
});
// Child table Work Order Item Details trigger
// frappe.ui.form.on('Work Order Item Details', {
frappe.ui.form.on('Total Item count in Warehouse', {
	item_code: function(frm, cdt, cdn){
		console.log("----- item code event called -----");
	var row = locals[cdt][cdn];
	frm.call({
    doc:frm.doc,
    method: "fetch_item_name",
    freeze: true,
    args: {
      item_code: row.item_code
    },
    callback: function(r) {
			console.log("----- call back from fetch_item_name ----");
         var resp = r.message
         for(var i = 0; i < resp.item_code.length; i++) {
           var childTable = cur_frm.add_child("required_item");
           childTable.item_code = resp.item_code[i];
           cur_frm.refresh_fields("required_item");
         };
       }
     });
	}
});
