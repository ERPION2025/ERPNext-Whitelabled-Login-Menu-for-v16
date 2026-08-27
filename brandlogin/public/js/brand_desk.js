(function () {
	var brand = frappe.boot && frappe.boot.brandlogin;
	if (!brand) return;

	var primary = brand.primary_color || "#E60000";
	var accent = brand.accent_color || "#A30000";

	// These are Frappe's own theme variables — the same ones its
	// light/dark toggle switches between (see desk/dark.scss). Setting
	// them as inline styles on <html> beats any [data-theme="..."] rule
	// from a stylesheet, so this survives the user switching themes
	// without needing to hook into that switch at all. It's Desk-wide by
	// design: every installed app (HR, CRM, POS, etc.) renders inside
	// this same Desk shell and reads these same variables, so buttons,
	// borders, checkboxes, focus rings, and the sidebar's active-item
	// highlight across every doctype/form/list pick this up uniformly —
	// nothing here is specific to ERPNext's own doctypes.
	var root = document.documentElement.style;
	root.setProperty("--primary", primary);
	root.setProperty("--primary-color", primary);
	root.setProperty("--btn-primary", primary);
	root.setProperty("--border-primary", primary);
	root.setProperty("--focus-default", "0px 0px 0px 2px " + accent);
	root.setProperty("--sidebar-active-color", "color-mix(in srgb, " + primary + " 12%, transparent)");
})();
