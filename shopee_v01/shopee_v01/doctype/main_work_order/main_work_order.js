// Copyright (c) 2021, Pratik Mane and contributors
// For license information, please see license.txt

frappe.ui.form.on('Main Work Order', {
  refresh:function(frm){
    if(frm.doc.docstatus==1){
    var start_btn = frm.add_custom_button(__('Start'), function() {
    frm.trigger("start_work_order");
//      erpnext.work_order.make_wo_table(frm)
//      erpnext.work_order.make_se(frm, 'Material Transfer for Manufacture');
    });
      start_btn.addClass('btn-primary');
    };
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
// frappe.ui.form.on('Work Order Item Details', {
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
	}
});
erpnext.work_order = {
  make_wo_table:function(frm){
    let qty = 0;
    let operations_data = [];
    frappe.call({
      method: "shopee_v01.shopee_v01.doctype.main_work_order.main_work_order.workorder_data",
      freeze: true,
      args: {
            'main_work_order': frm.doc.name,
//            'operations': data.operations,
          },
      callback: function(r) {
           var resp = r.message;
           console.log(resp);
//           for(var i = 0; i < resp.item_code.length; i++) {
//             var childTable = cur_frm.add_child("required_item");
//             childTable.item_code = resp.item_code[i];
//             cur_frm.refresh_fields("required_item");
//           };
         }
       });
       start_work_order:function(frm){

    const dialog = frappe.prompt({fieldname: 'name', fieldtype: 'Table', label: __('Work Order'),
      fields: [
        {
          fieldtype:'Link',
//          operation:['MFG-WO-2022-00016','MFG-WO-2022-00015'],
          fieldname: 'name',
          label: __('Work Order'),
          read_only:1,
          in_list_view:1
        },
        {
          fieldtype:'Link',
          fieldname:'workstation',
          label: __('Qty'),
          read_only:1,
          in_list_view:1
          },
        {
          fieldtype:'Float',
          fieldname:'qty',
          label: __('Quantity to Manufacture'),
          read_only:0,
          in_list_view:1,
        },
      ],
      data: work_order_data,
      in_place_edit: true,
      get_data: function() {
        return work_order_data;
      }
    }, function(data) {
      frappe.call({
        method: "shopee_v01.shopee_v01.doctype.main_work_order.main_work_order.workorder_data",
        args: {
          work_order: frm.doc.name,
          operations: data.operations,
        }
      });
    }, __("Select Work Orders"), __("Start"));
    }

    dialog.fields_dict["operations"].grid.wrapper.find('.grid-add-row').hide();

    var pending_qty = 0;
//    frm.doc.operations.forEach(data => {
//      if(data.completed_qty != frm.doc.qty) {
//        pending_qty = frm.doc.qty - flt(data.completed_qty);
//
//        dialog.fields_dict.operations.df.data.push({
//          'name': data.name,
//          'operation': data.operation,
//          'workstation': data.workstation,
//          'qty': pending_qty,
//          'pending_qty': pending_qty,
//        });
//      }
//    });
    dialog.fields_dict.operations.grid.refresh();
  },
  make_se: function(frm, purpose) {
    this.show_prompt_for_qty_input(frm, purpose)
			.then(data => {
				return frappe.xcall('erpnext.manufacturing.doctype.work_order.work_order.make_stock_entry', {
					'work_order_id': frm.doc.name,
					'purpose': purpose,
					'qty': data.qty
				});
			}).then(stock_entry => {
				frappe.model.sync(stock_entry);
				frappe.set_route('Form', stock_entry.doctype, stock_entry.name);
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
	},

};

