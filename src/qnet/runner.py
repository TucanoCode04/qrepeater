"""Run complete simulations and return their results.

Phase 1b: a single entanglement swap over Alice -- Repeater -- Bob.
"""

from dataclasses import dataclass

import netsquid as ns

from qnet.network.builder import ChainNetwork, classical_port
from qnet.operations.swap import CorrectionProtocol, SwapProtocol
from qnet.physics.states import bell_fidelity


@dataclass
class SwapResult:
    fidelity: float            # true F of the final Alice-Bob pair (oracle, not observable)
    outcome: tuple             # (m1, m2) of the Bell measurement
    qubits_ready_at: float     # [ns] both qubits stored at the repeater
    outcome_sent_at: float     # [ns] Bell measurement finished, message sent
    outcome_received_at: float  # [ns] message arrives at Bob
    completed_at: float        # [ns] Bob's correction done: end-to-end pair ready


def run_single_swap(config, seed=None):
    """Generate both links at t=0, swap at the repeater, correct at Bob."""
    if len(config.node_names) != 3:
        raise ValueError("run_single_swap supports exactly one repeater")
    ns.sim_reset()
    ns.set_qstate_formalism(ns.QFormalism.DM)
    if seed is not None:
        ns.set_random_state(seed=seed)

    chain = ChainNetwork(config)
    alice, repeater, bob = config.node_names
    swap = SwapProtocol(chain.node(repeater),
                        left_position=chain.position(repeater, alice),
                        right_position=chain.position(repeater, bob),
                        outcome_port=classical_port(bob))
    correction = CorrectionProtocol(chain.node(bob),
                                    position=chain.position(bob, repeater),
                                    outcome_port=classical_port(repeater))
    swap.start()
    correction.start()
    for link in chain.links:
        link.trigger()

    ns.sim_run()  # process events until nothing is left to happen
    if correction.completed_at is None:
        raise RuntimeError("Simulation ended before Bob's correction completed")

    q_a = chain.node(alice).qmemory.peek(chain.position(alice, repeater))[0]
    q_b = chain.node(bob).qmemory.peek(chain.position(bob, repeater))[0]
    return SwapResult(
        fidelity=bell_fidelity([q_a, q_b]),
        outcome=swap.outcome,
        qubits_ready_at=swap.qubits_ready_at,
        outcome_sent_at=swap.outcome_sent_at,
        outcome_received_at=correction.outcome_received_at,
        completed_at=correction.completed_at,
    )
