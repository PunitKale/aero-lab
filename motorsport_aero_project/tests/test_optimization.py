import numpy as np
import pytest
from src.schemas import Setup
from src.optimization import Evaluator,pareto_mask
from src.circuit_model import circuits
from src.synthetic_data import setup_design

def test_invalid_setup():
    with pytest.raises(ValueError): Setup(front_wing_deg=50).validate()

def test_pareto():
    assert pareto_mask(np.array([[1,3],[2,2],[3,1],[3,3],[1,3]])).tolist()==[True,True,True,False,True]

def test_rejected_setup_not_best():
    ev=Evaluator(circuits()['Apex Ring'])
    assert ev([100,20,.04,.06])>=1e6
    assert not ev.rows[-1]['feasible']
    assert ev(Setup().vector())<1e6

def test_generator_reproducibility():
    assert setup_design(42)==setup_design(42)
    assert setup_design(42)!=setup_design(43)
