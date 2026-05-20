from __future__ import annotations

from fastapi import APIRouter

from api.auth.router import router as auth_router
from api.accounts.router import router as accounts_router
from api.debug.router import router as debug_router
from api.trade_ingestion.router import router as trade_ingestion_router
from api.metric_computation.router import router as metric_computation_router
from api.ai_diagnostic.router import router as ai_diagnostic_router
from api.ai_insights.router import router as ai_insights_router
from api.decision_engine.router import router as decision_engine_router
from api.execution_tools.router import router as execution_tools_router
from api.risk_modeling.router import router as risk_modeling_router
from api.visualization.router import router as visualization_router
from api.monitoring.router import router as monitoring_router
from api.recovery.router import router as recovery_router
from api.governance_config.router import router as governance_config_router
from api.strategy_setup.router import router as strategy_setup_router
from api.journal.router import router as journal_router
from api.attachments.router import router as attachments_router
from api.notes.router import router as notes_router
from api.tags.router import router as tags_router
from api.ratings.router import router as ratings_router
from api.journal_views.router import router as journal_views_router
from api.dashboard_layouts.router import router as dashboard_layouts_router
from api.calendar.router import router as calendar_router
from api.trading_sessions.router import router as trading_sessions_router
from api.missed_opportunities.router import router as missed_opportunities_router
from api.share_export.router import router as share_export_router


api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(accounts_router)
api_router.include_router(trade_ingestion_router)
api_router.include_router(metric_computation_router)
api_router.include_router(ai_diagnostic_router)
api_router.include_router(ai_insights_router)
api_router.include_router(decision_engine_router)
api_router.include_router(execution_tools_router)
api_router.include_router(risk_modeling_router)
api_router.include_router(visualization_router)
api_router.include_router(monitoring_router)
api_router.include_router(recovery_router)
api_router.include_router(governance_config_router)
api_router.include_router(strategy_setup_router)
api_router.include_router(journal_router)
api_router.include_router(attachments_router)
api_router.include_router(notes_router)
api_router.include_router(tags_router)
api_router.include_router(ratings_router)
api_router.include_router(journal_views_router)
api_router.include_router(dashboard_layouts_router)
api_router.include_router(calendar_router)
api_router.include_router(trading_sessions_router)
api_router.include_router(missed_opportunities_router)
api_router.include_router(debug_router)
api_router.include_router(share_export_router)
