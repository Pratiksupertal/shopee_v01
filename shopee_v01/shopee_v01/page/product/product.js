frappe.pages['product'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Product',
		single_column: true
	});
	console.log("----- product page intialized ------");
	controller = new frappe.product(wrapper);
	controller.product_list()
	controller.filters()
	click_function()

};
function click_function(){
	console.log("------- click function run ---------");
	$(".10000").click(function(){
		console.log("----- hiiiii");
			alert("Hello world!");
	});
}
frappe.product = Class.extend({
	init : function(wrapper){
		console.log("------ init function called --------");
		var me = this ;
		me.wrapper_page = wrapper.page
		this.page = $(wrapper).find('.layout-main-section-wrapper');


		$(frappe.render_template('main')).appendTo(this.page);
		me.product_list()
		me.click_function()

		// $('.list').html($(frappe.render_template('product')));

	},
	click_function:function(wrapper,resp){
		var me = this;
		console.log(resp);



	},
	make:function(wrapper){
		const assets = [
		 "/assets/frappe/css/frappe-datatable.css",
		 "/assets/frappe/js/lib/clusterize.min.js",
		 "/assets/frappe/js/lib/Sortable.min.js",
		 "/assets/frappe/js/lib/frappe-datatable.js"
	 ];
		frappe.require(assets, () => {
			this.make();
		});
		const me = this;
		new frappe.ui.FileUploader({
			method: 'erpnext.accounts.doctype.bank_transaction.bank_transaction_upload.upload_bank_statement',
			allow_multiple: 0,
			on_success: function(attachment, r) {
				if (!r.exc && r.message) {
					me.data = r.message;
					me.setup_transactions_dom();
					me.create_datatable();
					me.add_primary_action();
				}
			}
		})
		frappe.call({
      method: "shopee_v01.shopee_v01.page.product.product.product_list",
      args: {"item_code":me.item_code},
      callback: function(r) {
           var resp = r.message
					 me.resp = resp
					 $('.list').html($(frappe.render_template('product',{"data":resp})));
					 $(".item_code").click(function(e){
						 console.log(e.target.innerHTML);
						 		frappe.set_route("List", "Item", {
									"item_code":e.target.innerHTML
								})

					 })
					}
       });
	},
	product_list : function(wrapper){
		var me = this;
		frappe.call({
      method: "shopee_v01.shopee_v01.page.product.product.product_list",
      args: {"item_code":me.item_code},
      callback: function(r) {
           var resp = r.message
					 me.resp = resp


					 $('.list').html($(frappe.render_template('product',{"data":resp})));
					 $(".item_code").click(function(e){
						 console.log(e.target.innerHTML);
						 		frappe.set_route("List", "Item", {
									"item_code":e.target.innerHTML
								})

					 })
					}
       });
	},
	filters : function(wrapper){
		var me = this;
		var item = frappe.ui.form.make_control({
	     parent: this.page.find("#item"),
	     df: {
				 label: '<b>Item</b>',
	       fieldtype: "Link",
	       options: "Item",
	       fieldname: "item_name",
	       placeholder: __(""),

	       change:function(){
					 me.item_code = item.get_value()
					 // me.product_list()

			 }
     },
     only_input: false,
   });
	 item.set_value(me.item);
	 item.refresh();
	$('.item_code').click(function(){

	});
	}
});
