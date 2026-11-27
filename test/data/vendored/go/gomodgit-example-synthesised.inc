# SYNTHESISED FIXTURE — not fetched from a real repo
# Faithfully represents the gomodgit:// SRC_URI format used by the go-mod class
# with git-based module sources.
#
# The gomodgit:// scheme is an OE variant of gomod:// that fetches a Go module
# from a git repository instead of a module proxy.
#
# Format: SCHEME://MODULE_PATH;version=SEMVER;cset=COMMIT;sha256sum=HASH  (scheme=gomodgit)
# Parameters: version, cset (commit hash), sha256sum, branch, protocol are common.
# The recipe name for this fixture is "gomodgit-example".

SRC_URI += "\
    gomodgit://github.com/google/uuid;version=v1.6.0;cset=0f11ee6d;sha256sum=22f66fdc4b454d0e9a4da5e0e5e6e3a7c1a1a7b6c2d3e4f5a6b7c8d9e0f1a2b \
    gomodgit://golang.org/x/net;version=v0.24.0;cset=aad5b6fb;sha256sum=33f55c83a87cc04e19ae2abd52ac8b5e5e7e9b1a2b3c4d5e6f7a8b9c0d1e2f3 \
    gomodgit://golang.org/x/text;version=v0.15.0;cset=1234abcd;sha256sum=44a66c84b98ce3be88cf0eadf52bc9c6e7e8f0a1b2c3d4e5f6a7b8c9d0e1f2a \
"
