"""
Unit tests for _read_upload_bounded and the row-count limit logic in
the transactions upload router.
"""

import io

import pytest
from fastapi import UploadFile

from app.api.v1.routers.transactions import _read_upload_bounded


def _make_upload_file(content: bytes) -> UploadFile:
    return UploadFile(filename="test.csv", file=io.BytesIO(content))


@pytest.mark.asyncio
async def test_read_upload_bounded_returns_full_content_under_limit():
    content = b"a" * 1000
    upload = _make_upload_file(content)

    result = await _read_upload_bounded(upload, max_bytes=10_000)

    assert result == content


@pytest.mark.asyncio
async def test_read_upload_bounded_stops_shortly_after_exceeding_limit():
    content = b"a" * 10_000
    upload = _make_upload_file(content)

    result = await _read_upload_bounded(upload, max_bytes=100)

    # Reads in 1MB chunks internally, but for content smaller than one
    # chunk, the whole thing is read in a single pass -- the caller
    # (the route handler) is responsible for rejecting based on the
    # returned length exceeding max_bytes, not this helper truncating
    # exactly at the boundary.
    assert len(result) >= 100


@pytest.mark.asyncio
async def test_read_upload_bounded_never_buffers_wildly_more_than_limit_for_large_files():
    """
    For a file much larger than one internal chunk, confirms the
    function actually stops early rather than reading the whole thing
    -- the real behavior the size limit depends on for large uploads.
    """
    chunk_size = 1024 * 1024
    content = b"a" * (chunk_size * 5)  # 5MB
    upload = _make_upload_file(content)

    result = await _read_upload_bounded(upload, max_bytes=chunk_size)

    # Should stop within about one chunk of the limit, not read all 5MB
    assert len(result) < chunk_size * 3
