frappe.ui.form.on('Sales Order Item', {
    item_code: function(frm, cdt, cdn){
        var row = locals[cdt][cdn];
        frappe.call({
           method: "shopee_v01.shopee_v01.custom_script.sales_order.size_filter",
           args: {
             item_code: row.item_code
           },
           callback: function(r) {
                var resp = r.message
                        frappe.model.set_value(row.doctype, row.name, "invent_size_id", resp[0]);
                        frappe.model.set_value(row.doctype, row.name, "available_qty", resp[1]);
              }
        });
    }
});