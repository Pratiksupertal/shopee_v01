frappe.provide("erpnext.stock");

frappe.ui.form.on('Stock Entry', {
    refresh: function(frm) {
        if(frm.doc.docstatus===0) {

        // Material Request
            frm.add_custom_button(__('Material Request'), function() {
                erpnext.utils.map_current_doc({
                    method: "shopee_v01.shopee_v01.custom_script.material_request.make_stock_entry",
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
                    method: "shopee_v01.shopee_v01.custom_script.sales_order.make_stock_entry123",
                    source_doctype: "Sales Order",
                    target: frm,
//                    date_field: "schedule_date",
                    setters: {
                        company: frm.doc.company,
                    },
                })
            }, __("Get items from"));


        // Purchase Invoice
            frm.add_custom_button(__('Purchase Invoice'), function() {
                erpnext.utils.map_current_doc({
                    method: "shopee_v01.shopee_v01.custom_script.purchase_invoice.make_stock_entry",
                    source_doctype: "Purchase Invoice",
                    target: frm,
//                    date_field: "schedule_date",
                    setters: {
                        company: frm.doc.company,
                    },
                })
            }, __("Get items from"));


        // Delivery Note
            frm.add_custom_button(__('Delivery Note'), function() {
                erpnext.utils.map_current_doc({
                    method: "shopee_v01.shopee_v01.custom_script.delivery_note.make_stock_entry",
                    source_doctype: "Delivery Note",
                    target: frm,
//                    date_field: "schedule_date",
                    setters: {
                        company: frm.doc.company,
                    },
                })
            }, __("Get items from"));


        // Stock Entry
            frm.add_custom_button(__('Stock Entry'), function() {
                erpnext.utils.map_current_doc({
                    method: "shopee_v01.shopee_v01.custom_script.stock_entry.make_stock_entry",
                    source_doctype: "Stock Entry",
                    target: frm,
//                    date_field: "schedule_date",
                    setters: {
                        company: frm.doc.company,
                    },
                })
            }, __("Get items from"));


        // Main Work Order
            frm.add_custom_button(__('Main Work Order'), function() {
                erpnext.utils.map_current_doc({
                    method: "shopee_v01.shopee_v01.custom_script.main_work__order.make_stock_entry",
                    source_doctype: "Material Request",
                    target: frm,
                    date_field: "schedule_date",
                    setters: {
                        company: frm.doc.company,
                    },
                })
            }, __("Get items from"));


        // Work Order
            frm.add_custom_button(__('Work Order'), function() {
                erpnext.utils.map_current_doc({
                    method: "shopee_v01.shopee_v01.custom_script.work_order.make_stock_entry",
                    source_doctype: "Material Request",
                    target: frm,
                    date_field: "schedule_date",
                    setters: {
                        company: frm.doc.company,
                    },
//                    get_query_filters: {
//                        docstatus: 1,
//                        material_request_type: ["in", ["Material Transfer", "Material Issue"]],
//                        status: ["not in", ["Transferred", "Issued"]]
//                    }
                })
            }, __("Get items from"));

        }
    }
})
