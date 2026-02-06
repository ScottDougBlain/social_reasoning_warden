"""ERA Social Warden — run experiments from the command line."""

import argparse
import json

from src.profiles import get_random_profile, list_profiles, load_profile
from src.runner import run_experiment
from src.scenarios.ai_in_box import AIInBoxScenario, AIInBoxPasswordScenario

SCENARIOS = {
    "ai_in_box": AIInBoxScenario,
    "ai_in_box_password": AIInBoxPasswordScenario,
}


def _parse_model_list(values):
    """Parse model arguments that can be space-separated, comma-separated, or JSON list."""
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
        default="ai_in_box_password",
        help="Scenario to run (default: ai_in_box_password)",
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
        "--requester-type",
        dest="requester_type",
        choices=["adversary", "benign_agent"],
        default="adversary",
        help="Requester type to run (default: adversary)",
    )
    parser.add_argument(
        "--adversary-model",
        nargs="+",
        default=["arcee-ai/trinity-large-preview:free"],
        help=(
            "One or more models for the requester agent (space-separated, "
            "comma-separated, or JSON list)"
        ),
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
        "--experiment-rounds",
        type=int,
        default=1,
        help="Number of experiment rounds to run per condition (default: 1)",
    )

    # Profile arguments
    profile_group = parser.add_argument_group("profiling options")
    profile_group.add_argument(
        "--profile",
        type=str,
        metavar="NAME",
        help="Use a specific profile by name (see --list-profiles)",
    )
    profile_group.add_argument(
        "--random-profile",
        action="store_true",
        help="Use a randomly selected profile",
    )
    profile_group.add_argument(
        "--no-profile-to-adversary",
        action="store_true",
        help="Don't give the adversary the target's profile dossier (ignored for benign_agent)",
    )
    profile_group.add_argument(
        "--profile-to-warden",
        action="store_true",
        help="Give the warden intel about the target's vulnerabilities",
    )
    profile_group.add_argument(
        "--list-profiles",
        action="store_true",
        help="List available profiles and exit",
    )

    args = parser.parse_args()

    # Handle --list-profiles
    if args.list_profiles:
        profiles = list_profiles()
        if profiles:
            print("Available profiles:")
            for name in sorted(profiles):
                print(f"  - {name}")
        else:
            print("No profiles found in prompts/profiles/")
        return

    # Parse model lists
    args.adversary_model = _parse_model_list(args.adversary_model)
    args.target_model = _parse_model_list(args.target_model)
    args.warden_model = _parse_model_list(args.warden_model)

    # Load profile if specified
    profile = None
    if args.profile:
        profile = load_profile(args.profile)
    elif args.random_profile:
        profile = get_random_profile()

    profile_to_adversary = not args.no_profile_to_adversary
    profile_to_warden = args.profile_to_warden

    # Calculate total experiments
    conditions = 2 if args.both else 1
    total_experiments = (
        args.experiment_rounds
        * len(args.adversary_model)
        * len(args.target_model)
        * len(args.warden_model)
        * conditions
    )

    # Show plan and confirm
    print(
        f"Planned experiments: {total_experiments} "
        f"({args.turns} conversation turns each)"
    )
    if profile:
        print(f"Profile: {profile.name}")
    while True:
        proceed = input("Continue? [y/n]: ").strip().lower()
        if proceed in {"y", "yes"}:
            break
        if proceed in {"n", "no"}:
            print("Aborted.")
            return

    # Run experiments
    for round_idx in range(1, args.experiment_rounds + 1):
        if args.experiment_rounds > 1:
            print(f"\n=== Round {round_idx}/{args.experiment_rounds} ===\n")

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
                            requester_type=args.requester_type,
                            adversary_model=adversary_model,
                            target_model=target_model,
                            warden_model=warden_model,
                            profile=profile,
                            profile_to_adversary=profile_to_adversary,
                            profile_to_warden=False,
                            dummy=args.dummy,
                        )
                        print("\n\n=== Running WITH warden ===\n")
                        scenario = SCENARIOS[args.scenario]()
                        run_experiment(
                            scenario=scenario,
                            num_turns=args.turns,
                            use_warden=True,
                            requester_type=args.requester_type,
                            adversary_model=adversary_model,
                            target_model=target_model,
                            warden_model=warden_model,
                            profile=profile,
                            profile_to_adversary=profile_to_adversary,
                            profile_to_warden=profile_to_warden,
                            dummy=args.dummy,
                        )
                    else:
                        scenario = SCENARIOS[args.scenario]()
                        run_experiment(
                            scenario=scenario,
                            num_turns=args.turns,
                            use_warden=not args.no_warden,
                            requester_type=args.requester_type,
                            adversary_model=adversary_model,
                            target_model=target_model,
                            warden_model=warden_model,
                            profile=profile,
                            profile_to_adversary=profile_to_adversary,
                            profile_to_warden=profile_to_warden,
                            dummy=args.dummy,
                        )


if __name__ == "__main__":
    main()
