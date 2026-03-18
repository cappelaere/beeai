"""
Bidder Onboarding & Verification Workflow

Automates the complete bidder registration and compliance verification process.
"""
import yaml
from pathlib import Path

from .workflow import BidderOnboardingWorkflow, BidderOnboardingState

# Load metadata from YAML file
_current_dir = Path(__file__).parent
with open(_current_dir / 'metadata.yaml', 'r') as f:
    METADATA = yaml.safe_load(f)

# Mermaid diagram removed; BPMN is now the source of truth
DIAGRAM = ""

__all__ = [
    'BidderOnboardingWorkflow',
    'BidderOnboardingState',
    'DIAGRAM',
    'METADATA',
]
