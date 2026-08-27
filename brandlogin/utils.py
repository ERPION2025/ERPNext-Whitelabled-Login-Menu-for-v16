import json

import frappe
from frappe import _


def get_branding_settings():
	return frappe.get_cached_doc("Login Branding Settings")


def get_home_page(user):
	"""
	Registered via hooks.py as get_website_user_home_page.
	Frappe calls this to resolve what a logged-in user sees at "/" —
	which is also where core's own post-login redirect lands unless a
	redirect-to param overrides it. Returning a route here means users
	see the module launcher first, then choose a workspace, instead of
	dropping straight into Desk.

	In practice this hook alone isn't reliable enough on its own to
	depend on — see after_request below for why, and why it's what
	actually makes this stick.
	"""
	if user == "Administrator":
		# Keep the System Manager escape hatch to Desk untouched.
		return "app"
	return "modules"


def after_request(response, request):
	"""
	Registered via hooks.py's after_request. This is what actually makes
	the launcher stick, on a site with several other apps installed
	alongside this one.

	The "obvious" approach — a get_website_user_home_page hook, or an
	on_login/before_request hook setting frappe.local.flags.home_page —
	is a *computation* that has to win against every other installed
	app's opinion about where a user should land (their own
	get_website_user_home_page hook, their own on_login hook, a per-user
	Default Workspace, etc.). Whichever one happens to run last for a
	given hook wins, and that's other apps' code, not something this app
	can reliably control — which is exactly what happened here: with
	several other apps also installed, the get_website_user_home_page
	hook above kept getting overridden, and the login page's own
	branding (which doesn't depend on any of this) was the only part
	that visibly worked.

	after_request sidesteps that race entirely by not trying to win a
	computation at all — it runs after every hook has had its say and
	the response is fully built, so it can just directly rewrite the
	final output for the two places a home page actually gets read:

	- POST /api/method/login: correct the JSON response's home_page
	  field, which is what login.js uses to send the browser somewhere
	  immediately after signing in.
	- GET "/", "/app", "/desk" (bare, no sub-path): turn the response
	  into a redirect to /modules outright, regardless of what page it
	  was originally going to render. A deep link into a specific
	  workspace ("/app/some-workspace") is left alone, so Desk
	  navigation afterwards isn't affected — only these bare landing
	  routes are.
	"""
	if frappe.session.user in ("Guest", "Administrator"):
		return

	path = request.path

	if path == "/api/method/login":
		if response.mimetype != "application/json":
			return
		try:
			data = json.loads(response.get_data(as_text=True))
		except ValueError:
			return
		if data.get("message") == "Logged In" and data.get("home_page") != "modules":
			data["home_page"] = "modules"
			response.set_data(json.dumps(data).encode("utf-8"))
		return

	if path in ("/", "", "/app", "/desk"):
		response.status_code = 302
		response.headers["Location"] = "/modules"
		response.set_data(b"")


def extend_bootinfo(bootinfo):
	"""
	Registered via hooks.py's extend_bootinfo. Runs once per Desk session
	and hands the branding settings to the client as frappe.boot.brandlogin
	— see public/js/brand_desk.js, which reads this and applies it as CSS
	custom properties on every Desk page, across every installed app
	(HR, CRM, POS, etc. all render inside the same Desk shell and read the
	same theme variables Frappe itself uses, so this isn't per-app).

	Guest sessions don't get a bootinfo call for this at all in practice
	(no Desk to theme), but check anyway since extend_bootinfo hooks can
	run for portal/website-adjacent boot too.
	"""
	if frappe.session.user == "Guest":
		return
	settings = get_branding_settings()
	bootinfo.brandlogin = {
		"primary_color": settings.primary_color or "#E60000",
		"accent_color": settings.accent_color or "#A30000",
		"product_name": settings.product_name or "Vodafone",
		"show_powered_by": bool(settings.show_powered_by),
	}


def update_website_context(context):
	"""
	Registered via hooks.py's update_website_context. Runs for every
	templated website page (not Desk — actual /web pages, e.g. a Web Page
	or portal page). Frappe's own footer template
	(templates/includes/footer/footer_info.html) already has a
	`footer_powered` context-variable escape hatch that, when set, is used
	instead of the hardcoded "Powered by ERPNext" include — see
	templates/includes/footer/footer_powered.html in core. This fills
	that in from the same settings driving everything else, so "Powered
	by ERPNext" doesn't show up on ordinary website pages either.
	"""
	settings = get_branding_settings()
	return {
		"footer_powered": f'{_("Powered by")} {settings.product_name or "Vodafone"}',
	}
