## MT5 Sync Bridge Contract

This MT5 integration is now sync-only.

MyPlatform does not open MT5 order tickets or render an MT5-side Position Sizer UI anymore. The MT5 bridge is responsible only for exporting trade data from MT5 into MyPlatform so the app stays up to date automatically.

### What the MT5 bridge should do

1. Export historical closed trades into MyPlatform during initial sync.
2. Export currently open positions into MyPlatform during initial sync.
3. Export future lifecycle events in near real time, including:
   - `TRADE_FILLED`
   - `TRADE_CLOSED`
   - `POSITION_MODIFIED`
   - `SCALE_IN`
   - `PARTIAL_CLOSE`
4. Write one JSON file per event into the configured `inbox` directory.
5. Move processed event files into the configured `archive` directory on the MyPlatform side.

### What MyPlatform does with these events

When the bridge is connected to an account:

- historical MT5 trades appear in Journal / Calendar / Dashboard
- open MT5 positions appear as open trades in the app
- future closes update the existing trade immediately
- stop-loss and target edits update the open trade in place
- scale-ins update the open trade quantity and cost basis
- partial closes create a partial-close record while keeping the parent trade open

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
- MyPlatform bridge folders used for sync:
  - `/Users/apple/Library/Application Support/net.metaquotes.wine.metatrader5/drive_c/users/user/AppData/Roaming/MetaQuotes/Terminal/Common/Files/MyPlatform/inbox`
  - `/Users/apple/Library/Application Support/net.metaquotes.wine.metatrader5/drive_c/users/user/AppData/Roaming/MetaQuotes/Terminal/Common/Files/MyPlatform/archive`

The EA source is installed at:

- `/Users/apple/Library/Application Support/net.metaquotes.wine.metatrader5/drive_c/Program Files/MetaTrader 5/MQL5/Experts/MyPlatform/MyPlatformBridgeEA.mq5`

### Compile note for the macOS Wine wrapper

The bundled Wine-backed MetaEditor process launches from the command line in this wrapper setup, but in testing it has been more reliable to compile from MetaEditor itself.

Recommended compile flow:

1. Open MT5 / MetaEditor normally.
2. Open `Experts/MyPlatform/MyPlatformBridgeEA.mq5`.
3. Compile from MetaEditor UI.
4. Confirm that `MyPlatformBridgeEA.ex5` appears next to the source file.

### Inbox event shape

MT5 should write one JSON file per event into the configured `inbox`.

Example:

```json
{
  "event_type": "POSITION_MODIFIED",
  "payload": {
    "trade_id": "mt5_12345678",
    "stop_loss_at_entry": 1.091,
    "target_at_entry": 1.104,
    "notes": "Updated in MT5",
    "metadata": {
      "source": "mt5_position_modify",
      "platform_name": "mt5",
      "position_id": "12345678"
    }
  }
}
```

Notes:

- `trade_id` should stay stable for the life of the MT5 position. This bridge uses the MT5 `position_id`.
- The bridge should continue writing future events even after historical sync has completed.
- MyPlatform treats the MT5 integration as the source of truth for trade lifecycle updates.
