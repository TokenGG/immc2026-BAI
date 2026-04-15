"""
Weight management system for the risk model.
"""

from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional
import json

from .defaults import RiskWeights, DEFAULT_RISK_WEIGHTS
from ..risk.human import HumanRiskWeights
from ..risk.environmental import EnvironmentalRiskWeights


@dataclass
class ModelConfig:
    """
    Complete model configuration including all weight sets.
    """
    risk_weights: RiskWeights
    human_risk_weights: HumanRiskWeights
    environmental_risk_weights: EnvironmentalRiskWeights

    @classmethod
    def default(cls) -> 'ModelConfig':
        """Create a model configuration with default values."""
        return cls(
            risk_weights=DEFAULT_RISK_WEIGHTS,
            human_risk_weights=HumanRiskWeights(),
            environmental_risk_weights=EnvironmentalRiskWeights()
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to a dictionary."""
        return {
            'risk_weights': asdict(self.risk_weights),
            'human_risk_weights': asdict(self.human_risk_weights),
            'environmental_risk_weights': asdict(self.environmental_risk_weights)
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert configuration to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModelConfig':
        """Load configuration from a dictionary."""
        return cls(
            risk_weights=RiskWeights(**data['risk_weights']),
            human_risk_weights=HumanRiskWeights(**data['human_risk_weights']),
            environmental_risk_weights=EnvironmentalRiskWeights(
                **data['environmental_risk_weights']
            )
        )

    @classmethod
    def from_json(cls, json_str: str) -> 'ModelConfig':
        """Load configuration from JSON string."""
        return cls.from_dict(json.loads(json_str))


class WeightManager:
    """
    Manages weight configurations for the risk model.
    """

    def __init__(self, config: Optional[ModelConfig] = None):
        """
        Initialize the weight manager.

        Args:
            config: Model configuration, uses default if None
        """
        self.config = config or ModelConfig.default()

    def get_risk_weights(self) -> RiskWeights:
        """Get the composite risk weights."""
        return self.config.risk_weights

    def get_human_risk_weights(self) -> HumanRiskWeights:
        """Get the human risk weights."""
        return self.config.human_risk_weights

    def get_environmental_risk_weights(self) -> EnvironmentalRiskWeights:
        """Get the environmental risk weights."""
        return self.config.environmental_risk_weights

    def set_risk_weights(
        self,
        human_weight: Optional[float] = None,
        environmental_weight: Optional[float] = None,
        density_weight: Optional[float] = None
    ) -> None:
        """
        Update composite risk weights.

        Args:
            human_weight: New human risk weight (optional)
            environmental_weight: New environmental risk weight (optional)
            density_weight: New density weight (optional)
        """
        current = self.config.risk_weights
        self.config.risk_weights = RiskWeights(
            human_weight=human_weight if human_weight is not None else current.human_weight,
            environmental_weight=environmental_weight if environmental_weight is not None else current.environmental_weight,
            density_weight=density_weight if density_weight is not None else current.density_weight
        )

    def save(self, filepath: str) -> None:
        """Save configuration to a JSON file."""
        with open(filepath, 'w') as f:
            f.write(self.config.to_json())

    @classmethod
    def load(cls, filepath: str) -> 'WeightManager':
        """Load configuration from a JSON file."""
        with open(filepath, 'r') as f:
            config = ModelConfig.from_json(f.read())
        return cls(config)
