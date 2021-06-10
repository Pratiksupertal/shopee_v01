// Copyright (c) 2021, Pratik Mane and contributors
// For license information, please see license.txt

frappe.ui.form.on('Main Work Order', {
  onload:function(frm){
    console.log("onload funxtion");
    frm.ignore_doctypes_on_cancel_all = ["Work Order"]
  },
  setup:function(frm){
  // // Set query for BOM
  // frm.set_query("bom", function() {
  //   if (frm.doc.production_item) {
  //     return {
  //       query: "erpnext.controllers.queries.bom",
  //       filters: {item: cstr(frm.doc.production_item)}
  //     };
  //   } else {
  //     frappe.msgprint(__("Please enter Production Item first"));
  //   }
  // });
  // // Set query for FG Item
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
