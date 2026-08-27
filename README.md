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

This repository is a complete, installable Frappe app (`pyproject.toml`,
`hooks.py`, the whole scaffold) — you don't need to run `bench new-app`
or hand-copy files into one; `bench get-app` this repo directly.

## 1. Install

```bash
cd ~/frappe-bench
bench get-app brandlogin https://github.com/ERPION2025/ERPNext-Whitelabled-Login-Menu-for-v16.git
bench --site your-site.com install-app brandlogin
bench --site your-site.com migrate
bench build --app brandlogin
bench --site your-site.com clear-cache
```

On Frappe Cloud: add this repo URL as a custom app to your **Private
Bench Group** (Dependencies/Apps tab) — it'll pass the app-validation
check because `pyproject.toml` lives at the repo root — then install it
on the site the same way as any other app from the dashboard.

`www/login.py` and `www/login.html` override core's `/login` purely by
matching Frappe's file-based routing (an app's `www/<path>` takes
precedence over an earlier-installed app's page of the same name), and
the CSS is linked directly inside `login.html`'s own `head_include`
block, so it never leaks into the rest of Desk.

## 2. Configure branding

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

## The post-login module launcher

A second page, `/modules`, replaces the raw drop into Desk with a
branded hub — top bar (logo, business name, user, log out) and a grid
of the modules actually available on that site.

It does **not** hardcode a module list. It queries the `Workspace`
doctype for top-level public workspaces (`public=1`, no parent page) —
the same records Desk's own sidebar reads — so it automatically
reflects whatever's actually installed: if HRMS isn't installed on a
site, "HR" simply won't appear; a custom app's workspace shows up the
same way core ones do. `frappe.get_all` is permission-checked by
default, so a workspace's own Roles restriction is respected exactly
as it is in Desk — this app doesn't add or bypass any access control.

Redirecting away from Desk is a real behavior change, not just a
template swap, so this ships with three `hooks.py` entries already
wired up:

```python
get_website_user_home_page = "brandlogin.utils.get_home_page"
on_login = ["brandlogin.utils.on_login"]
before_request = ["brandlogin.utils.before_request"]
```

`get_website_user_home_page` is Frappe's own documented extension
point for "what does a logged-in user see at `/`" — but on a real
ERPNext account it's **not enough by itself**, which is why login used
to appear branded while everything past it stayed default Desk:

- Core's `frappe.website.utils.get_home_page()` has a **"Default
  Workspace"** check that runs after everything else, including this
  hook, and silently overrides its result the moment a user has ever
  pinned a workspace from the Desk sidebar — normal, common state on
  any real account, just not on a freshly created one. The only thing
  that wins over that check is `frappe.local.flags.home_page`, so
  `on_login` and `before_request` set that flag directly instead of
  relying on the hook alone.
- `on_login` (not just `before_request`) is required because the very
  first `/api/method/login` call resolves and finishes inside
  `HTTPRequest.set_session()` — which runs *before* `before_request`
  hooks do — so by the time `before_request` would fire, the login
  response's own `home_page` field (what `login.js` uses to send the
  browser somewhere immediately after signing in) has already been
  computed. `on_login` fires early enough inside that same login flow
  to still catch it. `before_request` then covers the other case:
  an already-logged-in user visiting bare `/` on some later request,
  where no login is happening and `before_request` runs early enough
  on its own.

Both `on_login` and `before_request` send everyone to `/modules`
except Administrator, who still lands on `/app` — keep that escape
hatch, or every future `bench` debugging session gets routed through
the launcher too. (Note `utils.py` lives at the app's package root —
`brandlogin/utils.py` — since that's the path these hooks' dotted
strings actually import; it's *not* nested under the
`brandlogin/brandlogin/` module folder alongside the doctype, easy to
get backwards if you're moving files around.)

**Remaining caveat:** all of the above controls where **`/`** and the
login response resolve. If anything in your setup explicitly
redirects straight to `/app` by some *other* route (a custom
`redirect-to` link, a bookmarked URL to `/app` itself, an API
integration that logs users in and sends them elsewhere directly),
that will still skip the launcher, since nothing here can intercept a
request that never asks for `/` or goes through this app's login
response. Test by logging in fresh and watching where you land.

**Icons:** each card reads the workspace's own `icon` field and
renders it via Frappe's built-in icon sprite (`#icon-<name>`), the
same one Desk itself uses — so standard ERPNext workspaces (which
already have icons set) render correctly with zero extra config. A
workspace with no icon set falls back to a generic folder icon rather
than a blank card.

## Uninstall

```bash
bench --site your-site.com uninstall-app brandlogin
```

This restores core's default `/login` immediately.
