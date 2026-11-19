
import re


def create_chunks(pages, chunk_size=180, overlap=40):
    """
    Create paragraph-aware chunks from PDF pages.

    Preserves page numbers and avoids splitting sentences
    whenever possible.
    """

    chunks = []

    for page in pages:

        text = page["text"].strip()

        if not text:
            continue

        # Separate text into paragraphs
        paragraphs = re.split(r"\n\s*\n", text)

        sentences = []

        for paragraph in paragraphs:

            paragraph = re.sub(r"\s+", " ", paragraph).strip()

            if not paragraph:
                continue

            # Split paragraph into sentences
            parts = re.split(r"(?<=[.!?])\s+", paragraph)

            sentences.extend(parts)

        current_words = []

        for sentence in sentences:

            sentence_words = sentence.split()

            # Handle unusually long sentences
            if len(sentence_words) > chunk_size:

                if current_words:
                    chunks.append({
                        "text": " ".join(current_words),
                        "page": page["page"]
                    })

                current_words = []

                start = 0

                while start < len(sentence_words):

                    end = start + chunk_size

                    part = sentence_words[start:end]

                    chunks.append({
                        "text": " ".join(part),
                        "page": page["page"]
                    })

                    if end >= len(sentence_words):
                        break

                    start = end - overlap

                continue

            # Add sentence if it fits
            if len(current_words) + len(sentence_words) <= chunk_size:

                current_words.extend(sentence_words)

            else:

                # Save the current chunk
                if current_words:

                    chunks.append({
                        "text": " ".join(current_words),
                        "page": page["page"]
                    })

                # Carry some context into the next chunk
                current_words = current_words[-overlap:] + sentence_words

        # Save remaining words on this page
        if current_words:

            chunks.append({
                "text": " ".join(current_words),
                "page": page["page"]
            })

    return chunks
