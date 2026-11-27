"""
Regression test: capability-disabled SPDX normalised output must be byte-identical
to the normalised baseline (§7.3).

This test is SKIPPED until Step 2.4 (baseline capture) is complete.
Once the baseline files exist, it becomes a live regression gate.
"""
import pathlib
import json
import pytest

BASELINE_DIR = pathlib.Path(__file__).parent.parent / "data" / "baseline"
BASELINE_NORMALISED = BASELINE_DIR / "baseline.normalised.json"


@pytest.mark.skipif(
    not BASELINE_NORMALISED.exists(),
    reason="Baseline not yet captured (Step 2.4 pending)"
)
def test_capability_disabled_matches_baseline(tmp_path):
    """
    Run the pipeline offline with VENDORED_DEPS disabled and compare the
    normalised SPDX output to the normalised baseline from unmodified main.

    Steps:
    1. Run bd-scan-yocto-via-sbom with --modes OE_RECIPES (no VENDORED_DEPS)
       against test/data/license.manifest, offline.
    2. Normalise the output with test/spdx_normalise.py.
    3. Load both normalised documents as JSON and assert they are equal.
    """
    import subprocess
    import sys

    data_dir = pathlib.Path(__file__).parent.parent / "data"
    spdx_normalise = pathlib.Path(__file__).parent.parent / "spdx_normalise.py"

    out_spdx = tmp_path / "out.spdx.json"
    log_file = tmp_path / "out.log"

    result = subprocess.run(
        [
            sys.executable, "-m", "bd_scan_yocto.main",
            "--skip_bitbake",
            "--skip_oe_data",
            "--license_manifest", str(data_dir / "license.manifest"),
            "--bitbake_layers_file", str(data_dir / "layers.txt"),
            "-o", str(out_spdx),
            "--logfile", str(log_file),
            "--modes", "OE_RECIPES",
            "-p", "TEST",
            "-v", "TEST",
        ],
        capture_output=True, text=True, timeout=120
    )

    assert out_spdx.exists(), (
        f"SPDX output file not created. stderr:\n{result.stderr}\n"
        f"stdout:\n{result.stdout}"
    )

    # Normalise the output
    normalise_result = subprocess.run(
        [sys.executable, str(spdx_normalise), str(out_spdx)],
        capture_output=True, text=True, timeout=30
    )
    assert normalise_result.returncode == 0
    actual_normalised = json.loads(normalise_result.stdout)

    # Load baseline normalised
    with open(BASELINE_NORMALISED) as fh:
        baseline_normalised = json.load(fh)

    # Compare — must be byte-identical (as JSON data structures)
    assert actual_normalised == baseline_normalised, (
        "Capability-disabled SPDX does not match baseline. "
        "Differences indicate an unintended behaviour change."
    )
