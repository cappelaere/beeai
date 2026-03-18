"""
Property Due Diligence Workflow

Automates comprehensive property research and risk assessment.
"""
import yaml
from pathlib import Path

from .workflow import PropertyDueDiligenceWorkflow, PropertyDueDiligenceState

# Load metadata from YAML file
_current_dir = Path(__file__).parent
with open(_current_dir / 'metadata.yaml', 'r') as f:
    METADATA = yaml.safe_load(f)

# Mermaid diagram removed; BPMN is now the source of truth
DIAGRAM = ""

__all__ = [
    'PropertyDueDiligenceWorkflow',
    'PropertyDueDiligenceState',
    'DIAGRAM',
    'METADATA',
]
