console.log("Item doctype call");
frappe.ui.form.on('Item', { //frappe.ui.form.on("Job Opening", {
  //shopee_v01.shopeemarketplace_v01.doctype.custom.item

  sync_to_shopee : function(frm){
    console.log("sync button clicked");
  }
});
