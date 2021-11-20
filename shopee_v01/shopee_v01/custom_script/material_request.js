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
