// Copyright (c) 2021, Pratik Mane and contributors
// For license information, please see license.txt

frappe.ui.form.on('Main Work Order', {
  refresh:function(frm){

    console.log(frm.doc);

    if(frm.doc.docstatus==1){
      var start_btn = frm.add_custom_button(__('Create Pick List'), function() {
        frm.trigger("start_work_order");
      });
      start_btn.addClass('btn-primary');

       var job_card_btn = frm.add_custom_button(__('Job Card'),
           function() {
                        frm.trigger("start_job_card");

  					});

      job_card_btn.addClass('btn-primary');

      var job_card_btn = frm.add_custom_button(__('In Progress Job Card'),
           function() {
                        frm.trigger("in_progress_job_card");

  					});

      job_card_btn.addClass('btn-primary');
    };

  },


  start_job_card:function(frm){
		let job_card_list = [];

    const dialog = frappe.prompt({fieldname: 'job_card_list', fieldtype: 'Table', label: __('Job Card'),
      fields: [
        {
          fieldtype:'Data',
          fieldname: 'job_card',
          label: __('Job Card'),
          options:'Job Card',
          read_only:1,
          in_list_view:1
        },

        {
          fieldtype:'Link',
          fieldname: 'work_order',
          label: __('Work Order'),
          options:'Work Order',
          read_only:1,
          in_list_view:1
        },

        {
          fieldtype:'Data',
          fieldname:'status',
          label: __('Status'),
          read_only:1,
          in_list_view:1
        },

        {
          fieldtype:'Float',
          fieldname:'qty',
          label: __('Qty'),
          read_only:1,
          in_list_view:1
        },

        {
          fieldtype:'Float',
          fieldname:'total_completed_qty',
          label: __('Completed Qty'),
          read_only:1,
          in_list_view:1
        },

      ],
      data: job_card_list,
      in_place_edit: true,
      get_data: function() {

        return job_card_list;
      }
    }, function(data) {
    console.log(data);
       frappe.call({
          method: "shopee_v01.shopee_v01.doctype.main_work_order.main_work_order.start_job_cards",
          args: {
             job_card_list: job_card_list
          },
       });

    }, __("Select Job Card"), __("Start"));

    dialog.fields_dict["job_card_list"].grid.wrapper.find('.grid-add-row').hide();

    frappe.call({
      method: "shopee_v01.shopee_v01.doctype.main_work_order.main_work_order.job_card_data",
      args: {
        main_work_order: frm.doc.name,
      },
      freeze: true,
      callback: function(r) {
          var resp = r.message;
          console.log(resp);
          resp.forEach(data => {
              console.log(data);
              console.log(data.name);
              dialog.fields_dict.job_card_list.df.data.push({
                'job_card': data.operation,
                'name': data.name,
                'work_order': data.work_order,
                'qty': data.for_quantity,
                'status': data.status,
                'total_completed_qty': data.total_completed_qty,

              });
          });
          dialog.fields_dict.job_card_list.grid.refresh();
         }
       });
		dialog.fields_dict.job_card_list.grid.refresh();
  },


  in_progress_job_card:function(frm){
		let in_progress_job_card_list = [];

    const dialog = frappe.prompt({fieldname: 'in_progress_job_card_list', fieldtype: 'Table', label: __('Job Card'),
      fields: [
        {
          fieldtype:'Data',
          fieldname: 'job_card',
          label: __('Job Card'),
          options:'Job Card',
          read_only:1,
          in_list_view:1
        },

        {
          fieldtype:'Link',
          fieldname: 'work_order',
          label: __('Work Order'),
          options:'Work Order',
          read_only:1,
          in_list_view:1
        },

        {
          fieldtype:'Float',
          fieldname:'qty',
          label: __('Qty'),
          read_only:1,
          in_list_view:1
        },

        {
          fieldtype:'Float',
          fieldname:'total_completed_qty',
          label: __('Completed Qty'),
          read_only:1,
          in_list_view:1
        },
        {
          fieldtype:'Float',
          fieldname:'input_qty',
          label: __('Input Qty'),
          read_only:0,
          in_list_view:1,
        },

      ],
      data: in_progress_job_card_list,
      in_place_edit: true,
      get_data: function() {

        return in_progress_job_card_list;
      }
    }, function(data) {
    console.log(data);
       frappe.call({
          method: "shopee_v01.shopee_v01.doctype.main_work_order.main_work_order.stop_job_cards",
          args: {
             in_progress_job_card_list: in_progress_job_card_list
          },
       });
    }, __("Select Job Card"), __("Stop"));

    dialog.fields_dict["in_progress_job_card_list"].grid.wrapper.find('.grid-add-row').hide();

    frappe.call({
      method: "shopee_v01.shopee_v01.doctype.main_work_order.main_work_order.in_progress_job_card_data",
      args: {
        main_work_order: frm.doc.name,
      },
      freeze: true,
      callback: function(r) {
          var resp = r.message;
          console.log(resp);
          resp.forEach(data => {
              console.log(data);
              console.log(data.name);
              dialog.fields_dict.in_progress_job_card_list.df.data.push({
                'job_card': data.operation,
                'name': data.name,
                'work_order': data.work_order,
                'qty': data.for_quantity,
                'status': data.status,
                'total_completed_qty': data.total_completed_qty,

              });
          });
          dialog.fields_dict.in_progress_job_card_list.grid.refresh();
         }
       });
		dialog.fields_dict.in_progress_job_card_list.grid.refresh();
  },



 start_work_order:function(frm){
		let work_order_data = [];

    const dialog = frappe.prompt({fieldname: 'order_list', fieldtype: 'Table', label: __('Work Order'),
      fields: [
        {
          fieldtype:'Link',
          fieldname: 'name',
          label: __('Work Order'),
          options:'Work Order',
          read_only:1,
          in_list_view:1
        },
        {
          fieldtype:'Float',
          fieldname:'qty',
          label: __('Qty'),
          read_only:1,
          in_list_view:1
        }
      ],
      data: work_order_data,
      in_place_edit: true,
      get_data: function() {

        return work_order_data;
      }
    }, function(data) {
    console.log(data);
       frappe.call({
         method: "shopee_v01.shopee_v01.doctype.main_work_order.main_work_order.pick_lists",
         args: {
            work_order_list: data.order_list
         }
       });
    }, __("Select Work Orders"), __("Create Pick List"));

    dialog.fields_dict["order_list"].grid.wrapper.find('.grid-add-row').hide();

    frappe.call({
      method: "shopee_v01.shopee_v01.doctype.main_work_order.main_work_order.workorder_data",
      args: {
        main_work_order: frm.doc.name,
      },
      freeze: true,
      callback: function(r) {
          var resp = r.message;
          console.log(resp);
          resp.forEach(data => {
              console.log(data);
              console.log(data.name);
              dialog.fields_dict.order_list.df.data.push({
                'name': data.name,
                'qty': data.qty
              });
          });
          dialog.fields_dict.order_list.grid.refresh();
         }
       });

		dialog.fields_dict.order_list.grid.refresh();
    },


  setup: function(frm) {

  },
  onload:function(frm){
    //
    frm.set_query("wip_warehouse", function() {
                        return {
                                filters: {
                                        'company': frm.doc.company,
                                }
                        };
                });

                    frm.set_query("fg_warehouse", function() {
                        return {
                                filters: {
                                        'company': frm.doc.company,
                                        'is_group': 0
                                }
                        };
                });

                    frm.set_query("scrap_warehouse", function() {
                        return {
                                filters: {
                                        'company': frm.doc.company,
                                        'is_group': 0
                                }
                        };
                });

  },

  packing_template:function(frm){
    frappe.call({
      method: "shopee_v01.shopee_v01.custom_script.purchase_order.cara_packing",
      args: {"template_name":frm.doc.packing_template},
      callback: function(r) {
           var resp = r.message
           cur_frm.set_value("packing", resp);
           frm.refresh_field("packing");
         }
       });
  }
});

// Child table Work Order Item Details trigger

frappe.ui.form.on('Work Order Item Details', {
	bom: function(frm, cdt, cdn){
	var row = locals[cdt][cdn];
	frm.call({
    doc:frm.doc,
    method: "fetch_required_item",
    freeze: true,
    args: {
      bom: row.bom
    },
    callback: function(r) {
         var resp = r.message
         for(var i = 0; i < resp.item_code.length; i++) {
           var childTable = cur_frm.add_child("required_item");
           childTable.item_code = resp.item_code[i];
           cur_frm.refresh_fields("required_item");
         };
       }
     });
	},
//  make_se: function(frm, purpose) {
//    this.show_prompt_for_qty_input(frm, purpose)
//			.then(data => {
//				return frappe.xcall('erpnext.manufacturing.doctype.work_order.work_order.make_stock_entry', {
//					'work_order_id': frm.doc.name,
//					'purpose': purpose,
//					'qty': data.qty
//				});
//			}).then(stock_entry => {
//				frappe.model.sync(stock_entry);
//				frappe.set_route('Form', stock_entry.doctype, stock_entry.name);
//			});
//
//	},
    create_pick_list: function(frm, purpose='Material Transfer for Manufacture') {
		this.show_prompt_for_qty_input(frm, purpose)
			.then(data => {
				return frappe.xcall('erpnext.manufacturing.doctype.work_order.work_order.create_pick_list', {
					'source_name': frm.doc.name,
					'for_qty': data.qty
				});
			}).then(pick_list => {
				frappe.model.sync(pick_list);
				frappe.set_route('Form', pick_list.doctype, pick_list.name);
			});
	},
  show_prompt_for_qty_input: function(frm, purpose) {
    let max = this.get_max_transferable_qty(frm, purpose);
		return new Promise((resolve, reject) => {
			frappe.prompt({
				fieldtype: 'Float',
				label: __('Qty for {0}', [purpose]),
				fieldname: 'qty',
				description: __('Max: {0}', [max]),
				default: max
			}, data => {
				max += (frm.doc.qty * (frm.doc.__onload.overproduction_percentage || 0.0)) / 100;

				if (data.qty > max) {
					frappe.msgprint(__('Quantity must not be more than {0}', [max]));
					reject();
				}
				data.purpose = purpose;
				resolve(data);
			}, __('Select Quantity'), __('Create'));
		});
	},
  get_max_transferable_qty: (frm, purpose) => {
		let max = 0;
		if (frm.doc.skip_transfer) {
			max = flt(frm.doc.qty) - flt(frm.doc.produced_qty);
		} else {
			if (purpose === 'Manufacture') {
				max = flt(frm.doc.material_transferred_for_manufacturing) - flt(frm.doc.produced_qty);
			} else {
				max = flt(frm.doc.qty) - flt(frm.doc.material_transferred_for_manufacturing);
			}
		}
		return flt(max, precision('qty'));
	}

});
