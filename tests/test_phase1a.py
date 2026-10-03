import netsquid as ns
import numpy as np
import pytest

from qnet.physics.analytic import swapped_fidelity
from qnet.physics.bell import UNCORRECTED_STATE, entanglement_swap
from qnet.physics.states import (
    PHI_PLUS,
    bell_fidelity,
    create_bell_pair,
    werner_dm,
)


@pytest.fixture(autouse=True)
def dm_formalism():
    ns.set_qstate_formalism(ns.QFormalism.DM)
    ns.set_random_state(seed=1234)


@pytest.mark.parametrize("fidelity", [0.25, 0.6, 0.9, 1.0])
def test_werner_dm_is_valid_state_with_requested_fidelity(fidelity):
    rho = werner_dm(fidelity)
    assert np.isclose(np.trace(rho), 1.0)
    assert np.all(np.linalg.eigvalsh(rho) >= -1e-12)
    assert np.isclose((PHI_PLUS.conj().T @ rho @ PHI_PLUS).item().real, fidelity)


def test_created_pair_has_requested_fidelity():
    assert bell_fidelity(create_bell_pair(0.8)) == pytest.approx(0.8)


def test_werner_rejects_unphysical_fidelity():
    with pytest.raises(ValueError):
        werner_dm(0.2)


def test_swapped_fidelity_formula():
    assert swapped_fidelity(1.0, 1.0) == pytest.approx(1.0)
    assert swapped_fidelity(0.9, 0.9) == pytest.approx((1 + 3 * (2.6 / 3) ** 2) / 4)
    # A pair of pure noise destroys everything: output is maximally mixed.
    assert swapped_fidelity(0.25, 0.95) == pytest.approx(0.25)


def _swap(f_left, f_right, correct):
    q_a, q_r1 = create_bell_pair(f_left)
    q_r2, q_b = create_bell_pair(f_right)
    outcome = entanglement_swap((q_a, q_r1), (q_r2, q_b), correct=correct)
    return outcome, [q_a, q_b]


@pytest.mark.parametrize("f_left, f_right", [(1.0, 1.0), (0.9, 0.9), (0.95, 0.7)])
def test_swap_matches_analytic_for_every_outcome(f_left, f_right):
    expected = swapped_fidelity(f_left, f_right)
    seen = set()
    for _ in range(200):
        outcome, pair = _swap(f_left, f_right, correct=True)
        seen.add(outcome)
        assert bell_fidelity(pair) == pytest.approx(expected)
    assert seen == set(UNCORRECTED_STATE), "all four BSM outcomes should occur"


def test_uncorrected_state_is_the_predicted_rotated_bell_state():
    expected = swapped_fidelity(0.9, 0.85)
    seen = set()
    for _ in range(200):
        outcome, pair = _swap(0.9, 0.85, correct=False)
        seen.add(outcome)
        assert bell_fidelity(pair, UNCORRECTED_STATE[outcome]) == pytest.approx(expected)
    assert seen == set(UNCORRECTED_STATE)


def test_bsm_outcomes_are_uniform():
    counts = {}
    n = 4000
    for _ in range(n):
        outcome, _ = _swap(0.9, 0.9, correct=True)
        counts[outcome] = counts.get(outcome, 0) + 1
    for count in counts.values():
        assert count / n == pytest.approx(0.25, abs=0.03)
