# Gotchas

One entry per thing this bucket, its CI or the tooling has pulled on us,
written as Symptom / Cause / Action so a reader can check whether it is the
same one. the "Gotchas" section of `SKILL.md` carries the index; add a line here the moment a
new one shows up.

- **A non-manifest `.json` anywhere in this package turns CI red.**
  Symptom: CI fails on a file that is plainly not a manifest.
  Cause: the bucket CI hands Scoop's manifest gate every changed path matching
  its `*.json` include pattern -- a `-like` match on the repo-relative path,
  anywhere in the tree, so the `-Path` argument narrows nothing -- and validates
  each against `schema.json`.
  Action: keep data in `assets/recipes.jsonc` (or a `.py` module). The suffix is
  the whole point -- `*.json` does not match `.jsonc` -- and the content stays
  strict JSON, since the rename dodges the gate rather than licensing comments
  (`json-parse` in skill-draft would reject those).
- **The installed bucket outranks the cwd, and a bad `--repo` is refused.**
  Symptom: run the script from inside a different checkout, pass no `--repo`,
  and the manifest lands in `$env:Scoop/buckets/extras-cn`; pass a `--repo` that
  is not a bucket root and the run stops.
  Cause: the script prefers the copy Scoop has installed over the cwd, and it
  treats a `--repo` it cannot recognise as an error rather than trusting it.
  Action: pass `--repo <path>` whenever you mean the checkout you are standing
  in.
- **Tauri's `*_x64-setup.exe` has no recipe of its own.**
  Symptom: `github-nsis-7z` over-fits it -- 7z reads the bundle directly and
  there is no `$PLUGINSDIR` payload for that recipe's `pre_install` to strip.
  Cause: Tauri's NSIS bundle is not electron-builder's, so the two shapes differ
  even though both arrive as a `-setup.exe`.
  Action: use `github-portable-zip` with the `#/dl.7z` fragment, then finish
  with `upd --set`, because that recipe emits neither hook: `pre_install`
  removing `$PLUGINSDIR` and `uninstall.exe` (Tauri writes it in lower case),
  and `suggest` `{"Microsoft Edge WebView2": "extras/webview2"}` -- the
  installer would have fetched WebView2 itself, a plain extraction cannot. The
  shortcut target is `<product>-desktop.exe`. Confirm both against
  `7z l <asset>`, which is also how the root tree gets checked. `autoclip` is
  the local example here; `chiri`, `handy` and `easytier-gui` are upstream ones.
- **The line-ending pass reaches outside this skill, and it is read-only.**
  Symptom: `lint` reports files under `bin/`, `scripts/` and `.github/`.
  Cause: `W112` walks the whole working tree, because `.editorconfig` demands
  CRLF for `[*]`; those directories belong to Scoop and to the repo's CI.
  Action: leave them alone. `--fix-format` normalises only the two things this
  skill owns, `bucket/*.json` and `README.md`, and a README sync writes CRLF
  unconditionally, so it cannot quietly strip the endings from a file it only
  meant to add one row to.
- **Valid `--section` values come from the README, not from the catalog.**
  Symptom: a section name that looks right is rejected, or one taken from
  `summary_sections` quietly does nothing.
  Cause: the values are validated against the sections actually parsed out of
  the README, falling back to `summary_sections` only when no README is present
  -- so the tables this repo happens to have decide what is acceptable.
  Action: pass the table's own heading (`外语学习` / `学术研究` / ...), read off
  the README rather than guessed. An unknown name is rejected up front with the
  list of valid values, so nothing is written and the README is left untouched.
- **A `{"script": ...}` checkver cannot be probed offline.**
  Symptom: `--checkver` reports that it cannot probe the manifest.
  Cause: the script form needs a live Scoop environment, which the command does
  not have.
  Action: run `bin/checkver.ps1` instead.
- **The self-check measures the installed bucket, not this package.**
  Symptom: `sm_selftest.py` fails on a manifest you have never touched.
  Cause: the round-trip and lint-baseline groups read
  `$Scoop/buckets/extras-cn`, which grows with every autoupdate commit -- the
  package ships no bucket of its own.
  Action: read the failure as news about the bucket rather than a broken skill;
  the package groups (catalog, docs, name) are the ones judging the package.
- **Plain `rumdl fmt` litters the directory it runs in.**
  Symptom: a `.rumdl_cache/` appears in whatever directory the command ran from.
  Cause: `fmt` caches into the cwd instead of a shared location.
  Action: always `rumdl fmt --no-cache`.
- **A vendor CDN can refuse a download URL that lacks its query string.**
  Symptom: every `francochinois.com` / `frdic.com` download answers
  `410 Gone` while the product page still links it, so `eshelper`,
  `frhelper`, `dehelper` and `eudic` cannot be installed from scratch.
  Cause: that nginx requires the `?v=` parameter the page carries; without
  it the path is refused, and `HEAD` stays refused even with it.
  Action: keep `?v=$version` in the download URL **and** in the autoupdate
  URL. The value is not validated (`?v=2026` serves the same bytes), so it
  is a cache-buster, not a version pin -- never try to resolve it.
- **`releases/latest` means "most recently published", not "newest version".**
  Symptom: the checkver resolves to a rolling tag that has no Windows
  asset, or `{"github": ...}` silently picks one.
  Cause: that endpoint ranks by `published_at`, so a long-lived snapshot
  release climbs back to the top whenever it is republished --
  `aigcpanel`'s `vsnapshot` outranked `v2.4.0` this way, while `releases`
  still orders by `created_at`.
  Action: scrape the `releases` list and anchor the regex on the asset path
  (`/releases/download/v([\d.]+)/AigcPanel-`), which drops non-numeric tags
  for free.
- **Tie the checkver tag to the autoupdate tag with a backreference.**
  Symptom: a version is detected but the autoupdate URL 404s.
  Cause: upstream renames tag schemes -- `qingjian` went from
  `windows-v0.1.3` to the unified `v0.1.4`, one tag now covering Windows,
  macOS and Linux -- while the URL template hard-codes `v$version`.
  Action: spell the asset out --
  `.../download/v([\d.]+)/qingjian-\1-windows-x86_64-setup\.exe` --
  because the backreference binds the tag to the asset version.
  Detection then fails loudly instead of quietly building a wrong URL the
  moment the schemes diverge again.
- **GitHub release assets publish their own sha256 now.**
  Symptom: nothing breaks, but Excavator downloads a 100 MB+ installer only
  to hash it.
  Cause: `assets[].digest` has been served since 2025 and Scoop's built-in
  `github` hash mode reads exactly that field, normalising the `sha256:`
  prefix away -- so `qingjian` and `aigcpanel` need no `autoupdate.hash`.
  Action: cross-check the value against the release's `SHA256SUMS` when it
  ships one; the asset API serves that file with
  `Accept: application/octet-stream` when
  `release-assets.githubusercontent.com` is unreachable.
- **A locked-down CDN can refuse the CI runner while accepting this machine.**
  Symptom: `Could not update adrive, hash for aDrive-6.9.3.exe failed!`
  with `(403) Forbidden`, though the same URL opens here and installs fine.
  Cause: the runner's network, not the request shape -- four header sets, a
  five-connection aria2 split (Scoop's default) and a plain GET all returned
  200 locally, on both the versioned `update/<v>/win32/x64/` path and the
  flat one.
  Action: hand `autoupdate` a `hash` source that never touches the
  installer. For `adrive` that is winget-pkgs' installer YAML
  (`InstallerSha256`), which cannot drift because the checkver reads the
  same project's commit log; confirm the extracted value against one real
  download before trusting it.
- **A Chinese WAF can cut the TLS handshake for the runner alone.**
  Symptom: `cajviewer: The SSL connection could not be established, see inner
  exception.` followed by `URL https://cajviewer.cnki.net/download.html is not
  valid`, every run, while that page opens here.
  Cause: the runner reaches the host and the handshake is cut -- .NET's wording
  for "TCP connected, TLS failed", so this is neither DNS nor routing. The host
  answers with `Set-Cookie: SF_cookie_<id>`, SafeLine's fingerprint, and
  `curl --noproxy '*'`, OpenSSL and .NET 4.8 all finish the same handshake from
  here: leaf plus GlobalSign intermediate, `verify return code: 0`, and TLS 1.2
  and 1.3 both offered. `.NET` failing where three local stacks succeed rules
  the client out; the runner's address is what changed.
  Action: no header set or request shape fixes this, so check whether a
  reachable page publishes the version before hunting for one -- for CNKI none
  does (`download.cnki.net` has no index, `oversea.cnki.net` does not mirror the
  config, and winget, Chocolatey and Scoop's Extras never carried either app).
  With no reachable source, drop `checkver`/`autoupdate` and leave the app
  manual; `lint-rules.md` lists the apps that already sit in E003's known set.
- **An `autoupdate.url` without any `hash` crashes Excavator on `Get-Member`.**
  Symptom: `Autoupdating uu-remote` is followed by
  `Get-Member: You must specify an object for the Get-Member cmdlet` at
  `lib/autoupdate.ps1:384`, and the manifest is still written afterwards.
  Cause: `Invoke-AutoUpdate` appends `hash` to the properties it refreshes
  whenever the autoupdate block carries a `url`. `Update-ManifestProperty`
  then takes the global branch only if `$Manifest.hash` exists; without one it
  falls into the per-arch branch and pipes `$Manifest.architecture` -- absent
  on a single-URL manifest -- into `Get-Member`. The error is
  non-terminating, so the version bump survives and only the log turns red.
  Action: add the real sha256, taken from the file the URL serves (and
  cross-checked against the CDN's own `x-goog-hash` when it publishes one:
  `uu-remote`'s redirect target is a plain file on GCS that carries md5 and
  crc32c). Four more manifests here carry the same latent gap -- `aboboo`,
  `aboboo-full`, `evplayer`, `partition-assistant` -- and only fire on their
  next release, so they need no fix until then. Re-deriving one is a plain
  download and these hosts are slow: `aboboo`'s Portable is 133 MB and its
  Full is 1.6 GB, measured at roughly 100 KB/s on one connection with no
  multi-connection gain (the CDN answers `CN:1` however many segments are
  asked for, and protests with a 200-wrapped "拒绝服务" page when a second
  process joins in).
- **A vendor CDN can throttle concurrent fetches, and that breaks a probing checkver.**
  Symptom: `bin/checkver.ps1 <app>` reports `couldn't match ... in the output of
  script` while a hand-run `curl -I` of the very same URL answers `200` seconds
  later; stopping the unrelated downloads and re-running makes it pass.
  Cause: aboboo's download host refuses a second process fetching anything from
  the same source -- and it does so with **HTTP 200 plus an HTML "拒绝服务"
  page**, not a 4xx -- so every probe inside the script throws and the version
  silently comes out empty.
  Action: run probing checkvers serially, after all downloads finish. When a
  script checkver fails, re-check its URLs with `curl` before blaming the script.
- **A derived package can lag its own main version.**
  Symptom: the URL template `.../Aboboo.Full.$version.zip` 404s for the version
  the main app reports.
  Cause: `aboboo-full` trails `aboboo` -- 3.13.1 existed as Portable only, while
  Full stopped at 3.12.1, and nothing on the site says so.
  Action: probe downward in the script form: the current version first, then
  `oldClientInfo`, then the same minor's lower builds, then the previous minor.
  The page's `oldClientInfo` is the previous release and usually already exists
  in the derived channel, so the loop normally stops on the second try.
- **Version strings on SPA sites must be mined, not scraped.**
  Symptom: a regex over a homepage yields a number that is obviously wrong --
  `edgeless` reported version `8` for months, which every autoupdate then built
  into a nonexistent `..._Beta_8.7z`.
  Cause: `([\d.\d+])` is a character class, not a version pattern, so it matched
  the `8` in `charset="UTF-8"`; a Vue/Angular shell carries no version in its
  HTML at all.
  Action: go to the machine-readable source. `edgeless` has an API
  (`https://legacy.edgeless.top/api/v2/info/hub`, `jsonpath $.version`) and
  serves downloads through the same host's `api/v2/redirect?path=...`, which
  302s to a fresh signed URL -- prefer it over a hard-coded zfile `?sign=`, and
  remember spaces in the path must be `%20`. `aboboo` inlines
  `window.clientInfo` / `oldClientInfo`. `kingdraw` keeps its URLs in
  `js/public.js`, reachable only on `https://www.kingdraw.cn` (the bare
  `http://kingdraw.cn` host answers 403 for every path).
- **An empty `changed` list used to swallow `--readme`.**
  Symptom: the homepage moved, the README table still shows the old link, and
  `upd --name X --readme` only prints `nothing to change.`
  Cause: `cmd_update` returned early on `not changed`, and the README sync sits
  after that return -- so a README-only resync could never be requested, even
  though a moved homepage is exactly what makes one necessary.
  Action: fixed in `scoop_manifest.py` (`if not changed and not args.readme`),
  and the manifest is now left untouched when only `--readme` is asked for. The
  section name still has to be the table's own heading, e.g.
  `--readme --section 外语学习`.
- **`checkver.script` is PowerShell, and it hides two traps.**
  Symptom: the script works when pasted into a console but returns nothing under
  Scoop, or returns a number that appears nowhere in the page.
  Cause: (1) PowerShell variable names are **case-insensitive**, so `$M` and
  `$m` are one variable and `$Maj` / `$Min` / `$Bld` are the safe spelling;
  (2) Scoop runs it via `Invoke-Command ([scriptblock]::Create($script -join
  "`r`n"))`, and anything the script prints joins the captured text, so a bare
  `([\d.]+)` regex can lock onto noise.
  Action: give the last line a marker -- `"VERSION=$found"` matched with
  `"regex": "VERSION=([\\d.]+)"` -- and set
  `$ProgressPreference = 'SilentlyContinue'` first.
- **Upstream can repack the same version, silently invalidating the hash.**
  Symptom: installation fails hash verification although the version and the URL
  never moved, so `scoop update` stops working for a package nobody touched.
  Cause: the 2.32 `edgeless` 7z was rebuilt in place -- the old `ceed1177...`
  no longer matches, while the new digest `ce748483...` reproduced across two
  independent downloads.
  Action: after repairing a checkver, re-download and compare; a working
  checkver says nothing about the hash, and the bytes behind an unchanged URL
  can still have moved.
