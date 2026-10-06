import asyncio
from typing import AsyncGenerator, List, Dict, Any, Tuple
from app.config import settings
from app.services.vector_store import vector_store

SYSTEM_PROMPT = """You are EduVault, an institutional knowledge assistant for university students, faculty, and administration.
Answer the user's question strictly and solely based on the provided institutional context passages below.
Do not hallucinate, guess, or incorporate external assumptions.
If the answer is not contained in the context, explicitly respond with: "Information not found in the institutional knowledge base."
Format your response clearly with concise paragraphs or bullet points where appropriate."""


class RAGService:
    def __init__(self):
        self.top_k = settings.RETRIEVAL_TOP_K
        self.threshold = settings.SIMILARITY_THRESHOLD

    def retrieve(self, query: str) -> List[Dict[str, Any]]:
        candidates = vector_store.query(query, top_k=self.top_k)
        # Filter by similarity threshold
        filtered = [c for c in candidates if c["similarity"] >= self.threshold]
        return filtered

    async def stream_rag_response(
        self, question: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Yields events:
        - {"type": "token", "data": "..."}
        - {"type": "citation", "data": [...]}
        - {"type": "done"}
        """
        retrieved_chunks = self.retrieve(question)

        # Safe failure gate
        if not retrieved_chunks:
            yield {
                "type": "token",
                "data": "Information not found in the institutional knowledge base.",
            }
            yield {"type": "citation", "data": []}
            yield {"type": "done"}
            return

        # Prepare Citations
        citations = []
        seen_citations = set()
        for chunk in retrieved_chunks:
            meta = chunk.get("metadata", {})
            doc_name = meta.get("document_name", "Unknown Document")
            page = int(meta.get("page", 1))
            section = meta.get("section", "General")
            key = (doc_name, page, section)
            if key not in seen_citations:
                seen_citations.add(key)
                citations.append({
                    "document_name": doc_name,
                    "page": page,
                    "section": section,
                })

        # Assemble Context
        context_parts = []
        for idx, chunk in enumerate(retrieved_chunks, start=1):
            meta = chunk.get("metadata", {})
            doc_name = meta.get("document_name", "Document")
            page = meta.get("page", 1)
            section = meta.get("section", "General")
            context_parts.append(
                f"[Source {idx}: {doc_name} | Section: {section} | Page: {page}]\n{chunk['content']}"
            )
        context_str = "\n\n".join(context_parts)

        prompt = f"{SYSTEM_PROMPT}\n\nCONTEXT:\n{context_str}\n\nQUESTION:\n{question}\n\nANSWER:"

        # LLM Streaming
        generated_any = False
        try:
            if settings.LLM_PROVIDER == "gemini" and settings.GEMINI_API_KEY:
                import google.generativeai as genai
                genai.configure(api_key=settings.GEMINI_API_KEY)
                model = genai.GenerativeModel("gemini-1.5-flash")
                response = await asyncio.to_thread(
                    model.generate_content,
                    prompt,
                    stream=True,
                )
                for chunk in response:
                    if chunk.text:
                        generated_any = True
                        yield {"type": "token", "data": chunk.text}

            elif settings.LLM_PROVIDER == "groq" and settings.GROQ_API_KEY:
                from groq import Groq
                client = Groq(api_key=settings.GROQ_API_KEY)
                completion = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": f"CONTEXT:\n{context_str}\n\nQUESTION: {question}"},
                    ],
                    stream=True,
                )
                for chunk in completion:
                    token = chunk.choices[0].delta.content or ""
                    if token:
                        generated_any = True
                        yield {"type": "token", "data": token}
        except Exception as e:
            # Fall back gracefully to synthesized summary of retrieved context
            yield {"type": "token", "data": f"\n\n[Retrieved Context]:\n{retrieved_chunks[0]['content']}"}
            generated_any = True

        if not generated_any:
            # Built-in direct context response when external LLM API key is not yet set
            yield {
                "type": "token",
                "data": f"Based on {citations[0]['document_name']}:\n\n{retrieved_chunks[0]['content']}",
            }

        # Send citations and completion signal
        yield {"type": "citation", "data": citations}
        yield {"type": "done"}


rag_service = RAGService()
