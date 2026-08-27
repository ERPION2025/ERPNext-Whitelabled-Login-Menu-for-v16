import frappe


def get_home_page(user):
	"""
	Registered via hooks.py as get_website_user_home_page.
	Frappe calls this to resolve what a logged-in user sees at "/" —
	which is also where core's own post-login redirect lands unless a
	redirect-to param overrides it. Returning a route here means users
	see the module launcher first, then choose a workspace, instead of
	dropping straight into Desk.

	In practice this hook alone isn't enough — see on_login and
	before_request below for why, and why they're needed too.
	"""
	if user == "Administrator":
		# Keep the System Manager escape hatch to Desk untouched.
		return "app"
	return "modules"


def on_login(login_manager):
	"""
	Registered via hooks.py's on_login. This is what actually makes the
	very first post-login redirect land on /modules.

	frappe.website.utils.get_home_page() has a "Default Workspace" check
	that overrides everything else it computes — including the
	get_website_user_home_page hook above — the moment a user has ever
	pinned a workspace from the Desk sidebar. That's normal, common state
	on any real account (just not on a freshly created test user), which
	is why the launcher can appear to "only work on the login page": real
	users skip straight past the hook to their last workspace instead.

	The one thing get_home_page() checks *before* any of that logic runs
	is frappe.local.flags.home_page, so we set it directly. This has to
	happen here rather than in a before_request hook: for the initial
	`/api/method/login` call, LoginManager runs to completion (including
	computing the response's home_page field) inside
	HTTPRequest.set_session(), which fires *before* before_request hooks
	do — so by the time before_request would run, it's already too late
	to change that response. on_login fires at the start of
	post_login(), before set_user_info() reads get_home_page(), so it's
	early enough.
	"""
	if login_manager.user == "Administrator":
		return
	frappe.local.flags.home_page = "modules"


def before_request():
	"""
	Covers the other case get_home_page() gets used for: an
	already-logged-in user visiting "/" directly on some later request
	(a bookmark, a link with no query params) — no LoginManager involved
	that time, so before_request runs early enough on its own.
	"""
	if frappe.request.path not in ("/", ""):
		return
	if frappe.session.user in ("Guest", "Administrator"):
		return
	frappe.local.flags.home_page = "modules"
