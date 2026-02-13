"""Train scenario exports."""

from src.scenarios.train.ai_containment import AIContainmentScenario
from src.scenarios.train.ai_containment_board import AIContainmentBoardScenario
from src.scenarios.train.ai_override import AIOverrideScenario
from src.scenarios.train.ai_oversight import AIOversightScenario
from src.scenarios.train.ai_race import AIRaceScenario
from src.scenarios.train.ai_treaty import AITreatyScenario
from src.scenarios.train.automation_decision import AutomationDecisionScenario
from src.scenarios.train.board_acquisition import BoardAcquisitionScenario
from src.scenarios.train.coding_agent import CodingAgentScenario
from src.scenarios.train.file_access import FileAccessPasswordScenario, FileAccessScenario
from src.scenarios.train.hiring import HiringScenario
from src.scenarios.train.kill_switch import KillSwitchScenario
from src.scenarios.train.medical_ai import MedicalAIScenario
from src.scenarios.train.model_release import ModelReleaseScenario
from src.scenarios.train.open_weights import OpenWeightsScenario
from src.scenarios.train.sales import UpsellingScenario
from src.scenarios.train.vote import VoteScenario

__all__ = [
    "AIContainmentScenario",
    "AIContainmentBoardScenario",
    "AIRaceScenario",
    "AITreatyScenario",
    "AIOversightScenario",
    "AIOverrideScenario",
    "AutomationDecisionScenario",
    "BoardAcquisitionScenario",
    "CodingAgentScenario",
    "FileAccessScenario",
    "FileAccessPasswordScenario",
    "HiringScenario",
    "KillSwitchScenario",
    "MedicalAIScenario",
    "ModelReleaseScenario",
    "OpenWeightsScenario",
    "UpsellingScenario",
    "VoteScenario",
]
