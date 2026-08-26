// Copyright (c) 2026, and contributors
// For license information, please see license.txt

frappe.ui.form.on("Login Branding Settings", {
	refresh(frm) {
		frm.add_custom_button(__("Preview Login Page"), () => {
			window.open("/login", "_blank");
		});

		if (!frm.doc.business_name) {
			frm.dashboard.set_headline_alert(
				__(
					"No Business / Store Name set — the login page will fall back to showing just the Product Name."
				),
				"orange"
			);
		}
	},
});
