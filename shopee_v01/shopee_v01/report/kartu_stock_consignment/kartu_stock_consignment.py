# Copyright (c) 2013, Pratik Mane and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import msgprint, _
from frappe.utils import flt
import logging

def execute(filters=None):
    if not filters: filters = {}

    columns = get_columns(filters)
    entries = get_entries(filters)
    data = []
    count = 1
    stock_size = ""
    vcompare = ""
    item_name = ""
    warehouse = ""
    size_group = ""
    available_value = 0
    actual_value = 0
    available_actual = ""
    total = 0
    total2 = 0
    strjumlah = ""
    for d in entries:
        if vcompare != d.compare_name:
            if count == 1:
                item_name = d.item_name
                size_group = d.size_group
                stock_size += d.attribute_value + " = " + str(d.stock_akhir)
                available_value = get_available_value(d.item_code)
                actual_value = available_value - get_value_of_quantity_of_MRI(d.item_code) - get_value_of_quantity_of_SOI(d.item_code)
                available_actual += d.attribute_value + " = " + str(int(available_value)) + "/" + str(int(actual_value))
                warehouse = d.warehouse
                vcompare = d.compare_name
                total += d.stock_akhir
                total2 += actual_value
                count = 2
            else:
                data.append([item_name, size_group, available_actual, total2, warehouse])
                item_name = d.item_name
                size_group = d.size_group
                stock_size = ""
                stock_size += d.attribute_value + " = " + str(d.stock_akhir)
                available_actual = ""
                available_value = get_available_value(d.item_code)
                actual_value = available_value - get_value_of_quantity_of_MRI(d.item_code) - get_value_of_quantity_of_SOI(d.item_code)
                available_actual += d.attribute_value + " = " + str(int(available_value)) + "/" + str(int(actual_value))
                warehouse = d.warehouse
                total = 0
                total2 = 0;
                total2 += actual_value
                total += d.stock_akhir
                vcompare = d.compare_name
        else:
            stock_size += " | " + d.attribute_value + " = " + str(d.stock_akhir)
            available_value = get_available_value(d.item_code)
            actual_value = available_value - get_value_of_quantity_of_MRI(d.item_code) - get_value_of_quantity_of_SOI(d.item_code)
            available_actual += " | " + d.attribute_value + " = " + str(int(available_value)) + "/" + str(int(actual_value))
            warehouse = d.warehouse
            item_name = d.item_name
            size_group = d.size_group
            total += d.stock_akhir
            total2 += actual_value
            warehouse = d.warehouse
            vcompare = d.compare_name

    data.append([item_name, size_group, available_actual, total2, warehouse])
    return columns, data

def get_columns(filters):

    columns =[
        {
            "label": _("Article Description"),
            "fieldname": "item_name",
            "fieldtype": "Link",
            "options": "Item",
            "width": 160
        },
        {
            "label": _("Size Gr"),
            "fieldname": "size_group",
            "fieldtype": "Data",
            "width": 50
        },
        {
            "label": _("Available Actual Value"),
            "fieldname": "Available_Actual",
            "fieldtype": "Data",
            "width": 400
        },
        {
			"label": _("Total"),
			"fieldname": "total",
			"fieldtype": "Data",
			"width": 50
		},
        {
			"label": _("Warehouse"),
			"fieldname": "warehouse_name",
			"fieldtype": "Link",
            "options": "Warehouse",
			"width": 180
		},

    ]

    return columns

def get_entries(filters):
    conditions = get_conditions(filters)
    vfind = 0
    conditions2 = ""
    conditions3 = ""
    conditions4 = ""
    if filters.get("warehouse_name") == "All Warehouses - ISS":
        conditions2 += "and 1=1"
    elif filters.get("warehouse_name") == "[000] TRANSIT - ISS":
        conditions2 += " and 1=1 and b.warehouse like '%80000001%'"
    elif filters.get("warehouse_name") == "[901] - Finished - ISS":
        conditions3 += get_conditions_part("GUDANG BARANG JADI CASUAL - ISS")
        conditions4 += get_conditions_part("GUDANG BARANG JADI FORMAL - ISS")
    elif filters.get("warehouse_name") == "[903] - In Progress - ISS":
        conditions2 += " and 1=1 and b.warehouse like '903%'"
    elif filters.get("warehouse_name") == "[904] - Final Touch - ISS":
        conditions2 += " and 1=1 and b.warehouse like '904%'"
    elif filters.get("warehouse_name") == "[905] - Bad Product - ISS":
        conditions2 += " and 1=1 and b.warehouse like '905%'"
    else:
        vfilter = filters.get("warehouse_name")
        try:
           vfind = vfilter.find(" - ISS")
        except:
           pass
        if vfind > 1:
           child_warehouse = get_child_warehouse(vfilter)
           logging.basicConfig(level=logging.DEBUG)
           logging.debug("Child Warehousenya :{0}".format(child_warehouse))
           vfind2 = 0
           try:
              vfind2 = child_warehouse.find("==")
           except:
              pass
           if vfind2 > 1:
              vcond = child_warehouse[0:len(child_warehouse) - 2]
              conditions2 += "and 1=1 and b.warehouse in {0}".format(vcond)
           else:
              vend = len(child_warehouse)-6
              vcond = child_warehouse[0:vend]
              conditions2 += "and 1=1 and b.warehouse like '{0}%'".format(vcond)
           logging.basicConfig(level=logging.DEBUG)
           logging.debug("Conditions2 :{0}".format(conditions2))
        else:
           if filters.get("warehouse_name"):
              conditions2 += "and 1=1 and b.warehouse like '{0}%'".format(filters.get("warehouse_name"))
           else:
              conditions2 += "and 1=1"

    if filters.get("warehouse_name") == "[901] - Finished - ISS":
        entries = frappe.db.sql("""select z.item_code, z.item_name,z.size_group,z.item_group,z.warehouse,z.compare_name,z.attribute_value,z.stock_akhir,z.state
		from (select e.item_code,e.item_name,e.size_group,e.item_group,e.warehouse,e.compare_name,e.attribute_value,e.stock_akhir,e.state from (
		select b.item_code, b.item_name,b.size_group,b.item_group,b.warehouse,concat(b.item_name,b.warehouse) as compare_name,iav.abbr as attribute_value,convert(b.stock_akhir,int) stock_akhir,ad.state,ad.city from (select a.item_name,
        a.item_code,a.size_group,a.item_group,a.division_group,a.retail_group,a.price_list,
        sum(a.actual_qty)+sum(a.planned_qty)-sum(a.reserved_qty) as stock_akhir,replace(a.warehouse,' - ISS','') as warehouse
        from ( SELECT a.item_name ,a.item_code , a.size_group, a.item_group , a.division_group ,a.retail_group ,a.brand ,format(max(d.price_list_rate),0) as price_list,
        b.actual_qty ,c.delivered_qty ,b.reserved_qty as "reserved_qty",b.projected_qty ,(b.planned_qty+b.ordered_qty+b.indented_qty) as planned_qty,
        b.warehouse FROM `tabItem` a LEFT JOIN `tabBin` b ON a.item_code = b.item_code LEFT JOIN `tabSales Order Item` c
        ON a.item_code = c.item_code LEFT JOIN `tabItem Price` d ON a.item_code = d.item_code where
        a.item_group in ('J2B','C2B','JC2C','F2B','F2C','JC2B','F2A','U2B','C2C','J2C','J2A',
        'C2A','U2A','L2C','L2B','L2A','JC2A','Y2A','GIFT','2B','2A') {0}
        group by a.item_code, b.warehouse) a where a.reserved_qty > 0 or a.actual_qty > 0 or a.projected_qty > 0
        group by a.item_name,a.item_code,a.item_group,a.division_group,a.retail_group,a.price_list,a.warehouse
        order by a.item_name asc) b left join `tabAddress` ad on b.warehouse = substring(ad.name,1,length(b.warehouse))
        inner join `tabItem Variant Attribute` iva on b.item_code = iva.parent
        inner join `tabItem Attribute Value` iav on iva.attribute_value = iav.attribute_value
        where iva.attribute = 'Size' {1} order by b.item_name,b.warehouse,b.size_group,iav.abbr) e union select f.item_code,f.item_name,f.size_group,f.item_group,f.warehouse,f.compare_name,f.attribute_value,f.stock_akhir,f.state from (
		select b.item_code, b.item_name,b.size_group,b.item_group,b.warehouse,concat(b.item_name,b.warehouse) as compare_name,iav.abbr as attribute_value,convert(b.stock_akhir,int) stock_akhir,ad.state,ad.city from (select a.item_name,
        a.item_code,a.size_group,a.item_group,a.division_group,a.retail_group,a.price_list,
        sum(a.actual_qty)+sum(a.planned_qty)-sum(a.reserved_qty) as stock_akhir,replace(a.warehouse,' - ISS','') as warehouse
        from ( SELECT a.item_name ,a.item_code , a.size_group, a.item_group , a.division_group ,a.retail_group ,a.brand ,format(max(d.price_list_rate),0) as price_list,
        b.actual_qty ,c.delivered_qty ,b.reserved_qty as "reserved_qty",b.projected_qty ,(b.planned_qty+b.ordered_qty+b.indented_qty) as planned_qty,
        b.warehouse FROM `tabItem` a LEFT JOIN `tabBin` b ON a.item_code = b.item_code LEFT JOIN `tabSales Order Item` c
        ON a.item_code = c.item_code LEFT JOIN `tabItem Price` d ON a.item_code = d.item_code where
        a.item_group in ('J2B','C2B','JC2C','F2B','F2C','JC2B','F2A','U2B','C2C','J2C','J2A',
        'C2A','U2A','L2C','L2B','L2A','JC2A','Y2A','GIFT','2B','2A') {2}
        group by a.item_code, b.warehouse) a where a.reserved_qty > 0 or a.actual_qty > 0 or a.projected_qty > 0
        group by a.item_name,a.item_code,a.item_group,a.division_group,a.retail_group,a.price_list,a.warehouse
        order by a.item_name asc) b left join `tabAddress` ad on b.warehouse = substring(ad.name,1,length(b.warehouse))
        inner join `tabItem Variant Attribute` iva on b.item_code = iva.parent
        inner join `tabItem Attribute Value` iav on iva.attribute_value = iav.attribute_value
        where iva.attribute = 'Size' {3} order by b.item_name,b.warehouse,b.size_group,iav.abbr) f) z where z.item_name like '%.C%' or z.item_name like '%.A%'""".format(conditions3,conditions,conditions4,conditions), as_dict=1)
    else:
        entries = frappe.db.sql("""
        select k.item_code, k.item_name,k.size_group,k.item_group,k.warehouse,k.compare_name,k.attribute_value,k.stock_akhir,k.state,k.city from (select b.item_code, b.item_name,b.size_group,b.item_group,b.warehouse,concat(b.item_name,b.warehouse) as compare_name,iav.abbr as attribute_value,convert(b.stock_akhir,int) stock_akhir,ad.state,ad.city from (select a.item_name,
        a.item_code,a.size_group,a.item_group,a.division_group,a.retail_group,a.price_list,
        sum(a.actual_qty)+sum(a.planned_qty)-sum(a.reserved_qty) as stock_akhir,replace(a.warehouse,' - ISS','') as warehouse
        from ( SELECT a.item_name ,a.item_code , a.size_group, a.item_group , a.division_group ,a.retail_group ,a.brand ,format(max(d.price_list_rate),0) as price_list,
        b.actual_qty ,c.delivered_qty ,b.reserved_qty as "reserved_qty",b.projected_qty ,(b.planned_qty+b.ordered_qty+b.indented_qty) as planned_qty,
        b.warehouse FROM `tabItem` a LEFT JOIN `tabBin` b ON a.item_code = b.item_code LEFT JOIN `tabSales Order Item` c
        ON a.item_code = c.item_code LEFT JOIN `tabItem Price` d ON a.item_code = d.item_code where
        a.item_group in ('J2B','C2B','JC2C','F2B','F2C','JC2B','F2A','U2B','C2C','J2C','J2A',
        'C2A','U2A','L2C','L2B','L2A','JC2A','Y2A','GIFT','2B','2A') {0}
        group by a.item_code, b.warehouse) a where a.reserved_qty > 0 or a.actual_qty > 0 or a.projected_qty > 0
        group by a.item_name,a.item_code,a.item_group,a.division_group,a.retail_group,a.price_list,a.warehouse
        order by a.item_name asc) b left join `tabAddress` ad on b.warehouse = substring(ad.name,1,length(b.warehouse))
        inner join `tabItem Variant Attribute` iva on b.item_code = iva.parent
        inner join `tabItem Attribute Value` iav on iva.attribute_value = iav.attribute_value
        where iva.attribute = 'Size' {1} order by b.item_name,b.warehouse,b.size_group,iav.abbr) k where k.item_name like '%.C%' or k.item_name like '%.A%'""".format(conditions2,conditions), as_dict=1)
    return entries

def get_child_warehouse(conditions):
    warehouse_name = ""
    if conditions[0:1].isnumeric():
        entries = frappe.db.sql("""select parent_warehouse,warehouse_name,is_group from `tabWarehouse` where parent_warehouse = %s""", (conditions), as_dict=1)
        warehouse_name = ""
        for d in entries:
            warehouse_name = d.parent_warehouse
        logging.basicConfig(level=logging.DEBUG)
        logging.debug(warehouse_name)
        if warehouse_name == "":
            warehouse_name = conditions
    else:
        entries = frappe.db.sql("""select parent_warehouse,warehouse_name,is_group from `tabWarehouse` where parent_warehouse = %s""", (conditions), as_dict=1)
        warehouse_name = ""
        if len(entries) == 1:
            for d in entries:
                warehouse_name = d.warehouse_name + " - ISS"
        elif len(entries) > 1:
            parent_warehouse = "("
            warehouse_name = "("
            finish = len(entries)
            logging.basicConfig(level=logging.DEBUG)
            logging.debug("Checking for finish {0}".format(finish))
            while finish != 0:
                for d in entries:
                    if d.is_group == 0:
                       warehouse_name += "'" + d.warehouse_name + " - ISS" + "',"
                       logging.basicConfig(level=logging.DEBUG)
                       logging.debug("Checking for pernah ke sini {0}".format(warehouse_name))
                    else:
                       parent_warehouse += "'" + d.warehouse_name + " - ISS" + "',"
                       logging.basicConfig(level=logging.DEBUG)
                       logging.debug("Checking for warehouse name 1 {0}".format(d.warehouse_name))
                       logging.basicConfig(level=logging.DEBUG)
                       logging.debug("Checking for parent_warehouseny {0}".format(parent_warehouse))
                       logging.basicConfig(level=logging.DEBUG)
                       logging.debug("Checking for warehouse name {0}".format(d.warehouse_name))

                parent_warehouse = parent_warehouse[0:len(parent_warehouse)-1] + ")"
                logging.basicConfig(level=logging.DEBUG)
                logging.debug("Checking for warehouse_namenya :{0}".format(parent_warehouse))
                if parent_warehouse != ")":
                   entries = get_child_warehouse2(parent_warehouse)
                else:
                   finish = 0
                if finish > 0:
                   parent_warehouse = "("

            warehouse_name = warehouse_name[0:len(warehouse_name)-1] + ")=="
        else:
            warehouse_name = ""
        logging.basicConfig(level=logging.DEBUG)
        logging.debug("Checking for number gudang :{0}".format(warehouse_name))
        if warehouse_name == "":
            warehouse_name = conditions

    logging.basicConfig(level=logging.DEBUG)
    logging.debug("Checking for warehouse_name luar :{0}".format(warehouse_name))

    return warehouse_name

def get_child_warehouse2(conditions):
    logging.basicConfig(level=logging.DEBUG)
    logging.debug("Checking for conditions child warehouse 2 :{0}".format(conditions))
    entries = frappe.db.sql("""select parent_warehouse,warehouse_name,is_group from `tabWarehouse` where parent_warehouse in {0}""".format(conditions), as_dict=1)

    return entries

def get_parent_number_warehouse(conditions):
    logging.basicConfig(level=logging.DEBUG)
    logging.debug("Checking for conditions child warehouse 2 :{0}".format(conditions))
    entries = frappe.db.sql("""select parent_warehouse,warehouse_name,is_group from `tabWarehouse` where warehouse_name = %s""",(conditions), as_dict=1)

    return entries

def get_conditions(filters):
    conditions = ""
    if filters.get("item_name"):
        conditions += " and b.item_name = '{0}'".format(filters.get("item_name"))

    if filters.get("city"):
        conditions += " and ad.city = '{0}'".format(filters.get("city"))
    if filters.get("state"):
        conditions += " and ad.state = '{0}'".format(filters.get("state"))

    return conditions

def get_value_of_quantity_of_MRI(item_code):
    """warehouse is hard coded as per Mr. Albert's instructions"""
    sql = "select sum(qty) qty from `tabMaterial Request Item` where item_code = '{0}'".format(item_code)
    reserved_qty = frappe.db.sql(sql)
    return flt(reserved_qty[0][0]) if reserved_qty else 0

def get_value_of_quantity_of_SOI(item_code):
    """warehouse is hard coded as per Mr. Albert's instructions"""
    sql = "select sum(qty) qty from `tabSales Order Item` where item_code = '{0}'".format(item_code)
    reserved_qty = frappe.db.sql(sql)
    return flt(reserved_qty[0][0]) if reserved_qty else 0

def get_available_value(item_code):
    sql = "select sum(available_qty) qty from `tabFinished 901 Item Summary` where item_code = '{0}'".format(item_code)
    reserved_qty = frappe.db.sql(sql)
    return flt(reserved_qty[0][0]) if reserved_qty else 0

def get_conditions_part(conditions):
    vfilter = conditions
    vfind = 0
    conditions2 = ""
    try:
       vfind = vfilter.find(" - ISS")
    except:
       pass
    if vfind > 1:
       child_warehouse = get_child_warehouse(vfilter)
       vfind2 = 0
       try:
          vfind2 = child_warehouse.find("==")
       except:
          pass
       if vfind2 > 1:
          vcond = child_warehouse[0:len(child_warehouse) - 2]
          conditions2 += "and 1=1 and b.warehouse in {0}".format(vcond)
       else:
          vend = len(child_warehouse)-6
          vcond = child_warehouse[0:vend]
          conditions2 += "and 1=1 and b.warehouse like '{0}%'".format(vcond)
       logging.basicConfig(level=logging.DEBUG)
       logging.debug("Conditions2 :{0}".format(conditions2))
    else:
       if filters.get("warehouse_name"):
          conditions2 += "and 1=1 and b.warehouse like '{0}%'".format(filters.get("warehouse_name"))
       else:
          conditions2 += "and 1=1"

    return conditions2
