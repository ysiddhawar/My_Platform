import sqlite3
import json
from pathlib import Path

# 1. Check trade database
print("=== TRADE DATABASE ===")
conn = sqlite3.connect("trade_store.db")
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM trades WHERE account_id = 'dd38e1db-2a2a-4c34-9a65-38128d00d0b3'")
print(f"Yash trades: {cur.fetchone()[0]}")
cur.execute("SELECT COUNT(*) FROM trades")
print(f"Total trades (all accounts): {cur.fetchone()[0]}")
cur.execute("SELECT DISTINCT account_id FROM trades")
accounts = [r[0] for r in cur.fetchall()]
print(f"Accounts in trades: {accounts}")
conn.close()

# 2. Check inbox directory
print("\n=== INBOX ===")
inbox = Path("/Users/apple/Library/Application Support/net.metaquotes.wine.metatrader5/drive_c/users/user/AppData/Roaming/MetaQuotes/Terminal/Common/Files/MyPlatform/inbox")
pending = sorted(inbox.glob("*.json"))
print(f"Pending files: {len(pending)}")
if pending:
    for p in pending[:3]:
        print(f"  {p.name}")

# 3. Check archive directory  
print("\n=== ARCHIVE (recent non-account_state) ===")
archive = Path("/Users/apple/Library/Application Support/net.metaquotes.wine.metatrader5/drive_c/users/user/AppData/Roaming/MetaQuotes/Terminal/Common/Files/MyPlatform/archive")
recent = sorted(archive.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
trade_events = [p for p in recent if not p.name.startswith("account_state")]
print(f"Recent trade events: {len(trade_events)}")
if trade_events:
    for p in trade_events[:5]:
        print(f"  {p.name} ({p.stat().st_mtime})")

# 4. Check if backend is actually running and integration is alive
print("\n=== CHECKING RUNTIME ===")
import subprocess
result = subprocess.run(["curl", "-s", "-X", "POST", 
    "http://localhost:8000/api/v1/debug/reconcile-mt5",
    "-H", "Content-Type: application/json",
    "-H", "Authorization: Bearer test",
    "-d", '{"account_id":"dd38e1db-2a2a-4c34-9a65-38128d00d0b3"}'],
    capture_output=True, text=True, timeout=5)
print(f"HTTP Status: {result.returncode}")
print(f"Response: {result.stdout[:500]}")
if result.stderr:
    print(f"Error: {result.stderr[:500]}")