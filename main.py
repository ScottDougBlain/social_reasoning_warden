"""ERA Social Warden — run experiments from the command line."""

import argparse
import json

from src.runner import run_experiment
from src.scenarios.ai_in_box import AIInBoxScenario

SCENARIOS = {
    "ai_in_box": AIInBoxScenario,
}

def _parse_model_list(values):
    if len(values) == 1:
        raw = values[0].strip()
        if raw.startswith("["):
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                parsed = None
            if isinstance(parsed, list) and all(isinstance(item, str) for item in parsed):
                return parsed
        if "," in raw:
            return [item.strip() for item in raw.split(",") if item.strip()]
    return values


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
        default=4,
        help="Number of conversation turns (default: 4)",
    )
    parser.add_argument(
        "--no-warden",
        action="store_true",
        help="Run without the warden agent",
    )
    parser.add_argument(
        "--adversary-model",
        nargs="+",
        default=["arcee-ai/trinity-large-preview:free"],
        help="One or more models for the adversary agent (space-separated, comma-separated, or JSON list)",
    )
    parser.add_argument(
        "--target-model",
        nargs="+",
        default=["arcee-ai/trinity-mini:free"],
        help="One or more models for the target agent (space-separated, comma-separated, or JSON list)",
    )
    parser.add_argument(
        "--warden-model",
        nargs="+",
        default=["arcee-ai/trinity-large-preview:free"],
        help="One or more models for the warden agent (space-separated, comma-separated, or JSON list)",
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
    parser.add_argument(
        "--experiment_rounds",
        type=int,
        default=1,
        help="Number of experiment rounds to run per condition (default: 1)",
    )

    args = parser.parse_args()

    args.adversary_model = _parse_model_list(args.adversary_model)
    args.target_model = _parse_model_list(args.target_model)
    args.warden_model = _parse_model_list(args.warden_model)

    conditions = 2 if args.both else 1
    total_experiments = (
        args.experiment_rounds
        * len(args.adversary_model)
        * len(args.target_model)
        * len(args.warden_model)
        * conditions
    )
    print(
        "Planned experiments: "
        f"{total_experiments} "
        f"({args.turns} conversation turns each)"
    )
    while True:
        proceed = input("Continue? [y/n]: ").strip().lower()
        if proceed in {"y", "yes"}:
            break
        if proceed in {"n", "no"}:
            print("Aborted.")
            return

    for round_idx in range(1, args.experiment_rounds + 1):
        if args.experiment_rounds > 1:
            print(f"=== Round {round_idx}/{args.experiment_rounds} ===\n")

        for adversary_model in args.adversary_model:
            for target_model in args.target_model:
                for warden_model in args.warden_model:
                    if args.both:
                        print("=== Running WITHOUT warden ===\n")
                        scenario = SCENARIOS[args.scenario]()
                        run_experiment(
                            scenario=scenario,
                            num_turns=args.turns,
                            use_warden=False,
                            adversary_model=adversary_model,
                            target_model=target_model,
                            warden_model=warden_model,
                            dummy=args.dummy,
                        )
                        print("\n\n=== Running WITH warden ===\n")
                        scenario = SCENARIOS[args.scenario]()
                        run_experiment(
                            scenario=scenario,
                            num_turns=args.turns,
                            use_warden=True,
                            adversary_model=adversary_model,
                            target_model=target_model,
                            warden_model=warden_model,
                            dummy=args.dummy,
                        )
                    else:
                        scenario = SCENARIOS[args.scenario]()
                        run_experiment(
                            scenario=scenario,
                            num_turns=args.turns,
                            use_warden=not args.no_warden,
                            adversary_model=adversary_model,
                            target_model=target_model,
                            warden_model=warden_model,
                            dummy=args.dummy,
                        )


if __name__ == "__main__":
    main()
