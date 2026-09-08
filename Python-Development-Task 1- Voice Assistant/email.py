"""Conversational multi-turn email command with validation and confirmation."""

from typing import Any

from voice_assistant.application.session import SessionManager, SessionStep
from voice_assistant.commands.base import BaseCommand, CommandContext, CommandResult
from voice_assistant.config.constants import (
    CONFIRMATION_NO_WORDS,
    CONFIRMATION_YES_WORDS,
    IntentType,
)
from voice_assistant.errors.exceptions import EmailServiceError, SecurityValidationError
from voice_assistant.nlp.intent import IntentResult
from voice_assistant.observability.logging import get_logger
from voice_assistant.security.validators import validate_email_address
from voice_assistant.services.email.provider import EmailService
from voice_assistant.utils.text import normalize_spoken_email

logger = get_logger(__name__)


class EmailCommand(BaseCommand):
    """Conversational email dispatch command with step-by-step entity gathering and confirmation."""

    def __init__(self, email_service: EmailService, session_manager: SessionManager):
        self.email_service = email_service
        self.session_manager = session_manager

    @property
    def name(self) -> str:
        return "EmailCommand"

    @property
    def description(self) -> str:
        return "Composes and dispatches emails via SMTP with conversational multi-turn prompts and confirmation."

    @property
    def supported_intents(self) -> set[IntentType]:
        return {
            IntentType.SEND_EMAIL,
            IntentType.CONFIRMATION_YES,
            IntentType.CONFIRMATION_NO,
        }

    def execute(self, intent_result: IntentResult, context: CommandContext) -> CommandResult:
        sm = context.get("session_manager") or self.session_manager
        # Check if an active email session is ongoing
        session = sm.current_session
        if session and session.session_type == "email":
            return self._continue_session(intent_result, session, sm)

        # Starting a new email command
        entities = intent_result.entities
        recipient = entities.get("recipient")
        subject = entities.get("subject")
        body = entities.get("body")

        # Clean / validate recipient if provided
        if recipient:
            try:
                recipient = validate_email_address(normalize_spoken_email(recipient))
            except SecurityValidationError:
                recipient = None

        data = {
            "recipient": recipient,
            "subject": subject,
            "body": body,
        }

        # Step 1: If recipient is missing, prompt for it
        if not recipient:
            sm.start_session("email", SessionStep.AWAITING_RECIPIENT, data)
            return CommandResult.ok("Who should I send the email to?")

        # Step 2: If subject is missing, prompt for it
        if not subject:
            sm.start_session("email", SessionStep.AWAITING_SUBJECT, data)
            return CommandResult.ok(f"What should the subject be for {recipient}?")

        # Step 3: If body is missing, prompt for it
        if not body:
            sm.start_session("email", SessionStep.AWAITING_BODY, data)
            return CommandResult.ok("What should the message say?")

        # Step 4: All parameters present -> ask for confirmation
        sm.start_session("email", SessionStep.AWAITING_CONFIRMATION, data)
        return CommandResult.ok(
            f"You're about to send an email to {recipient} with subject '{subject}'. Should I send it?"
        )

    def _continue_session(self, intent_result: IntentResult, session: Any, session_manager: SessionManager) -> CommandResult:
        raw_text = intent_result.raw_text.strip()
        norm_text = intent_result.normalized_text.strip()
        step = session.current_step

        if step == SessionStep.AWAITING_RECIPIENT:
            email_candidate = normalize_spoken_email(raw_text)
            try:
                valid_recipient = validate_email_address(email_candidate)
                session.data["recipient"] = valid_recipient
                session_manager.advance_step(SessionStep.AWAITING_SUBJECT)
                return CommandResult.ok("What should the subject be?")
            except SecurityValidationError:
                return CommandResult.ok(
                    f"'{email_candidate}' does not look like a valid email address. Please state the recipient email again."
                )

        elif step == SessionStep.AWAITING_SUBJECT:
            if not raw_text:
                return CommandResult.ok("Subject cannot be empty. What should the subject be?")
            session.data["subject"] = raw_text
            session_manager.advance_step(SessionStep.AWAITING_BODY)
            return CommandResult.ok("What should the message say?")

        elif step == SessionStep.AWAITING_BODY:
            if not raw_text:
                return CommandResult.ok("Message body cannot be empty. What should the message say?")
            session.data["body"] = raw_text
            session_manager.advance_step(SessionStep.AWAITING_CONFIRMATION)
            rec = session.data["recipient"]
            subj = session.data["subject"]
            return CommandResult.ok(
                f"You're about to send an email to {rec} with subject '{subj}'. Should I send it?"
            )

        elif step == SessionStep.AWAITING_CONFIRMATION:
            if intent_result.intent == IntentType.CONFIRMATION_YES or norm_text in CONFIRMATION_YES_WORDS:
                rec = session.data["recipient"]
                subj = session.data["subject"]
                body = session.data["body"]
                session_manager.clear()

                try:
                    res = self.email_service.send(recipient=rec, subject=subj, body=body)
                    if res.success:
                        return CommandResult.ok(f"Email sent successfully to {rec}.")
                    return CommandResult.fail("Failed to send email.")
                except EmailServiceError as e:
                    return CommandResult.fail(f"Could not send email: {e.message}")
                except Exception as e:
                    logger.error(f"Unexpected email error: {e}")
                    return CommandResult.fail("An unexpected error occurred while sending the email.")

            elif intent_result.intent == IntentType.CONFIRMATION_NO or norm_text in CONFIRMATION_NO_WORDS:
                session_manager.clear()
                return CommandResult.ok("Email sending has been cancelled.")

            else:
                return CommandResult.ok(
                    "Please answer 'yes' to send the email, or 'no' to cancel."
                )

        return CommandResult.fail("Unknown session state.")
