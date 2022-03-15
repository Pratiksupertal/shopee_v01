import frappe
from frappe.model.document import Document
from six import string_types
import json, copy
from frappe.utils import cstr, flt

def validate(doc,method):
    try:
        if not doc.upload and not doc.has_variants:
            if doc.get("__islocal"):
                sql = "select barcode from `tabItem Barcode` order by creation desc limit 1".format(doc.item_code)
                pre_barcode = frappe.db.sql(sql,as_dict=True)
                barcode = int(pre_barcode[0].barcode)+1 if len(pre_barcode)>0 else 1000001
                if len(pre_barcode)>0:
                    barcode = barcode_design(barcode)
                    doc.append("barcodes",{
                    "barcode":str(barcode)
                    })
                else:
                    doc.append("barcodes",{
                    "barcode":"1000001"
                    })
            doc.item_bar_code = doc.barcodes[0].barcode
    except :
        raise

def barcode_design(barcode):
    if not frappe.db.exists('Item Barcode',{'barcode':barcode}):
        return barcode
    else:
        barcode = barcode_design(barcode+1)
        return barcode

@frappe.whitelist()
def enqueue_multiple_variant_creation(item, args):
	if isinstance(args, string_types):
		variants = json.loads(args)
	total_variants = 1
	for key in variants:
		total_variants *= len(variants[key])
	if total_variants >= 600:
		frappe.throw(_("Please do not create more than 500 items at a time"))
		return
	if total_variants < 10:
		return create_multiple_variants(item, args)
	else:
		frappe.enqueue("shopee_v01.shopee_v01.custom_script.item.create_multiple_variants",
			item=item, args=args, now=frappe.flags.in_test);
		return 'queued'

def create_multiple_variants(item, args):
	count = 0
	if isinstance(args, string_types):
		args = json.loads(args)

	args_set = generate_keyed_value_combinations(args)

	for attribute_values in args_set:
		if not get_variant(item, args=attribute_values):
			variant = create_variant(item, attribute_values)
			variant.save()
			count +=1

	return count

@frappe.whitelist()
def get_variant(template, args=None, variant=None, manufacturer=None,
	manufacturer_part_no=None):
	item_template = frappe.get_doc('Item', template)
	if item_template.variant_based_on=='Manufacturer' and manufacturer:
		return make_variant_based_on_manufacturer(item_template, manufacturer,
			manufacturer_part_no)
	else:
		if isinstance(args, string_types):
			args = json.loads(args)

		if not args:
			frappe.throw(_("Please specify at least one attribute in the Attributes table"))
		return find_variant(template, args, variant)

def find_variant(template, args, variant_item_code=None):
	conditions = ["""(iv_attribute.attribute={0} and iv_attribute.attribute_value={1})"""\
		.format(frappe.db.escape(key), frappe.db.escape(cstr(value))) for key, value in args.items()]

	conditions = " or ".join(conditions)

	from erpnext.portal.product_configurator.utils import get_item_codes_by_attributes
	possible_variants = [i for i in get_item_codes_by_attributes(args, template) if i != variant_item_code]

	for variant in possible_variants:
		variant = frappe.get_doc("Item", variant)

		if len(args.keys()) == len(variant.get("attributes")):
			match_count = 0
			for attribute, value in args.items():
				for row in variant.attributes:
					if row.attribute==attribute and row.attribute_value== cstr(value):
						match_count += 1
						break

			if match_count == len(args.keys()):
				return variant.name

def generate_keyed_value_combinations(args):
	if not args:
		return []
	key_value_lists = [[(key, val) for val in args[key]] for key in args.keys()]
	results = key_value_lists.pop(0)
	results = [{d[0]: d[1]} for d in results]
	for l in key_value_lists:
		new_results = []
		for res in results:
			for key_val in l:
				obj = copy.deepcopy(res)
				obj[key_val[0]] = key_val[1]
				new_results.append(obj)
		results = new_results
	return results

@frappe.whitelist()
def create_variant(item, args):
    if isinstance(args, string_types):
        args = json.loads(args)
    template = frappe.get_doc("Item", item)
    variant = frappe.new_doc("Item")
    variant.variant_based_on = 'Item Attribute'
    variant_attributes = []
    for d in template.attributes:
        variant_attributes.append({
			"attribute": d.attribute,
			"attribute_value": args.get(d.attribute)
		})
    variant.set("attributes", variant_attributes)
    custom_fields = ["gender","cut","rise","season","collar","waist","product_status","sleeve","wash","item_section","cuff_","fabric","pocket","fit","design","stitches","main_color","division_group","retail_group","item_category","size_group","valuation_rate","inveinvent_size_id","size_index","warranty_period","model","price","standard_rate","color","status_code"]
    temp = template.__dict__
    for i in custom_fields:
        if template.get(i):
            value = temp[i]
            variant.set(i,value)
    copy_attributes_to_variant(template, variant)
    make_variant_item_code(template.item_code, template.item_name, variant)
    return variant

def make_variant_item_code(template_item_code, template_item_name, variant):
    """Uses template's item code and abbreviations to make variant's item code"""
    if variant.item_code:
        return
    abbreviations = []
    for attr in variant.attributes:
        item_attribute = frappe.db.sql("""select i.numeric_values, v.abbr
			from `tabItem Attribute` i left join `tabItem Attribute Value` v
				on (i.name=v.parent)
			where i.name=%(attribute)s and (v.attribute_value=%(attribute_value)s or i.numeric_values = 1)""", {
				"attribute": attr.attribute,
				"attribute_value": attr.attribute_value
			}, as_dict=True)
        if not item_attribute:
            continue
        abbr_or_value = cstr(attr.attribute_value) if item_attribute[0].numeric_values else item_attribute[0].abbr
        abbreviations.append(abbr_or_value)
    if abbreviations:
        variant.item_code = "{0}-{1}".format(template_item_code, "-".join(abbreviations))
        variant.item_name = "{0}".format(template_item_name)


def copy_attributes_to_variant(item, variant):
	exclude_fields = ["naming_series", "item_code", "item_name", "show_in_website",
		"show_variant_in_website", "opening_stock", "variant_of"]
	if item.variant_based_on=='Manufacturer':
		exclude_fields += ['manufacturer', 'manufacturer_part_no']
	allow_fields = [d.field_name for d in frappe.get_all("Variant Field", fields = ['field_name'])]
	if "variant_based_on" not in allow_fields:
		allow_fields.append("variant_based_on")
	for field in item.meta.fields:
		if (field.reqd or field.fieldname in allow_fields) and field.fieldname not in exclude_fields:
			if variant.get(field.fieldname) != item.get(field.fieldname):
				if field.fieldtype == "Table":
					variant.set(field.fieldname, [])
					for d in item.get(field.fieldname):
						row = copy.deepcopy(d)
						if row.get("name"):
							row.name = None
						variant.append(field.fieldname, row)
				else:
					variant.set(field.fieldname, item.get(field.fieldname))

	variant.variant_of = item.name

	if 'description' not in allow_fields:
		if not variant.description:
				variant.description = ""
	else:
		if item.variant_based_on=='Item Attribute':
			if variant.attributes:
				attributes_description = item.description + " "
				for d in variant.attributes:
					attributes_description += "<div>" + d.attribute + ": " + cstr(d.attribute_value) + "</div>"
				if attributes_description not in variant.description:
					variant.description = attributes_description


@frappe.whitelist()
def categories(doctype,value,field):
    return frappe.db.get_value(doctype,value,field)

@frappe.whitelist()
def barcode(code):
    return str(code)


@frappe.whitelist()
def add_warehouse(f_path=None):
    import sys
    import os
    doc = frappe.get_single("Finished901ItemQtySummary")
    import csv
    path = os.path.join(os.path.dirname(__file__), f_path)
    file = open(path,"r")
    csvreader = csv.reader(file)
    header = []
    rows = []
    header = next(csvreader)
    for row in csvreader:
        rows.append(row)
        doc.append("child_warehouse",{"warehouse":row[0]})
    file.close()
    doc.save()

    # -----------------------------------
