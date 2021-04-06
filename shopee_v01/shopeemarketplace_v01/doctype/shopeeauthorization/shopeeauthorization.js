// Copyright (c) 2021, Pratik Mane and contributors
// For license information, please see license.txt

frappe.ui.form.on('ShopeeAuthorization', {
	// refresh: function(frm) {

	// }
  // get_code : function(frm){
  //   frappe.call({
	// 		method: "shopee_v01.shopeemarketplace_v01.doctype.shopeeauthorization.shopeeauthorization.get_code",
	// 		callback: function(r) {
	// 	       var url = r.message
  //          window.open(url, '_blank');
	// 		}
	// 	})
  // },
  // key : function(frm){
  //   console.log(cur_frm.doc.key);
  //   if(cur_frm.doc.key){
  //     frappe.call({
  // 			method: "shopee_v01.shopeemarketplace_v01.doctype.shopeeauthorization.shopeeauthorization.generate_refreshtoken",
  //       args: {"code": cur_frm.doc.key},
  // 			callback: function(r) {
  // 		       var resp = r.message
  //            cur_frm.set_value("value", resp.refresh_token);
  // 			}
  // 		})
  //   }
  // },
  validate : function(frm){
    // frappe.call({
    //   method: "shopee_v01.shopeemarketplace_v01.doctype.shopeeauthorization.shopeeauthorization.generate_keyvalues",
    //   args: {"code": cur_frm.doc.key},
    //   callback: function(r) {
    //        var resp = r.message
    //        cur_frm.set_value("value", resp.refresh_token);
    //   }
    // })
  }
});
