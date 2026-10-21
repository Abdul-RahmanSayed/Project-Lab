# Local Build Input

For an unpublished local Docker build only, place a byte-identical copy of the
archive pinned in `../release.lock.json` here as `release.tar.gz`. This archive is
ignored by Git. It is not included in the runtime image as a second copy.

Render builds instead supply a reviewed HTTPS `FDA_RELEASE_URL` pointing at that
exact archive after publication is separately approved. Nothing downloads at
application startup or in response to a visitor request.
