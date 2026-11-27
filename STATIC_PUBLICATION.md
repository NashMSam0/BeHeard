# Static public site and Flask founder dashboard

Production rollout completed on 27 November 2026. The public site is live at
https://beheard-public.onrender.com/. The Flask service at
https://beheard-zimbabwe.onrender.com/ remains the sole durable state writer and
serves the founder dashboard. Public page requests redirect to the static site.
Automatic production deployment through the private hook is verified. A separate
staging site is available. No custom domain has been connected.
See README.md for current content and remaining work.

## Publication path

1. Founder authentication, CSRF checks and revision checks remain in Flask.
2. Published news and immediately saved page edits update the working public HTML.
   Draft news and draft photographs remain solely in SQLite.
3. Flask renders a candidate export using the same homepage/news and gallery code
   as its public views. The export uses the explicit list in `public_manifest.py`.
4. The existing Supabase snapshot save must succeed before this export becomes
   available. The snapshot format stays `{database, pages}` and the same revision
   compare-and-swap protects it. No database schema or RLS changes are needed.
5. A changed public digest triggers the server-only Render deploy hook. The
   destination and submitted digest are recorded in private SQLite and the durable
   snapshot. Draft saves, logins and unchanged restarts do not redeploy the site.
6. The static build uses a separate bearer token to fetch
   `/publication/artifact.zip`. It has no Supabase credentials or database access.
   The endpoint checks its cloud revision before serving, rejecting retiring
   instances that no longer match durable storage.
7. `build_static.py` checks the exact file list, hashes, canonical origin, archive
   size, duplicate filenames and unsafe entries before writing a fresh output
   directory. Errors fail the build without falling back to repository content.
   Render keeps the previous successful static deployment available during builds.

The artifact includes all nine public pages, the current styles and shared script,
approved JPEG and MP4 assets, embedded published photos, static canonical/Open
Graph tags, `robots.txt` and `sitemap.xml`. It excludes `editor.js`, templates,
Python files, SQLite, settings, drafts, snapshot payloads and environment files.
Configured credential values are also checked against outgoing bytes. The public
site makes no request to Flask or Supabase when visitors view its pages.

## Failure and retry behavior

A failed durable save returns HTTP 503 and restores the durable snapshot. It never
triggers publication of unconfirmed content. If restoration also fails, founder
access and exports are blocked until restart. Storage details and secrets are not
printed in these errors.

A failed deploy-hook request leaves the saved content intact and a pending status
on the dashboard. It retries on the next successful founder request/dashboard
visit or process startup, with a one-minute retry limit for the same release.
**Retry static deployment** can also resend an accepted request when the subsequent
Render build failed. Delivery is at least once: a crash between accepting a hook
and saving its acknowledgement can cause one duplicate build. No timer, worker,
keep-alive monitor or paid job service is introduced.

A hook acknowledgement means that Render accepted a build, not that it went live.
The dashboard says this explicitly. Check Render deployment status and compare the
candidate site's `release.json` digest with the export response's
`X-BeHeard-Release` header. New changes made during a build enqueue another deploy.
Publication and withdrawal take effect on the CDN after a successful build; while
that build runs, the previous public revision remains visible.

## Environment boundaries

| Setting | Existing Flask service | Static build |
| --- | --- | --- |
| Existing `BEHEARD_STATE_*` | Preserve all current values | Never provide |
| Existing founder hash/generation/session settings | Preserve; never run setup | Never provide |
| `BEHEARD_EXPORT_TOKEN` | Private random token, at least 32 ASCII characters | Same private token, build environment only |
| `BEHEARD_STATIC_DEPLOY_HOOK` | Candidate static site's secret deploy hook | Never provide |
| `BEHEARD_EXPORT_URL` | Not needed | Existing admin HTTPS origin + `/publication/artifact.zip` |
| `BEHEARD_PUBLIC_URL` | Canonical public HTTPS origin | Same canonical origin |
| `BEHEARD_STATIC_STAGING=1` | Not needed | Staging only: noindex HTML and disallow robots |
| `BEHEARD_ADMIN_ONLY=1` | After traffic cutover: noindex all admin responses | Not needed |

Supply secrets through Render's private environment settings. Never paste them into
commands, URLs, commits, screenshots, logs or this document. No token is generated
or rotated by the migration code. Existing `sync: false` variables are retained;
Render only prompts for these on initial Blueprint creation, so new secrets on an
existing service must be added manually. Never replace the service's environment
variable collection.

## Safe staging and rollout

1. Review and merge the staged code only after completing the following gates.
   The current live service deploys `main` automatically; a merge can deploy it.
   Do not change that live branch to the staging branch or provision another Flask
   instance using the production state row. An isolated admin test requires a
   separate snapshot datastore with separate credentials.
2. Check the Render workspace's remaining included build minutes/bandwidth and its
   spending controls before any cloud build. Check GitHub runner allowances before
   running the optional manual workflow. No paid plan, disk, cron, worker or new
   database is required. A free base service does not guarantee zero overage costs.
3. Take a private, consistent backup of the existing durable snapshot and record
   its revision. Verify restore in isolation. Do not reset the founder password.
   This implementation's tests use disposable fake cloud state and do not write
   to the production snapshot.
4. Deploy the backwards-compatible Flask changes to the existing Python service
   while it still serves the public address. Preserve its Supabase and founder
   settings. Initially leave the new hook/token unset: ordinary behavior remains
   available. Then configure the export token privately and verify authenticated
   export; unauthenticated requests must be 404. Cloud state must be available.
5. Use `render.staging.yaml` for a **static-only** staging service on the staging
   branch, with the export URL/token configured privately. It declares no custom
   domain, disk, paid compute or second state writer. It requires the export route
   from step 4. `render.yaml` describes the existing free admin and a separate
   static candidate; it also defaults the static site to noindex staging mode.
   Both set automatic Git deploys off. Do not blindly create/adopt the whole
   Blueprint: review which existing resource each name will manage first.
6. Point the Flask hook at the staging static site. Verify all nine pages, media,
   mobile navigation, themes, slideshow controls, videos and SEO. Confirm a founder
   draft never appears, a published edit appears, a withdrawal disappears, and a
   restart restores credentials, drafts and content. Use an isolated admin test for
   mutations; do not publish dummy test text on the production website.
7. Verify failed export/build leaves the previous static release visible. Match
   release digests. Confirm the existing founder login works over HTTPS and
   unconfigured/missing secrets fail closed. Neither this branch nor this work
   claims that these hosted checks have been completed.
8. Only after those gates, select the final public origin/custom domain. Set
   `BEHEARD_PUBLIC_URL` consistently on admin and static builds, turn
   `BEHEARD_STATIC_STAGING` off, and remove the static `X-Robots-Tag: noindex`
   header. Rebuild and verify canonical tags and the sitemap before switching DNS.
   Add founder redirects to the admin origin if the new public domain needs to
   accept `/founder/` bookmarks. Keep the founder's admin URL recorded separately.
9. Retain the old Flask service and its durable state for rollback. Enable
   `BEHEARD_ADMIN_ONLY=1` only after traffic has moved; its previews continue to
   function but responses are noindex. The former `beheard-zimbabwe.onrender.com`
   hostname cannot be assigned to the new static service: use its new hostname or
   an approved custom domain. Do not rename/delete production to try to transfer it.

Rollback: direct the public domain back to the existing Flask service, unset
`BEHEARD_ADMIN_ONLY`, and stop the static deploy hook. Retain the latest Supabase
snapshot; do not restore an older snapshot over newer founder changes. If code must
be rolled back, the older app ignores the additional private `static_submitted`
setting and understands the unchanged snapshot format.

## Local verification

```powershell
python -m unittest discover -s tests -v
node --check dist/site.js
node --check dist/editor.js
python export_public.py --output .openai/review-public.zip
$env:BEHEARD_PUBLIC_URL = 'https://beheard-zimbabwe.onrender.com'
$env:BEHEARD_STATIC_STAGING = '1'
python build_static.py --artifact .openai/review-public.zip --output .openai/review-site
python -m http.server 8768 --bind 127.0.0.1 --directory .openai/review-site
```

Use fresh output names: the exporter and builder refuse to overwrite existing
artifacts. The offline exporter reads public files only, without opening the local
database or running content migrations. It is for review, not a substitute for a
confirmed live snapshot. `public-build/`, `.openai/`, `.beheard/`, `.env*` and private
database files stay excluded from Git.

Verified locally on 26 November 2026: 20 isolated regression tests; Python compilation;
JavaScript syntax; both Blueprints against Render's current JSON Schema; and browser
checks at phone/desktop sizes, light/dark themes, scrolling, homepage news, grouped
gallery, navigation, story slideshow and education tabs. The browser reported no
broken loaded images, video media errors or JavaScript console errors in the checked
views. Full hosted publication, DNS and actual founder password entry remain
unverified. The optional GitHub workflow is manual to avoid automatic runner costs.

Pre-existing local changes to `dist/programmes.html`, `dist/stories.html` and the
absence of local `christmas_event.py` are preserved outside the migration commit.
The migration does not publish those local differences to GitHub. Live export uses
the existing durable public state rather than overwriting it with a local copy.

## Prepared Render plan

On 26 November 2026, after workspace confirmation, Render successfully planned
`render.staging.yaml` in My Workspace. The plan proposes exactly one new static
service, `beheard-public-staging-0tdy`, and no changes to the existing Flask service.
Automatic Blueprint syncing and Git-triggered deploys are disabled; no custom
domains, compute workers, disks or databases are included. The plan requires a
private `BEHEARD_EXPORT_TOKEN`. It has **not** been approved or deployed.

[Review the staging plan](https://dashboard.render.com/blueprint/exs-dc43go49v7es73dorcug/sync/exe-dc43goc9v7es73dordkg).
The live export route, private token/hook configuration, verified free usage
allowances, a private backup and hosted verification are still deployment gates.

References: [Render static sites](https://render.com/docs/static-sites),
[deploy hooks](https://render.com/docs/deploy-hooks),
[Blueprint specification](https://render.com/docs/blueprint-spec), and
[Supabase API security](https://supabase.com/docs/guides/api/securing-your-api).
