"""
Unit tests for the vendored_deps parser module (§7.1).

These tests are written BEFORE the feature is implemented and are therefore
expected to FAIL with ImportError until Step 3 adds the module.
"""
import json
import logging
import pathlib
import re

import pytest

# ---------------------------------------------------------------------------
# Import guard — the module under test doesn't exist yet; mark as xfail
# rather than a collection error.
# ---------------------------------------------------------------------------
try:
    from bd_scan_yocto.vendored_deps import parse_src_uri  # noqa: F401
    from bd_scan_yocto.vendored_deps import VendoredDep    # noqa: F401
    MODULE_AVAILABLE = True
except ImportError:
    MODULE_AVAILABLE = False

pytestmark = pytest.mark.skipif(
    not MODULE_AVAILABLE,
    reason="bd_scan_yocto.vendored_deps not yet implemented (Step 3)"
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_expected(recipe: str) -> list[dict]:
    """Load the expected-results JSON for a recipe."""
    path = (
        pathlib.Path(__file__).parent.parent
        / "data" / "vendored" / "expected" / f"{recipe}.json"
    )
    with open(path) as fh:
        return json.load(fh)


def _inc_text(path: pathlib.Path) -> str:
    with open(path) as fh:
        return fh.read()


# ---------------------------------------------------------------------------
# Accuracy tests against real fixtures
# ---------------------------------------------------------------------------

class TestCrateAccuracy:
    """Parser must match expected-results for every Rust fixture (§7.2)."""

    def test_pyruvate_count_and_purls(self, pyruvate_crates_inc):
        expected = _load_expected("python3-pyruvate")
        src_uri_text = _inc_text(pyruvate_crates_inc)
        results = parse_src_uri(src_uri_text, "python3-pyruvate")

        found_purls = {d.purl for d in results}
        expected_purls = {e["purl"] for e in expected}

        missing = expected_purls - found_purls
        extra = found_purls - expected_purls

        assert not missing, f"Missing PURLs: {sorted(missing)[:5]}"
        assert not extra, f"Extra PURLs: {sorted(extra)[:5]}"
        assert len(results) == len(expected), (
            f"Expected {len(expected)} crates, found {len(results)}"
        )

    def test_pydantic_core_count_and_purls(self, pydantic_core_crates_inc):
        expected = _load_expected("python3-pydantic-core")
        src_uri_text = _inc_text(pydantic_core_crates_inc)
        results = parse_src_uri(src_uri_text, "python3-pydantic-core")

        found_purls = {d.purl for d in results}
        expected_purls = {e["purl"] for e in expected}

        missing = expected_purls - found_purls
        extra = found_purls - expected_purls

        assert not missing, f"Missing PURLs: {sorted(missing)[:5]}"
        assert not extra, f"Extra PURLs: {sorted(extra)[:5]}"
        assert len(results) == len(expected), (
            f"Expected {len(expected)} crates, found {len(results)}"
        )

    def test_crate_purl_format(self, pyruvate_crates_inc):
        """Each Rust dep must have purl = pkg:cargo/<name>@<version>."""
        src_uri_text = _inc_text(pyruvate_crates_inc)
        results = parse_src_uri(src_uri_text, "python3-pyruvate")
        for d in results:
            assert d.ecosystem == "cargo"
            assert d.purl.startswith("pkg:cargo/"), f"Bad purl: {d.purl}"
            assert "@" in d.purl, f"No version in purl: {d.purl}"


class TestGoModAccuracy:
    """Parser must match expected-results for crucible gomod:// fixture (§7.2)."""

    def test_crucible_count_and_purls(self, crucible_go_mods_inc):
        expected = _load_expected("crucible")
        src_uri_text = _inc_text(crucible_go_mods_inc)
        results = parse_src_uri(src_uri_text, "crucible")

        found_purls = {d.purl for d in results}
        expected_purls = {e["purl"] for e in expected}

        missing = expected_purls - found_purls
        extra = found_purls - expected_purls

        assert not missing, f"Missing PURLs: {sorted(missing)[:5]}"
        assert not extra, f"Extra PURLs: {sorted(extra)[:5]}"
        assert len(results) == len(expected), (
            f"Expected {len(expected)} modules, found {len(results)}"
        )

    def test_gomod_purl_format(self, crucible_go_mods_inc):
        """Each Go dep must have purl = pkg:golang/<path>@<version>."""
        src_uri_text = _inc_text(crucible_go_mods_inc)
        results = parse_src_uri(src_uri_text, "crucible")
        for d in results:
            assert d.ecosystem == "golang"
            assert d.purl.startswith("pkg:golang/"), f"Bad purl: {d.purl}"
            assert "@" in d.purl, f"No version in purl: {d.purl}"

    def test_pseudo_versions_preserved(self, crucible_go_mods_inc):
        """Go pseudo-versions must be preserved verbatim."""
        src_uri_text = _inc_text(crucible_go_mods_inc)
        results = parse_src_uri(src_uri_text, "crucible")
        pseudo = [d for d in results if re.match(r"v0\.0\.0-\d{14}-[0-9a-f]+", d.version)]
        assert len(pseudo) >= 3, "Expected several pseudo-version entries"
        for d in pseudo:
            # Version must be preserved as-is
            assert re.match(r"v0\.0\.0-\d{14}-[0-9a-f]+", d.version), (
                f"Pseudo-version altered: {d.version}"
            )

    def test_uppercase_module_path_preserved(self, crucible_go_mods_inc):
        """Module paths with uppercase letters must not be case-encoded."""
        src_uri_text = _inc_text(crucible_go_mods_inc)
        results = parse_src_uri(src_uri_text, "crucible")
        burnt = [d for d in results if "BurntSushi" in d.name]
        assert len(burnt) == 1, "Expected one BurntSushi/toml module"
        assert burnt[0].purl == "pkg:golang/github.com/BurntSushi/toml@v0.3.1"


class TestGoModGitAccuracy:
    """Parser must correctly handle gomodgit:// entries (synthesised fixture)."""

    def test_gomodgit_example_count_and_purls(self, gomodgit_example_inc):
        expected = _load_expected("gomodgit-example")
        src_uri_text = _inc_text(gomodgit_example_inc)
        results = parse_src_uri(src_uri_text, "gomodgit-example")

        found_purls = {d.purl for d in results}
        expected_purls = {e["purl"] for e in expected}

        missing = expected_purls - found_purls
        extra = found_purls - expected_purls

        assert not missing, f"Missing PURLs: {missing}"
        assert not extra, f"Extra PURLs: {extra}"

    def test_gomodgit_purl_format(self, gomodgit_example_inc):
        src_uri_text = _inc_text(gomodgit_example_inc)
        results = parse_src_uri(src_uri_text, "gomodgit-example")
        assert all(d.purl.startswith("pkg:golang/") for d in results)


# ---------------------------------------------------------------------------
# Edge-case unit tests (§7.1)
# ---------------------------------------------------------------------------

class TestEdgeCases:
    """Small inline strings for boundary conditions."""

    def test_empty_src_uri(self):
        results = parse_src_uri('SRC_URI = ""', "myrecipe")
        assert results == []

    def test_whitespace_only_src_uri(self):
        results = parse_src_uri('SRC_URI = "   "', "myrecipe")
        assert results == []

    def test_no_crates_or_gomod(self):
        src_uri = 'SRC_URI = "https://example.com/foo.tar.gz file://patch.patch"'
        results = parse_src_uri(src_uri, "plainrec")
        assert results == []

    def test_single_crate(self):
        src_uri = 'SRC_URI += "crate://crates.io/serde/1.0.200"'
        results = parse_src_uri(src_uri, "myrecipe")
        assert len(results) == 1
        assert results[0].purl == "pkg:cargo/serde@1.0.200"
        assert results[0].ecosystem == "cargo"
        assert results[0].name == "serde"
        assert results[0].version == "1.0.200"

    def test_non_crates_io_registry(self, caplog):
        """Non-crates.io registries include repository_url in purl and log INFO."""
        src_uri = 'SRC_URI += "crate://internal.company.io/foo/0.1.0"'
        with caplog.at_level(logging.INFO):
            results = parse_src_uri(src_uri, "myrecipe")
        assert len(results) == 1
        assert "repository_url=internal.company.io" in results[0].purl
        assert "pkg:cargo/foo@0.1.0" in results[0].purl

    def test_crate_missing_version_segment(self, caplog):
        """crate://crates.io/libfoo without version logs WARNING and is skipped."""
        src_uri = 'SRC_URI += "crate://crates.io/libfoo"'
        with caplog.at_level(logging.WARNING):
            results = parse_src_uri(src_uri, "myrecipe")
        assert results == []
        assert any("libfoo" in r.message for r in caplog.records
                   if r.levelno == logging.WARNING)

    def test_crate_empty_version(self, caplog):
        """crate://crates.io/libfoo/ (empty version) logs WARNING and is skipped."""
        src_uri = 'SRC_URI += "crate://crates.io/libfoo/"'
        with caplog.at_level(logging.WARNING):
            results = parse_src_uri(src_uri, "myrecipe")
        assert results == []
        assert any("libfoo" in r.message for r in caplog.records
                   if r.levelno == logging.WARNING)

    def test_single_gomod(self):
        src_uri = (
            'SRC_URI += "'
            'gomod://golang.org/x/sys;version=v0.20.0;'
            'sha256sum=abc123def456abc123def456abc123def456abc123def456abc1"'
        )
        results = parse_src_uri(src_uri, "myrecipe")
        assert len(results) == 1
        assert results[0].purl == "pkg:golang/golang.org/x/sys@v0.20.0"
        assert results[0].ecosystem == "golang"

    def test_gomod_parameter_order_independent(self):
        """Parameters after gomod:// may appear in any order."""
        src_uri = (
            'SRC_URI += "'
            'gomod://golang.org/x/text;sha256sum=abc123;version=v0.15.0;mod=1"'
        )
        results = parse_src_uri(src_uri, "myrecipe")
        assert len(results) == 1
        assert results[0].version == "v0.15.0"
        assert results[0].purl == "pkg:golang/golang.org/x/text@v0.15.0"

    def test_dedup_same_dep_same_recipe(self):
        """Duplicate crate in a single recipe's SRC_URI → one record."""
        src_uri = (
            'SRC_URI += " \\\n'
            '    crate://crates.io/serde/1.0.0 \\\n'
            '    crate://crates.io/serde/1.0.0 \\\n'
            '"'
        )
        results = parse_src_uri(src_uri, "myrecipe")
        assert len(results) == 1
        assert results[0].purl == "pkg:cargo/serde@1.0.0"

    def test_line_continuations_joined(self, pyruvate_crates_inc):
        """Fixture with line continuations: record count matches expected."""
        expected = _load_expected("python3-pyruvate")
        src_uri_text = _inc_text(pyruvate_crates_inc)
        results = parse_src_uri(src_uri_text, "python3-pyruvate")
        assert len(results) == len(expected), (
            f"Line-continuation join failed: expected {len(expected)}, "
            f"got {len(results)}"
        )

    def test_unrecognised_scheme_logged_at_debug_only(self, caplog):
        """Unknown schemes like crate+git:// are logged at DEBUG, never WARNING."""
        src_uri = 'SRC_URI += "crate+git://github.com/foo/bar.git"'
        with caplog.at_level(logging.DEBUG):
            results = parse_src_uri(src_uri, "myrecipe")
        assert results == []
        # Must not appear at WARNING or higher
        assert not any(
            r.levelno >= logging.WARNING for r in caplog.records
        ), "Unrecognised scheme must not log at WARNING"
        # Must appear at DEBUG (deferred scheme notice)
        debug_msgs = [r.message for r in caplog.records if r.levelno == logging.DEBUG]
        assert any("crate+git" in m for m in debug_msgs), (
            "Expected a DEBUG log mentioning crate+git://"
        )

    def test_unrecognised_scheme_dedup_per_run(self, caplog):
        """Same unknown scheme appearing twice logs DEBUG only once per run."""
        src_uri = (
            'SRC_URI += " \\\n'
            '    crate+git://github.com/foo/a.git \\\n'
            '    crate+git://github.com/foo/b.git \\\n'
            '"'
        )
        with caplog.at_level(logging.DEBUG):
            parse_src_uri(src_uri, "myrecipe", seen_unknown_schemes=set())
        debug_msgs = [
            r.message for r in caplog.records
            if r.levelno == logging.DEBUG and "crate+git" in r.message
        ]
        assert len(debug_msgs) == 1, (
            f"Expected 1 DEBUG log for crate+git, got {len(debug_msgs)}"
        )

    def test_go_vendor_git_not_emitted(self, caplog):
        """go-vendor git:// entries produce no golang PURLs (deferred scheme)."""
        # This is the gosu-style git:// approach
        src_uri = (
            'SRC_URI = "git://github.com/tianon/gosu.git;branch=master;protocol=https '
            'git://github.com/moby/sys;name=user;destsuffix=git/src/github.com/moby/sys;'
            'branch=main;protocol=https"'
        )
        with caplog.at_level(logging.DEBUG):
            results = parse_src_uri(src_uri, "gosu")
        assert results == []

    def test_parent_recipe_set(self):
        """Each result must carry the correct parent recipe name."""
        src_uri = 'SRC_URI += "crate://crates.io/tokio/1.40.0"'
        results = parse_src_uri(src_uri, "my-rust-recipe")
        assert len(results) == 1
        assert results[0].parent_recipe == "my-rust-recipe"

    def test_negative_case_zlib(self, zlib_bb):
        """zlib recipe (C, no vendored deps) produces empty result."""
        src_uri_text = _inc_text(zlib_bb)
        results = parse_src_uri(src_uri_text, "zlib")
        assert results == []


# ---------------------------------------------------------------------------
# Recipe-name validation tests (§7.9 + §3.6)
# ---------------------------------------------------------------------------

class TestRecipeNameAllowlist:
    """
    Validate recipe names against the allowlist regex:
        ^[A-Za-z0-9_][A-Za-z0-9._+/-]*$
    matched with re.fullmatch() so trailing \\n is rejected.
    """

    VALID_NAMES = [
        "virtual/kernel",
        "g++",
        "libstdc++",
        "python3-cryptography",
        "librsvg",
        "linux-yocto",
        "packagegroup-core-base",
        "a",                # single char
        "A_1",
        "meta-toolchain",
    ]

    INVALID_NAMES = [
        "--foo",            # leading --
        "-foo",             # leading -
        "+foo",             # leading +
        "a b",              # whitespace
        "foo;bar",          # semicolon
        "foo|bar",          # pipe
        "foo&bar",          # ampersand
        "foo\nbar",         # embedded newline
        "foo\x00bar",       # null byte
        "foo\n",            # trailing newline — must be caught by fullmatch/\\Z
        "",                 # empty string
    ]

    @pytest.mark.parametrize("name", VALID_NAMES)
    def test_valid_name_accepted(self, name):
        from bd_scan_yocto.vendored_deps import validate_recipe_name
        assert validate_recipe_name(name) is True, (
            f"Expected '{name}' to be valid"
        )

    @pytest.mark.parametrize("name", INVALID_NAMES)
    def test_invalid_name_rejected(self, name):
        from bd_scan_yocto.vendored_deps import validate_recipe_name
        assert validate_recipe_name(name) is False, (
            f"Expected '{name}' to be rejected"
        )

    def test_trailing_newline_rejected_fullmatch(self):
        """Trailing \\n must be rejected: proves fullmatch/\\Z is used, not $."""
        from bd_scan_yocto.vendored_deps import validate_recipe_name
        assert validate_recipe_name("foo\n") is False


# ---------------------------------------------------------------------------
# --vendored_deps_recipes "not found" warning message (§7.1 last bullet)
# ---------------------------------------------------------------------------

class TestVendoredDepsRecipesWarning:
    """§7.1: supplying a non-existent recipe name via --vendored_deps_recipes
    logs the exact warning text."""

    def test_missing_recipe_warning(self, caplog):
        """
        When a recipe name from --vendored_deps_recipes does not appear in
        RecipeList, a warning matching the exact pattern must be logged.
        """
        from bd_scan_yocto.vendored_deps import warn_missing_recipe_names

        with caplog.at_level(logging.WARNING):
            warn_missing_recipe_names(
                requested=["does-not-exist"],
                available={"zlib", "openssl"},
            )

        expected_fragment = (
            "Recipe 'does-not-exist' from --vendored_deps_recipes "
            "not found in processed recipes - skipping"
        )
        assert any(expected_fragment in r.message for r in caplog.records), (
            f"Expected warning containing: {expected_fragment!r}"
        )


# ---------------------------------------------------------------------------
# Fixture sanitisation lint (§7.9 positive self-test)
# ---------------------------------------------------------------------------

class TestFixtureSanitisation:
    """Prove the two-step lint pipeline runs and catches real credentials."""

    def test_sensitive_string_detected(self, tmp_path):
        """
        A file containing a known-bad string must survive step-1 grep
        and NOT be filtered out by step-2 grep.
        """
        import subprocess

        bad_file = tmp_path / "bad.txt"
        bad_file.write_text(
            "BLACKDUCK_API_TOKEN=hunter2\n/home/alice/build/tmp/log\n"
        )

        # Step 1: grep for sensitive patterns
        r1 = subprocess.run(
            ["grep", "-rnE",
             r'https?://|/home/|/root/|BLACKDUCK_|@[A-Za-z0-9.-]+\.(com|net|org)',
             str(tmp_path)],
            capture_output=True, text=True
        )
        assert r1.returncode == 0, "Step-1 grep must find hits in the bad file"
        assert "hunter2" in r1.stdout or "BLACKDUCK_API_TOKEN" in r1.stdout

        # Step 2: subtract known-good hosts — bad file lines must survive
        r2 = subprocess.run(
            ["grep", "-vE",
             r'https?://(layers\.openembedded\.org|git\.openembedded\.org|'
             r'git\.yoctoproject\.org|crates\.io|static\.crates\.io|'
             r'proxy\.golang\.org|sum\.golang\.org|github\.com|'
             r'raw\.githubusercontent\.com)(/|$|")'],
            input=r1.stdout, capture_output=True, text=True
        )
        # Remaining hits — must be non-empty (the bad strings are not allowlisted)
        assert r2.returncode == 0, (
            "Step-2 grep must return 0 (hits present after filtering)"
        )
        assert r2.stdout.strip(), (
            "Bad strings must survive step-2 allowlist filter"
        )

    def test_real_fixtures_clean(self, vendored_dir):
        """
        The real fixture directory must produce no hits after both steps.
        """
        import subprocess

        r1 = subprocess.run(
            ["grep", "-rnE",
             r'https?://|/home/|/root/|BLACKDUCK_|@[A-Za-z0-9.-]+\.(com|net|org)',
             str(vendored_dir)],
            capture_output=True, text=True
        )
        if r1.returncode != 0:
            # No hits at all — pass immediately
            return

        r2 = subprocess.run(
            ["grep", "-vE",
             r'https?://(layers\.openembedded\.org|git\.openembedded\.org|'
             r'git\.yoctoproject\.org|crates\.io|static\.crates\.io|'
             r'proxy\.golang\.org|sum\.golang\.org|github\.com|'
             r'raw\.githubusercontent\.com|google\.golang\.org|'
             r'gopkg\.in|cloud\.google\.com|honnef\.co|'
             r'golang\.org|gitlab\.com|zlib\.net|doc\.rust-lang\.org|'
             r'rust-lang\.org|cryptography\.io|www\.crowdsec\.net)(/|$|")'],
            input=r1.stdout, capture_output=True, text=True
        )
        assert r2.returncode != 0 or not r2.stdout.strip(), (
            f"Unexpected sensitive content in fixtures:\n{r2.stdout}"
        )
