from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable, Optional

from models.journal_note import JournalNote
from models.trade_rating import TradeRating
from persistence_layer.note_repository import NoteRepository
from persistence_layer.rating_repository import RatingRepository
from persistence_layer.tag_repository import TagRepository
from persistence_layer.trade_repository import TradeRepository


class JournalBulkEditor:
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

    def apply(
        self,
        account_id: str,
        trade_ids: Iterable[str],
        note_text: Optional[str] = None,
        note_title: str = "Bulk Update",
        tag_ids: Optional[Iterable[str]] = None,
        rating_value: Optional[float] = None,
        rating_rationale: Optional[str] = None,
    ) -> dict:
        updated = []
        trade_ids = list(trade_ids)
        for trade_id in trade_ids:
            trade = self._trade_repository.get_trade(trade_id)
            if trade is None:
                continue
            if note_text:
                trade.append_notes(note_text)
                self._note_repository.save(
                    JournalNote(
                        account_id=account_id,
                        note_type="trade",
                        title=note_title,
                        body=note_text,
                        trade_id=trade_id,
                        note_date=datetime.now(timezone.utc).date().isoformat(),
                        metadata={"source": "bulk_edit"},
                    )
                )
            if tag_ids:
                for tag_id in tag_ids:
                    self._tag_repository.assign_to_trade(
                        account_id=account_id,
                        trade_id=trade_id,
                        tag_id=tag_id,
                        linked_at=datetime.now(timezone.utc).isoformat(),
                    )
            if rating_value is not None:
                self._rating_repository.save(
                    TradeRating(
                        account_id=account_id,
                        trade_id=trade_id,
                        rating_value=float(rating_value),
                        rationale=rating_rationale,
                        metadata={"source": "bulk_edit"},
                    )
                )
            self._trade_repository.save_trade(trade)
            updated.append(trade_id)
        return {"updated_trade_ids": updated, "count": len(updated)}
