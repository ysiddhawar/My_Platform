import sys
sys.path.insert(0, '.')

from models.trade import Trade

# Real EA payload from the archive
payload = {
    "trade_id": "mt5_548474767",
    "account_id": "dd38e1db-2a2a-4c34-9a65-38128d00d0b3",
    "broker_id": "MT5",
    "symbol": "EURUSD",
    "market_type": "forex",
    "side": "sell",
    "strategy_tag": "MT5 Historical Sync",
    "setup_name": "MT5 Historical Sync",
    "entry_price": 1.17508,
    "entry_time": "2026.05.06 20:33:21",
    "quantity": 0.03,
    "lot_size": 1.0,
    "leverage_used": 1.0,
    "stop_loss_at_entry": 1.17634,
    "target_at_entry": 1.17327,
    "swaps": 0.0,
    "metadata": {
        "source": "mt5_live_sync",
        "platform_name": "mt5",
        "position_id": "548474767"
    }
}

try:
    trade = Trade.from_dict(payload)
    print("SUCCESS: Trade created")
    print(f"  trade_id: {trade.trade_id}")
    print(f"  account_id: {trade.account_id}")
    print(f"  symbol: {trade.symbol}")
    print(f"  entry_price: {trade.entry_price}")
    d = trade.to_dict()
    print(f"  to_dict keys: {list(d.keys())[:10]}...")
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
