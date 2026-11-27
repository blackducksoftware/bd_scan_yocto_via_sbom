"""
SPDX normalisation helper — standard library only, no runtime deps.

Produces a deterministic, diffable representation of an SPDX 2.3 JSON document
by stripping non-deterministic fields (timestamps, random UUIDs) and applying
stable ordering.

Single source of truth for both baseline capture (Step 2.4) and regression
comparison (§7.3). Import as a module or call as a CLI script:

    python3 test/spdx_normalise.py input.spdx.json > normalised.json
    python3 test/spdx_normalise.py input.spdx.json output.normalised.json

Algorithm
---------
1.  Build a mapping from each package's random SPDXID → a stable name derived
    from ``name + "@" + versionInfo`` (e.g. ``openssl@3.2.4``).  When two
    packages share the same name+version, a stable ordinal suffix is appended
    (``openssl@3.2.4#0``, ``openssl@3.2.4#1`` in sorted order of their
    original SPDXID strings so that the mapping is reproducible).

2.  Apply the SPDXID mapping to every ``SPDXID`` field in ``packages[]`` and
    to ``spdxElementId`` / ``relatedSpdxElement`` in ``relationships[]``, and
    to ``documentDescribes[]``.

3.  Strip ``documentNamespace`` (random UUID).

4.  Strip ``creationInfo.created`` (timestamp).

5.  Sort ``packages[]`` by ``(name, versionInfo, purl)``.  The PURL is the
    ``referenceLocator`` from the first entry in ``externalRefs[]`` whose
    ``referenceType`` is ``"purl"``; fall back to ``""`` if absent.

6.  Sort ``relationships[]`` by
    ``(spdxElementId_name, relationshipType, relatedSpdxElement_name)`` using
    the stable names from step 1.

Output is a JSON string with 2-space indentation.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from typing import Any


def _purl_for_package(pkg: dict[str, Any]) -> str:
    for ref in pkg.get("externalRefs", []):
        if ref.get("referenceType") == "purl":
            return ref.get("referenceLocator", "")
    return ""


def _build_spdxid_map(packages: list[dict[str, Any]]) -> dict[str, str]:
    """Map each random SPDXRef-package-<uuid> to a stable name."""
    # Group packages by (name, versionInfo)
    groups: dict[tuple[str, str], list[str]] = defaultdict(list)
    for pkg in packages:
        key = (pkg.get("name", ""), pkg.get("versionInfo", ""))
        groups[key].append(pkg.get("SPDXID", ""))

    mapping: dict[str, str] = {}
    for (name, ver), spdxids in groups.items():
        if len(spdxids) == 1:
            stable = f"{name}@{ver}"
            mapping[spdxids[0]] = stable
        else:
            # Multiple packages with same name+version: use sorted SPDXID for
            # reproducible ordinal (the original UUIDs are random but their
            # sort order is stable within a single document).
            for idx, sid in enumerate(sorted(spdxids)):
                stable = f"{name}@{ver}#{idx}"
                mapping[sid] = stable

    return mapping


def normalise(doc: dict[str, Any]) -> dict[str, Any]:
    """Return a new dict with the SPDX document normalised for diffing."""
    out: dict[str, Any] = {}

    # 1. Copy top-level scalar fields, skipping non-deterministic ones
    for key, val in doc.items():
        if key in ("documentNamespace", "packages", "relationships",
                   "creationInfo"):
            continue
        out[key] = val

    # 2. Strip creation timestamp from creationInfo (keep other fields)
    ci = dict(doc.get("creationInfo", {}))
    ci.pop("created", None)
    out["creationInfo"] = ci

    # 3. Build SPDXID → stable-name mapping
    packages = doc.get("packages", [])
    spdxid_map = _build_spdxid_map(packages)

    # 4. Rewrite packages
    normalised_packages = []
    for pkg in packages:
        np = dict(pkg)
        original_id = np.get("SPDXID", "")
        np["SPDXID"] = spdxid_map.get(original_id, original_id)
        normalised_packages.append(np)

    # 5. Sort packages by (name, versionInfo, purl)
    normalised_packages.sort(
        key=lambda p: (p.get("name", ""), p.get("versionInfo", ""),
                       _purl_for_package(p))
    )
    out["packages"] = normalised_packages

    # 6. Rewrite documentDescribes[]
    out["documentDescribes"] = [
        spdxid_map.get(sid, sid) for sid in doc.get("documentDescribes", [])
    ]

    # 7. Rewrite and sort relationships
    normalised_relationships = []
    for rel in doc.get("relationships", []):
        nr = dict(rel)
        nr["spdxElementId"] = spdxid_map.get(
            nr.get("spdxElementId", ""), nr.get("spdxElementId", "")
        )
        nr["relatedSpdxElement"] = spdxid_map.get(
            nr.get("relatedSpdxElement", ""), nr.get("relatedSpdxElement", "")
        )
        normalised_relationships.append(nr)

    normalised_relationships.sort(
        key=lambda r: (
            r.get("spdxElementId", ""),
            r.get("relationshipType", ""),
            r.get("relatedSpdxElement", ""),
        )
    )
    out["relationships"] = normalised_relationships

    return out


def normalise_file(input_path: str) -> str:
    """Read an SPDX JSON file, normalise it, and return the JSON string."""
    with open(input_path, encoding="utf-8") as fh:
        doc = json.load(fh)
    return json.dumps(normalise(doc), indent=2)


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: spdx_normalise.py INPUT.json [OUTPUT.json]", file=sys.stderr)
        sys.exit(1)

    result = normalise_file(sys.argv[1])

    if len(sys.argv) >= 3:
        with open(sys.argv[2], "w", encoding="utf-8") as fh:
            fh.write(result)
    else:
        print(result)


if __name__ == "__main__":
    main()
