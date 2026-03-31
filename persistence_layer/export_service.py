from __future__ import annotations

import csv
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List

from models.share_export_record import ShareExportRecord
from persistence_layer.export_repository import ExportRepository
from persistence_layer.note_repository import NoteRepository
from persistence_layer.rating_repository import RatingRepository
from persistence_layer.tag_repository import TagRepository
from persistence_layer.trade_repository import TradeRepository


class ExportService:
    def __init__(
        self,
        trade_repository: TradeRepository,
        note_repository: NoteRepository,
        tag_repository: TagRepository,
        rating_repository: RatingRepository,
        export_repository: ExportRepository,
    ):
        self._trade_repository = trade_repository
        self._note_repository = note_repository
        self._tag_repository = tag_repository
        self._rating_repository = rating_repository
        self._export_repository = export_repository

    def generate_account_export(
        self,
        account_id: str,
        export_format: str,
        output_dir: str = "exports",
    ) -> Dict:
        trades = [trade.to_dict() for trade in self._trade_repository.get_trades_by_account(account_id)]
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        file_path = output_path / f"{account_id}_journal_{timestamp}.{export_format}"

        if export_format == "json":
            payload = self._build_export_payload(account_id, trades)
            file_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        elif export_format == "csv":
            self._write_csv(file_path, trades)
        elif export_format == "pdf":
            payload = self._build_export_payload(account_id, trades)
            self._write_pdf(file_path, payload)
        else:
            raise ValueError("Unsupported export format")

        record = ShareExportRecord(
            account_id=account_id,
            record_type="export",
            target_type="account",
            target_id=account_id,
            format=export_format,
            status="ready",
            storage_path=str(file_path),
            metadata={"trade_count": len(trades)},
        )
        self._export_repository.save(record)
        return {"record": record.to_dict(), "path": str(file_path)}

    def _build_export_payload(self, account_id: str, trades: List[Dict]) -> Dict:
        return {
            "account_id": account_id,
            "trades": trades,
            "notes": [note.to_dict() for note in self._note_repository.get_by_account(account_id)],
            "tags": [tag.to_dict() for tag in self._tag_repository.list_by_account(account_id)],
            "ratings": [rating.to_dict() for rating in self._rating_repository.get_by_account(account_id)],
        }

    def _write_csv(self, file_path: Path, trades: List[Dict]):
        fieldnames = [
            "trade_id", "symbol", "market_type", "side", "setup_name",
            "entry_time", "entry_price", "exit_time", "exit_price",
            "net_pnl", "probability_bucket", "closed_before_plan",
        ]
        with file_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            for trade in trades:
                writer.writerow({key: trade.get(key) for key in fieldnames})

    def _write_pdf(self, file_path: Path, payload: Dict):
        lines = self._pdf_lines(payload)
        objects: List[bytes] = []

        objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
        objects.append(b"<< /Type /Pages /Count 1 /Kids [3 0 R] >>")
        objects.append(b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>")
        objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

        content = ["BT", "/F1 10 Tf", "50 760 Td", "14 TL"]
        first = True
        for line in lines:
            safe_line = self._escape_pdf_text(line)
            if first:
                content.append(f"({safe_line}) Tj")
                first = False
            else:
                content.append("T*")
                content.append(f"({safe_line}) Tj")
        content.append("ET")
        stream = "\n".join(content).encode("latin-1", errors="replace")
        objects.append(f"<< /Length {len(stream)} >>\nstream\n".encode("latin-1") + stream + b"\nendstream")

        pdf = bytearray(b"%PDF-1.4\n")
        offsets = [0]
        for index, obj in enumerate(objects, start=1):
            offsets.append(len(pdf))
            pdf.extend(f"{index} 0 obj\n".encode("latin-1"))
            pdf.extend(obj)
            pdf.extend(b"\nendobj\n")

        xref_offset = len(pdf)
        pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("latin-1"))
        pdf.extend(b"0000000000 65535 f \n")
        for offset in offsets[1:]:
            pdf.extend(f"{offset:010d} 00000 n \n".encode("latin-1"))
        pdf.extend(
            (
                f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
                f"startxref\n{xref_offset}\n%%EOF"
            ).encode("latin-1")
        )
        file_path.write_bytes(bytes(pdf))

    def _pdf_lines(self, payload: Dict) -> List[str]:
        account_id = payload.get("account_id", "UNKNOWN")
        trades = payload.get("trades", [])
        notes = payload.get("notes", [])
        ratings = payload.get("ratings", [])
        total_pnl = sum(float(trade.get("net_pnl") or 0.0) for trade in trades)
        wins = sum(1 for trade in trades if float(trade.get("net_pnl") or 0.0) > 0)
        losses = sum(1 for trade in trades if float(trade.get("net_pnl") or 0.0) < 0)

        lines = [
            f"Journal Export - Account: {account_id}",
            f"Generated: {datetime.now(timezone.utc).isoformat()}",
            f"Trades: {len(trades)} | Wins: {wins} | Losses: {losses} | NetPnL: {round(total_pnl, 2)}",
            f"Notes: {len(notes)} | Ratings: {len(ratings)} | Tags: {len(payload.get('tags', []))}",
            "",
            "Trade Summary",
        ]
        for trade in trades[:40]:
            lines.append(
                f"{trade.get('symbol')} {trade.get('side')} setup={trade.get('setup_name')} "
                f"entry={trade.get('entry_price')} exit={trade.get('exit_price')} pnl={trade.get('net_pnl')}"
            )
        if len(trades) > 40:
            lines.append(f"... truncated {len(trades) - 40} additional trades")
        return lines

    def _escape_pdf_text(self, value: str) -> str:
        return (
            str(value)
            .replace("\\", "\\\\")
            .replace("(", "\\(")
            .replace(")", "\\)")
        )
