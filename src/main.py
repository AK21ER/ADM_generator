import argparse
import logging
from pathlib import Path
from .config import get_settings
from .models import ClientProfile
from .utils import load_json
from .generator import generate_report

def parse_args():
    p = argparse.ArgumentParser(description="Generate ADM HTML report")
    p.add_argument("--client", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--force", action="store_true")
    p.add_argument("--model", default=None)
    p.add_argument("--debug", action="store_true")
    p.add_argument("--offline", action="store_true", help="Disable OpenAI calls and use offline narrative fallback")
    return p.parse_args()

def main():
    args = parse_args()
    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s")
    project_root = Path(__file__).resolve().parents[1]
    settings = get_settings(project_root)
    client = ClientProfile.model_validate(load_json(project_root / args.client))
    api_key = "" if args.offline else settings.openai_api_key
    final = generate_report(
        project_root,
        client,
        project_root / args.output,
        api_key,
        args.model or settings.model,
        discount_rate=settings.discount_rate,
        force=args.force,
    )
    logging.getLogger(__name__).info("ADM report generated: %s", final)

if __name__ == "__main__":
    main()
