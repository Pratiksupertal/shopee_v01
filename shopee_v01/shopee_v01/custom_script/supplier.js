console.log("------- supplier doctype ----");
frappe.ui.form.on('Supplier', {
  onload:function(frm){
    console.log("Supplier is loaded");
    if(frm.doc.credit_limit_range){
      console.log(frm.doc.name);
      frappe.call({
        method: "shopee_v01.shopee_v01.custom_script.supplier.available_credit",
        args: {"supplier":frm.doc.name},
        callback: function(r) {
             var resp = r.message[0]
             console.log("callback of frappe call");
             if(frm.doc.credit_limit_range>resp){
               cur_frm.set_value("available_credit_limit", (frm.doc.credit_limit_range-resp));
               frm.refresh_field("available_credit_limit");
              
             }
    		 		}
  				});
    }
  }
})
