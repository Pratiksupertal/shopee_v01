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
           method: "shopee_v01.shopee_v01.custom_script.sales_order.size_filter",
           args: {
             item_code: row.item_code
           },
           callback: function(r) {
                var resp = r.message
                        frappe.model.set_value(row.doctype, row.name, "available_qty", resp[2]);
                        frappe.model.set_value(row.doctype, row.name, "actual_available_qty", resp[2]-resp[3]);
              }
        });
    }
});
erpnext.buying.MaterialRequestController = erpnext.buying.BuyingController.extend({
    item_code: function() {
  		// to override item code trigger from transaction.js
  	},
    items_add: function(doc, cdt, cdn) {
        var row = frappe.get_doc(cdt, cdn);
        this.frm.script_manager.copy_from_first_row("items", row, ["warehouse"]);
        if(!row.warehouse) row.warehouse = this.frm.doc.from_warehouse;

    },
    from_warehouse: function(doc) {
        this.set_warehouse_in_children(doc.items, "warehouse", doc.from_warehouse);
  	},
    set_warehouse_in_children: function(child_table, warehouse_field, warehouse) {
    		let transaction_controller = new erpnext.TransactionController();
    		transaction_controller.autofill_warehouse(child_table, warehouse_field, warehouse);
  	}
});
// for backward compatibility: combine new and previous states
$.extend(cur_frm.cscript, new erpnext.buying.MaterialRequestController({frm: cur_frm}));
