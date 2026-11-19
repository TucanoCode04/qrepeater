# qnet: quantum-repeater simulation

A modular [NetSquid](https://netsquid.org) simulation of quantum repeater chains, built step by step and checked against analytic models at every phase.

- **Phase 1a:** entanglement swapping on bare qubits. Two Werner pairs, a Bell-state measurement at the repeater and a Pauli correction at Bob. The final fidelity is compared with the analytic value (1 + 3·p₁·p₂)/4.
- **Phase 1b:** the same protocol on a simulated network with fiber links and timing (Alice – Repeater – Bob), showing that distance costs time but not fidelity while memories are perfect.
- **Next:** noisy memories, longer chains, and heuristic and reinforcement-learning controllers.

## Structure
```
src/qnet/
  hardware/    links, quantum memories
  network/     network builder
  operations/  swapping and node programs
  physics/     states, Bell measurements, analytic predictions
experiments/   runnable scripts for each phase
tests/         pytest checks against the analytic results
```

## Run
```bash
pip install -e ".[dev]"     # NetSquid needs a netsquid.org account
python experiments/phase1a_bare_qubits.py --f-left 0.9 --f-right 0.9
python experiments/phase1b_network.py --length 10 --fidelity 0.9
pytest
```
