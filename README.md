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
template swap, so this ships with two `hooks.py` entries already
wired up:

```python
get_website_user_home_page = "brandlogin.utils.get_home_page"
after_request = ["brandlogin.utils.after_request"]
```

The "obvious" approach — just the `get_website_user_home_page` hook,
or setting `frappe.local.flags.home_page` from an `on_login`/
`before_request` hook — is a *computation* that has to win against
every other installed app's opinion about where a user should land:
their own `get_website_user_home_page` hook, their own `on_login`
hook, a per-user Default Workspace saved from the Desk sidebar, etc.
Whichever one happens to run last for a given hook wins, and on a site
with several other apps installed (which is the normal case, not the
exception — that's the whole point of installing ERPNext), that's
other apps' code, not something this app can reliably control. In
practice that showed up exactly like this: login stayed branded
(nothing about the login page depends on any of this), but everything
past it kept landing wherever some other app's hook — or plain old
Default Workspace — said to.

`after_request` sidesteps that race entirely by not trying to win a
computation at all. It runs *after* every hook has had its say and the
response is fully built, so it just directly rewrites the final output
for the two places a home page actually gets read:

- `POST /api/method/login` — corrects the JSON response's `home_page`
  field, which is what `login.js` uses to send the browser somewhere
  immediately after signing in.
- `GET /`, `/app`, `/desk` (bare, no sub-path) — turns the response
  into a redirect to `/modules` outright, regardless of what page it
  was originally going to render. A deep link into a specific
  workspace (`/app/some-workspace`) is left alone, so Desk navigation
  afterwards isn't affected — only these bare landing routes are.

Both send everyone to `/modules` except Administrator, who still lands
on `/app`/`/desk` as normal — keep that escape hatch, or every future
`bench` debugging session gets routed through the launcher too. (Note
`utils.py` lives at the app's package root — `brandlogin/utils.py` —
since that's the path these hooks' dotted strings actually import;
it's *not* nested under the `brandlogin/brandlogin/` module folder
alongside the doctype, easy to get backwards if you're moving files
around.)

**Remaining caveat:** all of the above controls where `/`, `/app`,
`/desk`, and the login response resolve. If anything in your setup
redirects straight into a *specific* workspace by some other route (a
custom `redirect-to` link, a bookmarked deep link, an API integration
that logs users in and sends them elsewhere directly), that will still
skip the launcher, since nothing here touches a request for a path
that isn't one of the bare landing routes above. Test by logging in
fresh and watching where you land.

**Icons:** each card reads the workspace's own `icon` field and
renders it via Frappe's built-in icon sprite (`#icon-<name>`), the
same one Desk itself uses — so standard ERPNext workspaces (which
already have icons set) render correctly with zero extra config. A
workspace with no icon set falls back to a generic folder icon rather
than a blank card.

## Theming the rest of Desk

Login and the launcher are one thing — the actual ERPNext workspace
you land in afterwards is another. This app also recolors Desk itself
using the same Primary/Accent Color you already set once in **Login
Branding Settings**, no separate configuration:

- Primary buttons, borders, checkboxes/radio buttons, focus rings, and
  the left sidebar's active-item highlight, across **every** doctype's
  list view and form view.
- **Not per-app.** This works by overriding Frappe's own theme CSS
  custom properties (`--primary`, `--btn-primary`, `--border-primary`,
  `--focus-default`, `--sidebar-active-color` — the same ones its own
  light/dark toggle switches between) at the Desk-shell level, once,
  via `app_include_js`. Every installed app — ERPNext, HR & Payroll,
  POSNext, a CRM, whatever else — renders its doctypes, forms, and
  lists inside that same shell and reads those same variables, so this
  isn't something that has to be repeated or configured per app.
- **How it works:** `extend_bootinfo` (`brandlogin.utils.extend_bootinfo`)
  hands the Primary/Accent Color to the client once per Desk session as
  `frappe.boot.brandlogin`; `public/js/brand_desk.js`
  (`app_include_js`) reads that and sets the CSS variables as inline
  styles on `<html>` — which, being inline, beats any stylesheet rule
  regardless of light/dark mode, so it doesn't need to hook the theme
  switcher separately.
- **Scope, honestly:** this covers Frappe's own foundational theme
  variables — the surface Frappe itself designed to be the "theme-able"
  one, and what drives the overwhelming majority of what you see in
  normal use. It won't reach a genuinely bespoke widget some other app
  hardcodes its own colors into (charts, a custom report, etc.) instead
  of reading these variables — if you hit one, it needs its own
  targeted CSS, the same as any other one-off override would.

**"Powered by ERPNext" → "Powered by \<Product Name\>":** core's own
website footer template (any ordinary `/`-style web page, not Desk)
has a `footer_powered` context variable that, when set, replaces its
hardcoded "Powered by ERPNext" credit line. `update_website_context`
(`brandlogin.utils.update_website_context`) fills that in from the
same Product Name field as everywhere else, so it reads "Powered by
Vodafone" by default, or whatever tenant name you set, without editing
core templates.

## Uninstall

```bash
bench --site your-site.com uninstall-app brandlogin
```

This restores core's default `/login` immediately.
