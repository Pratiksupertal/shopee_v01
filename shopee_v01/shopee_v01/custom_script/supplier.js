frappe.ui.form.on('Supplier', {
  onload:function(frm){
    if(frm.doc.credit_limit_range){
      frappe.call({
        method: "shopee_v01.shopee_v01.custom_script.supplier.available_credit",
        args: {"supplier":frm.doc.name},
        callback: function(r) {
             var resp = r.message[0]
             if(frm.doc.credit_limit_range>resp){
               cur_frm.set_value("available_credit_limit", (frm.doc.credit_limit_range-resp));
               frm.refresh_field("available_credit_limit");
             }
    		 		}
  				});
    }
  }
})
