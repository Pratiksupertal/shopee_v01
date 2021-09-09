import frappe
import datetime as dt
# from frappe.core.doctype.activity_log.activity_log import add_authentication_log

def scheduler_event_log(subject,content):
    doc = frappe.new_doc("Finished901Warehouse Log")
    doc.subject = subject
    doc.message = str(content)
    doc.time =  dt.datetime.now()
    try:
        doc.save()
        return doc
    except:
        print("Failed to create logs")
