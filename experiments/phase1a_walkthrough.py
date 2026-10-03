"""Phase 1a walkthrough: one entanglement swap, printed step by step.

Shows, at every stage, which qubits share a quantum state and what the
Alice-Bob density matrix looks like.

Run:  python experiments/phase1a_walkthrough.py --fidelity 1.0 --seed 3
      python experiments/phase1a_walkthrough.py --fidelity 0.9 --seed 3
"""

import argparse

import netsquid as ns
import netsquid.qubits.qubitapi as qapi
import numpy as np

from qnet.physics.analytic import swapped_fidelity
from qnet.physics.bell import UNCORRECTED_STATE, apply_pauli_correction, bell_state_measurement
from qnet.physics.states import PHI_PLUS, bell_fidelity, create_bell_pair, fidelity_to_werner_p

BELL_NAMES = {(0, 0): "Phi+", (0, 1): "Psi+", (1, 0): "Phi-", (1, 1): "Psi-"}


def show(label, matrix):
    print(f"{label}")
    print("  " + np.array2string(np.round(matrix.real, 3), prefix="  ", suppress_small=True))


def shared_with(qubit, names):
    """Names of the qubits that live in the same NetSquid quantum state as `qubit`."""
    return [names[q] for q in qubit.qstate.qubits]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fidelity", type=float, default=0.9)
    parser.add_argument("--seed", type=int, default=3)
    args = parser.parse_args()
    ns.set_qstate_formalism(ns.QFormalism.DM)
    ns.set_random_state(seed=args.seed)
    f = args.fidelity

    print(f"=== STEP 1: create two links, each with fidelity {f} "
          f"(Werner p = {fidelity_to_werner_p(f):.4f}) ===")
    q_a, q_r1 = create_bell_pair(f)   # link Alice-Repeater
    q_r2, q_b = create_bell_pair(f)   # link Repeater-Bob
    names = {q_a: "A", q_r1: "R1", q_r2: "R2", q_b: "B"}
    print("A  shares a state with", shared_with(q_a, names))
    print("B  shares a state with", shared_with(q_b, names))
    show("rho(A,R1)  -- the Alice-Repeater link (4x4: basis 00,01,10,11):",
         qapi.reduced_dm([q_a, q_r1]))
    show("rho(A,B)   -- Alice and Bob have never interacted: pure noise I/4",
         qapi.reduced_dm([q_a, q_b]))
    show("rho(R1,R2) -- the repeater's two qubits are ALSO uncorrelated",
         qapi.reduced_dm([q_r1, q_r2]))
    print(f"F(A,B) = {bell_fidelity([q_a, q_b]):.4f}   (0.25 = no entanglement)\n")

    print("=== STEP 2: Bell-state measurement on R1, R2 at the repeater ===")
    m1, m2 = bell_state_measurement(q_r1, q_r2)
    outcome = (m1, m2)
    print(f"outcome (m1, m2) = {outcome}  ->  'R1,R2 were found in {BELL_NAMES[outcome]}'")
    print("A  now shares a state with", shared_with(q_a, names), "(R1, R2 were destroyed)")
    rotated = UNCORRECTED_STATE[outcome]
    show(f"rho(A,B) right after the measurement -- now entangled, in {BELL_NAMES[outcome]}:",
         qapi.reduced_dm([q_a, q_b]))
    print(f"F(A,B) vs Phi+                 = {bell_fidelity([q_a, q_b]):.4f}")
    print(f"F(A,B) vs {BELL_NAMES[outcome]:<5} (the rotated state) = "
          f"{bell_fidelity([q_a, q_b], rotated):.4f}\n")

    print(f"=== STEP 3: Bob receives bits {outcome} and applies "
          f"{'X' if m2 else ''}{' then ' if m1 and m2 else ''}{'Z' if m1 else ''}"
          f"{'nothing' if not (m1 or m2) else ''} ===")
    apply_pauli_correction(q_b, m1, m2)
    show("rho(A,B) after correction -- Phi+ (plus the noise inherited from the links):",
         qapi.reduced_dm([q_a, q_b]))
    print(f"F(A,B) vs Phi+ = {bell_fidelity([q_a, q_b]):.4f}   "
          f"analytic (1+3p^2)/4 = {swapped_fidelity(f, f):.4f}")
    show("for reference, the ideal |Phi+><Phi+|:", PHI_PLUS @ PHI_PLUS.conj().T)


if __name__ == "__main__":
    main()
