// Copyright (c) 2022, Pratik Mane and contributors
// For license information, please see license.txt

frappe.ui.form.on('E_Signature', {
	refresh: function(frm) {
    console.log("--- E signature opened");
    if(frm.doc.signature_image){
      console.log(frm.doc.signature_image);
      frm.set_value("signature",frm.doc.signature_image);
    }
	},
  validate:function(frm){


  }
});
