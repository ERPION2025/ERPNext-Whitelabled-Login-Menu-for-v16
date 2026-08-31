// Frappe's Desk navbar hardcodes its home/logo icon to "/app" with no
// hook to override the target. Since that link is followed either as a
// full page load or as an in-SPA history.pushState/replaceState call
// depending on how core wires it up in a given version, we cover both:
// the server-side redirect in brandlogin.utils.before_request handles
// a real request to bare "/app", and the History API patch below
// catches the SPA-only navigation so the URL bar never even settles on
// "/app" for a user who isn't allowed to see raw Desk.
(function () {
	function is_desk_root(path) {
		return path === "/app" || path === "/app/";
	}

	function redirect_to_modules() {
		window.location.replace("/modules");
	}

	frappe.ready(function () {
		if (!frappe.session || frappe.session.user === "Administrator") return;
		if ((frappe.user_roles || []).includes("System Manager")) return;

		if (is_desk_root(window.location.pathname)) {
			redirect_to_modules();
			return;
		}

		["pushState", "replaceState"].forEach(function (method) {
			var original = history[method];
			history[method] = function () {
				var result = original.apply(this, arguments);
				if (is_desk_root(window.location.pathname)) redirect_to_modules();
				return result;
			};
		});

		window.addEventListener("popstate", function () {
			if (is_desk_root(window.location.pathname)) redirect_to_modules();
		});
	});
})();
