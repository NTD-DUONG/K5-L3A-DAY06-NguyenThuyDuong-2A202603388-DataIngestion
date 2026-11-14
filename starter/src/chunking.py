"""Deterministic chunks with exact character offsets into a source unit."""
import hashlib
import re

from .models import Chunk, DocumentPage


def _chunk(page: DocumentPage, start: int, end: int, method: str) -> Chunk:
    text = page.text[start:end]
    identity = f"{page.document_id}|{page.page}|{method}|{start}|{end}|{text}"
    chunk_id = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:24]
    base_offset = page.metadata.get("unit_start_char", 0)
    metadata = {
        **page.metadata,
        "document_id": page.document_id,
        "source": page.source,
        "page": page.page,
        "chunk_method": method,
        "unit_start_offset": start,
        "unit_end_offset": end,
        "document_start_char": base_offset + start,
        "document_end_char": base_offset + end,
        "char_count": len(text),
    }
    return Chunk(chunk_id, page.document_id, page.source, page.page, text, metadata)


def fixed_size(page: DocumentPage, size: int, overlap: int) -> list[Chunk]:
    """Fixed character windows; overlap applies only inside the same unit."""
    if size <= 0 or not 0 <= overlap < size:
        raise ValueError("Require size > 0 and 0 <= overlap < size")
    chunks = []
    start = 0
    while start < len(page.text):
        end = min(start + size, len(page.text))
        if page.text[start:end].strip():
            chunks.append(_chunk(page, start, end, "fixed"))
        if end == len(page.text):
            break
        start = end - overlap
    return chunks


def _split_long(text: str, start: int, end: int, max_size: int):
    """Prefer sentence endings, then whitespace, then hard split if necessary."""
    while end - start > max_size:
        window = text[start:start + max_size]
        candidates = [m.end() for m in re.finditer(r'[.!?](?=\s)', window)]
        if candidates and candidates[-1] >= max_size // 2:
            boundary = start + candidates[-1]
        else:
            spaces = [m.start() for m in re.finditer(r'\s+', window)]
            boundary = start + spaces[-1] if spaces and spaces[-1] > 0 else start + max_size
        yield start, boundary
        start = boundary
        while start < end and text[start].isspace():
            start += 1
    if start < end:
        yield start, end


def by_paragraph(page: DocumentPage, max_size: int) -> list[Chunk]:
    """Pack complete paragraphs; oversized ones split at sentence/word boundaries."""
    if max_size <= 0:
        raise ValueError("max_size must be positive")
    pieces = []
    start = 0
    for separator in re.finditer(r'\n\s*\n', page.text):
        pieces.append((start, separator.start()))
        start = separator.end()
    pieces.append((start, len(page.text)))

    spans = []
    for start, end in pieces:
        while start < end and page.text[start].isspace():
            start += 1
        while end > start and page.text[end - 1].isspace():
            end -= 1
        if start == end:
            continue
        spans.extend(_split_long(page.text, start, end, max_size))

    packed = []
    for start, end in spans:
        if packed and end - packed[-1][0] <= max_size:
            packed[-1] = (packed[-1][0], end)
        else:
            packed.append((start, end))
    return [_chunk(page, start, end, "paragraph") for start, end in packed]
