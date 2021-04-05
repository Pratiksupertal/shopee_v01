from frappe.model.naming import make_autoname

def test(doc,method):
    print("Hiiiii")
    print("test calling from hooks")

def autoname(doc,method):
    print("Hiiiii")
    if doc.is_new():
        po_type = doc.po_type
        if po_type:
            print(po_type[0])
            a = po_type.split(" ")
            print("---------------------------")
            doc.name = make_autoname(a[1][0]+"PO" + "-.#####")
        else:
            doc.name = make_autoname("PO" + "-.#####")
    print("test calling from hooks")
    #shopee_v01.shopee_v01.custom_script.purchase_order.test
    #shopee_v01/shopee_v01/custom_script/purchase_order.js
