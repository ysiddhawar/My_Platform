from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from models.trade_tag import TradeTag
from persistence_layer.tag_repository import TagRepository


DEFAULT_TAXONOMY_PRESETS = {
    "mistake": [
        {"name": "early_exit", "description": "Closed before the original plan completed."},
        {"name": "rule_break", "description": "Violated a defined trading rule."},
        {"name": "oversizing", "description": "Used too much size for the setup quality."},
        {"name": "revenge_trade", "description": "Triggered by prior loss or frustration."},
    ],
    "emotion": [
        {"name": "fear", "description": "Fear influenced execution or management."},
        {"name": "greed", "description": "Greed distorted target or risk decisions."},
        {"name": "hesitation", "description": "Delayed execution against the plan."},
        {"name": "confidence", "description": "Confident execution aligned with plan."},
    ],
    "setup": [
        {"name": "trend_continuation", "description": "Trend continuation setup."},
        {"name": "breakout", "description": "Breakout or opening range style setup."},
        {"name": "reversal", "description": "Reversal or fade setup."},
    ],
}


class TagTaxonomyService:
    def __init__(self, tag_repository: TagRepository):
        self._tag_repository = tag_repository

    def taxonomy_summary(self, account_id: str) -> Dict[str, Any]:
        tags = self._tag_repository.list_by_account(account_id)
        categories: Dict[str, Dict[str, Any]] = {}
        for tag in tags:
            bucket = categories.setdefault(
                tag.category,
                {"category": tag.category, "count": 0, "tags": []},
            )
            bucket["count"] += 1
            bucket["tags"].append(tag.to_dict())
        return {
            "account_id": account_id,
            "categories": sorted(categories.values(), key=lambda item: item["category"]),
            "category_names": sorted(categories.keys()),
            "total_tags": len(tags),
        }

    def list_by_category(self, account_id: str, category: str) -> Dict[str, Any]:
        tags = self._tag_repository.list_by_category(account_id, category)
        return {"account_id": account_id, "category": category, "tags": [tag.to_dict() for tag in tags]}

    def seed_presets(
        self,
        account_id: str,
        categories: Optional[List[str]] = None,
        overwrite_existing: bool = False,
    ) -> Dict[str, Any]:
        categories = categories or sorted(DEFAULT_TAXONOMY_PRESETS.keys())
        created: List[Dict[str, Any]] = []
        skipped: List[str] = []

        for category in categories:
            preset_items = DEFAULT_TAXONOMY_PRESETS.get(category, [])
            existing = {tag.name.lower(): tag for tag in self._tag_repository.list_by_category(account_id, category)}
            for item in preset_items:
                name_key = item["name"].lower()
                if name_key in existing and not overwrite_existing:
                    skipped.append(f"{category}:{item['name']}")
                    continue
                tag_kwargs = dict(
                    account_id=account_id,
                    name=item["name"],
                    category=category,
                    description=item.get("description"),
                    metadata={
                        "preset": True,
                        "seeded_at": datetime.now(timezone.utc).isoformat(),
                    },
                )
                if name_key in existing:
                    tag_kwargs["tag_id"] = existing[name_key].tag_id
                tag = TradeTag(**tag_kwargs)
                self._tag_repository.save(tag)
                created.append(tag.to_dict())

        return {"created": created, "skipped": skipped, "categories": categories}

    def upsert_tag(
        self,
        account_id: str,
        name: str,
        category: str,
        color: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tag_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        tag_kwargs = dict(
            account_id=account_id,
            name=name,
            category=category,
            color=color,
            description=description,
            metadata=metadata or {},
        )
        if tag_id is not None:
            tag_kwargs["tag_id"] = tag_id
        tag = TradeTag(**tag_kwargs)
        self._tag_repository.save(tag)
        return {"tag": tag.to_dict()}

    def delete_tag(self, tag_id: str) -> Dict[str, Any]:
        deleted = self._tag_repository.delete(tag_id)
        return {"deleted": deleted}
