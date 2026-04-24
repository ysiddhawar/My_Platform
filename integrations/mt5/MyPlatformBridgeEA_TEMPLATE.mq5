// Template contract for an MT5 bridge EA.
// This file documents the intended bridge workflow. It is not wired into the
// web build and may require project-specific JSON parsing helpers before use.

#property strict

input string MyPlatformOutbox = "MyPlatform\\outbox";
input string MyPlatformInbox = "MyPlatform\\inbox";

void OnTick()
{
   // 1. Poll the outbox for OPEN_ORDER_TICKET command files.
   // 2. Parse the payload and surface the planned entry / stop / target inside MT5.
   // 3. Keep the final trade confirmation inside MT5.
}

void OnTradeTransaction(const MqlTradeTransaction& trans,
                        const MqlTradeRequest& request,
                        const MqlTradeResult& result)
{
   // When MT5 confirms a fill or close, write a TRADE_FILLED / TRADE_CLOSED
   // JSON file into MyPlatformInbox.
   //
   // The payload must echo client_ticket_id when available so MyPlatform can
   // merge the prepared context with the real broker execution values.
}

// Suggested implementation notes:
// - Use a shared/common files location that both MT5 and MyPlatform can access.
// - Keep inbox and outbox separate.
// - Move processed outbox command files into an EA-side archive folder after read.
// - Emit one JSON file per broker event.
