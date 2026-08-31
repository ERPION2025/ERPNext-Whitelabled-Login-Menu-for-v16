import frappe


def has_desk_access(user):
	"""
	Whether this user is allowed to land on Desk itself (the /app
	workspace list) rather than being funneled through /modules.

	Kept role-based rather than a literal Administrator check: any
	System Manager should get normal Desk behaviour, and everyone else
	— regardless of which specific doctypes their other roles grant
	them — should never see raw Desk.
	"""
	if user == "Administrator":
		return True
	return "System Manager" in frappe.get_roles(user)


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
	if has_desk_access(user):
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
	if has_desk_access(login_manager.user):
		return
	frappe.local.flags.home_page = "modules"


def before_request():
	"""
	Covers the other cases get_home_page() and the /app SPA entry get
	used for: an already-logged-in user visiting "/" directly on some
	later request (a bookmark, a link with no query params), or hitting
	bare Desk ("/app") — via a bookmark, typed URL, or the Desk navbar's
	own home icon (which core hardcodes to /app; see
	brand_desk_home.js for the client-side half of that fix). No
	LoginManager is involved on either of these, so before_request runs
	early enough on its own.

	Only the bare Desk landing is blocked here — a specific workspace
	route like /app/selling is left alone, since users are meant to work
	inside Desk for whatever their roles permit once they've picked a
	module from /modules.
	"""
	user = frappe.session.user
	if user == "Guest" or has_desk_access(user):
		return

	path = frappe.request.path
	if path in ("/", ""):
		frappe.local.flags.home_page = "modules"
	elif path in ("/app", "/app/"):
		frappe.local.flags.redirect_location = "/modules"
		raise frappe.Redirect
