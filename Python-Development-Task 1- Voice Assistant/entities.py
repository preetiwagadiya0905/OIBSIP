"""Entity extraction logic and models for natural language queries."""

import re
from dataclasses import dataclass

from voice_assistant.config.constants import CustomActionType
from voice_assistant.utils.text import (
    normalize_spoken_email,
    normalize_text,
    parse_duration_seconds,
)


@dataclass(frozen=True)
class WeatherEntity:
    location: str


@dataclass(frozen=True)
class ReminderEntity:
    duration_seconds: int
    message: str


@dataclass(frozen=True)
class EmailEntity:
    recipient: str | None = None
    subject: str | None = None
    body: str | None = None


@dataclass(frozen=True)
class SearchEntity:
    query: str


@dataclass(frozen=True)
class KnowledgeEntity:
    query: str


@dataclass(frozen=True)
class CustomCommandEntity:
    name: str
    action: CustomActionType
    target: str


def extract_weather_entity(text: str) -> WeatherEntity | None:
    """Extract location from weather queries."""
    normalized = normalize_text(text)
    patterns = [
        r"(?:what(?:'s| is) (?:the )?weather like in|how is the weather in|weather like in)\s+([a-zA-Z\s.,'-]+)",
        r"(?:weather|forecast|temperature|temp|climate|how (?:warm|cold|hot|humid) is it|is it raining)(?:\s+(?:in|for|of|at))?\s+([a-zA-Z\s.,'-]+?)(?:\s+today|\s+now|\s+please)?$",
        r"(?:in|for)\s+([a-zA-Z\s.,'-]+?)\s+(?:weather|forecast|temperature)",
    ]

    for p in patterns:
        match = re.search(p, normalized, re.IGNORECASE)
        if match:
            loc = match.group(1).strip()
            loc = re.sub(r"^(?:like in|like|in|for|of|at)\s+", "", loc, flags=re.IGNORECASE).strip()
            loc = re.sub(r"\s+(?:today|now|please|outside)$", "", loc, flags=re.IGNORECASE).strip()
            if loc and loc not in ("the", "today", "now", "here", "outside", "like"):
                return WeatherEntity(location=loc)

    return None


def extract_reminder_entity(text: str) -> ReminderEntity | None:
    """Extract duration and reminder task from reminder phrases."""
    result = parse_duration_seconds(text)
    if result:
        secs, msg = result
        return ReminderEntity(duration_seconds=secs, message=msg)
    return None


def extract_email_entity(text: str) -> EmailEntity:
    """Extract email fields (recipient, subject, body) if present in a single spoken sentence."""
    raw = text.strip()
    recipient: str | None = None
    subject: str | None = None
    body: str | None = None

    # Check for direct standard email address with word boundaries
    direct_match = re.search(r"\b[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+\b", raw)
    if direct_match:
        recipient = direct_match.group(0)
    else:
        # Check for spoken pattern "to <spoken email>"
        spoken_to_match = re.search(r"\b(?:to|unto)\s+([a-zA-Z0-9_\-.\s]+(?:\bat\b|@)[a-zA-Z0-9_\-.\s]+)", raw, re.IGNORECASE)
        if spoken_to_match:
            candidate = normalize_spoken_email(spoken_to_match.group(1))
            if re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", candidate):
                recipient = candidate

    # Check for subject: "with subject <subject>" or "subject <subject>"
    subj_match = re.search(r"(?:with\s+)?subject\s+([^\n\r]+?)(?:\s+(?:and\s+)?(?:body|message)\s+|$)", raw, re.IGNORECASE)
    if subj_match:
        subject = subj_match.group(1).strip()

    # Check for body: "and body/message <body>" or "saying <body>"
    body_match = re.search(r"(?:(?:and\s+)?(?:body|message)|saying)\s+([^\n\r]+)$", raw, re.IGNORECASE)
    if body_match:
        body = body_match.group(1).strip()

    return EmailEntity(recipient=recipient, subject=subject, body=body)


def extract_search_entity(text: str) -> SearchEntity | None:
    """Extract web search query string."""
    normalized = normalize_text(text)
    patterns = [
        r"(?:search(?: the web)?(?: for)?|google|look up|find info on|browse for)\s+(.+)",
        r"what is\s+(.+)",
    ]
    for p in patterns:
        match = re.search(p, normalized, re.IGNORECASE)
        if match:
            query = match.group(1).strip()
            # Remove trailing please
            query = re.sub(r"\s+please$", "", query, flags=re.IGNORECASE).strip()
            if query:
                return SearchEntity(query=query)
    return None


def extract_knowledge_entity(text: str) -> KnowledgeEntity | None:
    """Extract subject/question topic for QA / Knowledge lookup."""
    normalized = normalize_text(text)
    patterns = [
        r"(?:who (?:is|was|were)|what (?:is|was|are|were)|tell me about|tell me who is|explain|define)\s+(.+)",
        r"(?:where is|what do you know about)\s+(.+)",
    ]
    for p in patterns:
        match = re.search(p, normalized, re.IGNORECASE)
        if match:
            topic = match.group(1).strip()
            topic = re.sub(r"\s+please$", "", topic, flags=re.IGNORECASE).strip()
            if topic:
                return KnowledgeEntity(query=topic)
    return None


def extract_custom_command_entity(text: str) -> CustomCommandEntity | None:
    """Extract custom command creation parameters."""
    normalized = text.strip()
    # Patterns:
    # "create a command called <name> that opens <url>"
    # "add custom command <name> to open <url>"
    # "add command <name> action open_url target <url>"
    # "add command <name> to speak <text>"

    url_match = re.search(
        r"(?:create|add)(?:\s+a)?(?:\s+custom)?\s+command(?:\s+called)?\s+[\"']?([^\"']+?)[\"']?\s+(?:that\s+opens|to\s+open|opening|open_url(?:\s+target)?)\s+[\"']?(https?://\S+)[\"']?",
        normalized,
        re.IGNORECASE
    )
    if url_match:
        name = normalize_text(url_match.group(1))
        url = url_match.group(2).strip()
        return CustomCommandEntity(name=name, action=CustomActionType.OPEN_URL, target=url)

    speak_match = re.search(
        r"(?:create|add)(?:\s+a)?(?:\s+custom)?\s+command(?:\s+called)?\s+[\"']?([^\"']+?)[\"']?\s+(?:that\s+speaks|to\s+speak|speaking|speak(?:\s+target)?|saying)\s+[\"']?(.+?)[\"']?$",
        normalized,
        re.IGNORECASE
    )
    if speak_match:
        name = normalize_text(speak_match.group(1))
        target_text = speak_match.group(2).strip()
        return CustomCommandEntity(name=name, action=CustomActionType.SPEAK, target=target_text)

    return None
