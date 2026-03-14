"""ERA Social Warden — run experiments from the command line."""

import argparse
import json
import random
import textwrap
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from src.client import supports_native_reasoning
from src.profiles import assign_profiles_to_seats, generate_profile
from src.runner import run_experiment, run_multi_target_experiment
from src.scenarios.base import MultiTargetScenario
from src.scenarios.experimental import (
    AIContainmentBoardScenario,
    AIMoratoriumScenario,
    AIOversightScenario,
    AIRaceScenario,
    AITreatyScenario,
    AutonomousWeaponsScenario,
    BiasInDeploymentScenario,
    BoardAcquisitionScenario,
    CompartmentalizedReviewScenario,
    ConcentrationOfPowerScenario,
    DeceptiveAlignmentScenario,
    DemocraticAIScenario,
    DisinformationScenario,
    DualUseBiosecurityScenario,
    EmergencyShutdownScenario,
    KillSwitchScenario,
    MedicalAIScenario,
    OpenWeightsScenario,
    RegulatoryCaptureScenario,
    SafetyBudgetScenario,
    SafetyCoalitionScenario,
    SurveillanceScenario,
)
from src.scenarios.test import (
    AIContainmentScenario,
    AIOverrideScenario,
    AutomationDecisionScenario,
    CodingAgentScenario,
    FileAccessPasswordScenario,
    FileAccessScenario,
    HiringScenario,
    ModelReleaseScenario,
    ProductLaunchScenario,
    UpsellingScenario,
    VoteScenario,
)

TRAIN_SCENARIOS = {}
TEST_SCENARIOS = {
    "ai_containment": AIContainmentScenario,
    "ai_override": AIOverrideScenario,
    "automation_decision": AutomationDecisionScenario,
    "coding_agent": CodingAgentScenario,
    "file_access": FileAccessScenario,
    "file_access_password": FileAccessPasswordScenario,
    "hiring": HiringScenario,
    "model_release": ModelReleaseScenario,
    "product_launch": ProductLaunchScenario,
    "upselling": UpsellingScenario,
    "vote": VoteScenario,
}
EXPERIMENTAL_SCENARIOS = {
    "ai_containment_board_mas": AIContainmentBoardScenario,
    "ai_moratorium_mas": AIMoratoriumScenario,
    "ai_race_mas": AIRaceScenario,
    "ai_treaty_mas": AITreatyScenario,
    "ai_oversight_mas": AIOversightScenario,
    "autonomous_weapons_mas": AutonomousWeaponsScenario,
    "bias_in_deployment_mas": BiasInDeploymentScenario,
    "board_acquisition_mas": BoardAcquisitionScenario,
    "compartmentalized_review_mas": CompartmentalizedReviewScenario,
    "concentration_of_power_mas": ConcentrationOfPowerScenario,
    "deceptive_alignment_mas": DeceptiveAlignmentScenario,
    "democratic_ai_mas": DemocraticAIScenario,
    "disinformation_mas": DisinformationScenario,
    "dual_use_biosecurity_mas": DualUseBiosecurityScenario,
    "emergency_shutdown_mas": EmergencyShutdownScenario,
    "kill_switch_mas": KillSwitchScenario,
    "medical_ai_mas": MedicalAIScenario,
    "open_weights_mas": OpenWeightsScenario,
    "regulatory_capture_mas": RegulatoryCaptureScenario,
    "safety_budget_mas": SafetyBudgetScenario,
    "safety_coalition_mas": SafetyCoalitionScenario,
    "surveillance_mas": SurveillanceScenario,
}
SCENARIOS = {**TRAIN_SCENARIOS, **TEST_SCENARIOS, **EXPERIMENTAL_SCENARIOS}
SCENARIO_GROUP_SELECTORS = ("all_train", "all_test", "all_experimental")
WARDEN_PROMPTS_DIR = Path(__file__).resolve().parent / "prompts" / "warden"
DEFAULT_WARDEN_SYSTEM_PROMPT = "warden_system_1.yaml"
ADVERSARY_PROMPTS_DIR = Path(__file__).resolve().parent / "prompts" / "adversary"
DEFAULT_ADVERSARY_SYSTEM_PROMPT = "adversary_system_1.yaml"
ANSI_RED = "\033[31m"
ANSI_RESET = "\033[0m"


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


def _expand_scenario_selection(selected: list[str]) -> list[str]:
    expanded: list[str] = []
    for scenario_name in selected:
        if scenario_name == "all_train":
            expanded.extend(sorted(TRAIN_SCENARIOS.keys()))
            continue
        if scenario_name == "all_test":
            expanded.extend(sorted(TEST_SCENARIOS.keys()))
            continue
        if scenario_name == "all_experimental":
            expanded.extend(sorted(EXPERIMENTAL_SCENARIOS.keys()))
            continue
        expanded.append(scenario_name)

    # Deduplicate while preserving order.
    deduped: list[str] = []
    seen: set[str] = set()
    for scenario_name in expanded:
        if scenario_name in seen:
            continue
        seen.add(scenario_name)
        deduped.append(scenario_name)
    return deduped


def _resolve_warden_prompt_file(prompt_file: str) -> str:
    """Validate and normalize a warden prompt path under prompts/warden."""
    prompts_root = WARDEN_PROMPTS_DIR.resolve()
    candidate = (prompts_root / prompt_file).resolve()

    try:
        relative = candidate.relative_to(prompts_root)
    except ValueError as exc:
        raise ValueError(
            "Warden prompt must be a file inside prompts/warden/"
        ) from exc

    if not candidate.is_file():
        raise FileNotFoundError(f"Warden prompt not found: prompts/warden/{relative.as_posix()}")

    return relative.as_posix()


def _resolve_adversary_prompt_file(prompt_file: str) -> str:
    """Validate and normalize an adversary prompt path under prompts/adversary."""
    prompts_root = ADVERSARY_PROMPTS_DIR.resolve()
    candidate = (prompts_root / prompt_file).resolve()

    try:
        relative = candidate.relative_to(prompts_root)
    except ValueError as exc:
        raise ValueError(
            "Adversary prompt must be a file inside prompts/adversary/"
        ) from exc

    if not candidate.is_file():
        raise FileNotFoundError(f"Adversary prompt not found: prompts/adversary/{relative.as_posix()}")

    return relative.as_posix()


def _find_models_without_native_reasoning_exact_matches(args) -> dict[str, list[str]]:
    """Return configured models per role that are not exact-match covered."""
    role_models = {
        "Requester": args.requester_model,
        "Target": args.target_model,
        "Warden": args.warden_model,
    }
    return {
        role: [model for model in models if not supports_native_reasoning(model)]
        for role, models in role_models.items()
    }


def _print_red(text: str) -> None:
    print(f"{ANSI_RED}{text}{ANSI_RESET}")


def _toggle_values(value: str) -> list[bool]:
    if value == "both":
        return [False, True]
    return [value == "yes"]


def _profiles_requested(args) -> bool:
    return any(
        value in {"yes", "both"}
        for value in (
            args.target_profiles,
            args.adversary_profile_access,
            args.warden_profile_access,
        )
    )


def _build_round_profile_seeds(num_rounds: int, seed: int) -> list[int]:
    rng = random.Random(seed)
    return [rng.randrange(0, 2**63) for _ in range(num_rounds)]


def main():
    parser = argparse.ArgumentParser(
        description="ERA Social Warden Experiment Runner",
        allow_abbrev=False,
    )
    parser.add_argument(
        "--scenario",
        nargs="+",
        choices=[*SCENARIOS.keys(), *SCENARIO_GROUP_SELECTORS],
        default=["file_access_password"],
        help=(
            "Scenario(s) to run (default: file_access_password). Space-separated list. "
            "Use all_train, all_test, or all_experimental to run full scenario sets."
        ),
    )
    parser.add_argument(
        "--turns",
        type=int,
        default=4,
        help="Number of conversation turns (default: 4)",
    )
    parser.add_argument(
        "--warden",
        choices=["with_warden", "without_warden", "both", "risk_level_only"],
        default="with_warden",
        help=(
            "Run with warden (default), without warden, both conditions, "
            "or risk_level_only (target only sees RISK: MEDIUM/HIGH, no explanation)"
        ),
    )
    parser.add_argument(
        "--requester-type",
        dest="requester_type",
        choices=["adversary", "benign_agent", "both"],
        default="adversary",
        help="Requester type to run (default: adversary). Use 'both' to run both types.",
    )
    parser.add_argument(
        "--requester-model",
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
        "--warden-system-prompt",
        type=str,
        default=DEFAULT_WARDEN_SYSTEM_PROMPT,
        help=(
            "Warden system prompt file under prompts/warden/ "
            f"(default: {DEFAULT_WARDEN_SYSTEM_PROMPT})"
        ),
    )
    parser.add_argument(
        "--adversary-system-prompt",
        type=str,
        default=DEFAULT_ADVERSARY_SYSTEM_PROMPT,
        help=(
            "Adversary system prompt file under prompts/adversary/ "
            f"(default: {DEFAULT_ADVERSARY_SYSTEM_PROMPT})"
        ),
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
        "--max-workers",
        type=int,
        default=1,
        help=(
            "Maximum number of concurrent experiments (default: 1). "
            "If >1, output is quiet and only progress updates are printed."
        ),
    )
    parser.add_argument(
        "--tag",
        type=str,
        default=None,
        help="Optional tag to attach to logs for filtering metrics",
    )
    parser.add_argument(
        "--decision-reprompt-attempts",
        type=int,
        default=1,
        help=(
            "Number of retries when final decision parsing fails due to format "
            "(default: 1)"
        ),
    )

    # Chain-of-thought arguments
    parser.add_argument(
        "--cot",
        choices=["none", "native", "scratchpad"],
        default="native",
        help=(
            "CoT mode for all agents: "
            "none (no scratchpad prompt; native reasoning traces still requested), "
            "native (request native reasoning traces via API only, default), "
            "scratchpad (prompt-elicited reasoning + native reasoning traces requested)"
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
        "--warden-awareness",
        "--warden_awareness",
        dest="warden_awareness",
        choices=["off", "on", "both"],
        default="off",
        help=(
            "Whether the adversary is informed their messages may be monitored "
            "by a persuasion monitor (warden). Use 'both' to run aware and "
            "unaware conditions."
        ),
    )
    parser.add_argument(
        "--target-skeptical",
        choices=["off", "on", "both"],
        default="off",
        help=(
            "Give the target baked-in skepticism instructions (ablation: "
            "prompt-based defense instead of warden agent). Use 'both' to "
            "run skeptical and non-skeptical conditions."
        ),
    )

    ############# PERSONALIZATION / PROFILING ARGUMENTS #############

    profile_group = parser.add_argument_group("profiling options")
    profile_group.add_argument(
        "--target-profiles",
        choices=["yes", "no", "both"],
        default="no",
        help=(
            "Whether the target receives a generated five-factor profile: "
            "yes, no, or both."
        ),
    )
    profile_group.add_argument(
        "--adversary-profile-access",
        choices=["yes", "no", "both"],
        default="no",
        help=(
            "Whether the adversary receives the generated five-factor "
            "profile: yes, no, or both."
        ),
    )
    profile_group.add_argument(
        "--warden-profile-access",
        choices=["yes", "no", "both"],
        default="no",
        help=(
            "Whether the warden receives the generated five-factor profile: "
            "yes, no, or both."
        ),
    )
    profile_group.add_argument(
        "--profile-seed",
        type=int,
        default=42,
        help=(
            "Seed for generated profiles. The same per-round profile list is "
            "reused across all condition cells."
        ),
    )
    parser.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Skip confirmation prompt and run immediately",
    )

    args = parser.parse_args()

    args.scenario = _expand_scenario_selection(args.scenario)
    if not args.scenario:
        parser.error(
            "--scenario selection expanded to zero scenarios."
        )

    # Parse model lists
    args.requester_model = _parse_model_list(args.requester_model)
    args.target_model = _parse_model_list(args.target_model)
    args.warden_model = _parse_model_list(args.warden_model)
    try:
        args.warden_system_prompt = _resolve_warden_prompt_file(args.warden_system_prompt)
    except (FileNotFoundError, ValueError) as exc:
        parser.error(str(exc))
    try:
        args.adversary_system_prompt = _resolve_adversary_prompt_file(args.adversary_system_prompt)
    except (FileNotFoundError, ValueError) as exc:
        parser.error(str(exc))

    if args.decision_reprompt_attempts < 0:
        parser.error("--decision-reprompt-attempts must be >= 0")

    profiles_requested = _profiles_requested(args)
    round_profile_seeds: list[int] | None = None
    profile_schedule: list | None = None
    if profiles_requested:
        round_profile_seeds = _build_round_profile_seeds(
            args.experiment_rounds,
            args.profile_seed,
        )
        profile_schedule = [
            generate_profile(random.Random(seed))
            for seed in round_profile_seeds
        ]

    # CoT setting (single mode for all agents)
    cot_mode = args.cot

    # Calculate total experiments
    target_profile_values = _toggle_values(args.target_profiles)
    adversary_profile_access_values = _toggle_values(args.adversary_profile_access)
    warden_awareness_values = (
        [False, True]
        if args.warden_awareness == "both"
        else [args.warden_awareness == "on"]
    )
    warden_profile_access_values = _toggle_values(args.warden_profile_access)
    requester_types = (
        ["adversary", "benign_agent"]
        if args.requester_type == "both"
        else [args.requester_type]
    )
    warden_modes = (
        [False, True]
        if args.warden == "both"
        else [args.warden in {"with_warden", "risk_level_only"}]
    )
    target_skeptical_values = (
        [False, True]
        if args.target_skeptical == "both"
        else [args.target_skeptical == "on"]
    )

    def effective_target_profile_values() -> list[bool]:
        if not profiles_requested:
            return [False]
        return target_profile_values

    def effective_adversary_profile_access_values(requester_type: str) -> list[bool]:
        if requester_type != "adversary":
            return [False]
        if not profiles_requested:
            return [False]
        return adversary_profile_access_values

    def effective_warden_awareness_values(requester_type: str) -> list[bool]:
        if requester_type != "adversary":
            return [False]
        return warden_awareness_values

    def effective_warden_profile_access_values(use_warden: bool) -> list[bool]:
        if not use_warden:
            return [False]
        if not profiles_requested:
            return [False]
        return warden_profile_access_values

    def effective_warden_models(use_warden: bool) -> list[str]:
        if not use_warden:
            return [args.warden_model[0]]
        return args.warden_model

    def warden_message_mode_for_run(use_warden: bool) -> str:
        if not use_warden:
            return "full"
        if args.warden == "risk_level_only":
            return "risk_level_only"
        return "full"

    branch_multiplier = 0
    for requester_type in requester_types:
        target_values = effective_target_profile_values()
        adversary_values = effective_adversary_profile_access_values(requester_type)
        awareness_values = effective_warden_awareness_values(requester_type)
        for use_warden in warden_modes:
            warden_access_values = effective_warden_profile_access_values(use_warden)
            warden_models = effective_warden_models(use_warden)
            branch_multiplier += (
                len(target_values)
                * len(adversary_values)
                * len(awareness_values)
                * len(warden_access_values)
                * len(warden_models)
                * len(target_skeptical_values)
            )

    total_experiments = (
        args.experiment_rounds
        * len(args.scenario)
        * len(args.requester_model)
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
    print(_format_plan_line("Experiment rounds", str(args.experiment_rounds)))
    print(_format_plan_line("Parallel workers", str(args.max_workers)))
    if profile_schedule:
        preview_profile = profile_schedule[0] if profile_schedule else None
        seed_note = f"seed={args.profile_seed}"
        if args.experiment_rounds > 1:
            print(_format_plan_line("Profiles", f"generated per round ({seed_note})"))
        elif preview_profile:
            print(_format_plan_line("Profile", f"{preview_profile.name} ({seed_note})"))
    print(_format_plan_line("Target profiles", args.target_profiles))
    print(_format_plan_line("Adversary access", args.adversary_profile_access))
    print(_format_plan_line("Warden access", args.warden_profile_access))
    if len(args.scenario) > 1:
        scenario_count = len(args.scenario)
        print(
            _format_plan_line(
                "Scenarios",
                f"{scenario_count}: {', '.join(args.scenario)}",
            )
        )
    print(_format_plan_line("Requester", ", ".join(args.requester_model)))
    print(_format_plan_line("Target", ", ".join(args.target_model)))
    print(_format_plan_line("Warden", ", ".join(args.warden_model)))
    print(_format_plan_line("Warden mode", args.warden))
    print(_format_plan_line("Warden prompt", f"prompts/warden/{args.warden_system_prompt}"))
    if args.adversary_system_prompt != DEFAULT_ADVERSARY_SYSTEM_PROMPT:
        print(_format_plan_line("Adversary prompt", f"prompts/adversary/{args.adversary_system_prompt}"))
    print(_format_plan_line("Warden awareness", args.warden_awareness))
    print()

    uncovered_models = _find_models_without_native_reasoning_exact_matches(args)
    has_uncovered_models = any(uncovered_models.values())
    if has_uncovered_models:
        _print_red(
            "Warning: Some configured models are not covered by "
            "src/client.py NATIVE_REASONING_EXACT_MODELS."
        )
        for role, models in uncovered_models.items():
            if models:
                _print_red(f"  {role}: {', '.join(models)}")
        print()

    if not args.yes:
        if has_uncovered_models:
            while True:
                intended = input(
                    f"{ANSI_RED}These models will receive a request to use a scratchpad instead. "
                    "Is this intended? [y/n]: "
                    f"{ANSI_RESET}"
                ).strip().lower()
                if intended in {"y", "yes"}:
                    break
                if intended in {"n", "no"}:
                    print("Aborted.")
                    return
        while True:
            proceed = input("Continue? [y/n]: ").strip().lower()
            if proceed in {"y", "yes"}:
                break
            if proceed in {"n", "no"}:
                print("Aborted.")
                return

    # Run experiments
    quiet_runs = args.max_workers > 1
    run_index = 0

    if args.max_workers > 1:
        print(f"\nCompleted 0/{total_experiments} runs")
        futures = []
        future_contexts = {}
        with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
            for round_idx in range(1, args.experiment_rounds + 1):
                profile = (
                    profile_schedule[round_idx - 1]
                    if profile_schedule
                    else None
                )
                round_profile_seed = (
                    round_profile_seeds[round_idx - 1]
                    if round_profile_seeds
                    else None
                )
                for requester_model in args.requester_model:
                    for target_model in args.target_model:
                        for requester_type in requester_types:
                            for use_warden in warden_modes:
                                effective_target_values = (
                                    effective_target_profile_values()
                                )
                                effective_adversary_values = (
                                    effective_adversary_profile_access_values(requester_type)
                                )
                                effective_awareness_values = (
                                    effective_warden_awareness_values(requester_type)
                                )
                                effective_warden_access_values = (
                                    effective_warden_profile_access_values(use_warden)
                                )
                                effective_models = effective_warden_models(use_warden)
                                for warden_model in effective_models:
                                    for target_profiles in effective_target_values:
                                        for adversary_profile_access in effective_adversary_values:
                                            for warden_awareness in effective_awareness_values:
                                                for warden_profile_access in effective_warden_access_values:
                                                    for target_skeptical in target_skeptical_values:
                                                        for scenario_name in args.scenario:
                                                            run_index += 1
                                                            scenario = SCENARIOS[scenario_name]()
                                                            warden_message_mode = warden_message_mode_for_run(use_warden)
                                                            future = executor.submit(
                                                                _run_scenario,
                                                                scenario=scenario,
                                                                args=args,
                                                                use_warden=use_warden,
                                                                warden_message_mode=warden_message_mode,
                                                                requester_type=requester_type,
                                                                requester_model=requester_model,
                                                                target_model=target_model,
                                                                warden_model=warden_model,
                                                                profile=profile,
                                                                round_profile_seed=round_profile_seed,
                                                                target_has_profile=target_profiles,
                                                                warden_profile_access=warden_profile_access,
                                                                adversary_profile_access=adversary_profile_access,
                                                                warden_awareness=warden_awareness,
                                                                target_skeptical=target_skeptical,
                                                                cot_mode=cot_mode,
                                                                warden_system_prompt=args.warden_system_prompt,
                                                                adversary_system_prompt=args.adversary_system_prompt,
                                                                run_index=run_index,
                                                                quiet=quiet_runs,
                                                            )
                                                            futures.append(future)
                                                            future_contexts[future] = {
                                                                "run_index": run_index,
                                                                "round_idx": round_idx,
                                                                "scenario": scenario_name,
                                                                "requester_type": requester_type,
                                                                "requester_model": requester_model,
                                                                "target_model": target_model,
                                                                "warden_model": warden_model if use_warden else "none",
                                                                "use_warden": use_warden,
                                                            }

            completed = 0
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as exc:
                    context = future_contexts.get(future, {})
                    print("\n[ERROR] Parallel run failed")
                    print(
                        "  run="
                        f"{context.get('run_index', '?')} "
                        f"(round {context.get('round_idx', '?')})"
                    )
                    print(
                        "  scenario="
                        f"{context.get('scenario', '?')}, requester_type="
                        f"{context.get('requester_type', '?')}, use_warden="
                        f"{context.get('use_warden', '?')}"
                    )
                    print(
                        "  requester_model="
                        f"{context.get('requester_model', '?')}, target_model="
                        f"{context.get('target_model', '?')}, warden_model="
                        f"{context.get('warden_model', '?')}"
                    )
                    print(f"  {type(exc).__name__}: {exc}\n")
                    raise
                completed += 1
                print(f"Completed {completed}/{total_experiments} runs")
    else:
        for round_idx in range(1, args.experiment_rounds + 1):
            if args.experiment_rounds > 1:
                print(f"\n=== Round {round_idx}/{args.experiment_rounds} ===\n")
            profile = (
                profile_schedule[round_idx - 1]
                if profile_schedule
                else None
            )
            round_profile_seed = (
                round_profile_seeds[round_idx - 1]
                if round_profile_seeds
                else None
            )
            if args.experiment_rounds > 1 and profile:
                print(f"Profile: {profile.name}")

            for requester_model in args.requester_model:
                for target_model in args.target_model:
                    for requester_type in requester_types:
                        for use_warden in warden_modes:
                            effective_target_values = (
                                effective_target_profile_values()
                            )
                            effective_adversary_values = (
                                effective_adversary_profile_access_values(requester_type)
                            )
                            effective_awareness_values = (
                                effective_warden_awareness_values(requester_type)
                            )
                            effective_warden_access_values = (
                                effective_warden_profile_access_values(use_warden)
                            )
                            effective_models = effective_warden_models(use_warden)
                            for warden_model in effective_models:
                                for target_profiles in effective_target_values:
                                    for adversary_profile_access in effective_adversary_values:
                                        for warden_awareness in effective_awareness_values:
                                            for warden_profile_access in effective_warden_access_values:
                                                for target_skeptical in target_skeptical_values:
                                                    if args.warden == "both":
                                                        if use_warden:
                                                            print("=== Running WITH warden ===\n")
                                                        else:
                                                            print("=== Running WITHOUT warden ===\n")
                                                    if target_skeptical:
                                                        print("=== Target: SKEPTICAL ===\n")
                                                    for scenario_name in args.scenario:
                                                        if len(args.scenario) > 1:
                                                            print(f"--- Scenario: {scenario_name} ---\n")
                                                        scenario = SCENARIOS[scenario_name]()
                                                        run_index += 1
                                                        warden_message_mode = warden_message_mode_for_run(use_warden)
                                                        _run_scenario(
                                                            scenario=scenario,
                                                            args=args,
                                                            use_warden=use_warden,
                                                            warden_message_mode=warden_message_mode,
                                                            requester_type=requester_type,
                                                            requester_model=requester_model,
                                                            target_model=target_model,
                                                            warden_model=warden_model,
                                                            profile=profile,
                                                            round_profile_seed=round_profile_seed,
                                                            target_has_profile=target_profiles,
                                                            warden_profile_access=warden_profile_access,
                                                            adversary_profile_access=adversary_profile_access,
                                                            warden_awareness=warden_awareness,
                                                            target_skeptical=target_skeptical,
                                                            cot_mode=cot_mode,
                                                            warden_system_prompt=args.warden_system_prompt,
                                                            adversary_system_prompt=args.adversary_system_prompt,
                                                            run_index=run_index,
                                                            quiet=quiet_runs,
                                                        )


def _run_scenario(
    scenario,
    args,
    use_warden,
    warden_message_mode,
    requester_type,
    requester_model,
    target_model,
    warden_model,
    profile,
    round_profile_seed,
    target_has_profile,
    warden_profile_access,
    adversary_profile_access,
    warden_awareness,
    target_skeptical,
    cot_mode,
    warden_system_prompt,
    adversary_system_prompt,
    run_index,
    quiet,
):
    """Route to the correct runner based on scenario type."""
    if isinstance(scenario, MultiTargetScenario):
        profiles_requested_for_run = (
            profile is not None
            or target_has_profile
            or adversary_profile_access
            or warden_profile_access
        )
        profiles = (
            assign_profiles_to_seats(
                scenario.num_targets(),
                random_seed=round_profile_seed,
            )
            if profiles_requested_for_run
            else []
        )
        run_multi_target_experiment(
            scenario=scenario,
            profiles=profiles,
            num_turns=args.turns,
            use_warden=use_warden,
            warden_message_mode=warden_message_mode,
            requester_type=requester_type,
            adversary_model=requester_model,
            target_model=target_model,
            warden_model=warden_model,
            warden_system_prompt=warden_system_prompt,
            adversary_system_prompt=adversary_system_prompt,
            tag=args.tag,
            target_has_profile=target_has_profile,
            warden_profile_access=warden_profile_access,
            cot_mode=cot_mode,
            adversary_generates_opening=args.adversary_generates_opening,
            benign_agent_generates_opening=args.benign_agent_generates_opening,
            adversary_profile_access=adversary_profile_access,
            warden_awareness=warden_awareness,
            target_skeptical=target_skeptical,
            debug=args.debug,
            decision_reprompt_attempts=args.decision_reprompt_attempts,
            run_index=run_index,
            quiet=quiet,
        )
    else:
        run_experiment(
            scenario=scenario,
            num_turns=args.turns,
            use_warden=use_warden,
            warden_message_mode=warden_message_mode,
            requester_type=requester_type,
            adversary_model=requester_model,
            target_model=target_model,
            warden_model=warden_model,
            warden_system_prompt=warden_system_prompt,
            adversary_system_prompt=adversary_system_prompt,
            tag=args.tag,
            profile=profile,
            target_has_profile=target_has_profile,
            warden_profile_access=warden_profile_access,
            cot_mode=cot_mode,
            adversary_generates_opening=args.adversary_generates_opening,
            benign_agent_generates_opening=args.benign_agent_generates_opening,
            adversary_profile_access=adversary_profile_access,
            warden_awareness=warden_awareness,
            target_skeptical=target_skeptical,
            debug=args.debug,
            decision_reprompt_attempts=args.decision_reprompt_attempts,
            run_index=run_index,
            quiet=quiet,
        )


if __name__ == "__main__":
    main()
