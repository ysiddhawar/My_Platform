from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from persistence_layer.note_repository import NoteRepository
from persistence_layer.rating_repository import RatingRepository
from persistence_layer.tag_repository import TagRepository
from persistence_layer.trade_repository import TradeRepository


class JournalQueryEngine:
    def __init__(
        self,
        trade_repository: TradeRepository,
        note_repository: NoteRepository,
        tag_repository: TagRepository,
        rating_repository: RatingRepository,
    ):
        self._trade_repository = trade_repository
        self._note_repository = note_repository
        self._tag_repository = tag_repository
        self._rating_repository = rating_repository

    def query(
        self,
        account_id: str,
        filters: Optional[Dict[str, Any]] = None,
        search_text: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        filters = filters or {}
        trades = [
            trade.to_dict()
            for trade in self._trade_repository.get_trades_by_account(
                account_id=account_id,
                closed_only=filters.get("closed_only"),
            )
        ]
        notes_by_trade = {
            trade["trade_id"]: self._note_repository.get_by_trade(trade["trade_id"])
            for trade in trades
        }
        tags_by_trade = {
            trade["trade_id"]: self._tag_repository.list_for_trade(trade["trade_id"])
            for trade in trades
        }

        results = []
        search_text_normalized = (search_text or "").strip().lower()

        for trade in trades:
            if filters.get("symbol") and trade.get("symbol") != filters["symbol"]:
                continue
            if filters.get("market_type") and trade.get("market_type") != filters["market_type"]:
                continue
            if filters.get("side") and trade.get("side") != filters["side"]:
                continue
            if filters.get("setup_name") and trade.get("setup_name") != filters["setup_name"]:
                continue
            if filters.get("probability_bucket") and trade.get("probability_bucket") != filters["probability_bucket"]:
                continue
            if filters.get("closed_before_plan") is not None and bool(trade.get("closed_before_plan")) != bool(filters["closed_before_plan"]):
                continue
            if filters.get("date_from") and not self._matches_date_from(trade, filters["date_from"]):
                continue
            if filters.get("date_to") and not self._matches_date_to(trade, filters["date_to"]):
                continue
            if filters.get("has_notes") and not notes_by_trade.get(trade["trade_id"]):
                continue

            rating = self._rating_repository.get_for_trade(trade["trade_id"])
            if filters.get("min_rating") is not None:
                if rating is None or float(rating.rating_value) < float(filters["min_rating"]):
                    continue

            trade_tags = tags_by_trade.get(trade["trade_id"], [])
            if filters.get("tag_names"):
                assigned_names = {tag.name for tag in trade_tags}
                if not set(filters["tag_names"]).issubset(assigned_names):
                    continue

            notes = notes_by_trade.get(trade["trade_id"], [])
            if search_text_normalized and not self._matches_search(trade, notes, trade_tags, rating, search_text_normalized):
                continue

            results.append(
                {
                    "trade": trade,
                    "notes": [note.to_dict() for note in notes],
                    "tags": [tag.to_dict() for tag in trade_tags],
                    "rating": rating.to_dict() if rating else None,
                }
            )

        return results

    def _matches_date_from(self, trade: Dict[str, Any], date_from: str) -> bool:
        entry_time = trade.get("entry_time")
        return bool(entry_time and datetime.fromisoformat(entry_time) >= datetime.fromisoformat(date_from))

    def _matches_date_to(self, trade: Dict[str, Any], date_to: str) -> bool:
        entry_time = trade.get("entry_time")
        return bool(entry_time and datetime.fromisoformat(entry_time) <= datetime.fromisoformat(date_to))

    def _matches_search(self, trade: Dict[str, Any], notes: List[Any], tags: List[Any], rating: Any, search_text: str) -> bool:
        haystack = [
            str(trade.get("symbol", "")),
            str(trade.get("setup_name", "")),
            str(trade.get("notes", "")),
            str(trade.get("exit_reason", "")),
            str(trade.get("probability_bucket", "")),
        ]
        haystack.extend(note.body for note in notes)
        haystack.extend(note.title for note in notes)
        haystack.extend(tag.name for tag in tags)
        if rating is not None and rating.rationale:
            haystack.append(rating.rationale)
        return any(search_text in value.lower() for value in haystack if value)
