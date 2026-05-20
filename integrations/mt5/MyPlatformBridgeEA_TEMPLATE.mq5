// Template contract for an MT5 sync bridge EA.
//
// Purpose:
// - export historical closed trades on init
// - export currently open positions on init
// - emit future TRADE_FILLED / TRADE_CLOSED / POSITION_MODIFIED / SCALE_IN / PARTIAL_CLOSE events
// - write one JSON file per event into Common\Files\MyPlatform\inbox
//
// This template is intentionally minimal. See MyPlatformBridgeEA.mq5 for the concrete implementation.

#property strict

input string MyPlatformInbox = "MyPlatform\\inbox";
input string BridgeAccountId = "DEFAULT";
input int PollIntervalSeconds = 1;

int OnInit()
  {
   // 1. Optionally sync historical trades.
   // 2. Optionally sync currently open positions.
   // 3. Build an in-memory snapshot of current MT5 positions.
   // 4. Start a timer to detect stop-loss / take-profit edits.
   EventSetTimer(MathMax(PollIntervalSeconds,1));
   return(INIT_SUCCEEDED);
  }

void OnDeinit(const int reason)
  {
   EventKillTimer();
  }

void OnTimer()
  {
   // Compare current MT5 positions against the cached snapshot.
   // Emit POSITION_MODIFIED when SL/TP changes.
   // Refresh the snapshot.
  }

void OnTradeTransaction(const MqlTradeTransaction &trans,
                        const MqlTradeRequest &request,
                        const MqlTradeResult &result)
  {
   // Inspect new deals and convert them into normalized MyPlatform events.
   // Typical mappings:
   // - new position -> TRADE_FILLED
   // - added volume -> SCALE_IN
   // - reduced volume -> PARTIAL_CLOSE
   // - zero remaining volume -> TRADE_CLOSED
  }

// Practical notes:
// - Use FILE_COMMON so the EA can write into MetaTrader's shared Common Files area.
// - Keep inbox and archive separate.
// - Use a stable trade_id based on MT5 position id so lifecycle updates target the same trade in MyPlatform.
