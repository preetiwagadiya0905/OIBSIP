"""Knowledge provider abstractions, composite search, and local fallback base."""

from typing import Protocol

from voice_assistant.errors.exceptions import KnowledgeServiceError
from voice_assistant.observability.logging import get_logger
from voice_assistant.services.knowledge.client import (
    DuckDuckGoKnowledgeClient,
    WikipediaKnowledgeClient,
)
from voice_assistant.services.knowledge.models import KnowledgeAnswer
from voice_assistant.utils.text import normalize_text

logger = get_logger(__name__)


class KnowledgeProvider(Protocol):
    """Protocol for answering general knowledge questions."""

    def get_answer(self, query: str) -> KnowledgeAnswer | None:
        """Look up answer for the given query."""
        ...


class LocalCuratedKnowledgeProvider:
    """Offline curated knowledge base for fast, reliable answers to common queries."""

    CURATED_KNOWLEDGE: dict[str, str] = {
        "alan turing": "Alan Turing was an English mathematician, computer scientist, and cryptanalyst considered the father of theoretical computer science and artificial intelligence.",
        "python": "Python is a high-level, interpreted programming language known for its clear syntax, dynamic typing, and widespread use in software development, data science, and AI.",
        "capital of japan": "The capital of Japan is Tokyo, a bustling metropolis that mixes ultramodern architecture with historic temples.",
        "capital of india": "The capital of India is New Delhi, the seat of all three branches of the Government of India.",
        "capital of france": "The capital of France is Paris, globally renowned for its art, fashion, gastronomy, and culture.",
        "capital of united states": "The capital of the United States is Washington, D.C., located on the Potomac River bordering Maryland and Virginia.",
        "photosynthesis": "Photosynthesis is the biological process used by plants and other organisms to convert light energy into chemical energy in the form of sugars.",
        "speed of light": "The speed of light in a vacuum is approximately 299,792 kilometers per second, or about 186,282 miles per second.",
        "albert einstein": "Albert Einstein was a German-born theoretical physicist who developed the theory of relativity and made foundational contributions to quantum mechanics.",
        "mount everest": "Mount Everest is Earth's highest mountain above sea level, located in the Mahalangur Himal sub-range of the Himalayas.",
    }

    def get_answer(self, query: str) -> KnowledgeAnswer | None:
        normalized = normalize_text(query)
        # Check direct or substring matches
        for key, summary in self.CURATED_KNOWLEDGE.items():
            if key in normalized or normalized in key:
                logger.info(f"Resolved query '{query}' from LocalCuratedKnowledgeProvider (key='{key}')")
                return KnowledgeAnswer(query=query, summary=summary, source="LocalKnowledgeBase")
        return None


class CompositeKnowledgeProvider:
    """Queries external sources (Wikipedia, DuckDuckGo) and falls back to local curated knowledge."""

    def __init__(
        self,
        wiki_client: WikipediaKnowledgeClient | None = None,
        ddg_client: DuckDuckGoKnowledgeClient | None = None,
        local_provider: LocalCuratedKnowledgeProvider | None = None,
    ):
        self.wiki_client = wiki_client or WikipediaKnowledgeClient()
        self.ddg_client = ddg_client or DuckDuckGoKnowledgeClient()
        self.local_provider = local_provider or LocalCuratedKnowledgeProvider()

    def get_answer(self, query: str) -> KnowledgeAnswer | None:
        clean_query = query.strip()
        if not clean_query:
            return None

        # 1. Check local knowledge first for instant hits
        local_ans = self.local_provider.get_answer(clean_query)
        if local_ans:
            return local_ans

        # 2. Try Wikipedia
        wiki_ans = self.wiki_client.search(clean_query)
        if wiki_ans:
            return wiki_ans

        # 3. Try DuckDuckGo
        ddg_ans = self.ddg_client.search(clean_query)
        if ddg_ans:
            return ddg_ans

        return None


class MockKnowledgeProvider:
    """Mock knowledge provider for testing."""

    def __init__(self, predefined: dict[str, str] | None = None):
        self._answers = predefined or {
            "alan turing": "Alan Turing was a mathematician and father of computer science.",
            "python": "Python is a popular programming language created by Guido van Rossum.",
            "capital of japan": "The capital of Japan is Tokyo.",
        }

    def get_answer(self, query: str) -> KnowledgeAnswer | None:
        norm = normalize_text(query)
        for k, v in self._answers.items():
            if k in norm:
                return KnowledgeAnswer(query=query, summary=v, source="Mock")
        return None


class KnowledgeService:
    """Application service for answering general knowledge questions."""

    def __init__(self, provider: KnowledgeProvider):
        self.provider = provider

    def answer_question(self, query: str) -> str:
        """Answer a knowledge question or return a polite fallback."""
        if not query or not query.strip():
            raise KnowledgeServiceError("Knowledge query cannot be empty.")

        clean_query = query.strip()
        logger.info(f"Looking up knowledge for: '{clean_query}'")
        answer = self.provider.get_answer(clean_query)

        if not answer:
            return f"I couldn't find detailed information about '{clean_query}'. You can try asking me to search the web for it."

        return answer.to_speech_text()
