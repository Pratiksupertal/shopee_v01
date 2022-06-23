frappe.provide("erpnext.stock");

frappe.ui.form.on("Stock Entry", {
	refresh: function(frm) {
        frm.remove_custom_button("Material Request", 'Get items from');
	}
});

frappe.ui.form.on('Stock Entry', {
    refresh: function(frm) {
        if(frm.doc.docstatus===0) {

        // Purchase Order
            frm.add_custom_button(__('Purchase Order'), function() {
                erpnext.utils.map_current_doc({
                    method: "shopee_v01.shopee_v01.custom_script.purchase_order.make_stock_entry",
                    source_doctype: "Purchase Order",
                    target: frm,
                    date_field: "schedule_date",
                    setters: {
                        company: frm.doc.company,
                    },
                })
            }, __("Get items from"));


        // Sales Order
            frm.add_custom_button(__('Sales Order'), function() {
                erpnext.utils.map_current_doc({
                    method: "shopee_v01.shopee_v01.custom_script.sales_order.make_stock_entry",
                    source_doctype: "Sales Order",
                    target: frm,
//                    date_field: "schedule_date",
                    setters: {
                        company: frm.doc.company,
                    },
                })
            }, __("Get items from"));

        // Material Request
            frm.add_custom_button(__('Material Request'), function() {
                erpnext.utils.map_current_doc({
                    method: "erpnext.stock.doctype.material_request.material_request.make_stock_entry",
                    source_doctype: "Material Request",
                    target: frm,
                    date_field: "schedule_date",
                    setters: {
                        company: frm.doc.company,
                        customer: frm.doc.customer,
                    },
                    get_query_filters: {
                        docstatus: 1,
                        material_request_type: ["in", ["Material Transfer", "Material Issue"]],
                        status: ["not in", ["Transferred", "Issued"]]
                    }
                })
            }, __("Get items from"));

        }
    },
})
