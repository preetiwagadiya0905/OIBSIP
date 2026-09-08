"""Web search command with safe URL construction and browser launching."""

import urllib.parse
import webbrowser

from voice_assistant.commands.base import BaseCommand, CommandContext, CommandResult
from voice_assistant.config.constants import IntentType
from voice_assistant.nlp.intent import IntentResult
from voice_assistant.observability.logging import get_logger

logger = get_logger(__name__)


class WebSearchCommand(BaseCommand):
    """Executes safe browser web searches on user-specified topics."""

    @property
    def name(self) -> str:
        return "WebSearchCommand"

    @property
    def description(self) -> str:
        return "Safely encodes search query and opens web search in default browser."

    @property
    def supported_intents(self) -> set[IntentType]:
        return {IntentType.WEB_SEARCH}

    def execute(self, intent_result: IntentResult, context: CommandContext) -> CommandResult:
        query = intent_result.entities.get("query")
        if not query or not query.strip():
            query = intent_result.normalized_text.strip()

        if not query:
            return CommandResult.fail("What would you like me to search for?")

        # Construct safe URL with standard encoding
        encoded_query = urllib.parse.urlencode({"q": query})
        search_url = f"https://www.google.com/search?{encoded_query}"

        logger.info(f"Opening browser search: {search_url}")
        try:
            # Safe browser opening without shell
            webbrowser.open_new_tab(search_url)
            return CommandResult.ok(
                f"Searching the web for {query}.",
                data={"query": query, "url": search_url},
            )
        except Exception as e:
            logger.error(f"Failed to open web browser: {e}")
            return CommandResult.fail(f"Could not open browser for search: {e}")
