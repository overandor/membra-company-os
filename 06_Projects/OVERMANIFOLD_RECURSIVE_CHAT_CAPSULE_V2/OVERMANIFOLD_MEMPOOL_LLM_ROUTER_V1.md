# OVERMANIFOLD_MEMPOOL_LLM_ROUTER_V1

## Core loop

```text
Public mempool / block stream
→ watcher
→ transaction decoder
→ event classifier
→ liquidity/oracle/KPI engine
→ LLM reviewer
→ action planner
→ deterministic risk gate
→ transaction builder
→ human / wallet / policy signer
→ relay / RPC / private route
→ confirmation worker
→ Merkle receipt
```

## Product doctrine

Every chain becomes a sensor network. Every transaction becomes a signal. Every mempool becomes a forecast layer. Every confirmation becomes a clock. Every routed action becomes provenance.

## LLM authority boundary

The LLM may classify, explain, score, and recommend. It may not sign or submit transactions. Any action that writes state, notifies a third party, bridges funds, changes oracle state, submits a transaction, or executes arbitrage must pass through a deterministic policy engine and authorized signer.

## Action classes

Safe: notify locally, update KPI, create Merkle leaf, simulate route, update local observation, queue user-owned transaction.

Restricted: submit transaction, bridge assets, rebalance treasury, execute arbitrage, update public oracle, send SMS/email, update GitHub/IPFS.

Forbidden: sandwich attacks, predatory frontrunning, liquidity spoofing, oracle manipulation, exploit execution, draining unowned funds.

## Formula

```text
NextAction = PolicyGate(
  LLMReview(
    MempoolObservation,
    LiquidityState,
    OracleState,
    WalletIntent,
    RiskRules
  )
)
```

## Invariant

```text
LLM may recommend.
Policy may permit.
Wallet may sign.
Chain may settle.
Merkle root records.
```
