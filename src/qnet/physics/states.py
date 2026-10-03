"""Bell pairs, Werner states and fidelity.

Physics recap
-------------
The target state of every link is the Bell state

    |Phi+> = (|00> + |11>) / sqrt(2)

A noisy pair is modelled as a *Werner state*: with probability ``p`` the pair is
perfect, otherwise it is replaced by white noise (the maximally mixed state I/4):

    rho_W = p |Phi+><Phi+| + (1 - p) I/4

Its fidelity with |Phi+> is F = <Phi+|rho_W|Phi+> = p + (1 - p)/4 = (1 + 3p)/4,
so a single number (F or equivalently p) fully characterises the pair.
"""

import numpy as np
import netsquid as ns
import netsquid.qubits.qubitapi as qapi
from netsquid.qubits import ketstates as ks

# NetSquid's Bell kets. Note the naming: b01 is Psi+, b10 is Phi-, b11 is Psi-.
PHI_PLUS = ks.b00   # (|00> + |11>)/sqrt2
PSI_PLUS = ks.b01   # (|01> + |10>)/sqrt2
PHI_MINUS = ks.b10  # (|00> - |11>)/sqrt2
PSI_MINUS = ks.b11  # (|01> - |10>)/sqrt2


def fidelity_to_werner_p(fidelity):
    """Invert F = (1 + 3p)/4."""
    if not 0.25 <= fidelity <= 1.0:
        raise ValueError(f"Werner fidelity must be in [1/4, 1], got {fidelity}")
    return (4 * fidelity - 1) / 3


def werner_p_to_fidelity(p):
    return (1 + 3 * p) / 4


def werner_dm(fidelity):
    """4x4 density matrix of a Werner state with the given fidelity to |Phi+>."""
    p = fidelity_to_werner_p(fidelity)
    phi_plus_dm = PHI_PLUS @ PHI_PLUS.conj().T
    return p * phi_plus_dm + (1 - p) * np.eye(4) / 4


def create_bell_pair(fidelity=1.0):
    """Create two fresh qubits sharing a Werner state with the given fidelity.

    Requires the DM formalism (mixed states cannot be represented as kets).
    """
    if ns.get_qstate_formalism() != ns.QFormalism.DM:
        raise RuntimeError("Call ns.set_qstate_formalism(ns.QFormalism.DM) first")
    qubits = ns.qubits.create_qubits(2)
    qapi.assign_qstate(qubits, werner_dm(fidelity))
    return qubits


def bell_fidelity(qubits, reference=PHI_PLUS):
    """F = <psi|rho|psi> of two qubits with respect to a Bell ket.

    NetSquid's ``fidelity`` returns sqrt(<psi|rho|psi>) unless squared=True;
    we always use the squared convention, which is the standard one in the
    quantum-networking literature.
    """
    return qapi.fidelity(qubits, reference, squared=True)
