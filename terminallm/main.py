import argparse
import logging
import sys
from typing import NoReturn

from dotenv import load_dotenv

from .app.factory import build_app
from .utility import get_version, llm_config_path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(lineno)d - %(funcName)s - %(pathname)s",
    handlers=[logging.StreamHandler()],
)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("urllib3").propagate = False
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("LiteLLM").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("comtypes").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


def main() -> NoReturn:
    parser = argparse.ArgumentParser(description="TerminalLM: A CLI for OpenAI' and other LLM")

    parser.add_argument(
        "-v",
        "--version",
        action="version",
        help="Show the version of the app",
        version=f"%(prog)s {get_version()}",
    )
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="Enable debug mode to print more information.",
    )
    parser.add_argument("--mode", choices=["tt", "ms", "mt", "ts"], default="tt", help="Mode of operation.")

    parser.add_argument("--llm", default="gpt-4o", help="name of the LLM to use.")
    args = parser.parse_args()
    env_var_path = llm_config_path()
    if env_var_path.is_file():
        load_dotenv(dotenv_path=env_var_path)
    else:
        logger.info("No .llmconfig file found in home directory, Expecting Environment Variables are set")
    if args.debug:
        # litellm.set_verbose = True
        logging.getLogger("LiteLLM").setLevel(logging.INFO)

    try:
        app = build_app(mode=args.mode, client_name=args.llm)
        app.run()
    except Exception as err:
        logging.exception(err)
        sys.exit(1)


if __name__ == "__main__":
    main()
