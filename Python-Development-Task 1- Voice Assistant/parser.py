"""Complete Natural Language Understanding pipeline parser."""

from typing import Any

from voice_assistant.config.constants import IntentType
from voice_assistant.nlp.classifier import HybridIntentClassifier
from voice_assistant.nlp.entities import (
    extract_custom_command_entity,
    extract_email_entity,
    extract_knowledge_entity,
    extract_reminder_entity,
    extract_search_entity,
    extract_weather_entity,
)
from voice_assistant.nlp.intent import IntentResult
from voice_assistant.observability.logging import get_logger
from voice_assistant.utils.text import normalize_text

logger = get_logger(__name__)


class NLUParser:
    """End-to-end NLU parser converting user raw text to structured IntentResult."""

    def __init__(self, classifier: HybridIntentClassifier, confidence_threshold: float = 0.50):
        self.classifier = classifier
        self.confidence_threshold = confidence_threshold

    def parse(self, text: str) -> IntentResult:
        """Parse raw speech/text input into an IntentResult with extracted entities."""
        raw_text = text.strip() if text else ""
        normalized = normalize_text(raw_text)

        if not normalized:
            return IntentResult.unknown(raw_text, normalized)

        intent, confidence = self.classifier.classify(normalized)
        logger.info(f"Classified intent: {intent.value} (confidence: {confidence:.2f}) for '{raw_text}'")

        # Check for low confidence ambiguity requiring clarification
        if 0.30 <= confidence < self.confidence_threshold:
            clarification_text = self._get_clarification_prompt(intent)
            return IntentResult.clarify(
                intent=intent,
                confidence=confidence,
                raw_text=raw_text,
                normalized_text=normalized,
                prompt=clarification_text,
            )

        if confidence < 0.30:
            return IntentResult.unknown(raw_text, normalized)

        # Extract entities based on intent
        entities: dict[str, Any] = {}
        if intent == IntentType.WEATHER:
            w_entity = extract_weather_entity(raw_text)
            if w_entity:
                entities["location"] = w_entity.location

        elif intent == IntentType.SET_REMINDER:
            r_entity = extract_reminder_entity(raw_text)
            if r_entity:
                entities["duration_seconds"] = r_entity.duration_seconds
                entities["message"] = r_entity.message

        elif intent == IntentType.SEND_EMAIL:
            e_entity = extract_email_entity(raw_text)
            if e_entity.recipient:
                entities["recipient"] = e_entity.recipient
            if e_entity.subject:
                entities["subject"] = e_entity.subject
            if e_entity.body:
                entities["body"] = e_entity.body

        elif intent == IntentType.WEB_SEARCH:
            s_entity = extract_search_entity(raw_text)
            if s_entity:
                entities["query"] = s_entity.query
            else:
                entities["query"] = normalized

        elif intent == IntentType.KNOWLEDGE:
            k_entity = extract_knowledge_entity(raw_text)
            if k_entity:
                entities["query"] = k_entity.query
            else:
                entities["query"] = normalized

        elif intent == IntentType.ADD_COMMAND:
            c_entity = extract_custom_command_entity(raw_text)
            if c_entity:
                entities["name"] = c_entity.name
                entities["action"] = c_entity.action.value
                entities["target"] = c_entity.target

        return IntentResult(
            intent=intent,
            confidence=confidence,
            raw_text=raw_text,
            normalized_text=normalized,
            entities=entities,
            requires_clarification=False,
        )

    def _get_clarification_prompt(self, intent: IntentType) -> str:
        prompts = {
            IntentType.WEATHER: "Do you want me to check the weather?",
            IntentType.SEND_EMAIL: "Did you want to compose and send an email?",
            IntentType.SET_REMINDER: "Would you like me to set a reminder for you?",
            IntentType.WEB_SEARCH: "Would you like me to search the web for that?",
            IntentType.KNOWLEDGE: "Are you asking a knowledge question?",
            IntentType.TIME: "Did you ask for the current time?",
            IntentType.DATE: "Did you ask for today's date?",
        }
        return prompts.get(intent, "I'm not completely sure what you mean. Could you please clarify?")
