from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.server.api_registry import api_registry
from api.server.security import ensure_account_access, get_current_user


router = APIRouter(prefix="/debug", tags=["debug"])


class ReconcileRequest(BaseModel):
    account_id: str = "DEFAULT"


@router.post("/reconcile-mt5")
def reconcile_mt5(request: ReconcileRequest, user: dict = Depends(get_current_user)):
    """
    Debug endpoint that reconciles MT5-sourced trade data.

    Returns:
      - total_trade_count
      - open_count / closed_count
      - total_net_pnl (sum of net_pnl across all trades)
      - corrupted_trades (is_closed=True but exit_price is None)
      - pending_inbox_files (unprocessed JSON files in the inbox directory)
    """
    try:
        ensure_account_access(user, request.account_id)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    # --- 1 & 2. Fetch all trades, count open vs closed ---
    trades = api_registry.trade_repository.get_trades_by_account(
        account_id=request.account_id,
        closed_only=None,  # all trades
    )

    open_trades = []
    closed_trades = []
    total_net_pnl = 0.0
    corrupted_trades = []

    for trade in trades:
        d = trade.to_dict()
        is_closed = d.get("is_closed", False)
        exit_price = d.get("exit_price")
        net_pnl = d.get("net_pnl") or 0.0

        if is_closed:
            closed_trades.append(d)
            if exit_price is None:
                corrupted_trades.append(
                    {
                        "trade_id": d.get("trade_id"),
                        "symbol": d.get("symbol"),
                        "side": d.get("side"),
                        "entry_price": d.get("entry_price"),
                        "exit_price": exit_price,
                        "net_pnl": net_pnl,
                        "error": "is_closed=True but exit_price is None",
                    }
                )
        else:
            open_trades.append(d)

        total_net_pnl += net_pnl

    # --- 5. Unprocessed inbox files ---
    inbox_dir = None
    pending_inbox_files = []
    try:
        integrations = api_registry.broker_integration_service.list_integrations()["integrations"]
        mt5_config = next(
            (
                item
                for item in integrations
                if item.get("account_id") == request.account_id
                and "mt5" in str(item.get("adapter_type", "")).lower()
            ),
            None,
        )
        if mt5_config and mt5_config.get("inbox_dir"):
            inbox_dir = mt5_config["inbox_dir"]
            inbox_path = Path(inbox_dir).expanduser()
            if inbox_path.is_dir():
                pending_inbox_files = sorted(
                    [
                        {"filename": p.name, "size_bytes": p.stat().st_size, "modified_at": p.stat().st_mtime}
                        for p in inbox_path.glob("*.json")
                    ],
                    key=lambda f: f["modified_at"],
                )
    except Exception:
        # If the integration service or inbox is unavailable, report that
        pending_inbox_files = []

    return {
        "account_id": request.account_id,
        "summary": {
            "total_trade_count": len(trades),
            "open_count": len(open_trades),
            "closed_count": len(closed_trades),
            "total_net_pnl": round(total_net_pnl, 6),
        },
        "corrupted_trades": corrupted_trades,
        "inbox": {
            "inbox_dir": inbox_dir,
            "pending_file_count": len(pending_inbox_files),
            "pending_files": pending_inbox_files[:50],  # cap at 50 to avoid huge responses
        },
        "hint": "Use /api/v1/journal/trades?account_id=<id>&closed_only=true to export all closed trades for comparison.",
    }