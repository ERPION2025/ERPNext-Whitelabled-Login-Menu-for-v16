# Copyright (c) 2026, and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class LoginBrandingSettings(Document):
	def validate(self):
		if not self.product_name:
			self.product_name = "Vodafone"
		if not self.tagline:
			self.tagline = "Run your business, beautifully simple."
		if not self.primary_color:
			self.primary_color = "#E60000"
		if not self.accent_color:
			self.accent_color = "#A30000"

	def on_update(self):
		# Login page is a plain www page — clear the website cache so the
		# new branding (colors, logo, copy) shows up immediately instead
		# of waiting for the next cache expiry.
		from frappe.website.utils import clear_cache

		clear_cache()
