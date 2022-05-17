frappe.provide("erpnext.buying");

{% include 'erpnext/public/js/controllers/buying.js' %};

frappe.ui.form.on("Purchase Order", {
  supplier: function (frm) {
    if (frm.doc.supplier) {
      frappe.call({
        method:
          "shopee_v01.shopee_v01.custom_script.purchase_order.warehouse_filter",
        args: { supplier: frm.doc.supplier },
        callback: function (r) {
          var resp = r.message[0];
          cur_frm.set_value("supplier_group", r.message[1]);
          frm.refresh_field("supplier_group");
          frm.set_query("set_warehouse", function () {
            return {
              filters: [
                ["Warehouse", "name", "in", resp],
                ["Warehouse", "company", "in", frm.doc.company],
              ],
            };
          });
        },
      });
    }
  },
  cara_packing_template: function (frm) {
    frappe.call({
      method: "shopee_v01.shopee_v01.custom_script.purchase_order.cara_packing",
      args: { template_name: frm.doc.cara_packing_template },
      callback: function (r) {
        var resp = r.message;
        cur_frm.set_value("cara_packing", resp);
        frm.refresh_field("cara_packing");
      },
    });
  },
  before_load: function (frm) {
    var df = frappe.meta.get_docfield(
      "Purchase Order Item",
      "rate",
      frm.doc.name
    );
    var df2 = frappe.meta.get_docfield(
      "Purchase Order Item",
      "amount",
      frm.doc.name
    );
    var df3 = frappe.meta.get_docfield(
      "Purchase Order Item",
      "last_purchase_rate",
      frm.doc.name
    );
    var df4 = frappe.meta.get_docfield(
      "Payment Schedule",
      "payment_amount",
      frm.doc.name
    );
    var df5 = frappe.meta.get_docfield(
      "Payment Schedule",
      "paid_amount",
      frm.doc.name
    );
    var df6 = frappe.meta.get_docfield(
      "Purchase Taxes and Charges",
      "tax_amount",
      frm.doc.name
    );
    var df7 = frappe.meta.get_docfield(
      "Purchase Taxes and Charges",
      "base_tax_amount",
      frm.doc.name
    );
    var df8 = frappe.meta.get_docfield(
      "Purchase Taxes and Charges",
      "total",
      frm.doc.name
    );
    var df9 = frappe.meta.get_docfield(
      "Purchase Taxes and Charges",
      "tax_amount_after_discount_amount",
      frm.doc.name
    );
    var df10 = frappe.meta.get_docfield(
      "Purchase Taxes and Charges",
      "base_tax_amount_after_discount_amount",
      frm.doc.name
    );
    var df11 = frappe.meta.get_docfield(
      "Purchase Order Item",
      "price_list_rate",
      frm.doc.name
    );
    var df12 = frappe.meta.get_docfield(
      "Purchase Order Item",
      "discount_amount",
      frm.doc.name
    );
    var df13 = frappe.meta.get_docfield(
      "Purchase Order Item",
      "net_rate",
      frm.doc.name
    );
    var df14 = frappe.meta.get_docfield(
      "Purchase Order Item",
      "net_amount",
      frm.doc.name
    );
    var df15 = frappe.meta.get_docfield(
      "Purchase Order Item",
      "billed_amt",
      frm.doc.name
    );
    var df16 = frappe.meta.get_docfield(
      "Purchase Order Item",
      "blanket_order_rate",
      frm.doc.name
    );

    if (
      frappe.user_roles.includes("ISS Purchase User") ||
      frappe.user_roles.includes("Accounting Supervisor") ||
      frappe.user_roles.includes("CEO") ||
      frappe.user_roles.includes("Purchase AP") ||
      frappe.user_roles.includes("Accounts Manager")
    ) {
      df.hidden = 0;
      df2.hidden = 0;
      df3.hidden = 0;
      df4.hidden = 0;
      df5.hidden = 0;
      df6.hidden = 0;
      df7.hidden = 0;
      df8.hidden = 0;
      df9.hidden = 0;
      df10.hidden = 0;
      df11.hidden = 0;
      df12.hidden = 0;
      df13.hidden = 0;
      df14.hidden = 0;
      df15.hidden = 0;
      df16.hidden = 0;
      frm.set_df_property("total", "hidden", 0);
      frm.set_df_property("net_total", "hidden", 0);
      frm.set_df_property("total_taxes_and_charges", "hidden", 0);
      frm.set_df_property("taxes_and_charges_added", "hidden", 0);
      frm.set_df_property("taxes_and_charges_deducted", "hidden", 0);
      frm.set_df_property("discount_amount", "hidden", 0);
      frm.set_df_property("grand_total", "hidden", 0);
      frm.set_df_property("rounding_adjustment", "hidden", 0);
      frm.set_df_property("rounded_total", "hidden", 0);
      frm.set_df_property("in_words", "hidden", 0);
      frm.set_df_property("advance_paid", "hidden", 0);
      frm.set_df_property("other_charges_calculation", "hidden", 0);
    } else {
      df.hidden = 1;
      df2.hidden = 1;
      df3.hidden = 1;
      df4.hidden = 1;
      df5.hidden = 1;
      df6.hidden = 1;
      df7.hidden = 1;
      df8.hidden = 1;
      df9.hidden = 1;
      df10.hidden = 1;
      df11.hidden = 1;
      df12.hidden = 1;
      df13.hidden = 1;
      df14.hidden = 1;
      df15.hidden = 1;
      df16.hidden = 1;
      frm.set_df_property("total", "hidden", 1);
      frm.set_df_property("net_total", "hidden", 1);
      frm.set_df_property("total_taxes_and_charges", "hidden", 1);
      frm.set_df_property("taxes_and_charges_added", "hidden", 1);
      frm.set_df_property("taxes_and_charges_deducted", "hidden", 1);
      frm.set_df_property("discount_amount", "hidden", 1);
      frm.set_df_property("grand_total", "hidden", 1);
      frm.set_df_property("rounding_adjustment", "hidden", 1);
      frm.set_df_property("rounded_total", "hidden", 1);
      frm.set_df_property("in_words", "hidden", 1);
      frm.set_df_property("advance_paid", "hidden", 1);
      frm.set_df_property("other_charges_calculation", "hidden", 1);
    }
    frm.refresh_fields();
  },
});

frappe.ui.form.on("Purchase Order Item", {
  item_code: function (frm, cdt, cdn) {
    var row = locals[cdt][cdn];
    frappe.call({
      method: "shopee_v01.shopee_v01.custom_script.purchase_order.size_filter",
      args: {
        item_code: row.item_code,
      },
      callback: function (r) {
        var resp = r.message;
        frappe.model.set_value(row.doctype, row.name, "invent_size_id", resp);
      },
    });
  },
});


erpnext.buying.PurchaseOrderController = erpnext.buying.BuyingController.extend({
	refresh: function(doc, cdt, cdn) {
		var me = this;
		this._super();
		var allow_receipt = false;
		var is_drop_ship = false;

		for (var i in cur_frm.doc.items) {
			var item = cur_frm.doc.items[i];
			if(item.delivered_by_supplier !== 1) {
				allow_receipt = true;
			} else {
				is_drop_ship = true;
			}

			if(is_drop_ship && allow_receipt) {
				break;
			}
		}

		this.frm.set_df_property("drop_ship", "hidden", !is_drop_ship);

		if(doc.docstatus == 1) {
			if(!in_list(["Closed", "Delivered"], doc.status)) {
				if(this.frm.doc.status !== 'Closed' && flt(this.frm.doc.per_received) < 100 && flt(this.frm.doc.per_billed) < 100) {
					this.frm.add_custom_button(__('Update Items'), () => {
						erpnext.utils.update_child_items({
							frm: this.frm,
							child_docname: "items",
							child_doctype: "Purchase Order Detail",
							cannot_add_row: false,
						})
					});
				}
				if (this.frm.has_perm("submit")) {
					if(flt(doc.per_billed, 6) < 100 || flt(doc.per_received, 6) < 100) {
						if (doc.status != "On Hold") {
							this.frm.add_custom_button(__('Hold'), () => this.hold_purchase_order(), __("Status"));
						} else{
							this.frm.add_custom_button(__('Resume'), () => this.unhold_purchase_order(), __("Status"));
						}
						this.frm.add_custom_button(__('Close'), () => this.close_purchase_order(), __("Status"));
					}
				}

				if(is_drop_ship && doc.status!="Delivered") {
					this.frm.add_custom_button(__('Delivered'),
						this.delivered_by_supplier, __("Status"));

					this.frm.page.set_inner_btn_group_as_primary(__("Status"));
				}
			} else if(in_list(["Closed", "Delivered"], doc.status)) {
				if (this.frm.has_perm("submit")) {
					this.frm.add_custom_button(__('Re-open'), () => this.unclose_purchase_order(), __("Status"));
				}
			}
			if(doc.status != "Closed") {
				if (doc.status != "On Hold") {
					if(flt(doc.per_received) < 100 && allow_receipt) {
						cur_frm.add_custom_button(__('Receipt'), this.make_purchase_receipt, __('Create'));
						if(doc.is_subcontracted==="Yes" && me.has_unsupplied_items()) {
							cur_frm.add_custom_button(__('Material to Supplier'),
								function() { me.make_stock_entry(); }, __("Transfer"));
						}
					}
					if(flt(doc.per_billed) < 100)
						cur_frm.add_custom_button(__('Invoice'),
							this.make_purchase_invoice, __('Create'));

					if(!doc.auto_repeat) {
						cur_frm.add_custom_button(__('Subscription'), function() {
							erpnext.utils.make_subscription(doc.doctype, doc.name)
						}, __('Create'))
					}

					if (doc.docstatus === 1 && !doc.inter_company_order_reference) {
						let me = this;
						frappe.model.with_doc("Supplier", me.frm.doc.supplier, () => {
							let supplier = frappe.model.get_doc("Supplier", me.frm.doc.supplier);
							let internal = supplier.is_internal_supplier;
							let disabled = supplier.disabled;
							if (internal === 1 && disabled === 0) {
								me.frm.add_custom_button("Inter Company Order", function() {
									me.make_inter_company_order(me.frm);
								}, __('Create'));
							}
						});
					}
				}
				if(flt(doc.per_billed)==0) {
					this.frm.add_custom_button(__('Payment Request'),
						function() { me.make_payment_request() }, __('Create'));
				}
				if(flt(doc.per_billed)==0 && doc.status != "Delivered") {
					cur_frm.add_custom_button(__('Payment'), cur_frm.cscript.make_payment_entry, __('Create'));
				}
				cur_frm.page.set_inner_btn_group_as_primary(__('Create'));
			}
		} else if(doc.docstatus===0) {
			cur_frm.cscript.add_from_mappers();
		}
	},

	make_stock_entry: function() {
		var items = $.map(cur_frm.doc.items, function(d) { return d.bom ? d.item_code : false; });
		var me = this;

		if(items.length >= 1){
			me.raw_material_data = [];
			me.show_dialog = 1;
			let title = __('Transfer Material to Supplier');
			let fields = [
			{fieldtype:'Section Break', label: __('Raw Materials')},
			{fieldname: 'sub_con_rm_items', fieldtype: 'Table', label: __('Items'),
				fields: [
					{
						fieldtype:'Data',
						fieldname:'item_code',
						label: __('Item'),
						read_only:1,
						in_list_view:1
					},
					{
						fieldtype:'Data',
						fieldname:'rm_item_code',
						label: __('Raw Material'),
						read_only:1,
						in_list_view:1
					},
					{
						fieldtype:'Float',
						read_only:1,
						fieldname:'qty',
						label: __('Quantity'),
						read_only:1,
						in_list_view:1
					},
					{
						fieldtype:'Data',
						read_only:1,
						fieldname:'warehouse',
						label: __('Reserve Warehouse'),
						in_list_view:1
					},
					{
						fieldtype:'Float',
						read_only:1,
						fieldname:'rate',
						label: __('Rate'),
						hidden:1
					},
					{
						fieldtype:'Float',
						read_only:1,
						fieldname:'amount',
						label: __('Amount'),
						hidden:1
					},
					{
						fieldtype:'Link',
						read_only:1,
						fieldname:'uom',
						label: __('UOM'),
						hidden:1
					}
				],
				data: me.raw_material_data,
				get_data: function() {
					return me.raw_material_data;
				}
			}
		]

		me.dialog = new frappe.ui.Dialog({
			title: title, fields: fields
		});

		// updating the qty to supplied_qty from (item.required_qty - item.supplied_qty)
		if (me.frm.doc['supplied_items']) {
			me.frm.doc['supplied_items'].forEach((item, index) => {
			if (item.rm_item_code && item.main_item_code && item.supplied_qty != 0) {
					me.raw_material_data.push ({
						'name':item.name,
						'item_code': item.main_item_code,
						'rm_item_code': item.rm_item_code,
						'item_name': item.rm_item_code,
						'qty': item.supplied_qty,
						'warehouse':item.reserve_warehouse,
						'rate':item.rate,
						'amount':item.amount,
						'stock_uom':item.stock_uom
					});
					me.dialog.fields_dict.sub_con_rm_items.grid.refresh();
				}
			})
		}

		me.dialog.get_field('sub_con_rm_items').check_all_rows()

		me.dialog.show()
		this.dialog.set_primary_action(__('Transfer'), function() {
			me.values = me.dialog.get_values();
			if(me.values) {
				me.values.sub_con_rm_items.map((row,i) => {
					if (!row.item_code || !row.rm_item_code || !row.warehouse || !row.qty || row.qty === 0) {
						frappe.throw(__("Item Code, warehouse, quantity are required on row" + (i+1)));
					}
				})
				me._make_rm_stock_entry(me.dialog.fields_dict.sub_con_rm_items.grid.get_selected_children())
				me.dialog.hide()
				}
			});
		}

		me.dialog.get_close_btn().on('click', () => {
			me.dialog.hide();
		});

	},

	
});

// for backward compatibility: combine new and previous states
$.extend(cur_frm.cscript, new erpnext.buying.PurchaseOrderController({frm: cur_frm}));


frappe.ui.form.on('Purchase Order', {
	refresh:function(frm){
	    if(frm.doc.docstatus==1){
          var start_btn = frm.add_custom_button(__('Create Pick List'), function() {
                frm.trigger("create_pick_list");
          });
          start_btn.addClass('btn-primary');
        }
    },

    create_pick_list: function(frm, purpose='Material Transfer for Manufacture') {
        let pick_list_data = [];
        let max_qty = frm.doc.total_qty/frm.doc.items.length
        const dialog = frappe.prompt({
            fieldname: 'input_qty',
            fieldtype: 'Data',
            label: __('Qty for Material Transfer for Manufacture'),
            description: __('Max: {0}', [max_qty]),
            data: pick_list_data,
            in_place_edit: true,
            get_data: function() {

            return pick_list_data;
            }
            }, function(data) {
            console.log(data.input_qty);
            frappe.call({
             method: "shopee_v01.shopee_v01.custom_script.purchase_order.create_pick_list",
             args: {
                'source_name': frm.doc.name,
                'input_qty': data.input_qty,
                'total_qty': frm.doc.total_qty
             }
            });
        }, __("Create Pick List"), __("Create"));
    },
});

