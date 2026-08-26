# Brand Login — whitelabel /login for Frappe/ERPNext v16

A modern, split-screen login page that replaces core Frappe's `/login`,
driven entirely by a single settings doctype — no code changes needed
per business. Set it up once, then reuse it across every site: just
change **Product Name**, **Business Name**, **logo**, and **colors** per
tenant.

- Left panel: your umbrella product brand (e.g. "Vodafone") — dark hero,
  gradient or solid, with a small pulsing "signal" mark and a live status
  badge.
- Right panel: the specific business's sign-in card — their logo, their
  name, your standard ERPNext auth (login, forgot password, signup,
  LDAP, social login, email-link login — whatever you already have
  enabled).

All actual auth logic (submitting the login form, password reset,
signup, hash-based routing between those screens) is still handled by
Frappe core's own `login.js` bundle. This app only replaces the
**template and styles** — nothing about how authentication works
changes, which means it keeps working across core upgrades without
you having to re-implement auth.

## 1. Scaffold the app

Don't hand-roll `hooks.py`/`pyproject.toml` — let bench generate the
boilerplate for your exact Frappe version, then drop these files in:

```bash
cd ~/frappe-bench
bench new-app brandlogin
# App Title: Brandlogin        <- one word, see warning below
# App Description: Whitelabel login page
# ... accept the rest of the defaults
```

**App Title must be entered as `Brandlogin` (one word), not "Brand
Login".** Bench names the app's default module folder after whatever
you type for App Title, scrubbed to snake_case — "Brand Login" becomes
a `brand_login/` folder, not `brandlogin/`. The doctype JSON below
hardcodes `"module": "Brandlogin"`, so a mismatched folder name means
`bench migrate` fails to find the module (or Desk can't resolve the
DocType) after you copy the files in step 2. If you already scaffolded
with a different title, just rename the generated module folder under
`apps/brandlogin/brandlogin/` to `brandlogin` and update the app's
`modules.txt` to read `Brandlogin` before continuing.

This creates `apps/brandlogin/brandlogin/` with a `brandlogin` module
already registered — that's the same module name used in the doctype
JSON below, so nothing extra needs wiring up.

## 2. Copy in these files

Copy everything under `brandlogin/` in this delivery into
`apps/brandlogin/brandlogin/`, matching this layout:

```
apps/brandlogin/brandlogin/
├── brandlogin/
│   └── doctype/
│       └── login_branding_settings/
│           ├── __init__.py
│           ├── login_branding_settings.json
│           ├── login_branding_settings.py
│           └── login_branding_settings.js
├── www/
│   ├── login.html
│   └── login.py
└── public/
    └── css/
        └── brand_login.css
```

No `hooks.py` edits are required — `www/login.py` and `www/login.html`
override core's `/login` purely by matching Frappe's file-based routing
(an app's `www/<path>` takes precedence over an earlier-installed app's
page of the same name), and the CSS is linked directly inside
`login.html`'s own `head_include` block, so it never leaks into the
rest of Desk.

## 3. Install

```bash
bench --site your-site.com install-app brandlogin
bench --site your-site.com migrate
bench build --app brandlogin
bench --site your-site.com clear-cache
```

On Frappe Cloud: push this as a custom app to your **Private Bench
Group** (Dependencies/Apps tab), then install it on the site the same
way as any other app from the dashboard.

## 4. Configure branding

Desk → search **Login Branding Settings** (Single doctype, System
Manager only):

| Field | Purpose |
|---|---|
| Product Name | Umbrella brand on the hero panel — defaults to "Vodafone" |
| Business / Store Name | This tenant's name — shown on the form card. Falls back to Product Name if blank |
| Tagline | One line under the wordmark |
| Business Logo | Shown above the sign-in heading |
| Primary Color | Drives the hero gradient, buttons, focus rings |
| Accent Color | Status dot + small highlights only — use sparingly |
| Hero Background | Gradient (default) or flat Solid using Primary Color |
| Show "Powered by" badge | Toggles a small footer credit line |

Click **Preview Login Page** on the form to open `/login` in a new tab
and see changes immediately (cache is cleared automatically on save).

## Multi-business / multi-site pattern

This is a **Single** doctype — one config per site. For your actual
use case (one Vodafone-branded programme, many separate SME
businesses), the pattern is:

- Each business = its own Frappe Cloud site/bench, as you're already
  doing.
- Install `brandlogin` on every site.
- Set **Product Name = "Vodafone"** (or whatever the umbrella brand is)
  identically on every site — that's the constant.
- Set **Business Name + Logo** per site — that's the only thing that
  changes per tenant.

If you'd rather manage all tenants' branding centrally instead of
per-site (e.g. from one admin site pushing config out to others via
API), that's a reasonable v2 — happy to sketch that out if you get
there; it's a bigger change (needs an API endpoint + a way to identify
which tenant is calling) so I kept this version to the single-site
case that matches your Frappe Cloud setup today.

## Notes / things to sanity-check on your exact instance

- `www/login.py` imports `frappe.www.login.get_context` and calls it
  first, then layers branding on top — this is the standard way to
  extend a core `www` page without duplicating its logic (social login
  providers, LDAP, signup, redirect-to handling, etc. all keep coming
  from core). If a future Frappe version renames that internal
  function, `bench migrate` will still run fine but you may see a
  Python import error on `/login` specifically — check
  `bench --site your-site.com console` → `from frappe.www.login import
  get_context` if that ever happens.
- The CSS uses `color-mix()` (for translucent tints of your brand
  color) — supported in all current evergreen browsers; if you need to
  support very old browsers, swap those lines for fixed rgba values.
- Google Fonts (Sora + Inter) load from `fonts.googleapis.com`. If your
  deployment must be fully offline/self-hosted, download the two
  font files and swap the `<link>` tags in `login.html` for a local
  `@font-face`.
- Favicon: if you set one in Login Branding Settings, it's applied to
  `/login` context but core's base template controls whether/how a
  `favicon` context variable renders — check the rendered `<head>` on
  your instance and adjust `www/login.py` if your version needs it
  passed differently.

## 5. The post-login module launcher

A second page, `/modules`, replaces the raw drop into Desk with a
branded hub — top bar (logo, business name, user, log out) and a grid
of the modules actually available on that site.

```
apps/brandlogin/brandlogin/
├── brandlogin/
│   ├── utils.py                       ← new
│   └── doctype/login_branding_settings/...
├── www/
│   ├── login.html / login.py
│   ├── modules.html                   ← new
│   └── modules.py                     ← new
└── public/css/
    ├── brand_login.css
    └── brand_modules.css              ← new
```

It does **not** hardcode a module list. It queries the `Workspace`
doctype for top-level public workspaces (`public=1`, no parent page) —
the same records Desk's own sidebar reads — so it automatically
reflects whatever's actually installed: if HRMS isn't installed on a
site, "HR" simply won't appear; a custom app's workspace shows up the
same way core ones do. `frappe.get_all` is permission-checked by
default, so a workspace's own Roles restriction is respected exactly
as it is in Desk — this app doesn't add or bypass any access control.

**This one needs one hooks.py line**, since redirecting away from Desk
is a real behavior change, not just a template swap. Open
`apps/brandlogin/brandlogin/hooks.py` and add:

```python
get_website_user_home_page = "brandlogin.utils.get_home_page"
```

This is Frappe's own documented extension point for "what does a
logged-in user see at `/`". `utils.get_home_page()` sends everyone to
`/modules` except Administrator, who still lands on `/app` — keep that
escape hatch, or every future `bench` debugging session gets routed
through the launcher too.

**Important caveat:** this controls where **`/`** resolves for a
logged-in user, which is also where core's login flow lands by
default. If anything in your setup explicitly redirects straight to
`/app` after login (a custom `redirect-to` link, a bookmarked URL,
etc.), that will still skip the launcher — the hook can't intercept a
request that never hits `/`. Test by logging in fresh and watching
where you land; if it's still `/app` directly, track down that
redirect and point it at `/modules` instead.

**Icons:** each card reads the workspace's own `icon` field and
renders it via Frappe's built-in icon sprite (`#icon-<name>`), the
same one Desk itself uses — so standard ERPNext workspaces (which
already have icons set) render correctly with zero extra config. A
workspace with no icon set falls back to a generic folder icon rather
than a blank card.

Reinstall steps are the same as the login page — `bench migrate`,
`bench build --app brandlogin`, `bench clear-cache` — since this is
just more files in the same app, not a separate install.

## Uninstall

```bash
bench --site your-site.com uninstall-app brandlogin
```

This restores core's default `/login` immediately.
