## MT5 Bridge Contract

This bridge now supports two filesystem channels:

- `inbox`: MT5 -> MyPlatform broker events
- `outbox`: MyPlatform -> MT5 prepared order ticket commands

Files in this folder:

- [MyPlatformBridgeEA.mq5](/Users/apple/Desktop/My_Platform/integrations/mt5/MyPlatformBridgeEA.mq5): the current MT5 EA bridge implementation
- [MyPlatformBridgeEA_TEMPLATE.mq5](/Users/apple/Desktop/My_Platform/integrations/mt5/MyPlatformBridgeEA_TEMPLATE.mq5): lightweight contract stub/reference

### What the current implementation supports

1. MyPlatform writes a prepared order ticket JSON file into the configured `outbox` when the user clicks `Proceed`.
2. An MT5-side bridge EA/script can read that file and apply the planned values inside MT5.
3. MT5 writes `TRADE_FILLED` and `TRADE_CLOSED` event files into the configured `inbox`.
4. MyPlatform ingests those real broker events and stores the actual execution prices/times in the trade snapshot.

### macOS MT5 wrapper paths discovered on this machine

This installed MT5 build uses the MetaQuotes macOS wrapper with Wine. On this machine the active paths are:

- MT5 app bundle:
  - `/Applications/MetaTrader 5.app`
- MT5 program root:
  - `/Users/apple/Library/Application Support/net.metaquotes.wine.metatrader5/drive_c/Program Files/MetaTrader 5`
- Experts folder:
  - `/Users/apple/Library/Application Support/net.metaquotes.wine.metatrader5/drive_c/Program Files/MetaTrader 5/MQL5/Experts`
- Shared Common Files root:
  - `/Users/apple/Library/Application Support/net.metaquotes.wine.metatrader5/drive_c/users/user/AppData/Roaming/MetaQuotes/Terminal/Common/Files`
- MyPlatform bridge folders created for testing:
  - `/Users/apple/Library/Application Support/net.metaquotes.wine.metatrader5/drive_c/users/user/AppData/Roaming/MetaQuotes/Terminal/Common/Files/MyPlatform/inbox`
  - `/Users/apple/Library/Application Support/net.metaquotes.wine.metatrader5/drive_c/users/user/AppData/Roaming/MetaQuotes/Terminal/Common/Files/MyPlatform/outbox`
  - `/Users/apple/Library/Application Support/net.metaquotes.wine.metatrader5/drive_c/users/user/AppData/Roaming/MetaQuotes/Terminal/Common/Files/MyPlatform/archive`

The bridge EA source has been copied to:

- `/Users/apple/Library/Application Support/net.metaquotes.wine.metatrader5/drive_c/Program Files/MetaTrader 5/MQL5/Experts/MyPlatform/MyPlatformBridgeEA.mq5`

### Compile note for the macOS Wine wrapper

The bundled Wine-backed MetaEditor process launches from the command line in this wrapper setup, but in testing it did not emit a source-side `.log` or compiled `.ex5` artifact when invoked headlessly.

Because of that, the reliable next step on this macOS install is:

1. Open MT5 / MetaEditor normally.
2. Open `Experts/MyPlatform/MyPlatformBridgeEA.mq5`.
3. Compile from MetaEditor UI.
4. Confirm that `MyPlatformBridgeEA.ex5` appears next to the source file.

Once desktop-control permission is available, this can be verified directly in the terminal UI workflow as well.

### Important MT5 limitation

The native MT5 manual order dialog is not exposed through a stable supported MQL API for direct programmatic prefill/open behavior.

Because of that, the contract here is:

- MyPlatform prepares and exports the ticket
- the MT5 bridge EA/script consumes it
- the EA/script can render the planned levels on chart, in an EA panel, or use a platform-specific workflow to assist the trader
- the actual trade must still be confirmed and executed inside MT5

The EA therefore acts as an on-chart assistant panel plus sync bridge, not as a hidden order router.

If you later add a desktop automation layer outside MT5, it can reuse the exact same `outbox` command files.

### Outbox command shape

```json
{
  "command_type": "OPEN_ORDER_TICKET",
  "bridge_contract_version": "2026-04-17",
  "submitted_at": "2026-04-17T12:34:56.000000+00:00",
  "payload": {
    "client_ticket_id": "uuid",
    "prepared_ticket_id": "uuid",
    "prepared_at": "2026-04-17T12:34:55.000000+00:00",
    "route_mode": "prefill_only",
    "account_id": "ACCOUNT_ID",
    "broker_id": "MT5",
    "symbol": "EURUSD",
    "market_type": "forex",
    "side": "buy",
    "order_type": "market",
    "entry_price": 1.1004,
    "planned_entry_price": 1.1004,
    "stop_loss_price": 1.095,
    "stop_loss_at_entry": 1.095,
    "target_price": 1.11,
    "target_at_entry": 1.11,
    "quantity": 10000,
    "lot_size": 1.0,
    "leverage_used": 10.0,
    "strategy_tag": "London Breakout",
    "strategy_setup": "London Breakout",
    "setup_name": "London Breakout",
    "probability_bucket": "60%",
    "selected_checklist": ["Breakout confirmed", "Volume aligned"],
    "checklist_before": ["Breakout confirmed", "Volume aligned"],
    "notes": "Prepared from position sizer",
    "pre_trade_capture": {},
    "line_history": [],
    "minimum_target_price": 1.108,
    "minimum_target_reward": 250,
    "metadata": {}
  }
}
```

### Inbox event shape

MT5 should write one JSON file per event into the configured `inbox`.

Supported event types:

- `TRADE_FILLED`
- `TRADE_CLOSED`

Recommended `TRADE_FILLED` payload fields:

```json
{
  "event_type": "TRADE_FILLED",
  "payload": {
    "client_ticket_id": "uuid-from-outbox",
    "trade_id": "broker-ticket-or-position-id",
    "broker_id": "MT5",
    "symbol": "EURUSD",
    "market_type": "forex",
    "side": "buy",
    "entry_price": 1.1006,
    "entry_time": "2026-04-17T12:35:10Z",
    "quantity": 10000,
    "lot_size": 1.0,
    "leverage_used": 10.0,
    "stop_loss_at_entry": 1.095,
    "target_at_entry": 1.11,
    "entry_spread": 0.0001,
    "slippage_at_entry": 0.4,
    "fees": 0.0,
    "commission": 4.0,
    "swaps": 0.0,
    "metadata": {
      "platform_name": "mt5"
    }
  }
}
```

`client_ticket_id` is the handshake key that lets MyPlatform merge the prepared strategy/setup/checklist context with the real broker fill data.
