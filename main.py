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
        "--warden",
        choices=["with_warden", "without_warden", "both"],
        default="with_warden",
        help="Run with warden (default), without warden, or both conditions",
    )
    parser.add_argument(
        "--requester-type",
        dest="requester_type",
        choices=["adversary", "benign_agent", "both"],
        default="adversary",
        help="Requester type to run (default: adversary). Use 'both' to run both types.",
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
        default=["mistralai/mistral-small-3.1-24b-instruct:free"],
        help="One or more models for the target agent (space-separated, comma-separated, or JSON list)",
    )
    parser.add_argument(
        "--warden-model",
        nargs="+",
        default=["arcee-ai/trinity-large-preview:free"],
        help="One or more models for the warden agent (space-separated, comma-separated, or JSON list)",
    )
    parser.add_argument(
        "--dummy",
        action="store_true",
        help="Run with placeholder responses (no model calls)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help=(
            "Print full model context for each query "
            "(system prompt, history, and messages)"
        ),
    )
    parser.add_argument(
        "--experiment-rounds",
        type=int,
        default=1,
        help="Number of experiment rounds to run per condition (default: 1)",
    )
    parser.add_argument(
        "--tag",
        type=str,
        default=None,
        help="Optional tag to attach to logs for filtering metrics",
    )

    # Chain-of-thought arguments
    cot_group = parser.add_argument_group("chain-of-thought options")
    cot_group.add_argument(
        "--no-adversary-cot",
        action="store_true",
        help="Disable chain-of-thought reasoning for the adversary",
    )
    cot_group.add_argument(
        "--no-target-cot",
        action="store_true",
        help="Disable chain-of-thought reasoning for the target",
    )
    cot_group.add_argument(
        "--no-warden-cot",
        action="store_true",
        help="Disable chain-of-thought reasoning for the warden",
    )

    # Adversary behavior
    parser.add_argument(
        "--adversary-generates-opening",
        action="store_true",
        help="Let the adversary generate its own opening message instead of using a fixed one",
    )
    parser.add_argument(
        "--benign-agent-generates-opening",
        action="store_true",
        help="Let the benign agent generate its own opening message instead of using a fixed one",
    )
    parser.add_argument(
        "--adversary-data-access",
        action="store_true",
        help="Give the adversary a static behavioral dossier about the target (requires a profile)",
    )
    parser.add_argument(
        "--dossier-variant",
        type=int,
        choices=[1, 2, 3],
        default=None,
        help="Dossier variant to use (1, 2, or 3). Omit for random selection.",
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

    profile_to_warden = args.profile_to_warden

    # CoT settings
    adversary_cot = not args.no_adversary_cot
    target_cot = not args.no_target_cot
    warden_cot = not args.no_warden_cot

    # Calculate total experiments
    requester_types = (
        ["adversary", "benign_agent"]
        if args.requester_type == "both"
        else [args.requester_type]
    )
    conditions = 2 if args.warden == "both" else 1
    total_experiments = (
        args.experiment_rounds
        * len(args.adversary_model)
        * len(args.target_model)
        * len(args.warden_model)
        * conditions
        * len(requester_types)
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
                    for requester_type in requester_types:
                        if args.warden == "both":
                            print("=== Running WITHOUT warden ===\n")
                            scenario = SCENARIOS[args.scenario]()
                            run_experiment(
                                scenario=scenario,
                                num_turns=args.turns,
                                use_warden=False,
                                requester_type=requester_type,
                                adversary_model=adversary_model,
                                target_model=target_model,
                                warden_model=warden_model,
                                tag=args.tag,
                                profile=profile,
                                profile_to_warden=False,
                                dummy=args.dummy,
                                adversary_cot=adversary_cot,
                                target_cot=target_cot,
                                warden_cot=warden_cot,
                                adversary_generates_opening=args.adversary_generates_opening,
                                benign_agent_generates_opening=args.benign_agent_generates_opening,
                                adversary_data_access=args.adversary_data_access,
                                dossier_variant=args.dossier_variant,
                                debug=args.debug,
                            )
                            print("\n\n=== Running WITH warden ===\n")
                            scenario = SCENARIOS[args.scenario]()
                            run_experiment(
                                scenario=scenario,
                                num_turns=args.turns,
                                use_warden=True,
                                requester_type=requester_type,
                                adversary_model=adversary_model,
                                target_model=target_model,
                                warden_model=warden_model,
                                tag=args.tag,
                                profile=profile,
                                profile_to_warden=profile_to_warden,
                                dummy=args.dummy,
                                adversary_cot=adversary_cot,
                                target_cot=target_cot,
                                warden_cot=warden_cot,
                                adversary_generates_opening=args.adversary_generates_opening,
                                benign_agent_generates_opening=args.benign_agent_generates_opening,
                                adversary_data_access=args.adversary_data_access,
                                dossier_variant=args.dossier_variant,
                                debug=args.debug,
                            )
                        else:
                            scenario = SCENARIOS[args.scenario]()
                            run_experiment(
                                scenario=scenario,
                                num_turns=args.turns,
                                use_warden=args.warden == "with_warden",
                                requester_type=requester_type,
                                adversary_model=adversary_model,
                                target_model=target_model,
                                warden_model=warden_model,
                                tag=args.tag,
                                profile=profile,
                                profile_to_warden=profile_to_warden,
                                dummy=args.dummy,
                                adversary_cot=adversary_cot,
                                target_cot=target_cot,
                                warden_cot=warden_cot,
                                adversary_generates_opening=args.adversary_generates_opening,
                                benign_agent_generates_opening=args.benign_agent_generates_opening,
                                adversary_data_access=args.adversary_data_access,
                                dossier_variant=args.dossier_variant,
                                debug=args.debug,
                            )


if __name__ == "__main__":
    main()
