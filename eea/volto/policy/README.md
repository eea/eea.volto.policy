# Overview

eea.volto.policy is the EEA Volto policy package for Plone.

It keeps stock Plone in place and layers EEA-specific REST API, navigation,
imaging, moderation, and admin behavior on top of it for Volto sites.

# What changes from stock Plone?

The addon changes behavior in these areas:

- REST API endpoints and expandable components used by Volto navigation,
  breadcrumbs, actions, context navigation, and control panel listing.
- Field and block serialization/deserialization, with inheritance support and
  Volto-oriented link/image transforms.
- Catalog metadata and image scale/indexer behavior for inherited images.
- Workflow/content-rule and browser maintenance views for migrations and URL
  cleanup.
- GenericSetup profiles and upgrades (registry records, multilingual query
  support, browser layer wiring).

# Table of Contents

- [REST API and Volto integration](#rest-api-and-volto-integration)
- [Block and content serialization](#block-and-content-serialization)
- [Images and catalog data](#images-and-catalog-data)
- [Workflow and administration](#workflow-and-administration)
- [Profiles and upgrades](#profiles-and-upgrades)
- [Installation](#installation)

# REST API and Volto integration

- `restapi/navigation/navigation.py` (`@navigation`):
  - If a nav brain has `getRemoteUrl` (for Link-like entries), the API uses
    the remote URL path as tree path input.
  - For anonymous users, `@id` is rewritten to the remote URL (via
    `uid_to_url`) so Volto links directly to the external target.
  - Tree rendering skips recursion when an item has no `path` key, preventing
    crashes seen in custom nav renderers.

- `restapi/services/contextnavigation/get.py` (`@contextnavigation`):
  - Extends navigation portlet input schema with `portal_type` filtering.
  - Falls back to registry `plone.side_nav_types` when no `portal_type` is
    passed.
  - Forces nav query path to the computed root path, with `navtree: 1`.
  - Special-cases `currentFolderOnly` on site root and report-navigation
    add-form flows to avoid expensive/noisy queries.
  - Adds `side_nav_title` support in root/items, includes `getObjSize` for
    `File` items, and allows intentionally empty title values.
  - Uses `level <= bottomLevel` recursion, effectively showing one extra
    level compared to stricter recursion.

- `restapi/services/breadcrumbs/get.py` + `browser/breadcrumbs.py`
  (`expand=breadcrumbs`):
  - Uses `@@eea_breadcrumbs_view` when available.
  - Adds `portal_type` to each breadcrumb item and prefers `nav_title` when
    present.
  - Falls back to stock breadcrumb adapter if custom view is unavailable.

- `restapi/services/actions/get.py` (`expand=actions`):
  - Returns almost all action properties, excluding only selected UI flags
    (`category`, `link_target`, `available`, `visible`, `allowed`,
    `modal`).
  - Translates action titles before returning payload.

- `restapi/services/controlpanel/*.py`
  (`@controlpanels` via `restapi/services/controlpanel/overrides.zcml`):
  - Keeps strict service permission and then enforces panel-specific runtime
    permission checks.
  - Returns explicit `401`/`403`/`404` style responses based on panel
    existence and caller access.

# Block and content serialization

- `inherit.py` + `restapi/serializer/dxfields.py`:
  - `InheritableFieldSerializer` and `InheritableImageFieldSerializer` read
    registry `eea.volto.policy.inherit.fields` and, when local value is
    empty, serialize the first viewable ancestor value instead.

- `restapi/serializer/dxfields.py`:
  - Publication/coremetadata datetime serializer uses callable field accessors
    (`context.<field>()`) so timezone-sensitive values are preserved.
  - Primary file target adapter returns `None` for `file` field, disabling
    stock primary-file target URL behavior in this addon context.

- `restapi/deserializer/dxfields.py`:
  - Publication/coremetadata datetime deserialization normalizes input using
    site default timezone and strips `tzinfo` before final validation.

- `restapi/serializer/summary.py`:
  - Summary metadata default set includes `effective` (in addition to the
    common summary fields).

- `restapi/blocks.py`:
  - HTML block deserializer converts `href`/`src` to `resolveuid` form
    (removing `/@@download/image` first when present).
  - HTML block serializer resolves `resolveuid` back to URLs and appends
    `/@@download/image` for image links.
  - Slate block serializer resolves image `resolveuid` links to downloadable
    URLs.
  - Restricted block transformer replaces restricted blocks with
    `{"@type": "empty"}` when user/group allow/deny and permission checks
    fail.
  - Context navigation block transformer sets `results` based on renderer
    availability and can derive `root_path` from configured root node.
  - Version block transformers set boolean `results` for
    `eea_versions`/`eea_latest_version` based on available versions.

- `restapi/serializer/blocks.py` + `restapi/serializer/__init__.py`:
  - Monkey patch for teaser serializer keeps non-http unresolved `href` values
    instead of clearing them, preserving teaser source data that stock logic may
    drop.

# Images and catalog data

- `profiles/default/catalog.xml`:
  - Adds catalog metadata columns: `image_scales` and `side_nav_title`.

- `indexers.py` (+ wired in `overrides.zcml`):
  - `hasPreviewImage` and `image_field` indexers become inheritance-aware.
  - If local preview/image fields are empty, indexer may reuse inherited parent
    field values.

- `image_scales/adapters.py`:
  - Image scale serialization supports inherited image fields.
  - For inherited images, payload includes `inherited_from` metadata.
  - Download paths are normalized so child content can reference parent image
    scales with relative `@@images` paths.
  - On Plone 6, wrapper adapter uses stock behavior for local images and falls
    back to inheritance-aware logic when local image is missing.

- `image_scales/indexer.py`:
  - Stores serialized scale data in catalog metadata as `PersistentDict` when
    scale info exists.

- `profiles/default/registry.xml`:
  - Overrides imaging `plone.allowed_sizes` defaults (includes EEA sizes like
    `tiny`, `small`, `medium`, `big`, `huge` values used by Volto
    setups).

# Workflow and administration

- `contentrules/actions.py` + `profiles/default/contentrules.xml`:
  - Registers content-rule action
    `eea.volto.policy.set_publication_date_to_null`.
  - Default installed rule triggers on successful action events when workflow
    state becomes `private` and clears publication date
    (`setEffectiveDate(None)`).

- `browser/controlpanel.py` + `profiles/default/controlpanel.xml`:
  - Adds `@@internal-api-path-controlpanel` configlet
    ("Internal API Path Correction").
  - Form stores replacement URL list in registry and provides a direct trigger
    button for the rewrite job.

- `browser/update_internal_api_path.py`:
  - `@@update-internal-api-path` scans catalog content in batches and rewrites
    configured backend URL prefixes to site-relative paths.
  - Recursively processes strings, RichText, dict/list values, and blocks.

- `browser/teaser.py`:
  - Provides `@@teaser-migrate` and `@@teaser-layout-migrate` utilities to
    migrate `teaserGrid` blocks to Volto `gridBlock` structures (content and
    DX layout definitions).

- `browser/image.py` + `upgrades/attached_images.py`:
  - `@@image-migrate` migrates block image references to resolveuid-style
    image objects for configured block types/fields.
  - Returns JSON with migration logs and processed summary.

- `subscribers.py` + `configure.zcml`:
  - On Dexterity modification, if a configured inheritable field changed,
    descendant objects that inherit that field are reindexed.

- `viewlets.zcml`:
  - Exposes key Classic UI managers/viewlets as public on this browser layer so
    error pages under private parents still render header/navigation resources.

- `permissions.zcml`:
  - Defines custom permission `EEA: Manage restricted blocks` used by
    restricted block serialization checks.

- `vocabularies/principals.py` (+ utility override in `overrides.zcml`):
  - Replaces users vocabulary factory with one that returns users having
    `fullname` and includes user email in serialized term JSON.

# Profiles and upgrades

- `profiles/multilingual/registry/plone.app.querystring.field.Language.xml`:
  - Enables QueryString "Language" field with supported-content-languages
    vocabulary for multilingual criteria building.

- `profiles/default/registry.xml` + `profiles/to_83/registry.xml` +
  `profiles/to_110/registry.xml`:
  - Registers internal API replacement settings, batch progress state, and
    inheritable fields settings.

- `upgrades/upgrade_svgs/upgrade_svg.py`:
  - Recomputes SVG width/height when broken and clears cached scale annotation
    for corrected rendering.

# Installation

- Add `eea.volto.policy` to your buildout or backend package set.
- Re-run buildout or restart the backend.
- Activate `eea.volto.policy` in `Site Setup > Add-ons`.
