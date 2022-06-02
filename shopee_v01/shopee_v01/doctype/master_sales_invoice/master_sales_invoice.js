frappe.ui.form.on('Master Sales Invoice', {
	on_change: function(frm) {
		frm.set_value("count", Math.random()*100);
		frm.refresh_fields();
	},

	get_outstanding_invoice: function(frm) {
		const today = frappe.datetime.get_today();
		const fields = [
			{fieldtype:"Section Break", label: __("Posting Date")},
			{fieldtype:"Date", label: __("From Date"),
				fieldname:"from_posting_date", default:frappe.datetime.add_days(today, -30)},
			{fieldtype:"Column Break"},
			{fieldtype:"Date", label: __("To Date"), fieldname:"to_posting_date", default:today},
			{fieldtype:"Section Break", label: __("Due Date")},
			{fieldtype:"Date", label: __("From Date"), fieldname:"from_due_date"},
			{fieldtype:"Column Break"},
			{fieldtype:"Date", label: __("To Date"), fieldname:"to_due_date"},
			{fieldtype:"Section Break", label: __("Outstanding Amount")},
			{fieldtype:"Float", label: __("Greater Than Amount"),
				fieldname:"outstanding_amt_greater_than", default: 0},
			{fieldtype:"Column Break"},
			{fieldtype:"Float", label: __("Less Than Amount"), fieldname:"outstanding_amt_less_than"},
			{fieldtype:"Section Break"},
			{fieldtype:"Data", label: __("Source App Name"), options: 'Source App Name', fieldname:"source_app_name"},
            {fieldtype:"Column Break"},
			{fieldtype:"Data", label: __("Store"), options: 'Store', fieldname:"store"},
			{fieldtype:"Section Break"},
			{fieldtype:"Data", label: __("Department Category"), options: 'Department Category', fieldname:"department_category"}
		];

		frappe.prompt(fields, function(filters){
			frappe.flags.allocate_payment_amount = true;
			frm.events.validate_filters_data(frm, filters);
			frm.events.get_outstanding_documents(frm, filters);
		}, __("Filters"), __("Get Outstanding Documents"));
	},

	validate_filters_data: function(frm, filters) {
		const fields = {
			'Posting Date': ['from_posting_date', 'to_posting_date'],
			'Due Date': ['from_posting_date', 'to_posting_date'],
			'Advance Amount': ['from_posting_date', 'to_posting_date'],
		};

		for (let key in fields) {
			let from_field = fields[key][0];
			let to_field = fields[key][1];

			if (filters[from_field] && !filters[to_field]) {
				frappe.throw(__("Error: {0} is mandatory field",
					[to_field.replace(/_/g, " ")]
				));
			} else if (filters[from_field] && filters[from_field] > filters[to_field]) {
				frappe.throw(__("{0}: {1} must be less than {2}",
					[key, from_field.replace(/_/g, " "), to_field.replace(/_/g, " ")]
				));
			}
		}
	},

    get_outstanding_documents: function(frm, filters) {
		frm.clear_table("references");

		var args = {
			"posting_date": frm.doc.posting_date,
			"cost_center": frm.doc.cost_center
		}

		for (let key in filters) {
			args[key] = filters[key];
		}

		return  frappe.call({
			method: 'shopee_v01.shopee_v01.doctype.master_sales_invoice.master_sales_invoice.get_outstanding_reference_documents',
			args: {
				args:args
			},
			callback: function(r, rt) {
				if(r.message) {
					console.log(r.message);
					var count = 0;
					var total_qty = 0;
					var total_amount = 0;

					$.each(r.message, function(i, d) {
						var c = frm.add_child("references");
						c.reference_doctype = d.voucher_type;
						c.reference_name = d.voucher_no;
						c.due_date = d.due_date
						c.total_amount = d.invoice_amount;
						c.outstanding_amount = d.outstanding_amount;
						c.bill_no = d.bill_no;
						c.exchange_rate = 1;
						count += 1;
						total_qty += parseInt(d.qty),
						total_amount += flt(d.outstanding_amount);
					});
					frm.set_value("count", count);
					frm.set_value("total_qty", total_qty);
					frm.set_value("total_amount", total_amount);
					frm.set_value("subtotal", total_amount);
					frm.set_value("subtotal_after_tax", total_amount);
					frm.set_value("final_total", total_amount);
					frm.refresh_fields();
				}
			}
		});
	},

	discount_percentage: function(frm) {
		if (frm.doc.discount_percentage != null) {
			frm.doc.discount_amount = (parseInt(frm.doc.total_amount) / 100.0) * parseInt(frm.doc.discount_percentage);
			frm.doc.subtotal = parseInt(frm.doc.total_amount) - parseInt(frm.doc.discount_amount);
			frm.set_value("discount_amount", frm.doc.discount_amount);
			frm.set_value("subtotal", frm.doc.subtotal);
			frm.set_value("subtotal_after_tax", frm.doc.subtotal);
			frm.set_value("final_total", frm.doc.subtotal);
			frm.refresh_fields();
		}
	},

	tax_percent: function(frm) {
		if (frm.doc.tax_percent != null) {
			frm.doc.tax_amount = (parseInt(frm.doc.subtotal) / 100.0) * parseInt(frm.doc.tax_percent);
			frm.doc.subtotal_after_tax = parseInt(frm.doc.subtotal) + parseInt(frm.doc.tax_amount);
			frm.set_value("tax_amount", frm.doc.tax_amount);
			frm.set_value("subtotal_after_tax", frm.doc.subtotal_after_tax);
			frm.set_value("final_total", frm.doc.subtotal_after_tax);
			frm.refresh_fields();
		}
	}
});
