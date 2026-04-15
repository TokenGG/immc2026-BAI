"""
Configuration management for the risk model.
"""

from .defaults import RiskWeights, DEFAULT_RISK_WEIGHTS
from .weights import ModelConfig, WeightManager

__all__ = [
    'RiskWeights',
    'DEFAULT_RISK_WEIGHTS',
    'ModelConfig',
    'WeightManager',
]
