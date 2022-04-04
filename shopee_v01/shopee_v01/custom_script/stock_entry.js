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
		before_load:function(frm) {
	  var df=frappe.meta.get_docfield("Stock Entry Detail", "basic_rate",frm.doc.name);
    var df2=frappe.meta.get_docfield("Stock Entry Detail", "basic_amount",frm.doc.name);
    var df3=frappe.meta.get_docfield("Stock Entry Detail", "amount",frm.doc.name);
    var df4=frappe.meta.get_docfield("Stock Entry Detail", "valuation_rate",frm.doc.name);
    var df5=frappe.meta.get_docfield("Stock Entry Detail", "additional_cost",frm.doc.name);
      if (frappe.user_roles.includes("Accounting Supervisor") || frappe.user_roles.includes("Accounts Manager") || frappe.user_roles.includes("CEO")) {
			 df.hidden=0;
			 df2.hidden=0;
			 df3.hidden=0;
			 df4.hidden=0;
			 df5.hidden=0;

			 frm.set_df_property("total_incoming_value", "hidden", 0);
			 frm.set_df_property("total_outgoing_value", "hidden", 0);
			 frm.set_df_property("value_difference", "hidden", 0);
			 frm.set_df_property("total_additional_cost", "hidden", 0);
			 frm.set_df_property("total_amount", "hidden", 0);
			 frm.set_df_property("total_additional_costs", "hidden", 0);
			 frm.set_df_property("additional_costs", "hidden", 0);
	  }
	  else {
			 df.hidden=1;
			 df2.hidden=1;
			 df3.hidden=1;
			 df4.hidden=1;
			 df5.hidden=1;

			 frm.set_df_property("total_incoming_value", "hidden", 1);
			 frm.set_df_property("total_outgoing_value", "hidden", 1);
			 frm.set_df_property("value_difference", "hidden", 1);
			 frm.set_df_property("total_additional_cost", "hidden", 1);
			 frm.set_df_property("total_amount", "hidden", 1);
			 frm.set_df_property("total_additional_costs", "hidden", 1);
			 frm.set_df_property("additional_costs", "hidden", 1);
	  }
	  frm.refresh_fields();
    }
})
