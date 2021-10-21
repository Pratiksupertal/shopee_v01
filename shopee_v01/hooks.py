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
                "Item" : "shopee_v01/shopeemarketplace_v01/doctype/custom/item.js",
                "Purchase Order":"shopee_v01/custom_script/purchase_order.js",
                "Sales Order": "shopee_v01/custom_script/sales_order.js",
                "Supplier":"shopee_v01/custom_script/supplier.js",
                "Item":"shopee_v01/custom_script/item.js"
             }
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
doctype_list_js = {"Purchase Order" : "shopee_v01/custom_script/purchase_order_list.js"}
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
    "on_submit":"shopee_v01.shopee_v01.custom_script.stock_entry.update_finished901itemsummary"
    },
    "Pick List":{
    "validate":"shopee_v01.shopee_v01.custom_script.pick_list.validate"
    },
    "Item":{
    "validate":"shopee_v01.shopee_v01.custom_script.item.validate"
    }
    # "Item Group":{
    # "autoname":"shopee_v01.shopee_v01.custom_script.item_group.autoname"
    # }
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
#	}
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
