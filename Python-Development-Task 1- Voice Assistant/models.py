"""Domain models for general knowledge queries and QA responses."""

from dataclasses import dataclass


@dataclass(frozen=True)
class KnowledgeAnswer:
    """Domain model for a knowledge query result."""
    query: str
    summary: str
    source: str

    def to_speech_text(self) -> str:
        """Format answer for natural speech playback."""
        # Ensure it's concise and readable
        text = self.summary.strip()
        # Keep within first 2 sentences for concise voice delivery if too long
        sentences = [s.strip() for s in text.split(". ") if s.strip()]
        if len(sentences) > 2:
            concise = ". ".join(sentences[:2])
            if not concise.endswith("."):
                concise += "."
            return concise
        return text
