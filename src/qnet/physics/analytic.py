"""Closed-form predictions used as test oracles for the simulation."""

from qnet.config import NS_PER_KM
from qnet.physics.states import fidelity_to_werner_p, werner_p_to_fidelity


def swapped_fidelity(f_left, f_right):
    """Fidelity after ideally swapping two Werner pairs.

    The white-noise parts never "repair" each other, and the result is again a
    Werner state, with p_out = p_left * p_right. Hence
    F_out = (1 + 3 p_left p_right) / 4.
    """
    p = fidelity_to_werner_p(f_left) * fidelity_to_werner_p(f_right)
    return werner_p_to_fidelity(p)


def single_swap_timeline_ns(config, outcome):
    """Expected event times [ns] for one swap over Alice -- Repeater -- Bob.

    Both sources fire at t=0 from the middle of their link:
      qubits_ready  = slower photon reaches the repeater: max(L_left, L_right)/2 * 5 us/km
      outcome_sent  = + CNOT + H + 2 measurements (executed one after the other)
      received      = + classical message over the right link: L_right * 5 us/km
      completed     = + one single-qubit gate per correction bit (X if m2, Z if m1)
    """
    left, right = config.links
    gates = config.gates
    qubits_ready = max(left.length_km, right.length_km) / 2 * NS_PER_KM
    outcome_sent = qubits_ready + gates.two_qubit_ns + gates.single_qubit_ns + 2 * gates.measure_ns
    received = outcome_sent + right.length_km * NS_PER_KM
    m1, m2 = outcome
    completed = received + (m1 + m2) * gates.single_qubit_ns
    return {"qubits_ready_at": qubits_ready, "outcome_sent_at": outcome_sent,
            "outcome_received_at": received, "completed_at": completed}
