frappe.ui.form.on('Material Request', {
    refresh: function(frm) {
        if(frm.doc.docstatus===0) {
            frm.add_custom_button(__('Purchase Order'), function() {
                erpnext.utils.map_current_doc({
                    method: "shopee_v01.shopee_v01.custom_script.purchase_order.make_stock_entry_material_request",
                    source_doctype: "Purchase Order",
                    target: frm,
                    date_field: "schedule_date",
                    setters: {
                        company: frm.doc.company,
                    },
                })
            }, __("Get items from"));

        }
    }
});
frappe.ui.form.on('Material Request Item', {
    item_code: function(frm, cdt, cdn){
        var row = locals[cdt][cdn];
        frappe.call({
           method: "shopee_v01.shopee_v01.custom_script.material_request.size_filter",
           args: {
             item_code: row.item_code
           },
           callback: function(r) {
                var resp = r.message
                        frappe.model.set_value(row.doctype, row.name, "available_qty", resp[2]);
                        frappe.model.set_value(row.doctype, row.name, "actual_available_qty", resp[3]);
                        frm.refresh_field('items');
              }
        });
    },
    qty: function(frm, cdt, cdn){
        var row = locals[cdt][cdn];
        frappe.call({
           method: "shopee_v01.shopee_v01.custom_script.material_request.actual_available_qty_schedule_date",
           args: {
             item_code: row.item_code,
             qty: row.qty
           },
           callback: function(r) {
                var resp = r.message
                        frappe.model.set_value(row.doctype, row.name, "actual_available_qty", resp[1]);
                        frm.refresh_field('items');
              }
        });
    },
});
