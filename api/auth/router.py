from __future__ import annotations

import random
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from api.server.api_registry import api_registry
from api.server.security import ensure_admin, get_current_session, get_current_user
from models.account import Account
from models.auth_user import AuthUser
from models.missed_opportunity import MissedOpportunity
from models.strategy import Strategy
from models.trade import Trade
from models.trading_platform_session import TradingPlatformSession


router = APIRouter(prefix="/auth", tags=["auth"])


class BootstrapAdminRequest(BaseModel):
    username: str
    password: str
    account_ids: List[str] = Field(default_factory=lambda: ["*"])


class CreateUserRequest(BaseModel):
    username: str
    password: str
    account_ids: List[str] = Field(default_factory=list)
    roles: List[str] = Field(default_factory=lambda: ["user"])
    metadata: Dict[str, Any] = Field(default_factory=dict)


class LoginRequest(BaseModel):
    username: str
    password: str


class DemoSessionRequest(BaseModel):
    username: str = "demo_admin"
    password: str = "demo_pass_123"
    account_id: str = "DEFAULT"
    broker_id: str = "BROKER"
    account_name: str = "Demo Workspace"
    initial_balance: float = 100000.0


class DemoDatasetRequest(BaseModel):
    account_id: str = "DEFAULT"
    broker_id: str = "BROKER"
    account_name: str = "Prototype Workspace"
    initial_balance: float = 100000.0
    timezone_name: str = "Asia/Kolkata"
    trade_count: int = Field(default=300, ge=100, le=300)


@router.post("/bootstrap-admin")
def bootstrap_admin(request: BootstrapAdminRequest):
    try:
        return api_registry.auth_service.bootstrap_admin(
            username=request.username,
            password=request.password,
            account_ids=request.account_ids,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/demo-session")
def demo_session(request: DemoSessionRequest):
    try:
        account = api_registry.account_repository.get(request.account_id)
        if account is None:
            account = Account(
                broker_id=request.broker_id,
                account_name=request.account_name,
                initial_balance=request.initial_balance,
                risk_level="survival",
            )
            account._account_id = request.account_id
            api_registry.account_repository.save(account)

        normalized_username = request.username.strip().lower()
        user = api_registry.user_repository.get_by_username(normalized_username)
        if user is None:
            api_registry.auth_service.create_user(
                username=normalized_username,
                password=request.password,
                account_ids=["*"],
                roles=["admin"],
                metadata={"demo_user": True},
            )
        else:
            # Reset demo credentials deterministically so the prototype can always log in.
            import secrets
            salt = secrets.token_hex(16)
            password_hash = api_registry.auth_service._hash_password(request.password, salt)
            updated_user = replace(
                user,
                password_hash=password_hash,
                password_salt=salt,
                account_ids=["*"],
                roles=["admin"],
                is_active=True,
                metadata={**dict(user.metadata), "demo_user": True},
                updated_at=datetime.now(timezone.utc),
            )
            api_registry.user_repository.save(updated_user)

        return api_registry.auth_service.login(
            username=normalized_username,
            password=request.password,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/seed-demo-dataset")
def seed_demo_dataset(
    request: DemoDatasetRequest,
    user: Dict[str, Any] = Depends(get_current_user),
):
    try:
        ensure_admin(user)
        _ensure_demo_account(request)
        _ensure_demo_strategies()
        _clear_demo_account_data(request.account_id)
        result = _seed_demo_account_dataset(request)
        day_summaries = api_registry.calendar_aggregation_engine.rebuild_for_account(request.account_id)
        return {**result, "day_summaries": day_summaries}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/users")
def create_user(
    request: CreateUserRequest,
    user: Dict[str, Any] = Depends(get_current_user),
):
    try:
        ensure_admin(user)
        return api_registry.auth_service.create_user(
            username=request.username,
            password=request.password,
            account_ids=request.account_ids,
            roles=request.roles,
            metadata=request.metadata,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/login")
def login(request: LoginRequest):
    try:
        return api_registry.auth_service.login(
            username=request.username,
            password=request.password,
        )
    except Exception as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@router.get("/me")
def me(
    user: Dict[str, Any] = Depends(get_current_user),
    session: Dict[str, Any] = Depends(get_current_session),
):
    return {"user": user, "session": session}


@router.post("/logout")
def logout(
    request: Request,
    session: Dict[str, Any] = Depends(get_current_session),
):
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.split(" ", 1)[1].strip() if " " in auth_header else session["session_token"]
    try:
        return api_registry.auth_service.logout(token)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _ensure_demo_account(request: DemoDatasetRequest) -> None:
    account = api_registry.account_repository.get(request.account_id)
    if account is not None:
        return
    account = Account(
        broker_id=request.broker_id,
        account_name=request.account_name,
        initial_balance=request.initial_balance,
        risk_level="survival",
    )
    account._account_id = request.account_id
    api_registry.account_repository.save(account)


def _ensure_demo_strategies() -> None:
    strategies = [
        Strategy(
            name="Breakout Continuation",
            description="Momentum continuation after consolidation break.",
            market_types=["stock", "forex", "crypto", "futures"],
            checklist_items=["Trend aligned", "Level marked", "Risk defined", "Volume confirmation"],
            mandatory_checklist_items=["Trend aligned", "Risk defined"],
            default_risk_percent=1.0,
            max_risk_percent=2.0,
        ),
        Strategy(
            name="Pullback Reclaim",
            description="Pullback into support or value area with reclaim.",
            market_types=["stock", "forex", "crypto", "futures"],
            checklist_items=["Context valid", "Reclaim confirmed", "Stop placed", "Target mapped"],
            mandatory_checklist_items=["Context valid", "Stop placed"],
            default_risk_percent=0.8,
            max_risk_percent=1.5,
        ),
        Strategy(
            name="Range Expansion",
            description="Intraday range expansion after compression.",
            market_types=["stock", "forex", "crypto", "futures"],
            checklist_items=["Compression identified", "Catalyst present", "Risk acceptable", "Liquidity sufficient"],
            mandatory_checklist_items=["Compression identified", "Risk acceptable"],
            default_risk_percent=1.0,
            max_risk_percent=2.0,
        ),
        Strategy(
            name="Mean Reversion Fade",
            description="Fade stretched move back into mean.",
            market_types=["stock", "forex", "crypto"],
            checklist_items=["Extension confirmed", "Mean level mapped", "Risk defined", "Time window valid"],
            mandatory_checklist_items=["Extension confirmed", "Risk defined"],
            default_risk_percent=0.7,
            max_risk_percent=1.2,
        ),
    ]
    existing_names = {item["name"] for item in api_registry.strategy_repository.list_strategies()}
    for strategy in strategies:
        if strategy.name not in existing_names:
            api_registry.strategy_repository.save_strategy(strategy)


def _clear_demo_account_data(account_id: str) -> None:
    api_registry.attachment_repository.delete_by_account(account_id)
    api_registry.note_repository.delete_by_account(account_id)
    api_registry.rating_repository.delete_by_account(account_id)
    api_registry.tag_repository.delete_by_account(account_id)
    api_registry.missed_opportunity_repository.delete_by_account(account_id)
    api_registry.trading_platform_session_repository.delete_by_account(account_id)
    api_registry.trade_repository.delete_by_account(account_id)
    api_registry.calendar_repository.delete_by_account(account_id)


def _seed_demo_account_dataset(request: DemoDatasetRequest) -> Dict[str, Any]:
    rng = random.Random(7)
    strategies = api_registry.strategy_repository.list_strategies(active_only=True)
    strategies = strategies[:4]
    symbols_by_market = {
        "stock": ["AAPL", "NVDA", "MSFT", "TSLA", "AMZN", "META", "AMD", "NFLX"],
        "forex": ["EUR/USD", "GBP/USD", "USD/JPY", "XAU/USD", "AUD/USD"],
        "crypto": ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT"],
        "futures": ["ES1!", "NQ1!", "GC1!", "CL1!", "YM1!"],
    }
    base_prices = {
        "AAPL": 190.0,
        "NVDA": 905.0,
        "MSFT": 415.0,
        "TSLA": 225.0,
        "AMZN": 176.0,
        "META": 505.0,
        "AMD": 185.0,
        "NFLX": 630.0,
        "EUR/USD": 1.086,
        "GBP/USD": 1.273,
        "USD/JPY": 148.4,
        "XAU/USD": 2195.0,
        "AUD/USD": 0.661,
        "BTCUSDT": 68250.0,
        "ETHUSDT": 3820.0,
        "SOLUSDT": 164.0,
        "BNBUSDT": 588.0,
        "XRPUSDT": 0.71,
        "ES1!": 5210.0,
        "NQ1!": 18150.0,
        "GC1!": 2198.0,
        "CL1!": 78.0,
        "YM1!": 39200.0,
    }

    now_utc = datetime.now(timezone.utc)
    today_local = now_utc.astimezone(timezone(timedelta(hours=5, minutes=30)))
    trade_count = request.trade_count
    open_trade_count = max(12, trade_count // 10)
    closed_trade_count = trade_count - open_trade_count

    session_records: list[TradingPlatformSession] = []
    closed_sessions_by_day: dict[str, list[TradingPlatformSession]] = {}
    account_balance = request.initial_balance

    for day_offset in range(75):
        local_day = (today_local - timedelta(days=(74 - day_offset))).date()
        if local_day > today_local.date():
            continue
        daily_session_count = rng.randint(0, 3)
        for session_index in range(daily_session_count):
            start_hour = rng.choice([7, 9, 11, 13, 15, 19, 21])
            start_minute = rng.choice([0, 10, 20, 30, 40, 50])
            duration_minutes = rng.randint(45, 210)
            opened_local = datetime(
                local_day.year,
                local_day.month,
                local_day.day,
                start_hour,
                start_minute,
                tzinfo=timezone(timedelta(hours=5, minutes=30)),
            )
            closed_local = opened_local + timedelta(minutes=duration_minutes)
            session = TradingPlatformSession(
                account_id=request.account_id,
                broker_id=request.broker_id,
                platform_name="MT5 Demo",
                opened_at=opened_local.astimezone(timezone.utc),
                closed_at=closed_local.astimezone(timezone.utc),
                timezone_name=request.timezone_name,
                metadata={"seeded": True, "session_index": session_index},
            )
            session_records.append(session)
            closed_sessions_by_day.setdefault(local_day.isoformat(), []).append(session)

    open_session_start = (
        today_local.replace(hour=14, minute=15, second=0, microsecond=0).astimezone(timezone.utc)
    )
    open_session = TradingPlatformSession(
        account_id=request.account_id,
        broker_id=request.broker_id,
        platform_name="MT5 Demo",
        opened_at=open_session_start,
        closed_at=None,
        timezone_name=request.timezone_name,
        metadata={"seeded": True, "live": True},
    )
    session_records.append(open_session)

    for session in session_records:
        api_registry.trading_platform_session_repository.save_session(session)

    closed_session_pool = [session for sessions in closed_sessions_by_day.values() for session in sessions]

    for index in range(closed_trade_count):
        session = closed_session_pool[index % len(closed_session_pool)]
        account_balance = _save_demo_trade(
            request=request,
            rng=rng,
            strategies=strategies,
            symbols_by_market=symbols_by_market,
            base_prices=base_prices,
            account_balance=account_balance,
            session=session,
            trade_index=index,
            is_open=False,
        )

    for index in range(open_trade_count):
        account_balance = _save_demo_trade(
            request=request,
            rng=rng,
            strategies=strategies,
            symbols_by_market=symbols_by_market,
            base_prices=base_prices,
            account_balance=account_balance,
            session=open_session,
            trade_index=closed_trade_count + index,
            is_open=True,
        )

    missed_count = max(35, trade_count // 8)
    for item_index in range(missed_count):
        local_day = (today_local - timedelta(days=rng.randint(0, 60))).date()
        observed_local = datetime(
            local_day.year,
            local_day.month,
            local_day.day,
            rng.choice([8, 10, 11, 14, 15, 19, 21]),
            rng.choice([5, 11, 17, 23, 31, 42, 53]),
            tzinfo=timezone(timedelta(hours=5, minutes=30)),
        )
        market_type = rng.choice(list(symbols_by_market))
        symbol = rng.choice(symbols_by_market[market_type])
        strategy = rng.choice(strategies)
        entry_price = _price_with_noise(base_prices[symbol], rng, market_type)
        stop_loss = round(entry_price * (1 - _risk_percent_for_market(market_type, rng)), 5)
        target = round(entry_price * (1 + _reward_percent_for_market(market_type, rng)), 5)
        exit_price = round(target * rng.uniform(0.985, 1.015), 5)
        opportunity = MissedOpportunity(
            account_id=request.account_id,
            broker_id=request.broker_id,
            symbol=symbol,
            market_type=market_type,
            side=rng.choice(["buy", "sell"]),
            strategy_name=strategy["name"],
            probability_bucket=rng.choice(["<40%", "40%", "50%", "60%", ">60%"]),
            entry_price=entry_price,
            stop_loss_price=stop_loss,
            target_price=target,
            minimum_target_price=round((entry_price + target) / 2, 5),
            observed_at=observed_local.astimezone(timezone.utc),
            timezone_name=request.timezone_name,
            exit_price=exit_price,
            exit_at=(observed_local + timedelta(minutes=rng.randint(30, 220))).astimezone(timezone.utc),
            exit_reason=rng.choice(["not_taken", "hesitation", "session_end", "missed_alert"]),
            checklist_items=rng.sample(strategy["checklist_items"], k=rng.randint(1, len(strategy["checklist_items"]))),
            notes=rng.choice([
                "Saw the setup but skipped because risk felt too wide.",
                "Marked the trade late after price already expanded.",
                "Missed due to platform distraction.",
                "Valid setup, but confidence dropped after the first pullback.",
            ]),
            metadata={"seeded": True},
        )
        api_registry.missed_opportunity_repository.save_opportunity(opportunity)

    return {
        "status": "ok",
        "detail": f"Replaced demo data with {trade_count} seeded trades across multiple markets.",
        "trade_count": trade_count,
        "missed_opportunity_count": missed_count,
        "session_count": len(session_records),
    }


def _save_demo_trade(
    *,
    request: DemoDatasetRequest,
    rng: random.Random,
    strategies: List[Dict[str, Any]],
    symbols_by_market: Dict[str, List[str]],
    base_prices: Dict[str, float],
    account_balance: float,
    session: TradingPlatformSession,
    trade_index: int,
    is_open: bool,
) -> float:
    market_type = rng.choice(list(symbols_by_market))
    symbol = rng.choice(symbols_by_market[market_type])
    strategy = rng.choice(strategies)
    side = rng.choice(["buy", "sell"])
    probability = rng.choice(["<40%", "40%", "50%", "60%", ">60%"])
    checklist_items = strategy["checklist_items"]
    selected_checklist = rng.sample(checklist_items, k=rng.randint(1, len(checklist_items)))
    entry_price = _price_with_noise(base_prices[symbol], rng, market_type)
    risk_pct = _risk_percent_for_market(market_type, rng)
    reward_pct = _reward_percent_for_market(market_type, rng)
    stop_loss = round(entry_price * (1 - risk_pct if side == "buy" else 1 + risk_pct), 5)
    target = round(entry_price * (1 + reward_pct if side == "buy" else 1 - reward_pct), 5)
    quantity = _quantity_for_market(entry_price, market_type, rng)
    leverage_used = 1.0 if market_type == "stock" else rng.choice([1.0, 2.0, 3.0, 5.0, 10.0])
    commission = round(rng.uniform(0.4, 4.2), 2)
    fees = round(rng.uniform(0.1, 2.4), 2)
    swaps = 0.0 if market_type in {"stock", "crypto"} else round(rng.uniform(-1.1, 1.1), 2)
    entry_spread = round(rng.uniform(0.0, 0.7 if market_type == "stock" else 0.03), 5)
    slippage_entry = round(rng.uniform(0.0, 0.8), 4)
    entry_offset = rng.randint(3, 55)
    opened_at = session.opened_at + timedelta(minutes=entry_offset)

    payload: Dict[str, Any] = {
        "account_id": request.account_id,
        "broker_id": request.broker_id,
        "symbol": symbol,
        "market_type": market_type,
        "side": side,
        "strategy": strategy["name"],
        "setup_name": strategy["name"],
        "entry_price": entry_price,
        "quantity": quantity,
        "lot_size": 1.0 if market_type != "forex" else 0.1,
        "leverage_used": leverage_used,
        "stop_loss_at_entry": stop_loss,
        "target_at_entry": target,
        "entry_spread": entry_spread,
        "slippage_at_entry": slippage_entry,
        "fees": fees,
        "commission": commission,
        "swaps": swaps,
        "entry_time": opened_at.isoformat(),
        "checklist_before": selected_checklist,
        "probability_bucket": probability,
        "confidence_score": round(rng.uniform(0.42, 0.93), 2),
        "emotion_tag": rng.choice(["calm", "focused", "hesitant", "confident"]),
        "rule_violations_snapshot": [] if rng.random() < 0.78 else [rng.choice(["late_entry", "sized_up", "moved_stop"])],
        "pre_trade_capture": {
            "phase": "pre_trade",
            "strategy_name": strategy["name"],
            "probability_bucket": probability,
            "selected_checklist": selected_checklist,
            "mandatory_checklist": strategy["mandatory_checklist_items"],
            "all_criteria_selected": True,
            "notes": rng.choice([None, "Entry planned before trigger.", "Waited for reclaim confirmation."]),
            "metadata": {"discipline_mode_enabled": True, "alerts": []},
        },
        "line_history": [
            {
                "timestamp": opened_at.isoformat(),
                "entry_line": entry_price,
                "stop_loss_line": stop_loss,
                "target_line": target,
            }
        ],
        "minimum_target_price": round((entry_price + target) / 2, 5),
        "minimum_target_reward": round(abs(target - entry_price) * quantity * 0.5, 2),
        "notes": f"Seeded trade {trade_index + 1}",
        "metadata": {"seeded": True, "session_id": session.session_id},
        "equity_at_entry": round(account_balance, 2),
        "open_positions_count": rng.randint(0, 4),
        "volatility_regime_at_entry": rng.choice(["calm", "normal", "expanding"]),
    }

    if not is_open:
        outcome = rng.choices(["win", "loss", "scratch"], weights=[52, 33, 15], k=1)[0]
        exit_offset = entry_offset + rng.randint(25, 185)
        if session.closed_at is not None:
            session_duration = max(int((session.closed_at - session.opened_at).total_seconds() / 60), entry_offset + 15)
            exit_offset = min(exit_offset, session_duration - 1)
        exit_at = session.opened_at + timedelta(minutes=max(exit_offset, entry_offset + 1))
        if outcome == "win":
            move = rng.uniform(risk_pct * 0.8, reward_pct)
        elif outcome == "loss":
            move = -rng.uniform(risk_pct * 0.45, risk_pct)
        else:
            move = rng.uniform(-risk_pct * 0.15, risk_pct * 0.2)
        if side == "sell":
            move *= -1
        exit_price = round(entry_price * (1 + move), 5)
        payload.update(
            {
                "is_closed": True,
                "exit_price": exit_price,
                "exit_time": exit_at.isoformat(),
                "exit_reason": "target_hit" if outcome == "win" else ("stop_hit" if outcome == "loss" else "manual_exit"),
                "slippage_at_exit": round(rng.uniform(0.0, 0.9), 4),
                "checklist_after": rng.sample(checklist_items, k=rng.randint(1, len(checklist_items))),
                "post_trade_capture": {
                    "phase": "post_trade",
                    "strategy_name": strategy["name"],
                    "probability_bucket": probability,
                    "selected_checklist": rng.sample(checklist_items, k=rng.randint(1, len(checklist_items))),
                    "notes": rng.choice([None, "Closed at plan.", "Held through pullback.", "Took manual exit near target."]),
                },
                "close_classification": "target_hit" if outcome == "win" else ("stop_hit" if outcome == "loss" else "manual_exit"),
            }
        )

    trade = Trade.from_dict(payload)
    api_registry.trade_repository.save_trade(trade)
    trade_dict = trade.to_dict()
    return account_balance + float(trade_dict.get("net_pnl") or 0.0)


def _price_with_noise(base_price: float, rng: random.Random, market_type: str) -> float:
    magnitude = 0.014 if market_type in {"stock", "futures"} else 0.006 if market_type == "forex" else 0.03
    return round(base_price * (1 + rng.uniform(-magnitude, magnitude)), 5)


def _risk_percent_for_market(market_type: str, rng: random.Random) -> float:
    if market_type == "forex":
        return rng.uniform(0.0025, 0.009)
    if market_type == "crypto":
        return rng.uniform(0.01, 0.035)
    if market_type == "futures":
        return rng.uniform(0.003, 0.012)
    return rng.uniform(0.004, 0.018)


def _reward_percent_for_market(market_type: str, rng: random.Random) -> float:
    if market_type == "forex":
        return rng.uniform(0.005, 0.02)
    if market_type == "crypto":
        return rng.uniform(0.02, 0.08)
    if market_type == "futures":
        return rng.uniform(0.008, 0.03)
    return rng.uniform(0.01, 0.04)


def _quantity_for_market(entry_price: float, market_type: str, rng: random.Random) -> float:
    if market_type == "forex":
        return round(rng.choice([0.1, 0.2, 0.5, 1.0, 2.0]), 2)
    if market_type == "crypto":
        return round(rng.uniform(0.05, 3.5), 4)
    if market_type == "futures":
        return float(rng.randint(1, 8))
    notional = rng.uniform(6000, 30000)
    return round(max(notional / max(entry_price, 1.0), 1.0), 2)
