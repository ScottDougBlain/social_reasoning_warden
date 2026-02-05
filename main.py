"""ERA Social Warden — run experiments from the command line."""

import argparse
import sys

from src.runner import run_experiment
from src.scenarios.ai_in_box import AIInBoxScenario

SCENARIOS = {
    "ai_in_box": AIInBoxScenario,
}


def main():
    parser = argparse.ArgumentParser(description="ERA Social Warden experiment runner")
    parser.add_argument(
        "--scenario",
        choices=list(SCENARIOS.keys()),
        default="ai_in_box",
        help="Scenario to run (default: ai_in_box)",
    )
    parser.add_argument(
        "--turns",
        type=int,
        default=6,
        help="Number of conversation turns (default: 6)",
    )
    parser.add_argument(
        "--no-warden",
        action="store_true",
        help="Run without the warden agent",
    )
    parser.add_argument(
        "--adversary-model",
        default="arcee-ai/trinity-large-preview:free",
        help="Model for the adversary agent",
    )
    parser.add_argument(
        "--target-model",
        default="arcee-ai/trinity-large-preview:free",
        help="Model for the target agent",
    )
    parser.add_argument(
        "--warden-model",
        default="arcee-ai/trinity-large-preview:free",
        help="Model for the warden agent",
    )
    parser.add_argument(
        "--both",
        action="store_true",
        help="Run both conditions (with and without warden)",
    )
    parser.add_argument(
        "--dummy",
        action="store_true",
        help="Run with placeholder responses (no model calls)",
    )

    args = parser.parse_args()
    scenario = SCENARIOS[args.scenario]()

    if args.both:
        print("=== Running WITHOUT warden ===\n")
        run_experiment(
            scenario=scenario,
            num_turns=args.turns,
            use_warden=False,
            adversary_model=args.adversary_model,
            target_model=args.target_model,
            warden_model=args.warden_model,
            dummy=args.dummy,
        )
        print("\n\n=== Running WITH warden ===\n")
        run_experiment(
            scenario=scenario,
            num_turns=args.turns,
            use_warden=True,
            adversary_model=args.adversary_model,
            target_model=args.target_model,
            warden_model=args.warden_model,
            dummy=args.dummy,
        )
    else:
        run_experiment(
            scenario=scenario,
            num_turns=args.turns,
            use_warden=not args.no_warden,
            adversary_model=args.adversary_model,
            target_model=args.target_model,
            warden_model=args.warden_model,
            dummy=args.dummy,
        )


if __name__ == "__main__":
    main()
