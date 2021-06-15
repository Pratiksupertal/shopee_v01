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
  },

bom: function(frm) {
  frm.call({
    doc:frm.doc,
    method: "fetch_required_item",
    freeze: true,
    callback: function(r) {
         var resp = r.message
         var childTable = cur_frm.add_child("required_items");
         childTable.item_code = r.message.item_code
         childTable.qty = r.message.qty
         childTable.item_code = r.message.uom
         cur_frm.refresh_fields("required_items");
}
});
},
});
