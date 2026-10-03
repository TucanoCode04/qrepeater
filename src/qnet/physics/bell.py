"""Bell-state measurement and entanglement swapping on bare qubits.

Physics recap
-------------
With pairs (A, R1) and (R2, B), both in |Phi+>, the four-qubit state can be
regrouped as

    |Phi+>_{A R1} |Phi+>_{R2 B} = 1/2 sum_k |beta_k>_{R1 R2} (sigma_k |Phi+>)_{AB}

A Bell-state measurement (BSM) on R1, R2 picks one term (each with prob 1/4),
leaving A-B in a Bell state rotated by a known Pauli sigma_k. The repeater sends
the two outcome bits to B, which undoes the rotation.

The BSM circuit is CNOT(R1 -> R2), H(R1), then measure both in Z. It maps each
Bell state to a computational basis state:

    outcome (m1, m2)   Bell state at R1R2   state left on A-B      correction at B
    (0, 0)             Phi+                 Phi+                   I
    (0, 1)             Psi+                 Psi+  = X_B Phi+       X
    (1, 0)             Phi-                 Phi-  = Z_B Phi+       Z
    (1, 1)             Psi-                 Psi-  = X_B Z_B Phi+   X then Z

So in general: m1 is the phase bit, m2 the parity bit, and the correction is
"apply X^m2, then Z^m1".
"""

import netsquid.qubits.qubitapi as qapi
from netsquid.qubits import operators as ops

from qnet.physics.states import PHI_MINUS, PHI_PLUS, PSI_MINUS, PSI_PLUS

# State left on A-B (before correction) for each BSM outcome.
UNCORRECTED_STATE = {
    (0, 0): PHI_PLUS,
    (0, 1): PSI_PLUS,
    (1, 0): PHI_MINUS,
    (1, 1): PSI_MINUS,
}


def bell_state_measurement(q_left, q_right):
    """Destructively measure two qubits in the Bell basis; return (m1, m2)."""
    qapi.operate([q_left, q_right], ops.CNOT)
    qapi.operate(q_left, ops.H)
    m1, _ = qapi.measure(q_left, discard=True)
    m2, _ = qapi.measure(q_right, discard=True)
    return m1, m2


def apply_pauli_correction(qubit, m1, m2):
    """Undo the Pauli rotation left by a BSM with outcome (m1, m2)."""
    if m2:
        qapi.operate(qubit, ops.X)
    if m1:
        qapi.operate(qubit, ops.Z)


def entanglement_swap(pair_left, pair_right, correct=True):
    """Swap (A, R1) and (R2, B) into a pair (A, B).

    Returns the BSM outcome. If ``correct`` is False, B is left un-corrected so
    the rotated Bell state can be inspected.
    """
    _, q_r1 = pair_left
    q_r2, q_b = pair_right
    outcome = bell_state_measurement(q_r1, q_r2)
    if correct:
        apply_pauli_correction(q_b, *outcome)
    return outcome
