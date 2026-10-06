from typing import AsyncIterator, List
import asyncio

from app.config import settings
from app.core.exceptions import RAGException
from app.core.logging import logger
from app.rag.prompts import (
    FALLBACK_RESPONSE,
    SYSTEM_PROMPT,
    build_rag_prompt,
)
from app.storage.vector_store import VectorQueryResult


class RAGGenerator:
    """Generates source-grounded answers via Gemini or Groq with token-level streaming."""

    def __init__(self):
        self.provider = settings.LLM_PROVIDER.lower()

    async def stream_answer(
        self,
        question: str,
        chunks: List[VectorQueryResult],
    ) -> AsyncIterator[str]:
        """Streams LLM tokens grounded on the provided retrieved chunks."""
        prompt = build_rag_prompt(question, chunks)

        if self.provider == "gemini" and settings.GEMINI_API_KEY:
            async for token in self._stream_gemini(prompt):
                yield token
        elif self.provider == "groq" and settings.GROQ_API_KEY:
            async for token in self._stream_groq(prompt):
                yield token
        else:
            # Fallback local generator for development/testing when external API key is not yet set
            logger.info("Using local mock generator (no external LLM key provided)...")
            async for token in self._stream_mock_grounded(question, chunks):
                yield token

    async def _stream_gemini(self, prompt: str) -> AsyncIterator[str]:
        try:
            import google.generativeai as genai

            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                system_instruction=SYSTEM_PROMPT,
            )

            # Note: generate_content in google-generativeai is synchronous with stream=True
            response = model.generate_content(prompt, stream=True)
            for chunk in response:
                if chunk.text:
                    yield chunk.text
                    await asyncio.sleep(0.01)
        except Exception as e:
            logger.error(f"Gemini generation error: {e}")
            raise RAGException(f"LLM generation failed: {str(e)}")

    async def _stream_groq(self, prompt: str) -> AsyncIterator[str]:
        try:
            from groq import AsyncGroq

            client = AsyncGroq(api_key=settings.GROQ_API_KEY)
            stream = await client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                stream=True,
            )
            async for chunk in stream:
                content = chunk.choices[0].delta.content or ""
                if content:
                    yield content
        except Exception as e:
            logger.error(f"Groq generation error: {e}")
            raise RAGException(f"LLM generation failed: {str(e)}")

    async def _stream_mock_grounded(
        self,
        question: str,
        chunks: List[VectorQueryResult],
    ) -> AsyncIterator[str]:
        """Provides simulated streaming grounded strictly on context passages for local tests."""
        if not chunks:
            yield FALLBACK_RESPONSE
            return

        # Produce a concise grounded summary from retrieved text
        context_snippets = [c.text.strip() for c in chunks if c.text.strip()]
        full_text = " ".join(context_snippets)

        # Stream words smoothly
        answer_text = f"Based on the institutional documentation: {full_text[:400]}."
        words = answer_text.split(" ")
        for i, word in enumerate(words):
            yield word + (" " if i < len(words) - 1 else "")
            await asyncio.sleep(0.02)


generator = RAGGenerator()
