"""TAPAS tests"""
import pytest
from random import randint
from web3.contract import Contract
from ico.tests.utils import check_gas

@pytest.fixture
def tapas_token_name() -> str:
    return "TAPAS"


@pytest.fixture
def tapas_token_symbol() -> str:
    return "TAP"


@pytest.fixture
def tapas_initial_supply() -> str:
    return 999999999000000000000000000

@pytest.fixture
def zero_address() -> str:
    return "0x0000000000000000000000000000000000000000"
#
# ERC-20 fixtures
#

@pytest.fixture
def tapas_token(chain, team_multisig, tapas_token_name, tapas_token_symbol, tapas_initial_supply) -> Contract:
    """Create the token contract."""

    args = [tapas_token_name, tapas_token_symbol]  # Owner set

    tx = {
        "from": team_multisig
    }

    contract, hash = chain.provider.deploy_contract('TAPASToken', deploy_args=args, deploy_transaction=tx)

    check_gas(chain, hash)

    check_gas(chain, contract.transact(tx).addAddressToWhitelist(team_multisig))
    check_gas(chain, contract.transact(tx).issueTokens(tapas_initial_supply))

    assert contract.call().totalSupply() == tapas_initial_supply
    assert contract.call().balanceOf(team_multisig) == tapas_initial_supply

    return contract

def test_tapas_issue(chain, tapas_token, tapas_initial_supply, team_multisig, zero_address, customer):
    check_gas(chain, tapas_token.transact({"from": team_multisig}).issueTokens(tapas_initial_supply))
    assert tapas_token.call().totalSupply() == (tapas_initial_supply * 2)


def test_tapas_burn(chain, tapas_token, tapas_initial_supply, team_multisig, zero_address, customer):
    check_gas(chain, tapas_token.transact({"from": team_multisig}).transfer(tapas_token.address, tapas_initial_supply))
    check_gas(chain, tapas_token.transact({"from": team_multisig}).burnTokens(tapas_initial_supply - 1))
    assert tapas_token.call().totalSupply() == 1


def test_tapas_force(chain, tapas_token, tapas_initial_supply, team_multisig, zero_address, customer):
    assert tapas_token.call().balanceOf(team_multisig) == tapas_initial_supply
    check_gas(chain, tapas_token.transact({"from": team_multisig}).forceTransfer(team_multisig, customer, tapas_initial_supply))
    assert tapas_token.call().totalSupply() == tapas_initial_supply
    assert tapas_token.call().balanceOf(team_multisig) == 0
    assert tapas_token.call().balanceOf(customer) == tapas_initial_supply

def test_tapas_ask_balanceat(chain, tapas_token, tapas_initial_supply, team_multisig, zero_address, customer):
    check_gas(chain, tapas_token.transact().balanceAt(team_multisig, 1), gaslimit=26000)


def test_tapas_change_name_and_symbol(chain, tapas_token, tapas_initial_supply, team_multisig, zero_address, customer):
    check_gas(chain, tapas_token.transact({"from": team_multisig}).setTokenInformation("NewToken", "NEW"))
    assert tapas_token.call().name() == "NewToken"
    assert tapas_token.call().symbol() == "NEW"


def test_tapas_approve(chain, tapas_token, tapas_initial_supply, team_multisig, zero_address, customer):
    check_gas(chain, tapas_token.transact({"from": team_multisig}).approve(customer, tapas_initial_supply))
    assert tapas_token.call().allowance(team_multisig, customer) == tapas_initial_supply
    check_gas(chain, tapas_token.transact({"from": customer}).transferFrom(team_multisig, customer, tapas_initial_supply))
    assert tapas_token.call().balanceOf(team_multisig) == 0
    assert tapas_token.call().balanceOf(customer) == tapas_initial_supply


def test_tapas_token_interface(tapas_token, token_owner: str, zero_address: str):
    """TAPAS satisfies ERC-20/ERC-827 interface."""

    # https://github.com/OpenZeppelin/zeppelin-solidity/blob/master/contracts/token/ERC20.sol

    assert tapas_token.call().name() == "TAPAS"
    assert tapas_token.call().symbol() == "TAP"
    assert tapas_token.call().decimals() == 18
    assert tapas_token.call().balanceOf(zero_address) == 0
    assert tapas_token.call().allowance(token_owner, zero_address) == 0

    # Event
    # We follow OpenZeppelin - in the ERO20 issue names are _from, _to, _value
    transfer = tapas_token._find_matching_event_abi("Transfer", ["from", "to", "value"])
    assert transfer

    approval = tapas_token._find_matching_event_abi("Approval", ["owner", "spender", "value"])
    assert approval


def test_tapas_transfer(chain, tapas_token, team_multisig, zero_address, customer):
    """Basic ERC-20 Transfer"""

    # https://github.com/OpenZeppelin/zeppelin-solidity/blob/master/contracts/token/ERC20.sol

    check_gas(chain, tapas_token.transact({"from": team_multisig}).transfer(customer, 100), gaslimit=140000)
    assert tapas_token.call().balanceOf(customer) == 100
    assert tapas_token.call().balanceOf(zero_address) == 0
    assert tapas_token.call().balanceAt(customer, 1) == 0
    assert tapas_token.call().balanceAt(customer, 999999) == 100

def test_tapas_transfer_stresstest(chain, tapas_token, team_multisig, zero_address, customer):
    """Basic ERC-20 Transfer"""

    # Feel free to raise the number of iterations according to your needs:
    # (These were run with fixed y = 1)
    # After 3 iterations, balanceAt() takes      25,177 gas each
    # After 3,000 iterations, balanceAt() takes  37,224 gas each
    # After 10,000 iterations, balanceAt() takes 39,780 gas each
    # Randomized 3,000 iterations (current) took 37,284 gas per transaction
    for x in range(3):
        check_gas(chain, tapas_token.transact({"from": team_multisig}).transfer(customer, 100))
        assert tapas_token.call().balanceOf(customer) == 100
        assert tapas_token.call().balanceOf(zero_address) == 0
        check_gas(chain, tapas_token.transact({"from": customer}).transfer(team_multisig, 100))
        y = 1+randint(0, x)
        check_gas(chain, tapas_token.transact().balanceAt(customer, y), tag=str(y))
        assert tapas_token.call().balanceOf(customer) == 0