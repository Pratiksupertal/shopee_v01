console.log("Purchase Order doctype call");
frappe.ui.form.on('Purchase Order', { //frappe.ui.form.on("Job Opening", {
  //shopee_v01.shopeemarketplace_v01.doctype.custom.item

  cara_packing_template : function(frm){
    frappe.call({
      method: "shopee_v01.shopeemarketplace_v01.doctype.custom.purchase_order.cara_packing",
      args: {"template_name":frm.doc.cara_packing_template},
      callback: function(r) {
           var resp = r.message
           cur_frm.set_value("cara_packing", resp);
           frm.refresh_field("cara_packing");
  }
});
}
})
