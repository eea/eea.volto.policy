"""Helpers for detecting and resolving duplicate layout-block UUIDs."""

import copy
import uuid


def collect_block_uuids(blocks, layout_items, location="top-level"):
    """Yield (uuid, location) for blocks referenced by ``layout_items``.

    Only UUIDs actually listed in ``blocks_layout.items`` are visited —
    orphan entries in ``blocks`` (unreachable from the rendered page) are
    ignored, since duplicates among them have no runtime effect.

    Handles both layout-block variants: nested blocks stored directly on
    the parent (``block["blocks"]``, e.g. gridBlock) and nested blocks
    stored under ``block["data"]`` (e.g. Section / Columns).
    """
    if not isinstance(blocks, dict) or not isinstance(layout_items, list):
        return
    for block_uuid in layout_items:
        block = blocks.get(block_uuid)
        if block is None:
            continue
        if not isinstance(block, dict):
            continue
        if block.get("@type"):
            yield block_uuid, location
        nested = block.get("blocks")
        nested_layout = block.get("blocks_layout") or {}
        if isinstance(nested, dict):
            yield from collect_block_uuids(
                nested, nested_layout.get("items"), location=f"block:{block_uuid}"
            )
        data = block.get("data")
        if isinstance(data, dict):
            data_blocks = data.get("blocks")
            data_layout = data.get("blocks_layout") or {}
            if isinstance(data_blocks, dict):
                yield from collect_block_uuids(
                    data_blocks,
                    data_layout.get("items"),
                    location=f"block:{block_uuid}/data",
                )


def find_duplicates(blocks, blocks_layout):
    """Return duplicate-UUID issue dicts for a single content item."""
    layout_items = (blocks_layout or {}).get("items")
    seen = {}
    for block_uuid, location in collect_block_uuids(blocks, layout_items):
        seen.setdefault(block_uuid, []).append(location)
    return [
        {
            "block_uuid": block_uuid,
            "occurrences": len(locations),
            "locations": locations,
        }
        for block_uuid, locations in seen.items()
        if len(locations) > 1
    ]


def _new_uuid():
    return str(uuid.uuid4())


def _regenerate_subtree_uuids(blocks, layout_items, location, rewrites):
    """Replace every UUID inside a freshly copied subtree.

    When a block is duplicated (deep-copied), every nested UUID in the
    copy also collides with the original subtree. Rewrite all of them
    unconditionally so the copy is fully disjoint.
    """
    if not isinstance(blocks, dict) or not isinstance(layout_items, list):
        return
    old_keys = list(blocks.keys())
    key_map = {old: _new_uuid() for old in old_keys}
    for old_key, new_key in key_map.items():
        blocks[new_key] = blocks.pop(old_key)
    for i, old in enumerate(layout_items):
        if old in key_map:
            layout_items[i] = key_map[old]
    for old_key, new_key in key_map.items():
        rewrites.append(
            {
                "old": old_key,
                "new": new_key,
                "location": location,
                "reason": "regenerated-in-copied-subtree",
            }
        )
        block = blocks.get(new_key)
        if not isinstance(block, dict):
            continue
        nested = block.get("blocks")
        nested_layout = block.get("blocks_layout") or {}
        if isinstance(nested, dict):
            _regenerate_subtree_uuids(
                nested,
                nested_layout.get("items"),
                f"block:{new_key}",
                rewrites,
            )
        data = block.get("data")
        if isinstance(data, dict):
            data_blocks = data.get("blocks")
            data_layout = data.get("blocks_layout") or {}
            if isinstance(data_blocks, dict):
                _regenerate_subtree_uuids(
                    data_blocks,
                    data_layout.get("items"),
                    f"block:{new_key}/data",
                    rewrites,
                )


def _rewrite_container(blocks, layout_items, location, seen, rewrites):
    """Walk one (blocks, layout_items) container, dedupe against ``seen``."""
    if not isinstance(blocks, dict) or not isinstance(layout_items, list):
        return
    for i, block_uuid in enumerate(layout_items):
        block = blocks.get(block_uuid)
        if not isinstance(block, dict):
            continue

        if block_uuid in seen:
            new_uuid = _new_uuid()
            copied = copy.deepcopy(block)
            blocks[new_uuid] = copied
            layout_items[i] = new_uuid
            rewrites.append(
                {
                    "old": block_uuid,
                    "new": new_uuid,
                    "location": location,
                    "reason": "duplicate-layout-entry",
                }
            )
            # Recurse into copied subtree and rename every nested UUID,
            # since the copy duplicates them against the original subtree.
            nested = copied.get("blocks")
            nested_layout = copied.get("blocks_layout") or {}
            if isinstance(nested, dict):
                _regenerate_subtree_uuids(
                    nested,
                    nested_layout.get("items"),
                    f"block:{new_uuid}",
                    rewrites,
                )
            data = copied.get("data")
            if isinstance(data, dict):
                data_blocks = data.get("blocks")
                data_layout = data.get("blocks_layout") or {}
                if isinstance(data_blocks, dict):
                    _regenerate_subtree_uuids(
                        data_blocks,
                        data_layout.get("items"),
                        f"block:{new_uuid}/data",
                        rewrites,
                    )
            seen.add(new_uuid)
            active_uuid = new_uuid
            active_block = copied
        else:
            seen.add(block_uuid)
            active_uuid = block_uuid
            active_block = block

        nested = active_block.get("blocks")
        nested_layout = active_block.get("blocks_layout") or {}
        if isinstance(nested, dict):
            _rewrite_container(
                nested,
                nested_layout.get("items"),
                f"block:{active_uuid}",
                seen,
                rewrites,
            )
        data = active_block.get("data")
        if isinstance(data, dict):
            data_blocks = data.get("blocks")
            data_layout = data.get("blocks_layout") or {}
            if isinstance(data_blocks, dict):
                _rewrite_container(
                    data_blocks,
                    data_layout.get("items"),
                    f"block:{active_uuid}/data",
                    seen,
                    rewrites,
                )


def rewrite_duplicates(blocks, blocks_layout):
    """Mutate ``blocks`` / ``blocks_layout`` in place, dedupe UUIDs globally.

    Returns a list of rewrite records describing every UUID change. Empty
    list means nothing to fix.
    """
    rewrites = []
    if not isinstance(blocks, dict) or not isinstance(blocks_layout, dict):
        return rewrites
    layout_items = blocks_layout.get("items")
    if not isinstance(layout_items, list):
        return rewrites
    seen = set()
    _rewrite_container(blocks, layout_items, "top-level", seen, rewrites)
    return rewrites
