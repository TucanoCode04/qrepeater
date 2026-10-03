import pytest

from qnet.config import ChainConfig, GateDurations, LinkConfig
from qnet.network.builder import ChainNetwork
from qnet.physics.analytic import single_swap_timeline_ns, swapped_fidelity
from qnet.runner import run_single_swap

ASYMMETRIC = ChainConfig(("Alice", "Repeater", "Bob"),
                         (LinkConfig(30.0, 0.95), LinkConfig(12.0, 0.8)),
                         GateDurations(single_qubit_ns=20, two_qubit_ns=300, measure_ns=700))


def test_chain_config_rejects_wrong_number_of_links():
    with pytest.raises(ValueError):
        ChainConfig(("Alice", "Repeater", "Bob"), (LinkConfig(10.0),))


def test_chain_network_memory_layout():
    chain = ChainNetwork(ChainConfig.alice_repeater_bob())
    assert chain.node("Alice").qmemory.num_positions == 1
    assert chain.node("Repeater").qmemory.num_positions == 2
    assert chain.node("Bob").qmemory.num_positions == 1
    assert chain.position("Repeater", "Alice") == 0
    assert chain.position("Repeater", "Bob") == 1
    assert chain.link("Bob", "Repeater") is chain.links[1]
    with pytest.raises(ValueError):
        chain.link("Alice", "Bob")


@pytest.mark.parametrize("config", [
    ChainConfig.alice_repeater_bob(10.0, 1.0),
    ChainConfig.alice_repeater_bob(10.0, 0.9),
    ASYMMETRIC,
], ids=["perfect", "F0.9", "asymmetric"])
def test_network_swap_matches_analytic_fidelity_and_timeline(config):
    f_left, f_right = (link.fidelity for link in config.links)
    expected_f = swapped_fidelity(f_left, f_right)
    seen = set()
    for seed in range(20):
        result = run_single_swap(config, seed=seed)
        seen.add(result.outcome)
        assert result.fidelity == pytest.approx(expected_f)
        expected_t = single_swap_timeline_ns(config, result.outcome)
        for event, t in expected_t.items():
            assert getattr(result, event) == pytest.approx(t), event
    assert len(seen) == 4, "all four Bell outcomes (and corrections) should be exercised"


def test_latency_grows_with_distance_but_fidelity_does_not():
    short = run_single_swap(ChainConfig.alice_repeater_bob(1.0, 0.9), seed=0)
    long = run_single_swap(ChainConfig.alice_repeater_bob(100.0, 0.9), seed=0)
    assert long.completed_at > short.completed_at
    assert long.fidelity == pytest.approx(short.fidelity)


def test_same_seed_gives_same_run():
    a = run_single_swap(ASYMMETRIC, seed=7)
    b = run_single_swap(ASYMMETRIC, seed=7)
    assert a == b
