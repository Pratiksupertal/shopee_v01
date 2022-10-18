# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version

app_name = "shopee_v01"
app_title = "Shopee V01"
app_publisher = "Pratik Mane"
app_description = "Authentication App"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "pratik@supertal.io"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
app_include_css = "/assets/css/min.logo.css"
# app_include_js = "/assets/shopee_v01/js/shopee_v01.js"

# include js, css files in header of web template
# web_include_css = "/assets/shopee_v01/css/shopee_v01.css"
# web_include_js = "/assets/shopee_v01/js/shopee_v01.js"

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views // /home/abc/workspace/mamba/frappe-bench/apps/shopee_v01/shopee_v01/shopeemarketplace_v01/doctype/custom/item.js
doctype_js = {
                "Stock Entry": "shopee_v01/custom_script/stock_entry.js",
                "Material Request": "shopee_v01/custom_script/material_request.js",
                "Item" : "shopee_v01/shopeemarketplace_v01/doctype/custom/item.js",
                "Purchase Order":"shopee_v01/custom_script/purchase_order.js",
                "Sales Order": "shopee_v01/custom_script/sales_order.js",
                "Supplier":"shopee_v01/custom_script/supplier.js",
                "Item":"shopee_v01/custom_script/item.js",
                "Payment Entry": "shopee_v01/custom_script/payment_entry.js"
             }
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
doctype_list_js = {"Purchase Order" : "shopee_v01/custom_script/purchase_order_list.js",
                    "Delivery Note" : "shopee_v01/custom_script/delivery_note_list.js"
                  }
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Website user home page (by function)
# get_website_user_home_page = "shopee_v01.utils.get_home_page"

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "shopee_v01.install.before_install"
# after_install = "shopee_v01.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "shopee_v01.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
    "ShopeeAuthorization":{
    # "after_insert":"shopee_v01.shopeemarketplace_v01.doctype.shopeeauthorization.shopeeauthorization.generate_refreshtoken"
    },
    "Purchase Order":{
    "autoname":"shopee_v01.shopee_v01.custom_script.purchase_order.autoname"
    },
    "Stock Entry":{
    "on_submit":["shopee_v01.shopee_v01.custom_script.stock_entry.finished901ItemQtySummary","shopee_v01.shopee_v01.custom_script.stock_entry.submit"],
    "on_cancel": "shopee_v01.shopee_v01.custom_script.stock_entry.cancel_update"
    },
    "Pick List":{
    "validate":"shopee_v01.shopee_v01.custom_script.pick_list.validate"
    },
    "Sales Invoice":{
    "validate":"shopee_v01.shopee_v01.custom_script.sales_invoice.validate",
    "on_submit":"shopee_v01.shopee_v01.custom_script.sales_invoice.make_customer_gl_entry"
    },
    "Sales Order":{
    "on_cancel":"shopee_v01.shopee_v01.custom_script.sales_order.cancel_update"
    },
    "Item":{
    "validate":"shopee_v01.shopee_v01.custom_script.item.validate"
    },
    "Stock Reconciliation":{
    "on_submit":["shopee_v01.shopee_v01.custom_script.stock_reconciliation.update_finished_901_item_qty_summary_stock_rec"]
    },
    "Material Request":{
    "on_cancel": "shopee_v01.shopee_v01.custom_script.material_request.cancel_update"
    },
    # "Item Group":{
    # "autoname":"shopee_v01.shopee_v01.custom_script.item_group.autoname"
    # }
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
#	}
}

# Jinja Configuration Methods
jenv = {
    "methods": [
        "get_summary_sales_invoice:shopee_v01.shopee_v01.custom_script.sales_invoice.get_summary_sales_invoice",
        "get_summary_sales_order:shopee_v01.shopee_v01.custom_script.sales_order.get_summary_sales_order",
        "get_pick_list_sales_order:shopee_v01.shopee_v01.custom_script.pick_list.get_pick_list_sales_order",
        "get_first_name:shopee_v01.shopee_v01.custom_script.purchase_order.get_first_name",
        "get_sales_order:shopee_v01.shopee_v01.custom_script.delivery_note.get_sales_order",
        "get_delivery_note:shopee_v01.shopee_v01.custom_script.delivery_note.get_delivery_note",
        "get_pick_list_sort:shopee_v01.shopee_v01.custom_script.pick_list.get_pick_list_sort",

    ]
}

# Scheduled Tasks
# ---------------

scheduler_events = {
# 	"all": [
# 		"shopee_v01.tasks.all"
# 	],
# 	"daily": [
#        "shopee_v01.tasks.daily"
# 	],
# 	"hourly": [
# 		"shopee_v01.tasks.hourly"
# 	],
# 	"weekly": [
# 		"shopee_v01.tasks.weekly"
# 	]
# 	"monthly": [
# 		"shopee_v01.tasks.monthly"
# 	]
    "cron": {
        "0 0 * * *": [
            "shopee_v01.schedular.schedular.update_finished_901_item_qty_summary"
        ]
    }
}

# Testing
# -------

# fixtures = ["Custom Field", "Property Setter","Role","Print Format", "Letter Head", "Workflow State", "Workflow Action", "Workflow", "Address Template","Web Page"]
fixtures = ["Custom Field", "Property Setter","Print Format","Role","Report","Workflow State", "Workflow Action", "Workflow"]
# before_tests = "shopee_v01.install.before_tests"

# Overriding Methods
# ------------------------------
#
override_whitelisted_methods = {
    "erpnext.controllers.item_variant.create_variant": "shopee_v01.shopee_v01.custom_script.item.create_variant",
    "erpnext.controllers.item_variant.enqueue_multiple_variant_creation":"shopee_v01.shopee_v01.custom_script.item.enqueue_multiple_variant_creation"
}
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "shopee_v01.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "shopee_v01.task.get_dashboard_data"
# }
