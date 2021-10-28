frappe.pages['product'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Product',
		single_column: true
	});
	// $(frappe.render_template('test')).appendTo(page.body);
	console.log("----- product page intialized ------");
	controller = new frappe.product(wrapper);
	// controller.product_list()
	controller.filters()
	controller.item_record()
	// item_record();
};
// function item_record(){
// 	console.log("----- item record called------");
// }

frappe.product = Class.extend({
	init : function(wrapper){
		console.log("------ init function called --------");
		var me = this ;
		me.wrapper_page = wrapper.page
		this.page = $(wrapper).find('.layout-main-section-wrapper');
		$(frappe.render_template('test')).appendTo(this.page);
		me.product_list()
		console.log("----- printing product_ list ");
		console.log(me.resp);
		// me.click_function()

		// $('.list').html($(frappe.render_template('product')));

	},
	item_record:function(wrapper){
		var me = this ;
		if(me.data){
			const assets = [
				"/assets/frappe/css/frappe-datatable.css",
				"/assets/frappe/js/lib/clusterize.min.js",
				"/assets/frappe/js/lib/Sortable.min.js",
				"/assets/frappe/js/lib/frappe-datatable.js"
			]
			frappe.require(assets, () => {
				var datatable = new DataTable('#datatable', {
					columns:this.data.columns,
					data:this.data.data
				});
			});
		}
	},
	product_list : function(wrapper){
		var me = this;
		frappe.call({
      method: "shopee_v01.shopee_v01.page.product.product.product_list",
      args: {"item_code":me.item_code,
							"item_group":me.item_group,
							"division_group":me.division_group
		},
			freeze:true,
      callback: function(r) {
           var resp = r.message
					 me.data = resp
					 console.log(me.data);
					 if(me.data){
						 me.item_record()
					 }
					 // $('.list').html($(frappe.render_template('product',{"data":resp})));
					 // $(".item_code").click(function(e){
						//  console.log(e.target.innerHTML);
						//  		frappe.set_route("List", "Item", {
						// 			"item_code":e.target.innerHTML
						// 		})
					 //
					 // })
					}
       });
	},
	filters : function(wrapper){
		var me = this;
		// Item code filter
		var item_code = frappe.ui.form.make_control({
	     parent: this.page.find("#item_code"),
	     df: {
				 label: '<b>Item</b>',
	       fieldtype: "Link",
	       options: "Item",
	       fieldname: "item_name",
	       placeholder: __(""),

	       change:function(){
					 me.item_code = item_code.get_value()
					 console.log("----- item code filter",item_code.get_value());
					 console.log(me.item_code);
					 // console.log("------- item_code filter");
					 me.product_list()


			 }
     },
     only_input: false,
   });
	 item_code.set_value(me.item);
	 item_code.refresh();
	 // Item group
	 var item_group = frappe.ui.form.make_control({
			parent: this.page.find("#item_group"),
			df: {
				label: '<b>Item Group</b>',
				fieldtype: "Link",
				options: "Item Group",
				fieldname: "item_group",
				placeholder: __(""),

				change:function(){
					me.item_group = item_group.get_value()
					me.product_list()
					console.log("------- item_group filter");
			}
		},
		only_input: false,
	});
	item_group.set_value(me.item);
	item_group.refresh();
	//division_group filter
	var division_group = frappe.ui.form.make_control({
		 parent: this.page.find("#division_group"),
		 df: {
			 label: '<b>Division Group</b>',
			 fieldtype: "Link",
			 options: "Division Group",
			 fieldname: "division_group",
			 placeholder: __(""),

			 change:function(){
				 me.division_group = division_group.get_value()

				 me.product_list()
				 console.log("------- division group filter");
		 }
	 },
	 only_input: false,
 });
 division_group.set_value(me.item);
 division_group.refresh();
// me.product_list()
	// $('.item_code').click(function(){
	//
	// });
	}
});
