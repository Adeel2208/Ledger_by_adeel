"""Founder profile — consented, founder-supplied identity data.

Photos and biography are *never* scraped. They arrive one of two ways:

    1. the founder uploads them through the inbound apply flow, or
    2. an investor edits the profile of a founder who supplied details offline.

That keeps the product on the right side of GDPR for an EU-facing fund: we hold
a photo only because the person handed it to us. Outbound-discovered founders
therefore have no photo until they provide one — and rather than render a sad
grey placeholder, `monogram()` derives a deterministic, brand-consistent
initials avatar so those profiles still look finished.

Uploads are re-encoded rather than stored as received: decoding to raw pixels
and re-writing strips EXIF (which carries GPS and device identifiers) and
guarantees the bytes we serve are actually an image, not a payload with an
image extension.
"""
from __future__ import annotations

import logging
import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.founder import Founder

logger = logging.getLogger(__name__)

UPLOAD_DIR = os.path.join("data", "uploads")
PHOTO_SUBDIR = "photos"

# Formats we are willing to decode. Deliberately excludes SVG: it is XML, can
# carry script, and is served back to the browser.
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_PHOTO_BYTES = 5 * 1024 * 1024
PHOTO_EDGE_PX = 512  # square, retina-adequate for a 256px display slot

# Editable profile fields. Anything not listed here cannot be written through
# the profile endpoint — notably `is_cold_start` and any score field, which are
# derived by the Intelligence layer and must never be settable by a subject.
EDITABLE_FIELDS = (
    "headline",
    "bio",
    "role",
    "location",
    "personal_url",
    "twitter_handle",
    "linkedin_url",
    "work_history",
)

# Facets that make a profile feel "complete" to an investor reading it.
_COMPLETENESS_FACETS = (
    "photo_path",
    "headline",
    "bio",
    "role",
    "location",
    "work_history",
)

_MONOGRAM_PALETTE = (
    "#1e40af", "#0f766e", "#7c3aed", "#b45309",
    "#be123c", "#0369a1", "#4d7c0f", "#a21caf",
)


class ProfileError(ValueError):
    """Invalid profile input — surfaced to the caller as a 400."""


@dataclass
class Monogram:
    """Deterministic fallback avatar for a founder with no uploaded photo."""

    initials: str
    color: str


def monogram(founder: Founder) -> Monogram:
    """Initials + a stable colour derived from the founder's identity.

    Keyed on `id` so a founder's colour never changes between page loads, and
    two founders sharing initials still get distinguishable avatars.
    """
    parts = [p for p in (founder.name or "").split() if p]
    if not parts:
        initials = "?"
    elif len(parts) == 1:
        initials = parts[0][:2].upper()
    else:
        initials = (parts[0][0] + parts[-1][0]).upper()
    return Monogram(initials=initials, color=_MONOGRAM_PALETTE[(founder.id or 0) % len(_MONOGRAM_PALETTE)])


def completeness(founder: Founder) -> dict:
    """Which profile facets are present vs. missing.

    Mirrors the data-quality convention used for signals: gaps are *reported*,
    so a thin profile reads as disclosed-incomplete rather than as a low score.
    """
    present = [f for f in _COMPLETENESS_FACETS if _has_value(getattr(founder, f, None))]
    missing = [f for f in _COMPLETENESS_FACETS if f not in present]
    return {
        "present": present,
        "missing": missing,
        "pct": round(100 * len(present) / len(_COMPLETENESS_FACETS)),
    }


def _has_value(v: object) -> bool:
    if v is None:
        return False
    if isinstance(v, str):
        return bool(v.strip())
    if isinstance(v, (list, dict)):
        return len(v) > 0
    return True


def save_photo(founder: Founder, raw: bytes, content_type: str | None, db: Session) -> str:
    """Validate, normalise, and store a founder-supplied photo.

    Returns the stored relative path. Replaces any previous photo so we do not
    accumulate stale images of a person who asked to change theirs.
    """
    if content_type not in ALLOWED_IMAGE_TYPES:
        raise ProfileError(
            f"Unsupported image type {content_type or 'unknown'} — use JPEG, PNG, or WebP."
        )
    if not raw:
        raise ProfileError("Empty image upload.")
    if len(raw) > MAX_PHOTO_BYTES:
        raise ProfileError(f"Image exceeds {MAX_PHOTO_BYTES // (1024 * 1024)}MB.")

    try:
        from PIL import Image, ImageOps
    except ImportError as exc:  # pragma: no cover - dependency is declared
        raise ProfileError("Image processing unavailable (Pillow not installed).") from exc

    import io

    try:
        img = Image.open(io.BytesIO(raw))
        img.verify()  # structural check; consumes the object, so reopen below
        img = Image.open(io.BytesIO(raw))
        img = ImageOps.exif_transpose(img)  # honour camera rotation before stripping EXIF
        img = img.convert("RGB")
    except ProfileError:
        raise
    except Exception as exc:
        raise ProfileError("File is not a readable image.") from exc

    # Centre-crop to a square so every avatar renders identically in the UI,
    # then downscale. ImageOps.fit does both without distorting aspect ratio.
    img = ImageOps.fit(img, (PHOTO_EDGE_PX, PHOTO_EDGE_PX), method=Image.LANCZOS, centering=(0.5, 0.4))

    dest_dir = os.path.join(UPLOAD_DIR, PHOTO_SUBDIR)
    os.makedirs(dest_dir, exist_ok=True)
    # Store with forward slashes: this value is served as a URL path, and
    # os.path.join would emit a backslash on Windows that browsers won't follow.
    rel_path = f"{PHOTO_SUBDIR}/{uuid.uuid4().hex}.jpg"
    img.save(os.path.join(UPLOAD_DIR, *rel_path.split("/")), format="JPEG", quality=88, optimize=True)

    previous = founder.photo_path
    founder.photo_path = rel_path
    founder.profile_updated_at = datetime.now(timezone.utc)
    db.commit()

    if previous:
        # Tolerate legacy backslash-separated paths written before the fix.
        _remove_quietly(os.path.join(UPLOAD_DIR, *previous.replace("\\", "/").split("/")))
    return rel_path


def _remove_quietly(path: str) -> None:
    """Best-effort cleanup — a leftover file must never fail the request."""
    try:
        os.remove(path)
    except OSError as exc:
        logger.warning("Could not remove superseded photo %s: %s", path, exc)


def update_profile(founder: Founder, fields: dict, db: Session) -> Founder:
    """Apply a partial profile update, ignoring keys outside `EDITABLE_FIELDS`.

    Empty strings clear a field (the founder removing something they wrote);
    keys omitted entirely are left untouched, so a partial form never wipes
    data it did not render.
    """
    changed = False
    for key in EDITABLE_FIELDS:
        if key not in fields:
            continue
        value = fields[key]
        if key == "work_history":
            value = _clean_work_history(value)
        elif isinstance(value, str):
            value = value.strip() or None
        setattr(founder, key, value)
        changed = True

    if changed:
        founder.profile_updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(founder)
    return founder


def _clean_work_history(value: object) -> list | None:
    """Coerce work history to a predictable shape so the UI can trust it."""
    if value in (None, "", []):
        return None
    if not isinstance(value, list):
        raise ProfileError("work_history must be a list of roles.")

    cleaned: list[dict] = []
    for entry in value:
        if not isinstance(entry, dict):
            raise ProfileError("Each work_history entry must be an object.")
        row = {
            k: (str(entry[k]).strip() or None) if entry.get(k) is not None else None
            for k in ("company", "title", "start", "end", "summary")
        }
        if row["company"] or row["title"]:  # drop wholly-empty rows from the form
            cleaned.append(row)
    return cleaned or None
