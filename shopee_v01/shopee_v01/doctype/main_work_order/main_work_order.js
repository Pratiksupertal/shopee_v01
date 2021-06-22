// Copyright (c) 2021, Pratik Mane and contributors
// For license information, please see license.txt

frappe.ui.form.on('Main Work Order', {
  onload:function(frm){
    //
    frm.set_query("wip_warehouse", function() {
			return {
				filters: {
					'company': frm.doc.company,
				}
			};
		});

		frm.set_query("fg_warehouse", function() {
			return {
				filters: {
					'company': frm.doc.company,
					'is_group': 0
				}
			};
		});

		frm.set_query("scrap_warehouse", function() {
			return {
				filters: {
					'company': frm.doc.company,
					'is_group': 0
				}
			};
		});
  },

  packing_template:function(frm){
    frappe.call({
      method: "shopee_v01.shopee_v01.custom_script.purchase_order.cara_packing",
      args: {"template_name":frm.doc.packing_template},
      callback: function(r) {
           var resp = r.message
           cur_frm.set_value("packing", resp);
           frm.refresh_field("packing");
         }
       });
  }
});
// Child table Work Order Item Details trigger
// frappe.ui.form.on('Work Order Item Details', {
frappe.ui.form.on('Work Order Item Details', {
	bom: function(frm, cdt, cdn){
	var row = locals[cdt][cdn];
	frm.call({
    doc:frm.doc,
    method: "fetch_required_item",
    freeze: true,
    args: {
      bom: row.bom
    },
    callback: function(r) {
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
