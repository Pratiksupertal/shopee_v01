frappe.ui.form.on('Item', {
  onload: function(frm) {
    if(frm.doc.has_variants==1) {
		  frm.add_custom_button(__('Update to Halosis'), function () {
        console.log("Clicking Works")
        frappe.call({
          method: "shopee_v01.shopee_v01.custom_script.item.create_template_payload",
          args: {
            "template" : frm.doc.item_code,
          },
          callback: function(r) {
            var resp = r.message
          }
        });
			});
    }
	},
  item_group:function(frm){
    frappe.call({
      method: "shopee_v01.shopee_v01.custom_script.item.categories",
      args: {"doctype":"Item Group",
              "value" : frm.doc.item_group,
              "field" : "item_group_description"
            },
      callback: function(r) {
           var resp = r.message
           cur_frm.set_value("item_group_description", resp);
           frm.refresh_field("item_group_description");
         }
       });
	},
	item_category:function(frm){
    frappe.call({
      method: "shopee_v01.shopee_v01.custom_script.item.categories",
      args: {"doctype":"Item Category",
              "value" : frm.doc.item_category,
              "field" : "item_category"
            },
      callback: function(r) {
           var resp = r.message
           cur_frm.set_value("item_category_description", resp);
           frm.refresh_field("item_category_description");
         }
       });
	},
  division_group:function(frm){
    frappe.call({
      method: "shopee_v01.shopee_v01.custom_script.item.categories",
      args: {"doctype":"Division Group",
              "value" : frm.doc.division_group,
              "field" : "division_description"
            },
      callback: function(r) {
           var resp = r.message
           cur_frm.set_value("division_group_description", resp);
           frm.refresh_field("division_group_description");
         }
       });
	},
  retail_group:function(frm){
    frappe.call({
      method: "shopee_v01.shopee_v01.custom_script.item.categories",
      args: {"doctype":"Retail Group",
              "value" : frm.doc.retail_group,
              "field" : "retail_description"
            },
      callback: function(r) {
           var resp = r.message
           cur_frm.set_value("retail_group_description", resp);
           frm.refresh_field("retail_group_description");
         }
       });
	}
});

frappe.ui.form.on('Item Barcode', {
    barcode: function(frm, cdt, cdn){
        var row = locals[cdt][cdn];
        frappe.call({
           method: "shopee_v01.shopee_v01.custom_script.item.barcode",
           args: {
             "code": row.barcode
           },
           callback: function(r) {
                var resp = r.message
                cur_frm.set_value("item_bar_code", resp);
              }
        });
    }
});
