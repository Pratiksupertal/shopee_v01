// Copyright (c) 2021, Pratik Mane and contributors
// For license information, please see license.txt

frappe.ui.form.on('ShopeeAuthentication01', {
  get_code : function(frm){
    frappe.call({
			method: "shopee_v01.shopeemarketplace_v01.doctype.shopeeauthentication01.shopeeauthentication01.get_code",
			callback: function(r) {
		       var url = r.message
           window.open(url, '_blank');
			}
		})
  },
  key : function(frm){
    console.log(cur_frm.doc.key);
    if(cur_frm.doc.key){
      frappe.call({
  			method: "shopee_v01.shopeemarketplace_v01.doctype.shopeeauthentication01.shopeeauthentication01.generate_refreshtoken",
        args: {"code": cur_frm.doc.key},
  			callback: function(r) {
  		       var resp = r.message
             cur_frm.set_value("value", resp.refresh_token);
             frm.refresh_field("value");
  			}
  		})
    }
  },
  validate : function(frm){
    console.log(cur_frm.doc.code);
    frappe.call({
      method: "shopee_v01.shopeemarketplace_v01.doctype.shopeeauthentication01.shopeeauthentication01.generate_keyvalues",
      args: {"code": cur_frm.doc.code},
      callback: function(r) {
           var resp = r.message
           console.log(resp);
           // cur_frm.set_value("value", resp.refresh_token);
      }
    })
  }
});
