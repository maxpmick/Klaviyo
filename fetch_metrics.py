#!/usr/bin/env python3
"""
Aug 2025 — Klaviyo sync:
- For all profiles in segment SEGMENT_ID (default 'UM5yp4'):
  - Fetch newest "Checkout Started" (or "Started Checkout") event per profile
  - Build a compact `last_checkout_snapshot`
  - Upload to that profile (PATCH) — unless --dry-run is provided

Dry run:
  python sync_checkout_snapshot.py --dry-run
  python sync_checkout_snapshot.py --dry-run --segment YOURSEGID --limit 50

Real run:
  python sync_checkout_snapshot.py
"""

import os
import time
import json
import logging
import argparse
from typing import Dict, Any, Optional, Iterable, List, Tuple
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("KLAVIYO_API_KEY", "").strip()
if not API_KEY:
    raise SystemExit("Set KLAVIYO_API_KEY in environment or .env")

DEFAULT_SEGMENT_ID = os.getenv("SEGMENT_ID", "UM5yp4").strip()
REVISION = os.getenv("REVISION", "2025-07-15").strip()
PLACEHOLDER_IMAGE_URL = os.getenv("PLACEHOLDER_IMAGE_URL") or None

BASE = "https://a.klaviyo.com/api"
HEADERS = {
    "accept": "application/json",
    "content-type": "application/json",
    "revision": REVISION,
    "Authorization": f"Klaviyo-API-Key {API_KEY}",
}

# PAGE_SIZE removed - let API use default pagination
TARGET_METRIC_NAMES = {n.lower() for n in ["Checkout Started", "Started Checkout"]}

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s | %(message)s")


# ----------------------- HTTP helpers ----------------------- #
def _get(url: str, params: Optional[dict] = None, retry: int = 5) -> dict:
    for attempt in range(retry):
        r = requests.get(url, headers=HEADERS, params=params, timeout=60)
        if r.status_code == 429:
            wait = int(r.headers.get("Retry-After", "2"))
            logging.warning("429 rate limited (GET); sleeping %ss", wait)
            time.sleep(wait); continue
        if 500 <= r.status_code < 600:
            wait = 2 ** attempt
            logging.warning("Server error %s (GET); retry in %ss", r.status_code, wait)
            time.sleep(wait); continue
        r.raise_for_status()
        try:
            return r.json()
        except Exception:
            return {}
    r.raise_for_status()
    return {}


def _patch(url: str, payload: dict, retry: int = 5) -> dict:
    body = json.dumps(payload)
    for attempt in range(retry):
        r = requests.patch(url, headers=HEADERS, data=body, timeout=60)
        if r.status_code == 429:
            wait = int(r.headers.get("Retry-After", "2"))
            logging.warning("429 rate limited (PATCH); sleeping %ss", wait)
            time.sleep(wait); continue
        if 500 <= r.status_code < 600:
            wait = 2 ** attempt
            logging.warning("Server error %s (PATCH); retry in %ss", r.status_code, wait)
            time.sleep(wait); continue
        if r.status_code in (200, 202):
            try: return r.json()
            except Exception: return {}
        r.raise_for_status()
    r.raise_for_status()
    return {}


# ----------------------- Segments ----------------------- #
def get_segment_profiles(segment_id: str, limit: Optional[int] = None) -> Dict[str, Dict[str, Any]]:
    """
    GET /api/segments/{id}/profiles (paged) -> {profile_id: attributes}
    Returns a dict keyed by profile id with attributes (email etc. when present).
    """
    url = f"{BASE}/segments/{segment_id}/profiles"
    params = {}  # No pagination params - let API use defaults
    
    out: Dict[str, Dict[str, Any]] = {}
    while True:
        data = _get(url, params=params)
        for row in data.get("data", []):
            if row.get("type") == "profile":
                pid = row.get("id")
                attrs = row.get("attributes") or {}
                out[pid] = attrs
                if limit and len(out) >= limit:
                    logging.info("Segment %s truncated to limit=%d", segment_id, limit)
                    return out
        next_url = data.get("links", {}).get("next")
        if not next_url:
            break
        url, params = next_url, None
    return out


# ----------------------- Events (per profile) ----------------------- #
def iterate_profile_events(profile_id: str) -> Iterable[dict]:
    """
    GET /api/events?filter=equals(profile_id,"...")&sort=-timestamp
    include=metric&fields[metric]=name
    """
    url = f"{BASE}/events"
    params = {
        "filter": f'equals(profile_id,"{profile_id}")',
        "sort": "-timestamp",
        "include": "metric",
        "fields[metric]": "name",
    }
    while True:
        data = _get(url, params=params)
        # map metric id -> name
        metric_name_by_id: Dict[str, str] = {}
        for inc in data.get("included", []):
            if inc.get("type") == "metric":
                mid = inc.get("id")
                name = (inc.get("attributes", {}) or {}).get("name")
                if mid and name:
                    metric_name_by_id[mid] = name
        for e in data.get("data", []):
            rel = (e.get("relationships") or {}).get("metric") or {}
            mid = (rel.get("data") or {}).get("id")
            e["_metric_name"] = metric_name_by_id.get(mid, "")
            yield e
        next_url = data.get("links", {}).get("next")
        if not next_url:
            break
        url, params = next_url, None


# ----------------------- Mapping helpers ----------------------- #
def _first_src(arr: Any) -> Optional[str]:
    try:
        if isinstance(arr, list) and arr:
            v = arr[0]
            if isinstance(v, dict):
                return v.get("src")
    except Exception:
        pass
    return None


def _coerce_float(x: Any) -> float:
    try:
        if isinstance(x, (int, float)):
            return float(x)
        if isinstance(x, str):
            return float(x.strip())
    except Exception:
        pass
    return 0.0


def pick_image_url(item: dict, placeholder: Optional[str]) -> Optional[str]:
    product = item.get("product") or {}
    variant = product.get("variant") or {}
    variant_images = variant.get("images") or []
    product_images = product.get("images") or []
    return _first_src(variant_images) or _first_src(product_images) or placeholder


def line_item_to_snapshot(item: dict) -> dict:
    product = item.get("product") or {}
    title = product.get("title") or item.get("presentment_title") or item.get("title") or ""
    return {
        "product_id": product.get("id"),
        "variant_id": item.get("variant_id") or (product.get("variant") or {}).get("id"),
        "title": title,
        "image_url": pick_image_url(item, PLACEHOLDER_IMAGE_URL),
        "quantity": int(item.get("quantity") or 0),
        "line_price": _coerce_float(item.get("line_price")),
    }


def event_to_snapshot(event: dict) -> Optional[dict]:
    attrs = event.get("attributes") or {}
    # sometimes 'properties' vs 'event_properties'
    props = attrs.get("properties") or attrs.get("event_properties") or {}
    
    # Try multiple locations for extra data
    extra = props.get("extra") or props.get("$extra") or {}
    
    # Try multiple locations for line items
    line_items = extra.get("line_items") or props.get("Items") or props.get("items") or []
    items = [line_item_to_snapshot(li) for li in line_items]

    # Try multiple locations for checkout URL
    checkout_url = (extra.get("checkout_url") or
                   extra.get("responsive_checkout_url") or
                   props.get("checkout_url") or
                   props.get("Checkout URL"))
    
    # Try multiple locations for currency
    currency = (extra.get("presentment_currency") or
               props.get("presentment_currency") or
               props.get("$currency_code") or
               "USD")
    
    updated_at = attrs.get("timestamp") or attrs.get("datetime") or attrs.get("time")

    if not checkout_url and not items:
        return None

    return {
        "checkout_url": checkout_url,
        "currency": currency,
        "updated_at": updated_at,
        "items": items,
    }


# ----------------------- Profile PATCH ----------------------- #
def patch_profile_snapshot(profile_id: str, snapshot: dict) -> None:
    url = f"{BASE}/profiles/{profile_id}"
    payload = {
        "data": {
            "type": "profile",
            "id": profile_id,
            "attributes": {
                "properties": {
                    "last_checkout_snapshot": snapshot
                }
            }
        }
    }
    _patch(url, payload)


# ----------------------- Dry-run printing ----------------------- #
def summarize_snapshot_for_print(profile_id: str, profile_attrs: Dict[str, Any], snapshot: dict) -> str:
    email = profile_attrs.get("email") or profile_attrs.get("properties", {}).get("$email") or "-"
    lines = []
    lines.append(f"Profile: {profile_id}  Email: {email}")
    lines.append(f"  Checkout URL: {snapshot.get('checkout_url') or '-'}")
    lines.append(f"  Currency: {snapshot.get('currency','USD')}   Updated At: {snapshot.get('updated_at','-')}")
    items = snapshot.get("items") or []
    lines.append(f"  Items ({len(items)}):")
    for i, it in enumerate(items, 1):
        title = it.get("title") or "-"
        qty = it.get("quantity", 0)
        price = it.get("line_price", 0.0)
        img = it.get("image_url") or "-"
        lines.append(f"    {i}. {title} | Qty: {qty} | Price: {price:.2f}")
        lines.append(f"       image: {img}")
    return "\n".join(lines)


# ----------------------- Main ----------------------- #
def main():
    parser = argparse.ArgumentParser(description="Klaviyo: sync Checkout Started → profile.last_checkout_snapshot")
    parser.add_argument("--segment", default=DEFAULT_SEGMENT_ID, help="Segment ID (default: %(default)s)")
    parser.add_argument("--dry-run", action="store_true", help="Do not PATCH; print what would be uploaded")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of profiles processed")
    parser.add_argument("--verbose", action="store_true", help="More logging")
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # 1) Load segment members (optionally limited)
    profiles = get_segment_profiles(args.segment, limit=args.limit)
    if not profiles:
        logging.info("No profiles in segment %s", args.segment)
        return
    logging.info("Loaded %d profiles from segment %s", len(profiles), args.segment)

    updated = 0
    matched = 0
    no_event = 0
    no_snapshot = 0

    for idx, (profile_id, profile_attrs) in enumerate(profiles.items(), 1):
        # Stream newest events first and stop at first matching metric name
        matching_event = None
        for ev in iterate_profile_events(profile_id):
            name = (ev.get("_metric_name") or "").strip().lower()
            if name in TARGET_METRIC_NAMES:
                matching_event = ev
                break
        if not matching_event:
            no_event += 1
            continue

        snapshot = event_to_snapshot(matching_event)
        if not snapshot:
            no_snapshot += 1
            continue

        matched += 1

        if args.dry_run:
            print(summarize_snapshot_for_print(profile_id, profile_attrs, snapshot))
            print("-" * 80)
        else:
            try:
                patch_profile_snapshot(profile_id, snapshot)
                updated += 1
                if updated % 25 == 0:
                    logging.info("Updated %d profiles so far...", updated)
            except Exception as e:
                email = profile_attrs.get("email") or profile_attrs.get("properties", {}).get("$email") or "no-email"
                logging.exception("Failed updating profile %s (%s): %s", profile_id, email, e)

        # Small courtesy sleep every 50 to spread load a bit
        if idx % 50 == 0:
            time.sleep(0.2)

    if args.dry_run:
        logging.info("DRY RUN COMPLETE — profiles with a matching event: %d (skipped PATCH)", matched)
    else:
        logging.info("DONE — updated %d profiles with last_checkout_snapshot", updated)

    logging.info("Stats: matched=%d, updated=%d, no_event=%d, no_snapshot=%d",
                 matched, updated, no_event, no_snapshot)


if __name__ == "__main__":
    main()
