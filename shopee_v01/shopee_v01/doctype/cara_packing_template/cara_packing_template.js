// Copyright (c) 2021, Pratik Mane and contributors
// For license information, please see license.txt
console.log("Cara packing doctype call");
frappe.ui.form.on('Cara Packing Template', {
  refresh : function(frm){
    console.log("Cara packing clicked");
  }
});
