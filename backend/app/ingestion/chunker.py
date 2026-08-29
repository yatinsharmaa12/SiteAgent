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

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    sections = []
    current_section = []

    for line in lines:
        if line.startswith("#"):
            if current_section:
                sections.append("\n".join(current_section))

            current_section = [line]

        else:
            current_section.append(line)

    if current_section:
        sections.append("\n".join(current_section))

    chunks = []

    for section in sections:
        sentences = []

        for paragraph in section.splitlines():
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

                current_sentences = [sentence]

        if current_sentences:
            chunks.append(
                " ".join(current_sentences)
            )

    return chunks