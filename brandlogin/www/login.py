import frappe
from frappe.www.login import get_context as get_core_login_context

no_cache = 1


def get_context(context):
	"""
	Extends Frappe core's own /login context builder instead of
	replacing it, so social login, LDAP, signup, email-link login,
	redirect-to handling, etc. all keep working exactly as before.
	Only the presentation (login.html + brand_login.css) changes.
	"""
	get_core_login_context(context)

	settings = frappe.get_single("Login Branding Settings")

	context.brand_product_name = settings.product_name or "Vodafone"
	context.brand_business_name = settings.business_name or ""
	context.brand_tagline = settings.tagline or ""
	context.brand_primary = settings.primary_color or "#6C5CE7"
	context.brand_accent = settings.accent_color or "#22C55E"
	context.brand_bg_style = settings.background_style or "Gradient"
	context.brand_show_powered_by = settings.show_powered_by
	context.brand_footer_text = settings.footer_text or ""
	context.brand_support_email = settings.support_email or ""

	context.brand_logo = frappe.utils.get_url(settings.logo) if settings.logo else context.get("logo")
	if settings.favicon:
		context.favicon = frappe.utils.get_url(settings.favicon)

	# Core login.html falls back to app_name in a couple of copy strings —
	# keep that aligned with our own branding so nothing shows "Frappe".
	context.app_name = settings.business_name or settings.product_name or context.get("app_name")

	return context
