def build_prompt(question: str, context: str) -> str:
    return f"""
You are a helpful assistant for a company website.

Answer the user's question using only the provided website context.

If the context does not contain enough information to answer,
say that you don't have enough information.

Do not invent facts.

Website context:
----------------
{context}
----------------

User question:
{question}

Answer:
""".strip()