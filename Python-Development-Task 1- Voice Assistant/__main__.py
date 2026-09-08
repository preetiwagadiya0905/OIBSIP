"""CLI and Web Server entry point for Aura Voice Assistant."""

import argparse
import sys

import uvicorn

from voice_assistant.config.settings import Settings
from voice_assistant.factory import build_app
from voice_assistant.observability.logging import get_logger, setup_logging
from voice_assistant.web.app import create_app

logger = get_logger(__name__)


def main() -> None:
    """Parse CLI arguments and run Voice Assistant (Web or CLI)."""
    parser = argparse.ArgumentParser(
        description="Aura Voice Assistant - Production Full-Stack Voice Assistant"
    )
    parser.add_argument(
        "--web",
        action="store_true",
        default=True,
        help="Run as FastAPI Web application with browser microphone & speaker support (Default).",
    )
    parser.add_argument(
        "--demo", "--text",
        action="store_true",
        dest="demo_mode",
        help="Run in interactive CLI / Text mode in terminal without microphone.",
    )
    parser.add_argument(
        "--voice",
        action="store_true",
        help="Run in local microphone voice recognition mode.",
    )
    parser.add_argument(
        "--host",
        type=str,
        default=None,
        help="Host address to bind the web server to (e.g. 0.0.0.0).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Port to bind the web server to (e.g. 8000).",
    )
    parser.add_argument(
        "--list-mics",
        action="store_true",
        help="List available microphone devices on this machine and exit.",
    )
    parser.add_argument(
        "--env-file",
        type=str,
        default=None,
        help="Path to custom .env configuration file.",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default=None,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Override logging verbosity level.",
    )

    args = parser.parse_args()

    # Load configuration
    settings = Settings.load(env_file=args.env_file)
    log_level = args.log_level or settings.log_level
    setup_logging(log_level=log_level)

    # Microphone discovery
    if args.list_mics:
        import speech_recognition as sr
        print("\n--- Available Microphone Devices ---")
        try:
            mics = sr.Microphone.list_microphone_names()
            if not mics:
                print("No microphone devices detected.")
            else:
                for idx, name in enumerate(mics):
                    print(f"[{idx}] {name}")
        except Exception as e:
            print(f"Error querying microphone devices: {e}")
        sys.exit(0)

    # CLI Voice Mode
    if args.voice:
        logger.info("Initializing Aura in local microphone CLI mode...")
        app = build_app(settings=settings, demo_mode=False)
        app.run_loop()
        return

    # CLI Demo/Text Mode
    if args.demo_mode:
        logger.info("Initializing Aura in interactive text CLI mode...")
        app = build_app(settings=settings, demo_mode=True)
        app.run_loop()
        return

    # Web Mode (Default)
    host = args.host or settings.web.host
    port = args.port or settings.web.port

    logger.info(f"Starting Aura Web Voice Assistant server at http://{host}:{port}")
    web_app = create_app(settings=settings)
    uvicorn.run(web_app, host=host, port=port, log_level=log_level.lower())


if __name__ == "__main__":
    main()
