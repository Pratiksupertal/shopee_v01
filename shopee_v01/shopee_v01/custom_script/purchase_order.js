frappe.ui.form.on('Purchase Order', {
	cara_packing_template : function(frm){
    frappe.call({
      method: "shopee_v01.shopee_v01.custom_script.purchase_order.cara_packing",
      args: {"template_name":frm.doc.cara_packing_template},
      callback: function(r) {
           var resp = r.message
           cur_frm.set_value("cara_packing", resp);
           frm.refresh_field("cara_packing");
  }
});
}
});
