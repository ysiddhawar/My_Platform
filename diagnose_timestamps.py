import json, sqlite3, os
from datetime import datetime

# 1. Read raw MT5 archived files
archive = '/Users/apple/Library/Application Support/net.metaquotes.wine.metatrader5/drive_c/users/user/AppData/Roaming/MetaQuotes/Terminal/Common/Files/MyPlatform/archive'

# Find a mix of fill and close files
files_to_check = sorted(
    [f for f in os.listdir(archive) if 'fill' in f or 'close' in f]
)[:6]

print("=" * 70)
print("RAW MT5 ARCHIVED EVENT FILES")
print("=" * 70)
for fname in files_to_check:
    path = os.path.join(archive, fname)
    content = json.loads(open(path, 'r').read())
    print(f"\n--- {fname} ---")
    print(json.dumps(content, indent=2))

print("\n" + "=" * 70)
print("STORED TRADES IN DB (for comparison)")
print("=" * 70)

# 2. Check trades in DB - find ones matching MT5 file patterns
conn = sqlite3.connect('api_trade_store.db')
conn.row_factory = sqlite3.Row

# Check the MT5 account's latest 5 closed trades
rows = conn.execute(
    "SELECT trade_id, symbol, entry_data, exit_data, created_at, updated_at, account_id "
    "FROM trades WHERE account_id = 'dd38e1db-2a2a-4c34-9a65-38128d00d0b3' "
    "AND is_closed = 1 ORDER BY created_at DESC LIMIT 5"
).fetchall()

print("\n5 Most Recent Closed Trades (MT5 Account):")
for r in rows:
    entry_data = json.loads(r['entry_data']) if r['entry_data'] else {}
    exit_data = json.loads(r['exit_data']) if r['exit_data'] else {}
    entry_time = entry_data.get('entry_time', 'N/A')
    exit_time = exit_data.get('exit_time', 'N/A')
    print(f"  {r['trade_id'][:25]:25s} {r['symbol']:8s}")
    print(f"    entry_time: {entry_time}")
    print(f"    exit_time:  {exit_time}")

    if entry_time != 'N/A' and exit_time != 'N/A':
        try:
            t1 = datetime.fromisoformat(entry_time.replace('Z','+00:00'))
            t2 = datetime.fromisoformat(exit_time.replace('Z','+00:00'))
            diff = (t2 - t1).total_seconds() / 60.0
            print(f"    hold_time:  {diff:.2f} minutes ({round(diff)}m)")
        except Exception as e:
            print(f"    hold_time:  ERROR {e}")
    print()

# 3. Check DEFAULT account for comparison
print("-" * 50)
rows_default = conn.execute(
    "SELECT trade_id, symbol, entry_data, exit_data FROM trades WHERE account_id = 'DEFAULT' AND is_closed = 1 LIMIT 3"
).fetchall()
print("3 Closed Trades from DEFAULT Account:")
for r in rows_default:
    entry_data = json.loads(r['entry_data']) if r['entry_data'] else {}
    exit_data = json.loads(r['exit_data']) if r['exit_data'] else {}
    print(f"  {r['trade_id'][:25]:25s} {r['symbol']:8s} entry={entry_data.get('entry_time','N/A')} exit={exit_data.get('exit_time','N/A')}")

# 4. Check if any open trades have a non-null exit_time
open_trades = conn.execute(
    "SELECT trade_id, exit_data, is_closed FROM trades WHERE is_closed = 0 LIMIT 5"
).fetchall()
print("\n5 Open Trades (checking exit_time):")
for r in open_trades:
    exit_data = json.loads(r['exit_data']) if r['exit_data'] else {}
    has_exit_time = 'exit_time' in exit_data and exit_data['exit_time'] is not None
    print(f"  {r['trade_id'][:25]:25s} is_closed={r['is_closed']} exit_data='{exit_data}' has_exit_time={has_exit_time}")

conn.close()