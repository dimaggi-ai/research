"""Local multi-repository closure check; standalone CI validates its own copy."""
import hashlib
import json
from pathlib import Path
from validate import validate

def test_available_portfolio_manifests_and_validator_parity():
    research=Path(__file__).resolve().parents[1]
    canonical=(research/'evidence/validate.py').read_bytes()
    manifests=list(research.parent.glob('*/evidence.json'))
    assert manifests
    for path in manifests:
        assert validate(json.loads(path.read_text()),path.parent)==[],path
        assert (path.parent/'tools/validate_evidence.py').read_bytes()==canonical,path
