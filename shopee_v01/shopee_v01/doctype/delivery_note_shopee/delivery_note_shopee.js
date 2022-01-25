frappe.ui.form.on('Delivery Note Shopee', {
  	// refresh: function(frm) {
    refresh(frm) {
            frm.add_custom_button(__('Purchase Order'),
  					function() {
  						show_purchase_order_dialog(frm);
  					}, __("Get items from"));
  		  frm.add_custom_button(__('CMT'),
  					function() {
  						show_CMT_dialog(frm);
  					}, __("Get items from"));
  	}
  	// }
  });

  var show_purchase_order_dialog = function(frm){

      new frappe.ui.form.MultiSelectDialog({
          doctype: "Purchase Order",
          target: cur_frm,
          setters: [{
              fieldname: 'supplier_name',
              fieldtype: 'Data',
              label: __('Supplier Name')
          }],
           get_query() {
           return {
              filters: { docstatus: ['=', 1] }
          }
      },
          action(selections) {
              if(selections.length == 0){
              }else{
                  for (var ia = 0; ia < selections.length; ia=ia+1) {
                    console.log(selections);
                      frappe.call({
                          method: "shopee_v01.shopee_v01.doctype.delivery_note_shopee.delivery_note_shopee.get_item_purchase_order",
                          args: {
                              name: selections[ia]
                          },
                          callback: function(res){
                              //console.log("test Res 4");
                              //console.log(res);
                              //console.log(res.message.length);
                              if (res && res.message){
                                  for (var i = 0; i<res.message.length; i=i+1) {
                                      var tflag=0;
                                      //console.log("check here");
                                      var row = frm.add_child("items");
                                      //console.log("Go in here");
                                      //console.log(res.message[i].item_code);
                                      //console.log(frm.doc.items);
                                      frappe.model.set_value(row.doctype, row.name, 'item_code', res.message[i].item_code)
                                      frappe.model.set_value(row.doctype, row.name, 'item_name', res.message[i].item_name);
                                      frappe.model.set_value(row.doctype, row.name, 'qty', res.message[i].qty);
                                      frappe.model.set_value(row.doctype, row.name, 'uom', res.message[i].uom);
                                      frappe.model.set_value(row.doctype, row.name, 'stock_uom', res.message[i].stock_uom);
                                      frappe.model.set_value(row.doctype, row.name, 'rate', res.message[i].rate);
                                      frappe.model.set_value(row.doctype, row.name, 'amount', res.message[i].amount);
                                      frappe.model.set_value(row.doctype, row.name, 'conversion_factor', res.message[i].conversion_factor);
                                      frappe.model.set_value(row.doctype, row.name, 'description', res.message[i].description);
                                      frm.refresh_field('items');
                                  }
                              }
                          }
                      })
                  }

                  for (var ia = 0; ia < selections.length; ia=ia+1) {
                    console.log(selections);
                      frappe.call({
                          method: "shopee_v01.shopee_v01.doctype.delivery_note_shopee.delivery_note_shopee.get_purchase_order",
                          args: {
                              name: selections[ia]
                          },
                          callback: function(res2){
                              console.log("test Res 3");
                              //console.log(res2);
                              //console.log(res2.message.length);
                              if (res2 && res2.message){
                                  for (var i = 0; i<res2.message.length; i=i+1) {
  									                  //console.log(res2.message[i].supplier);
                                      //console.log(res2.message[i].supplier_address);
                                      var row = frm.add_child("taxes");
                                      frm.set_value({supplier: res2.message[i].supplier, supplier_address: res2.message[i].supplier_address,company: res2.message[i].company,po_address_display: res2.message[i].address_display,po_contact_person: res2.message[i].contact_person,total: res2.message[i].total,net_total: res2.message[i].net_total,base_total_taxes_and_charges: res2.message[i].base_total_taxes_and_charges,grand_total: res2.message[i].grand_total,currency: res2.message[i].currency,conversion_rate: res2.message[i].conversion_rate,total_qty: res2.message[i].total_qty,total_net_weight: res2.message[i].total_net_weight,base_total: res2.message[i].base_total,base_net_total: res2.message[i].base_net_total,total_taxes_and_charges: res2.message[i].total_taxes_and_charges,base_rounded_total: res2.message[i].base_rounded_total,rounded_total: res2.message[i].rounded_total,base_in_words: res2.message[i].base_in_words,po_reference: res2.message[i].name});
                                      frm.refresh();
                                  }
                              }
                          }
                      })
                  }
                  cur_dialog.hide();
              }
          }
      });
  	}

    var show_CMT_dialog = function(frm){

        new frappe.ui.form.MultiSelectDialog({
            doctype: "Main Work Order",
            target: cur_frm,
            setters: [
		      {
            fieldname: 'is_external',
            fieldtype: 'Data',
            label: __('Is External')
          },
		      ],
             get_query() {
             return {
                filters: { docstatus: ['=', 1] }
            }
        },
            action(selections) {
                if(selections.length == 0){
                }else{
                    var tot_qty = 0;
				            var tot_amount = 0;
                    for (var ia = 0; ia < selections.length; ia=ia+1) {
                      console.log(selections);
                        frappe.call({
                            method: "shopee_v01.shopee_v01.doctype.delivery_note_shopee.delivery_note_shopee.get_item_CMT",
                            args: {
                                name: selections[ia]
                            },
                            callback: function(res){
                                //console.log("test Res 4");
                                //console.log(res);
                                //console.log(res.message.length);
                                if (res && res.message){
                                    for (var i = 0; i<res.message.length; i=i+1) {
                                        var tflag=0;
                                        //console.log("check here");
                                        tot_qty = tot_qty + res.message[i].qty;
									                      tot_amount = tot_amount + res.message[i].amount;
                                        var row = frm.add_child("items");
                                        //console.log("Go in here");
                                        //console.log(res.message[i].item_code);
                                        //console.log(frm.doc.items);
                                        frappe.model.set_value(row.doctype, row.name, 'item_code', res.message[i].item_code)
                                        frappe.model.set_value(row.doctype, row.name, 'item_name', res.message[i].item_name);
                                        frappe.model.set_value(row.doctype, row.name, 'qty', res.message[i].qty);
                                        frappe.model.set_value(row.doctype, row.name, 'uom', res.message[i].uom);
                                        frappe.model.set_value(row.doctype, row.name, 'stock_uom', res.message[i].stock_uom);
                                        frappe.model.set_value(row.doctype, row.name, 'rate', res.message[i].rate);
                                        frappe.model.set_value(row.doctype, row.name, 'amount', res.message[i].amount);
                                        frappe.model.set_value(row.doctype, row.name, 'conversion_factor', res.message[i].conversion_factor);
                                        frappe.model.set_value(row.doctype, row.name, 'description', res.message[i].description);
                                        frm.refresh_field('items');
                                    }
                                }
                            }
                        })
                    }

                    for (var ia = 0; ia < selections.length; ia=ia+1) {
                    console.log(selections);
                    frappe.call({
                        method: "shopee_v01.shopee_v01.doctype.delivery_note_shopee.delivery_note_shopee.get_item_CMT_Address_Supplier",
                        args: {
                            name: selections[ia]
                        },
                        callback: function(res2){
                            console.log("test Res 3");
                            console.log(res2);
                            console.log(res2.message.length);
                            if (res2 && res2.message){
                                for (var i = 0; i<res2.message.length; i=i+1) {
									                  console.log(res2.message[i].supplier);
                                    console.log(res2.message[i].supplier_address);
                                    frm.set_value({mwo_name: res2.message[i].name,supplier: res2.message[i].supplier, supplier_address: res2.message[i].supplier_address,company: res2.message[i].company,po_address_display: res2.message[i].address_display,po_contact_person: res2.message[i].contact_person,total: tot_amount,grand_total: tot_amount,total_qty: tot_qty,rounded_total: tot_amount});
                                    frm.refresh();
                                    }
                                }
                            }
                        })
                    }

                    cur_dialog.hide();
                }
            }
        });
    	}
