import re

import frappe

no_cache = 1


def get_context(context):
	if frappe.session.user == "Guest":
		frappe.local.flags.redirect_location = "/login"
		raise frappe.Redirect

	settings = frappe.get_single("Login Branding Settings")

	context.brand_product_name = settings.product_name or "Vodafone"
	context.brand_business_name = settings.business_name or ""
	context.brand_primary = settings.primary_color or "#6C5CE7"
	context.brand_accent = settings.accent_color or "#22C55E"
	context.brand_logo = frappe.utils.get_url(settings.logo) if settings.logo else None

	user = frappe.get_doc("User", frappe.session.user)
	context.full_name = user.full_name or frappe.session.user
	context.first_name = (user.first_name or user.full_name or frappe.session.user or "").strip()

	context.modules = get_modules()

	return context


def get_modules():
	"""
	Pulls the current user's visible top-level public Workspaces — the
	same set ERPNext's own Desk sidebar shows under "Public" — rather
	than a hardcoded module list, so this automatically matches whatever
	is actually installed on a given site (HRMS present or not, custom
	apps, POS Next, etc.) and whatever the user's roles allow.

	frappe.get_all() is permission-checked by default (ignore_permissions
	is not set), so Workspace's own role-based visibility rules are
	respected here exactly as they are in Desk.
	"""
	workspaces = frappe.get_all(
		"Workspace",
		filters={"public": 1, "parent_page": ["in", ["", None]]},
		fields=["name", "title", "icon", "sequence_id"],
		order_by="sequence_id asc",
	)

	modules = []
	for ws in workspaces:
		title = ws.title or ws.name
		modules.append(
			{
				"title": title,
				"icon": ws.icon or "folder-normal",
				"route": "/app/" + _slugify(title),
			}
		)
	return modules


def _slugify(title):
	slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
	return slug or "home"
