import frappe


def get_home_page(user):
	"""
	Registered via hooks.py as get_website_user_home_page.
	Frappe calls this to resolve what a logged-in user sees at "/" —
	which is also where core's own post-login redirect lands unless a
	redirect-to param overrides it. Returning a route here means users
	see the module launcher first, then choose a workspace, instead of
	dropping straight into Desk.
	"""
	if user == "Administrator":
		# Keep the System Manager escape hatch to Desk untouched.
		return "app"
	return "modules"
