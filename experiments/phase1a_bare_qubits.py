"""Phase 1a: entanglement swapping on bare qubits (no network, no time).

Alice ---(F_left)--- Repeater ---(F_right)--- Bob

Creates two Werner pairs, performs a Bell-state measurement at the repeater,
applies the Pauli correction at Bob and compares the resulting Alice-Bob
fidelity with the analytic prediction (1 + 3 p_left p_right) / 4.

Run:  python experiments/phase1a_bare_qubits.py --f-left 0.9 --f-right 0.9
"""

import argparse
from collections import defaultdict

import netsquid as ns
import netsquid.qubits.qubitapi as qapi
import numpy as np

from qnet.physics.analytic import swapped_fidelity
from qnet.physics.bell import UNCORRECTED_STATE, entanglement_swap
from qnet.physics.states import bell_fidelity, create_bell_pair

BELL_NAMES = {(0, 0): "Phi+", (0, 1): "Psi+", (1, 0): "Phi-", (1, 1): "Psi-"}


def run_trial(f_left, f_right, correct=True):
    q_a, q_r1 = create_bell_pair(f_left)
    q_r2, q_b = create_bell_pair(f_right)
    outcome = entanglement_swap((q_a, q_r1), (q_r2, q_b), correct=correct)
    return outcome, q_a, q_b


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--f-left", type=float, default=0.9)
    parser.add_argument("--f-right", type=float, default=0.9)
    parser.add_argument("--trials", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    ns.set_qstate_formalism(ns.QFormalism.DM)
    ns.set_random_state(seed=args.seed)
    expected = swapped_fidelity(args.f_left, args.f_right)

    # One annotated run: look at the actual density matrix of A-B.
    outcome, q_a, q_b = run_trial(args.f_left, args.f_right, correct=False)
    print(f"Example run: BSM outcome {outcome} -> A-B in {BELL_NAMES[outcome]} before correction")
    print("rho_AB (real part, before correction):")
    print(np.round(qapi.reduced_dm([q_a, q_b]).real, 3))

    # Many runs, grouped by BSM outcome.
    counts = defaultdict(int)
    f_uncorrected = {}
    f_corrected = {}
    for _ in range(args.trials):
        outcome, q_a, q_b = run_trial(args.f_left, args.f_right, correct=False)
        counts[outcome] += 1
        f_uncorrected[outcome] = bell_fidelity([q_a, q_b], UNCORRECTED_STATE[outcome])
        outcome, q_a, q_b = run_trial(args.f_left, args.f_right, correct=True)
        f_corrected[outcome] = bell_fidelity([q_a, q_b])

    print(f"\nF_left={args.f_left}  F_right={args.f_right}  trials={args.trials}")
    print(f"Analytic prediction F_AB = {expected:.6f}\n")
    print(f"{'outcome':>8} {'Bell':>5} {'freq':>6} {'F vs rotated':>13} {'F_AB corrected':>15}")
    for outcome in sorted(BELL_NAMES):
        print(f"{str(outcome):>8} {BELL_NAMES[outcome]:>5} {counts[outcome] / args.trials:>6.3f} "
              f"{f_uncorrected.get(outcome, float('nan')):>13.6f} "
              f"{f_corrected.get(outcome, float('nan')):>15.6f}")


if __name__ == "__main__":
    main()
