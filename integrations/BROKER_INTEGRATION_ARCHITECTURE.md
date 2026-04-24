## Broker Integration Architecture

This document captures the shared requirements for every broker integration after MT5.

### Product requirement

For any supported broker, the integration should aim to provide:

1. account linking
2. automatic ingestion of:
   - historical trades
   - future trades
   - open positions
3. broker-side trade assistant experience that mirrors the Position Sizer design as closely as the broker platform allows
4. actual execution remaining inside the broker platform unless compliance/legal strategy changes later

### Shared contract

Each broker adapter should implement three layers:

1. `Link layer`
   - connect a broker account or bridge to MyPlatform
   - expose connection health
   - expose last successful sync

2. `Sync layer`
   - import historical trades
   - import open positions
   - stream future lifecycle events:
     - open / fill
     - close
     - modification
     - cancellation
     - partial close
     - scale in / scale out

3. `Assistant layer`
   - receive prepared Position Sizer tickets from MyPlatform
   - display planned trade context on the broker side
   - preserve manual broker-side execution

### Canonical prepared ticket fields

Every broker assistant should understand a normalized prepared ticket that includes at least:

- `client_ticket_id`
- `account_id`
- `broker_id`
- `symbol`
- `market_type`
- `side`
- `order_type`
- `entry_price`
- `stop_loss_price`
- `target_price`
- `minimum_target_price`
- `quantity`
- `lot_size`
- `leverage_used`
- `strategy_setup`
- `probability_bucket`
- `selected_checklist`
- `notes`

### Canonical lifecycle events

Every broker sync bridge should be able to emit normalized events that MyPlatform can ingest:

- `TRADE_FILLED`
- `TRADE_CLOSED`

Additional events we should support progressively:

- `ORDER_UPDATED`
- `ORDER_CANCELLED`
- `POSITION_MODIFIED`
- `PARTIAL_CLOSE`
- `SYNC_HEARTBEAT`

### Identity and matching

Every broker integration should provide stable IDs for:

- account
- position
- order
- deal/fill

Whenever MyPlatform sends a prepared ticket, the broker bridge should echo back `client_ticket_id` when possible so the platform can merge:

- planned setup/checklist/probability context
with
- actual execution prices/times

### Broker-specific constraint

Not every broker platform exposes the same UI automation capabilities.

So the assistant layer has three acceptable capability levels:

1. `Native ticket prefill`
   - best case
   - broker allows opening/prefilling its own order dialog

2. `Broker-side assistant panel`
   - acceptable fallback
   - broker-side plugin/addon/panel displays entry/SL/TP/min target/setup/checklist context
   - trader still confirms manually inside the broker platform

3. `External desktop bridge`
   - only when broker platform APIs are too limited
   - desktop automation assists with focus/prefill behavior

### Current MT5 status

MT5 currently fits the second model first:

- filesystem bridge
- broker-side EA assistant panel
- manual confirmation inside MT5

If later testing shows native MT5 ticket automation is not viable, this remains the supported route for MT5.
