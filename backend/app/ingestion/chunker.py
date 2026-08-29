import re
import tiktoken


encoding = tiktoken.get_encoding("cl100k_base")


def token_count(text: str) -> int:
    return len(encoding.encode(text))


def split_long_sentence(
    sentence: str,
    chunk_size: int,
) -> list[str]:

    words = sentence.split()
    parts = []
    current_words = []

    for word in words:
        candidate = " ".join(current_words + [word])

        if token_count(candidate) <= chunk_size:
            current_words.append(word)
        else:
            if current_words:
                parts.append(" ".join(current_words))

            current_words = [word]

    if current_words:
        parts.append(" ".join(current_words))

    return parts


def chunk_text(
    text: str,
    chunk_size: int = 400,
    overlap_tokens: int = 50,
) -> list[str]:

    paragraphs = [
        paragraph.strip()
        for paragraph in text.splitlines()
        if paragraph.strip()
    ]

    sentences = []

    for paragraph in paragraphs:
        parts = re.split(
            r"(?<=[.!?])\s+",
            paragraph,
        )

        for sentence in parts:
            sentence = sentence.strip()

            if not sentence:
                continue

            if token_count(sentence) <= chunk_size:
                sentences.append(sentence)
            else:
                sentences.extend(
                    split_long_sentence(
                        sentence,
                        chunk_size,
                    )
                )

    chunks = []
    current_sentences = []

    for sentence in sentences:

        candidate = " ".join(
            current_sentences + [sentence]
        )

        if token_count(candidate) <= chunk_size:
            current_sentences.append(sentence)

        else:
            if current_sentences:
                chunks.append(
                    " ".join(current_sentences)
                )

            # Build token-based overlap.
            overlap_text = ""

            for previous in reversed(current_sentences):
                candidate_overlap = (
                    previous
                    + " "
                    + overlap_text
                )

                if token_count(candidate_overlap) > overlap_tokens:
                    break

                overlap_text = candidate_overlap

            current_sentences = []

            if overlap_text:
                current_sentences.append(
                    overlap_text
                )

            current_sentences.append(sentence)

    if current_sentences:
        chunks.append(
            " ".join(current_sentences)
        )

    return chunks