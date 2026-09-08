"""External knowledge API clients for Wikipedia and DuckDuckGo."""


import requests
import wikipediaapi

from voice_assistant.observability.logging import get_logger
from voice_assistant.services.knowledge.models import KnowledgeAnswer

logger = get_logger(__name__)


class WikipediaKnowledgeClient:
    """Client using official Wikipedia API via wikipedia-api library."""

    def __init__(self, user_agent: str = "AuraVoiceAssistant/1.0 (contact@example.com)", timeout: float = 8.0):
        self.wiki = wikipediaapi.Wikipedia(
            user_agent=user_agent,
            language="en",
            extract_format=wikipediaapi.ExtractFormat.WIKI,
        )
        self.timeout = timeout

    def search(self, query: str) -> KnowledgeAnswer | None:
        """Query Wikipedia for article summary."""
        clean_query = query.strip()
        if not clean_query:
            return None

        try:
            logger.debug(f"Querying Wikipedia for: '{clean_query}'")
            page = self.wiki.page(clean_query)
            if not page.exists():
                logger.debug(f"Wikipedia page '{clean_query}' not found.")
                return None

            summary = page.summary.strip()
            if not summary:
                return None

            logger.info(f"Wikipedia returned summary for '{clean_query}' ({len(summary)} chars)")
            return KnowledgeAnswer(
                query=clean_query,
                summary=summary,
                source="Wikipedia",
            )
        except Exception as e:
            logger.warning(f"Wikipedia query error for '{clean_query}': {e}")
            return None


class DuckDuckGoKnowledgeClient:
    """Client for DuckDuckGo Instant Answer API."""

    API_URL = "https://api.duckduckgo.com/"

    def __init__(self, timeout: float = 8.0):
        self.timeout = timeout

    def search(self, query: str) -> KnowledgeAnswer | None:
        """Query DuckDuckGo Instant Answer API."""
        clean_query = query.strip()
        if not clean_query:
            return None

        params = {
            "q": clean_query,
            "format": "json",
            "no_html": "1",
            "skip_disambig": "1",
        }

        try:
            logger.debug(f"Querying DuckDuckGo Instant Answer for: '{clean_query}'")
            response = requests.get(self.API_URL, params=params, timeout=self.timeout)
            if response.status_code != 200:
                return None

            data = response.json()
            abstract = data.get("AbstractText", "").strip()
            if abstract:
                return KnowledgeAnswer(
                    query=clean_query,
                    summary=abstract,
                    source="DuckDuckGo",
                )

            answer = data.get("Answer", "").strip()
            if answer:
                return KnowledgeAnswer(
                    query=clean_query,
                    summary=answer,
                    source="DuckDuckGo",
                )

            return None
        except Exception as e:
            logger.warning(f"DuckDuckGo query error: {e}")
            return None
