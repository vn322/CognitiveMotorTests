# tests/__init__.py
from .simple_reaction import SimpleReactionTest
from .choice_reaction import ChoiceReactionTest
from .complex_choice import ComplexChoiceTest
from .combined_a import CombinedTestA
from .combined_b import CombinedTestB
from .tracking_following import TrackingFollowingTest
from .moving_object_reaction import MovingObjectReactionTest
from .attention_switching import AttentionSwitchingTest
from .trajectory_prediction import TrajectoryPredictionTest
from .gorbov_shulte import GorbovShulteTest
from .gorbov_shulte_no_hint import GorbovShulteTestNoHint
from .stroop_test import StroopTest
from .working_memory import WorkingMemoryTest
from .size_discrimination import SizeDiscriminationTest
from .color_discrimination import ColorDiscriminationTest


__all__ = [
    'SimpleReactionTest',
    'ChoiceReactionTest',
    'ComplexChoiceTest',
    'CombinedTestA',
    'CombinedTestB',
    'TrackingFollowingTest',
    'MovingObjectReactionTest',
    'AttentionSwitchingTest',
    'TrajectoryPredictionTest',
    'GorbovShulteTest',
    'GorbovShulteTestNoHint',
    'StroopTest',
    'WorkingMemoryTest',
    'SizeDiscriminationTest',
    'ColorDiscriminationTest',
]