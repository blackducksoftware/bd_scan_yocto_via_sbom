# Baseline capture

This directory holds the reference SPDX output and log from the **unmodified upstream
`main`** (pre-TASK-001), used for regression comparison in §7.3.

## Status

Baseline has NOT been captured yet. It will be captured as the final sub-step of
Step 2, after the fixtures and failing tests are in place but before any feature
code is written.

## Capture instructions (Step 2.4 commands — to be run on unmodified main)

Before running, confirm no Black Duck credentials are set:

```bash
env | grep BLACKDUCK
# expected: no output; if any are set, unset them:
unset BLACKDUCK_URL BLACKDUCK_API_TOKEN BLACKDUCK_TRUST_CERT
```

Run the script offline using the existing test/data/ fixtures:

```bash
pip install -e '.[dev]'

bd-scan-yocto-via-sbom \
    --skip_bitbake \
    --skip_oe_data \
    --license_manifest test/data/license.manifest \
    --bitbake_layers_file test/data/layers.txt \
    -o test/data/baseline/baseline.spdx.json \
    --logfile test/data/baseline/baseline.log \
    --modes OE_RECIPES 2>&1 | tee test/data/baseline/baseline.stdout

# Normalise the baseline SPDX for deterministic comparison:
python3 test/spdx_normalise.py \
    test/data/baseline/baseline.spdx.json \
    > test/data/baseline/baseline.normalised.json
```

After capture, check the files for credentials:
```bash
grep -rnE 'https?://|/home/|/root/|BLACKDUCK_|@[A-Za-z0-9.-]+\.(com|net|org)' \
    test/data/baseline/ > /tmp/hits.txt

grep -vE 'https?://(layers\.openembedded\.org|git\.openembedded\.org|git\.yoctoproject\.org|crates\.io|static\.crates\.io|proxy\.golang\.org|sum\.golang\.org|github\.com|raw\.githubusercontent\.com)(/|$|")' \
    /tmp/hits.txt
# Expected: empty output
```

If the baseline stdout shows an error (e.g. because license.manifest can't drive
an offline run without project/version), adjust the command with `-p TEST -v TEST`
and add `--blackduck_url http://localhost` (a dummy URL, safe since no real server
is available with only `-o` specified).

## Files (after capture)

- `baseline.spdx.json` — raw SPDX output from unmodified main
- `baseline.log` — log file from the run
- `baseline.stdout` — stdout from the run (tee'd)
- `baseline.normalised.json` — SPDX normalised by `test/spdx_normalise.py`
- `baseline.command` — exact command line used (written manually after capture)
