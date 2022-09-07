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
                        frappe.model.set_value(row.doctype, row.name, "basic_rate", resp[1]);
                        frappe.model.set_value(row.doctype, row.name, "available_qty", resp[2]);
                        frappe.model.set_value(row.doctype, row.name, "actual_available_qty", resp[3]);
              }
        });
    },
    qty: function(frm, cdt, cdn){
        var row = locals[cdt][cdn];
        frappe.call({
           method: "shopee_v01.shopee_v01.custom_script.sales_order.actual_qty_delivery_date",
           args: {
             item_code: row.item_code,
             qty: row.qty
           },
           callback: function(r) {
                var resp = r.message
                        frappe.model.set_value(row.doctype, row.name, "actual_available_qty", resp[1]);
              }
        });
    },
});
