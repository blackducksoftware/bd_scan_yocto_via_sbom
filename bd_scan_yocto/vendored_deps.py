"""
vendored_deps — enumerate Rust crate and Go module vendored dependencies
declared via crate://, gomod://, and gomodgit:// SRC_URI entries in
OpenEmbedded recipe .inc files.

Public API:
    VendoredDep         dataclass representing one enumerated dependency
    validate_recipe_name(name) -> bool
    parse_src_uri(text, recipe_name, seen_unknown_schemes=None) -> list[VendoredDep]
    warn_missing_recipe_names(requested, available) -> None
"""
import logging
import re
import urllib.parse
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class VendoredDep:
    """One vendored dependency extracted from an OE recipe's SRC_URI."""
    ecosystem: str     # "cargo" or "golang"
    name: str          # package / module name (e.g. "serde", "golang.org/x/sys")
    version: str       # version string (e.g. "1.0.200", "v0.20.0")
    purl: str          # PURL (e.g. "pkg:cargo/serde@1.0.200")
    parent_recipe: str # originating recipe name

# ---------------------------------------------------------------------------
# Recipe-name validation
# ---------------------------------------------------------------------------

def validate_recipe_name(name: str) -> bool:
    """
    Return True when *name* is a valid OE recipe name.

    Validation uses re.fullmatch so trailing newlines and embedded whitespace
    or shell-special characters are always rejected.
    """
    if not name:
        return False
    return bool(re.fullmatch(r'[A-Za-z0-9_][A-Za-z0-9._+/\-]*', name))


# ---------------------------------------------------------------------------
# URI token extraction regex
# ---------------------------------------------------------------------------

# Match any URI scheme token.  The path portion stops at whitespace or a
# double-quote so we don't swallow the closing " of SRC_URI assignments.
_URI_RE = re.compile(r'[a-zA-Z][a-zA-Z0-9+.\-]*://[^\s"]+')

# ---------------------------------------------------------------------------
# Internal parsers
# ---------------------------------------------------------------------------

def _parse_crate_token(
    token: str, recipe_name: str
) -> "VendoredDep | None":
    """
    Parse one crate:// URI token.  Returns a VendoredDep or None on error.

    Recognised format: crate://<registry>/<name>/<version>
    """
    try:
        parsed = urllib.parse.urlparse(token)
        registry = parsed.netloc          # "crates.io" or custom
        parts = parsed.path.strip('/').split('/')
        if len(parts) < 2:
            logging.warning(
                f"Skipping crate URI with missing version: {token!r} "
                f"in recipe '{recipe_name}'"
            )
            return None
        name = parts[0]
        version = parts[1]
        if not version:
            logging.warning(
                f"Skipping crate URI with empty version: {token!r} "
                f"in recipe '{recipe_name}'"
            )
            return None
        # URL-decode version (e.g. %2B → +) for canonical PURL
        version = urllib.parse.unquote(version)
        if registry == 'crates.io':
            purl = f"pkg:cargo/{name}@{version}"
        else:
            purl = f"pkg:cargo/{name}@{version}?repository_url={registry}"
        return VendoredDep(
            ecosystem='cargo',
            name=name,
            version=version,
            purl=purl,
            parent_recipe=recipe_name,
        )
    except Exception as exc:
        logging.warning(
            f"Skipping malformed crate URI {token!r} in recipe "
            f"'{recipe_name}': {exc}"
        )
        return None


def _parse_gomod_token(
    token: str, scheme: str, recipe_name: str
) -> "VendoredDep | None":
    """
    Parse one gomod:// or gomodgit:// URI token.

    Recognised format: <scheme>://<module_path>;<param>=<value>;...
    Required parameter: version=<semver>
    """
    prefix = scheme + "://"
    rest = token[len(prefix):]           # strip "gomod://" or "gomodgit://"

    semi = rest.find(';')
    if semi == -1:
        module_path = rest
        params_str = ''
    else:
        module_path = rest[:semi]
        params_str = rest[semi + 1:]

    if not module_path:
        logging.warning(
            f"Skipping {scheme}:// URI with empty module path: "
            f"{token!r} in recipe '{recipe_name}'"
        )
        return None

    vm = re.search(r'(?:^|;)version=([^;]+)', params_str)
    if not vm:
        logging.warning(
            f"Skipping {scheme}:// URI with no version parameter: "
            f"{token!r} in recipe '{recipe_name}'"
        )
        return None
    version = vm.group(1)
    if not version:
        logging.warning(
            f"Skipping {scheme}:// URI with empty version: "
            f"{token!r} in recipe '{recipe_name}'"
        )
        return None

    purl = f"pkg:golang/{module_path}@{version}"
    return VendoredDep(
        ecosystem='golang',
        name=module_path,
        version=version,
        purl=purl,
        parent_recipe=recipe_name,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_src_uri(
    src_uri_text: str,
    recipe_name: str,
    seen_unknown_schemes: "set[str] | None" = None,
) -> "list[VendoredDep]":
    """
    Parse all vendored-dependency URIs from *src_uri_text* (the full text of
    a .inc file or a SRC_URI assignment) for *recipe_name*.

    Supported schemes: crate://, gomod://, gomodgit://
    All other URI schemes are logged once at DEBUG level (deferred/unknown)
    and produce no output.

    *seen_unknown_schemes* — optional set shared across multiple calls for
    per-run deduplication of the DEBUG logs.  Pass ``set()`` to enable
    cross-recipe dedup; omit (None) for per-call dedup.

    Returns a list of VendoredDep objects, deduplicated by (name, version).
    """
    if seen_unknown_schemes is None:
        seen_unknown_schemes = set()

    # Join BitBake line continuations (backslash-newline → space)
    joined = src_uri_text.replace('\\\n', ' ')

    deps: list[VendoredDep] = []
    seen: set[tuple[str, str]] = set()   # (name, version) dedup within this call

    for token in _URI_RE.findall(joined):
        # Determine scheme without re-parsing the whole token
        sep = token.find('://')
        if sep == -1:
            continue
        scheme = token[:sep]

        if scheme == 'crate':
            dep = _parse_crate_token(token, recipe_name)
            if dep is not None:
                key = (dep.name, dep.version)
                if key not in seen:
                    seen.add(key)
                    deps.append(dep)

        elif scheme in ('gomod', 'gomodgit'):
            dep = _parse_gomod_token(token, scheme, recipe_name)
            if dep is not None:
                key = (dep.name, dep.version)
                if key not in seen:
                    seen.add(key)
                    deps.append(dep)

        else:
            # Deferred / unknown scheme — log once per scheme per run
            if scheme not in seen_unknown_schemes:
                seen_unknown_schemes.add(scheme)
                logging.debug(
                    f"Skipping URI with unsupported scheme '{scheme}://' "
                    f"(deferred/unknown) in recipe '{recipe_name}'"
                )

    return deps


def warn_missing_recipe_names(
    requested: "list[str]",
    available: "set[str]",
) -> None:
    """
    For each name in *requested* that is not present in *available*, log a
    WARNING so operators know which --vendored_deps_recipes entries were not
    found in the recipe list.
    """
    for name in requested:
        if name not in available:
            logging.warning(
                f"Recipe '{name}' from --vendored_deps_recipes "
                f"not found in processed recipes - skipping"
            )
