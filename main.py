"""ERA Social Warden — run experiments from the command line."""

import argparse
import json
import random
import textwrap

from src.profiles import list_profiles, load_profile
from src.runner import run_experiment
from src.scenarios.file_access import FileAccessScenario, FileAccessPasswordScenario
from src.scenarios.sales import UpsellingScenario

SCENARIOS = {
    "file_access": FileAccessScenario,
    "file_access_password": FileAccessPasswordScenario,
    "upselling": UpsellingScenario,
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
    parser = argparse.ArgumentParser(description="ERA Social Warden Experiment Runner")
    parser.add_argument(
        "--scenario",
        nargs="+",
        choices=list(SCENARIOS.keys()),
        default=["file_access_password"],
        help="Scenario(s) to run (default: file_access_password). Space-separated list.",
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
        default=["google/gemini-3-flash-preview"],
        help=(
            "One or more models for the requester agent (space-separated, "
            "comma-separated, or JSON list)"
        ),
    )
    parser.add_argument(
        "--target-model",
        nargs="+",
        default=["google/gemini-2.5-flash-lite"],
        help="One or more models for the target agent (space-separated, comma-separated, or JSON list)",
    )
    parser.add_argument(
        "--warden-model",
        nargs="+",
        default=["google/gemini-3-flash-preview"],
        help="One or more models for the warden agent (space-separated, comma-separated, or JSON list)",
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
    parser.add_argument(
        "--cot",
        choices=["none", "native", "scratchpad"],
        default="native",
        help=(
            "CoT mode for all agents: "
            "none (no reasoning), "
            "native (request reasoning via API only, default), "
            "scratchpad (prompt-elicited reasoning only, native traces suppressed)"
        ),
    )

    # Adversary behavior
    parser.add_argument(
        "--adversary-generates-opening",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Let the adversary generate its own opening message instead of using a fixed one",
    )
    parser.add_argument(
        "--benign-agent-generates-opening",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Let the benign agent generate its own opening message instead of using a fixed one",
    )
    parser.add_argument(
        "--adversary-data-access",
        choices=["no_access", "access", "both"],
        default="no_access",
        help=(
            "Adversary behavioral dossier access: no_access, access, or both. "
            "Requires a profile when access is enabled."
        ),
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
        help="Use a specific profile by name (see --list-profiles); if not specified, no profile is used",
    )
    profile_group.add_argument(
        "--random-profile",
        action="store_true",
        help="Use a randomly selected profile",
    )
    profile_group.add_argument(
        "--profile-seed",
        type=int,
        default=None,
        help=(
            "Seed for random profile selection when using --random-profile "
            "(deterministic per-round schedule)."
        ),
    )
    profile_group.add_argument(
        "--warden-profile-access",
        choices=["no_access", "access", "both"],
        default="no_access",
        help=(
            "Warden access to target vulnerability profile: no_access, access, or both. "
            "Requires a profile when access is enabled."
        ),
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

    profile_requested = bool(args.profile or args.random_profile)
    if args.adversary_data_access in {"access", "both"} and not profile_requested:
        parser.error(
            "--adversary-data-access access|both requires --profile or --random-profile"
        )
    if args.warden_profile_access in {"access", "both"} and not profile_requested:
        parser.error(
            "--warden-profile-access access|both requires --profile or --random-profile"
        )

    # Build a deterministic profile schedule per round (if enabled)
    profile_schedule: list | None = None
    if args.profile:
        profile = load_profile(args.profile)
        profile_schedule = [profile] * args.experiment_rounds
    elif args.random_profile:
        available_profiles = sorted(list_profiles())
        if not available_profiles:
            parser.error("No profiles available in prompts/profiles/")
        rng = random.Random(args.profile_seed)
        profile_schedule = [
            load_profile(rng.choice(available_profiles))
            for _ in range(args.experiment_rounds)
        ]

    # CoT setting (single mode for all agents)
    cot_mode = args.cot

    # Calculate total experiments
    adversary_data_access_values = (
        [False, True]
        if args.adversary_data_access == "both"
        else [args.adversary_data_access == "access"]
    )
    warden_profile_access_values = (
        [False, True]
        if args.warden_profile_access == "both"
        else [args.warden_profile_access == "access"]
    )
    requester_types = (
        ["adversary", "benign_agent"]
        if args.requester_type == "both"
        else [args.requester_type]
    )
    warden_modes = (
        [False, True]
        if args.warden == "both"
        else [args.warden == "with_warden"]
    )

    def effective_adversary_data_access_values(requester_type: str) -> list[bool]:
        if requester_type != "adversary":
            return [False]
        return adversary_data_access_values

    def effective_warden_profile_access_values(use_warden: bool) -> list[bool]:
        if not use_warden:
            return [False]
        return warden_profile_access_values

    def effective_warden_models(use_warden: bool) -> list[str]:
        if not use_warden:
            return [args.warden_model[0]]
        return args.warden_model

    branch_multiplier = 0
    for requester_type in requester_types:
        access_values = effective_adversary_data_access_values(requester_type)
        for use_warden in warden_modes:
            warden_access_values = effective_warden_profile_access_values(use_warden)
            warden_models = effective_warden_models(use_warden)
            branch_multiplier += (
                len(access_values)
                * len(warden_access_values)
                * len(warden_models)
            )

    total_experiments = (
        args.experiment_rounds
        * len(args.scenario)
        * len(args.adversary_model)
        * len(args.target_model)
        * branch_multiplier
    )

    # Show plan and confirm
    def _format_plan_line(label: str, value: str, width: int = 88) -> str:
        prefix = f"{label:<18}: "
        return textwrap.fill(
            value,
            width=width,
            initial_indent=prefix,
            subsequent_indent=" " * len(prefix),
        )

    print("\n=== Experiment Plan ===")
    print(
        _format_plan_line(
            "Planned runs",
            f"{total_experiments} ({args.turns} conversation turns each)",
        )
    )
    if profile_schedule:
        preview_profile = profile_schedule[0] if profile_schedule else None
        if preview_profile and args.random_profile and args.experiment_rounds > 1:
            seed_note = (
                f" (seed={args.profile_seed})"
                if args.profile_seed is not None
                else ""
            )
            print(_format_plan_line("Profiles", f"random per round{seed_note}"))
        elif preview_profile:
            print(_format_plan_line("Profile", preview_profile.name))
    if len(args.scenario) > 1:
        print(_format_plan_line("Scenarios", ", ".join(args.scenario)))
    print(_format_plan_line("Requester", ", ".join(args.adversary_model)))
    print(_format_plan_line("Target", ", ".join(args.target_model)))
    print(_format_plan_line("Warden", ", ".join(args.warden_model)))
    print()
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
        profile = (
            profile_schedule[round_idx - 1]
            if profile_schedule
            else None
        )
        if args.experiment_rounds > 1 and profile:
            print(f"Profile: {profile.name}")

        for adversary_model in args.adversary_model:
            for target_model in args.target_model:
                for requester_type in requester_types:
                    for use_warden in warden_modes:
                        effective_access_values = (
                            effective_adversary_data_access_values(requester_type)
                        )
                        effective_warden_access_values = (
                            effective_warden_profile_access_values(use_warden)
                        )
                        effective_models = effective_warden_models(use_warden)
                        for warden_model in effective_models:
                            for adversary_data_access in effective_access_values:
                                for warden_profile_access in effective_warden_access_values:
                                    if args.warden == "both":
                                        if use_warden:
                                            print("=== Running WITH warden ===\n")
                                        else:
                                            print("=== Running WITHOUT warden ===\n")
                                    for scenario_name in args.scenario:
                                        if len(args.scenario) > 1:
                                            print(f"--- Scenario: {scenario_name} ---\n")
                                        scenario = SCENARIOS[scenario_name]()
                                        run_experiment(
                                            scenario=scenario,
                                            num_turns=args.turns,
                                            use_warden=use_warden,
                                            requester_type=requester_type,
                                            adversary_model=adversary_model,
                                            target_model=target_model,
                                            warden_model=warden_model,
                                            tag=args.tag,
                                            profile=profile,
                                            profile_to_warden=warden_profile_access,
                                            cot_mode=cot_mode,
                                            adversary_generates_opening=args.adversary_generates_opening,
                                            benign_agent_generates_opening=args.benign_agent_generates_opening,
                                            adversary_data_access=adversary_data_access,
                                            dossier_variant=args.dossier_variant,
                                            debug=args.debug,
                                        )


if __name__ == "__main__":
    main()
