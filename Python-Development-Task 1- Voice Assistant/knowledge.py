"""Knowledge query and QA command."""


from voice_assistant.commands.base import BaseCommand, CommandContext, CommandResult
from voice_assistant.config.constants import IntentType
from voice_assistant.nlp.intent import IntentResult
from voice_assistant.observability.logging import get_logger
from voice_assistant.services.knowledge.provider import KnowledgeService

logger = get_logger(__name__)


class KnowledgeCommand(BaseCommand):
    """Answers general knowledge questions using Wikipedia, DuckDuckGo, and Local Curated Base."""

    def __init__(self, knowledge_service: KnowledgeService):
        self.knowledge_service = knowledge_service

    @property
    def name(self) -> str:
        return "KnowledgeCommand"

    @property
    def description(self) -> str:
        return "Answers general knowledge, factual, and biographical questions."

    @property
    def supported_intents(self) -> set[IntentType]:
        return {IntentType.KNOWLEDGE}

    def execute(self, intent_result: IntentResult, context: CommandContext) -> CommandResult:
        query = intent_result.entities.get("query")
        if not query or not query.strip():
            query = intent_result.normalized_text.strip()

        if not query:
            return CommandResult.fail("What would you like to know?")

        try:
            answer = self.knowledge_service.answer_question(query)
            return CommandResult.ok(answer, data={"query": query})
        except Exception as e:
            logger.error(f"Error answering knowledge query: {e}")
            return CommandResult.fail(f"I couldn't look up that information: {e}")
