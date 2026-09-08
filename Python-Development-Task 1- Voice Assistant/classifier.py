"""Hybrid Natural Language Intent Classifier."""

import math
import re
from collections import Counter

from voice_assistant.config.constants import (
    CANCELLATION_WORDS,
    CONFIRMATION_NO_WORDS,
    CONFIRMATION_YES_WORDS,
    IntentType,
)
from voice_assistant.nlp.corpus import INTENT_CORPUS
from voice_assistant.observability.logging import get_logger
from voice_assistant.utils.text import normalize_text

logger = get_logger(__name__)

# Stopwords list for lightweight token filtering
STOPWORDS: set[str] = {
    "a", "an", "the", "in", "on", "at", "for", "to", "of", "with", "by", "is",
    "are", "was", "were", "be", "been", "being", "have", "has", "had", "do",
    "does", "did", "can", "could", "should", "would", "may", "might", "must",
    "i", "you", "he", "she", "it", "we", "they", "me", "him", "her", "us",
    "them", "my", "your", "his", "their", "our", "please", "assistant", "aura",
}


def tokenize(text: str) -> list[str]:
    """Tokenize and filter text into word tokens."""
    tokens = re.findall(r"\b[a-z0-9'-]+\b", normalize_text(text))
    return [t for t in tokens if t not in STOPWORDS]


class HybridIntentClassifier:
    """Hybrid rule-based and vector-space similarity intent classifier."""

    def __init__(self, confidence_threshold: float = 0.50):
        self.confidence_threshold = confidence_threshold
        self._corpus_vectors: dict[IntentType, list[Counter[str]]] = {}
        self._idf: dict[str, float] = {}
        self._train()

    def _train(self) -> None:
        """Build TF-IDF vocabulary and intent corpus representation."""
        doc_count = sum(len(samples) for samples in INTENT_CORPUS.values())
        doc_freq: Counter[str] = Counter()

        for intent, samples in INTENT_CORPUS.items():
            vectors = []
            for sample in samples:
                tokens = tokenize(sample)
                tf = Counter(tokens)
                vectors.append(tf)
                for unique_token in set(tokens):
                    doc_freq[unique_token] += 1
            self._corpus_vectors[intent] = vectors

        for word, count in doc_freq.items():
            self._idf[word] = math.log((1.0 + doc_count) / (1.0 + count)) + 1.0

        logger.debug(f"Trained intent classifier with {len(self._idf)} vocabulary tokens.")

    def _compute_cosine_sim(self, query_tf: Counter[str], target_tf: Counter[str]) -> float:
        """Compute cosine similarity between two TF-IDF token frequency counters."""
        dot_product = 0.0
        norm_q = 0.0
        norm_t = 0.0

        for word, count in query_tf.items():
            weight_q = count * self._idf.get(word, 1.0)
            norm_q += weight_q * weight_q
            if word in target_tf:
                weight_t = target_tf[word] * self._idf.get(word, 1.0)
                dot_product += weight_q * weight_t

        for word, count in target_tf.items():
            weight_t = count * self._idf.get(word, 1.0)
            norm_t += weight_t * weight_t

        if norm_q == 0 or norm_t == 0:
            return 0.0

        return dot_product / (math.sqrt(norm_q) * math.sqrt(norm_t))

    def _rule_match(self, normalized_text: str) -> tuple[IntentType, float] | None:
        """High-precision pattern matching for unambiguous phrases."""
        text = normalized_text.strip()

        # Exit
        if re.search(r"^(?:goodbye|bye|exit|quit|shut down|turn off)$", text):
            return IntentType.EXIT, 1.0

        # Cancellation
        if text in CANCELLATION_WORDS or text in ("cancel", "never mind", "abort", "cancel that"):
            return IntentType.CANCEL, 1.0

        # Exact confirmation
        if text in CONFIRMATION_YES_WORDS:
            return IntentType.CONFIRMATION_YES, 1.0
        if text in CONFIRMATION_NO_WORDS:
            return IntentType.CONFIRMATION_NO, 1.0

        # Greetings
        if re.search(r"^(?:hello|hi|hey|good (?:morning|afternoon|evening)|howdy)(?:\s+(?:there|assistant|aura))?$", text):
            return IntentType.GREETING, 0.98

        # Time
        if re.search(r"(?:what(?:'s| is) the (?:current )?time|tell me the time|what time is it|current time)", text):
            return IntentType.TIME, 0.98

        # Date
        if re.search(r"(?:what(?:'s| is) (?:today's|the) date|tell me (?:today's|the) date|what day is it|which day is it)", text):
            return IntentType.DATE, 0.98

        # Reminders
        if re.search(r"\b(?:remind me|set (?:a )?reminder)\b", text):
            return IntentType.SET_REMINDER, 0.95

        # Weather
        if re.search(r"\b(?:weather|forecast|temperature|temp|climate|how (?:warm|cold|hot) is it|is it raining)\b", text):
            return IntentType.WEATHER, 0.95

        # Email
        if re.search(r"\b(?:send|compose|write)(?:\s+an)?\s+email\b", text):
            return IntentType.SEND_EMAIL, 0.95

        # Custom command addition
        if re.search(r"\b(?:create|add)(?:\s+a)?(?:\s+custom)?\s+command\b", text):
            return IntentType.ADD_COMMAND, 0.95

        # Web Search
        if re.search(r"^(?:search(?: the web)?|google|look up|find info on|browse)\b", text):
            return IntentType.WEB_SEARCH, 0.92

        # Knowledge
        if re.search(r"^(?:who (?:was|is)|what (?:is|are|was)|where is|tell me about|explain|define)\b", text):
            return IntentType.KNOWLEDGE, 0.90

        # Help
        if re.search(r"^(?:help|what can you do|how to use|commands)$", text):
            return IntentType.HELP, 0.98

        return None

    def classify(self, text: str) -> tuple[IntentType, float]:
        """Classify input text into an IntentType with an associated confidence score."""
        normalized = normalize_text(text)
        if not normalized:
            return IntentType.UNKNOWN, 0.0

        # 1. Check high-precision rule match first
        rule_result = self._rule_match(normalized)
        if rule_result:
            return rule_result

        # 2. Vector-space TF-IDF similarity against training corpus
        tokens = tokenize(normalized)
        if not tokens:
            return IntentType.UNKNOWN, 0.0

        query_tf = Counter(tokens)
        best_intent = IntentType.UNKNOWN
        best_score = 0.0

        for intent, sample_vectors in self._corpus_vectors.items():
            for sample_tf in sample_vectors:
                sim = self._compute_cosine_sim(query_tf, sample_tf)
                if sim > best_score:
                    best_score = sim
                    best_intent = intent

        logger.debug(f"Statistical classification: '{normalized}' -> {best_intent.value} (score={best_score:.2f})")
        return best_intent, round(best_score, 3)
