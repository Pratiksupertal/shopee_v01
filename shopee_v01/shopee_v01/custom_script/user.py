import frappe


@frappe.whitelist()
def generate_keys(user):
    """
    tasks: generate api key and api secret
    param user: str

    modified by: Amirul Islam (9 May, 2022)
    original path: /api/method/frappe.core.doctype.user.user.generate_keys
    updates: added more role (Warehouse Login)
    """
    allowed_roles = ["System Manager", "Warehouse Login"]
    user_roles = frappe.get_roles()

    def intersection(lst1, lst2):
        return list(set(lst1) & set(lst2))

    if intersection(allowed_roles, user_roles):
        user_details = frappe.get_doc("User", user)
        api_secret = frappe.generate_hash(length=15)

        # if api key is not set generate api key
        if not user_details.api_key:
            api_key = frappe.generate_hash(length=15)
            user_details.api_key = api_key

        user_details.api_secret = api_secret
        user_details.save()
        return {"api_secret": api_secret}
    frappe.throw(frappe._("Not Permitted"), frappe.PermissionError)
