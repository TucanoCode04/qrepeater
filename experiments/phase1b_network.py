"""Phase 1b: entanglement swapping on a simulated network, with time.

Alice --(L km)-- Repeater --(L km)-- Bob

Prints the timeline of one run, then sweeps the link length to show that in
this phase distance costs TIME but not FIDELITY (memories are still perfect).

Run:  python experiments/phase1b_network.py --length 10 --fidelity 0.9
"""

import argparse

from qnet.config import ChainConfig
from qnet.physics.analytic import single_swap_timeline_ns, swapped_fidelity
from qnet.runner import run_single_swap


def us(t_ns):
    return f"{t_ns / 1000:10.3f} us"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--length", type=float, default=10.0, help="km per link")
    parser.add_argument("--fidelity", type=float, default=0.9, help="F of each link")
    parser.add_argument("--seed", type=int, default=3)
    args = parser.parse_args()

    config = ChainConfig.alice_repeater_bob(args.length, args.fidelity)
    r = run_single_swap(config, seed=args.seed)
    expected = single_swap_timeline_ns(config, r.outcome)
    g = config.gates

    print(f"=== One run: 2 links of {args.length} km, F = {args.fidelity} each ===")
    print(f"{us(0)}  both sources emit a pair (midpoint of each link)")
    print(f"{us(r.qubits_ready_at)}  photons reach the repeater after {args.length / 2} km "
          f"(Alice's and Bob's halves arrive at their nodes at the same time)")
    print(f"{us(r.outcome_sent_at)}  Bell measurement done "
          f"(CNOT {g.two_qubit_ns:.0f} + H {g.single_qubit_ns:.0f} + 2 x measure "
          f"{g.measure_ns:.0f} ns), outcome {r.outcome} sent to Bob")
    print(f"{us(r.outcome_received_at)}  message arrives at Bob after {args.length} km of fibre")
    print(f"{us(r.completed_at)}  Bob's correction done -> Alice-Bob pair READY")
    print(f"\nF(A,B) = {r.fidelity:.4f}   analytic {swapped_fidelity(args.fidelity, args.fidelity):.4f}")
    print(f"completion time matches analytic timeline: "
          f"{abs(r.completed_at - expected['completed_at']) < 1e-6}")

    print("\n=== Length sweep (F per link fixed) ===")
    print(f"{'L per link':>11} {'latency':>13} {'of which classical':>19} {'F(A,B)':>8}")
    for length in (1, 10, 50, 100, 200):
        cfg = ChainConfig.alice_repeater_bob(length, args.fidelity)
        res = run_single_swap(cfg, seed=args.seed)
        classical = res.outcome_received_at - res.outcome_sent_at
        print(f"{length:>8} km {us(res.completed_at)} {us(classical):>19} {res.fidelity:>8.4f}")


if __name__ == "__main__":
    main()
