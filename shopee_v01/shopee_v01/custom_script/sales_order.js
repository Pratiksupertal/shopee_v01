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
              }
        });
    }
});
frappe.ui.form.on("Sales Order",{ before_load:function(frm) {
  var df=frappe.meta.get_docfield("Sales Order Item", "rate",frm.doc.name);
  var df2=frappe.meta.get_docfield("Sales Order Item", "amount",frm.doc.name);
  var df3=frappe.meta.get_docfield("Sales Order Item", "basic_rate",frm.doc.name);
  var df4=frappe.meta.get_docfield("Payment Schedule", "payment_amount",frm.doc.name);
  var df5=frappe.meta.get_docfield("Sales Taxes and Charges", "tax_amount",frm.doc.name);
  var df6=frappe.meta.get_docfield("Sales Taxes and Charges", "total",frm.doc.name);
  var df7=frappe.meta.get_docfield("Sales Team", "allocated_amount",frm.doc.name);
  var df8=frappe.meta.get_docfield("Sales Order Item", "price_list_rate",frm.doc.name);
  var df9=frappe.meta.get_docfield("Sales Order Item", "discount_and_margin",frm.doc.name);
  var df10=frappe.meta.get_docfield("Sales Order Item", "rate_with_margin",frm.doc.name);
  var df11=frappe.meta.get_docfield("Sales Order Item", "discount_amount",frm.doc.name);
  var df12=frappe.meta.get_docfield("Sales Order Item", "net_rate",frm.doc.name);
  var df13=frappe.meta.get_docfield("Sales Order Item", "net_amount",frm.doc.name);
  var df14=frappe.meta.get_docfield("Sales Order Item", "valuation_rate",frm.doc.name);
  var df15=frappe.meta.get_docfield("Sales Order Item", "billed_amt",frm.doc.name);
  var df16=frappe.meta.get_docfield("Sales Order Item", "gross_profit",frm.doc.name);
  var df17=frappe.meta.get_docfield("Sales Order Item", "blanket_order_rate",frm.doc.name);
  if (frappe.user_roles.includes("Sales User") || frappe.user_roles.includes("Accounting Supervisor") ||
       frappe.user_roles.includes("CEO")) {
     df.hidden=0;
     df2.hidden=0;
     df3.hidden=0;
     df4.hidden=0;
     df5.hidden=0;
     df6.hidden=0;
     df7.hidden=0;
     df8.hidden=0;
     df9.hidden=0;
     df10.hidden=0;
     df11.hidden=0;
     df12.hidden=0;
     df13.hidden=0;
     df14.hidden=0;
     df15.hidden=0;
     df16.hidden=0;
     df17.hidden=0;
     frm.set_df_property("total", "hidden", 0);
     frm.set_df_property("base_net_total", "hidden", 0);
     frm.set_df_property("net_total", "hidden", 0);
     frm.set_df_property("total_taxes_and_charges", "hidden", 0);
     frm.set_df_property("discount_amount", "hidden", 0);
     frm.set_df_property("grand_total", "hidden", 0);
     frm.set_df_property("rounding_adjustment", "hidden", 0);
     frm.set_df_property("rounded_total", "hidden", 0);
     frm.set_df_property("in_words", "hidden", 0);
     frm.set_df_property("advance_paid", "hidden", 0);

  }
  else {
     df.hidden=1;
     df2.hidden=1;
     df3.hidden=1;
     df4.hidden=1;
     df5.hidden=1;
     df6.hidden=1;
     df7.hidden=1;
     df8.hidden=1;
     df9.hidden=1;
     df10.hidden=1;
     df11.hidden=1;
     df12.hidden=1;
     df13.hidden=1;
     df14.hidden=1;
     df15.hidden=1;
     df16.hidden=1;
     df17.hidden=1;
     frm.set_df_property("total", "hidden", 1);
     frm.set_df_property("base_net_total", "hidden", 1);
     frm.set_df_property("net_total", "hidden", 1);
     frm.set_df_property("total_taxes_and_charges", "hidden", 1);
     frm.set_df_property("discount_amount", "hidden", 1);
     frm.set_df_property("grand_total", "hidden", 1);
     frm.set_df_property("rounding_adjustment", "hidden",1);
     frm.set_df_property("rounded_total", "hidden", 1);
     frm.set_df_property("in_words", "hidden", 1);
     frm.set_df_property("advance_paid", "hidden", 1);

  }
  frm.refresh_fields();
}
});
