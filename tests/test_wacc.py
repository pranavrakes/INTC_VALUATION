import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.wacc import wacc, cost_of_equity

def test_wacc_toy_case():
    assert abs(wacc(100, 100, 0.10, 0.04) - 0.07) < 1e-12

def test_capm():
    assert abs(cost_of_equity(0.04, 1.5, 0.05) - 0.115) < 1e-12