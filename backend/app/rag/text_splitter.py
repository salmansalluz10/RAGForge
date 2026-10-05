from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from app.core.config import settings
from app.rag.extractors import ExtractedContent


@dataclass
class TextChunk:
    chunk_index: int
    content: str
    metadata: Dict[str, Any]
    page_number: Optional[int] = None


class RecursiveCharacterTextSplitter:
    """
    Intelligent recursive text splitter that breaks text into semantic chunks
    along paragraphs, sentences, and words while preserving configurable overlap.
    """

    def __init__(
        self,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        separators: Optional[List[str]] = None,
        min_chunk_len: int = 40,
    ):
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap if chunk_overlap is not None else settings.CHUNK_OVERLAP
        self.separators = separators or ["\n\n", "\n", ". ", "? ", "! ", "; ", ", ", " "]
        self.min_chunk_len = min_chunk_len

        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap must be strictly less than chunk_size")

    def _split_text(self, text: str, separators: List[str]) -> List[str]:
        final_chunks: List[str] = []
        separator = separators[-1]
        new_separators = []

        for i, sep in enumerate(separators):
            if sep == "":
                separator = ""
                break
            if sep in text:
                separator = sep
                new_separators = separators[i + 1:]
                break

        splits = text.split(separator) if separator else list(text)
        good_splits: List[str] = []

        for s in splits:
            if not s.strip():
                continue
            if len(s) < self.chunk_size:
                good_splits.append(s)
            else:
                if new_separators:
                    sub_splits = self._split_text(s, new_separators)
                    good_splits.extend(sub_splits)
                else:
                    # Forced character slicing
                    for j in range(0, len(s), self.chunk_size - self.chunk_overlap):
                        good_splits.append(s[j : j + self.chunk_size])

        # Merge splits into chunks of size <= chunk_size with overlap
        current_chunk: List[str] = []
        current_length = 0

        for s in good_splits:
            s_len = len(s)
            sep_len = len(separator) if current_chunk else 0

            if current_length + s_len + sep_len > self.chunk_size and current_chunk:
                doc = separator.join(current_chunk).strip()
                if len(doc) >= self.min_chunk_len:
                    final_chunks.append(doc)

                # Keep overlapping elements
                overlap_splits: List[str] = []
                overlap_len = 0
                for prev in reversed(current_chunk):
                    if overlap_len + len(prev) <= self.chunk_overlap:
                        overlap_splits.insert(0, prev)
                        overlap_len += len(prev) + len(separator)
                    else:
                        break
                current_chunk = overlap_splits
                current_length = overlap_len

            current_chunk.append(s)
            current_length += s_len + (len(separator) if len(current_chunk) > 1 else 0)

        if current_chunk:
            doc = separator.join(current_chunk).strip()
            if len(doc) >= self.min_chunk_len or not final_chunks:
                final_chunks.append(doc)

        return final_chunks

    def split_extracted_content(
        self,
        extracted_pages: List[ExtractedContent],
        document_id: str,
        document_name: str,
        file_type: str,
    ) -> List[TextChunk]:
        chunks: List[TextChunk] = []
        chunk_idx = 0

        for page in extracted_pages:
            raw_text = page.text.strip()
            if not raw_text:
                continue

            # Split each page's text
            page_chunks = self._split_text(raw_text, self.separators)
            for c_text in page_chunks:
                chunk_meta = {
                    "document_id": document_id,
                    "document_name": document_name,
                    "file_type": file_type,
                    "page_number": page.page_number,
                    "chunk_index": chunk_idx,
                    "char_count": len(c_text),
                }
                if page.metadata:
                    chunk_meta.update(page.metadata)

                chunks.append(
                    TextChunk(
                        chunk_index=chunk_idx,
                        content=c_text,
                        page_number=page.page_number,
                        metadata=chunk_meta,
                    )
                )
                chunk_idx += 1

        return chunks
