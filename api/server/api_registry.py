from __future__ import annotations
import atexit

from core.context import Context
from core.execution_engine import ExecutionEngine
from core.registry import registry
from core.dependency_graph import DependencyGraph
from core.evaluator import Evaluator
from load_metrics import load_all

from connectors.execution_event_bus import ExecutionEventBus
from connectors.trade_listener import TradeListener
from connectors.broker_adapter import BrokerAdapterRegistry
from connectors.account_registry import AccountRegistry
from connectors.broker_integration_service import BrokerIntegrationService

from execution_tools.execution_orchestrator import ExecutionOrchestrator
from execution_tools.position_sizer import PositionSizer
from execution_tools.risk_line_manager import RiskLineManager
from execution_tools.slippage_guard import SlippageGuard
from execution_tools.platform_session_tracker import PlatformSessionTracker
from execution_tools.missed_opportunity_capture_service import MissedOpportunityCaptureService

from ai.diagnostic_orchestrator import DiagnosticOrchestrator
from ai.behavioral_analyzer import BehavioralAnalyzer
from ai.insights_orchestrator import AIInsightsOrchestrator
from decisions.decision_engine import DecisionEngine

from monitoring.monitoring_registry import MonitoringRegistry
from monitoring.health_monitor import HealthMonitor
from observability.audit_logger import AuditLogger

from persistence_layer.memory_backend import MemoryBackend
from persistence_layer.event_store import EventStore
from persistence_layer.snapshot_store import SnapshotStore
from persistence_layer.config_repository import ConfigRepository
from persistence_layer.trade_repository import TradeRepository
from persistence_layer.strategy_repository import StrategyRepository
from persistence_layer.attachment_repository import AttachmentRepository
from persistence_layer.note_repository import NoteRepository
from persistence_layer.tag_repository import TagRepository
from persistence_layer.rating_repository import RatingRepository
from persistence_layer.journal_view_repository import JournalViewRepository
from persistence_layer.dashboard_repository import DashboardRepository
from persistence_layer.calendar_repository import CalendarRepository
from persistence_layer.export_repository import ExportRepository
from persistence_layer.journal_query_engine import JournalQueryEngine
from persistence_layer.journal_bulk_editor import JournalBulkEditor
from persistence_layer.calendar_aggregation_engine import CalendarAggregationEngine
from persistence_layer.calendar_day_detail_service import CalendarDayDetailService
from persistence_layer.export_service import ExportService
from persistence_layer.screenshot_capture_repository import ScreenshotCaptureRepository
from persistence_layer.screenshot_capture_service import ScreenshotCaptureService
from persistence_layer.screenshot_capture_source_repository import ScreenshotCaptureSourceRepository
from persistence_layer.screenshot_source_integration_service import ScreenshotSourceIntegrationService
from persistence_layer.share_link_service import ShareLinkService
from persistence_layer.tag_taxonomy_service import TagTaxonomyService
from persistence_layer.account_repository import AccountRepository
from persistence_layer.trading_platform_session_repository import TradingPlatformSessionRepository
from persistence_layer.missed_opportunity_repository import MissedOpportunityRepository
from persistence_layer.user_repository import UserRepository
from persistence_layer.session_repository import SessionRepository
from api.server.auth_service import AuthService

from recovery.replay_controller import ReplayController
from recovery.integrity_checker import IntegrityChecker
from recovery.recovery_policy import RecoveryPolicy
from recovery.recovery_engine import RecoveryEngine

from risk_modeling.risk_modeling_engine import RiskModelingEngine


class APIRegistry:
    """
    Shared API service container.
    Keeps the API layer thin by reusing existing platform services.
    """

    def __init__(self):
        load_all()

        self.registry = registry
        self.execution_engine = ExecutionEngine(fail_fast=False)
        self.context = Context()

        self.position_sizer = PositionSizer()
        self.risk_line_manager = RiskLineManager()
        self.slippage_guard = SlippageGuard()
        self.broker_adapter_registry = BrokerAdapterRegistry()
        self.strategy_repository = StrategyRepository(db_path="api_strategy_store.db")
        self.account_repository = AccountRepository(db_path="api_account_store.db")
        self.trade_repository = TradeRepository(db_path="api_trade_store.db")
        self.attachment_repository = AttachmentRepository(db_path="api_attachment_store.db")
        self.note_repository = NoteRepository(db_path="api_note_store.db")
        self.tag_repository = TagRepository(db_path="api_tag_store.db")
        self.tag_taxonomy_service = TagTaxonomyService(
            tag_repository=self.tag_repository,
        )
        self.rating_repository = RatingRepository(db_path="api_rating_store.db")
        self.journal_view_repository = JournalViewRepository(db_path="api_journal_view_store.db")
        self.dashboard_repository = DashboardRepository(db_path="api_dashboard_store.db")
        self.calendar_repository = CalendarRepository(db_path="api_calendar_store.db")
        self.export_repository = ExportRepository(db_path="api_export_store.db")
        self.trading_platform_session_repository = TradingPlatformSessionRepository(
            db_path="api_trading_platform_session_store.db"
        )
        self.missed_opportunity_repository = MissedOpportunityRepository(
            db_path="api_missed_opportunity_store.db"
        )
        self.screenshot_capture_repository = ScreenshotCaptureRepository(db_path="api_screenshot_capture_store.db")
        self.screenshot_capture_source_repository = ScreenshotCaptureSourceRepository(
            db_path="api_screenshot_capture_source_store.db"
        )
        self.user_repository = UserRepository(db_path="api_user_store.db")
        self.session_repository = SessionRepository(db_path="api_session_store.db")
        self.auth_service = AuthService(
            user_repository=self.user_repository,
            session_repository=self.session_repository,
        )
        self.journal_query_engine = JournalQueryEngine(
            trade_repository=self.trade_repository,
            note_repository=self.note_repository,
            tag_repository=self.tag_repository,
            rating_repository=self.rating_repository,
        )
        self.journal_bulk_editor = JournalBulkEditor(
            trade_repository=self.trade_repository,
            note_repository=self.note_repository,
            tag_repository=self.tag_repository,
            rating_repository=self.rating_repository,
        )
        self.calendar_aggregation_engine = CalendarAggregationEngine(
            trade_repository=self.trade_repository,
            note_repository=self.note_repository,
            calendar_repository=self.calendar_repository,
            trading_platform_session_repository=self.trading_platform_session_repository,
            missed_opportunity_repository=self.missed_opportunity_repository,
        )
        self.calendar_day_detail_service = CalendarDayDetailService(
            trade_repository=self.trade_repository,
            note_repository=self.note_repository,
            calendar_repository=self.calendar_repository,
            trading_platform_session_repository=self.trading_platform_session_repository,
            missed_opportunity_repository=self.missed_opportunity_repository,
        )
        self.export_service = ExportService(
            trade_repository=self.trade_repository,
            note_repository=self.note_repository,
            tag_repository=self.tag_repository,
            rating_repository=self.rating_repository,
            export_repository=self.export_repository,
        )
        self.share_link_service = ShareLinkService(
            trade_repository=self.trade_repository,
            attachment_repository=self.attachment_repository,
            note_repository=self.note_repository,
            tag_repository=self.tag_repository,
            rating_repository=self.rating_repository,
            export_repository=self.export_repository,
        )
        self.screenshot_capture_service = ScreenshotCaptureService(
            trade_repository=self.trade_repository,
            attachment_repository=self.attachment_repository,
            capture_repository=self.screenshot_capture_repository,
        )
        self.screenshot_source_integration_service = ScreenshotSourceIntegrationService(
            source_repository=self.screenshot_capture_source_repository,
            capture_repository=self.screenshot_capture_repository,
            capture_service=self.screenshot_capture_service,
        )
        self.platform_session_tracker = PlatformSessionTracker(
            session_repository=self.trading_platform_session_repository,
        )
        self.missed_opportunity_capture_service = MissedOpportunityCaptureService(
            repository=self.missed_opportunity_repository,
            position_sizer=self.position_sizer,
        )
        self.account_registry = AccountRegistry(
            trade_repository=self.trade_repository,
            screenshot_capture_service=self.screenshot_capture_service,
            strategy_repository=self.strategy_repository,
            platform_session_tracker=self.platform_session_tracker,
        )
        self.broker_integration_service = BrokerIntegrationService(
            account_repository=self.account_repository,
            account_registry=self.account_registry,
            broker_adapter_registry=self.broker_adapter_registry,
        )
        self.execution_orchestrator = ExecutionOrchestrator(
            context=self.context,
            execution_engine=self.execution_engine,
            position_sizer=self.position_sizer,
            risk_line_manager=self.risk_line_manager,
            slippage_guard=self.slippage_guard,
            strategy_repository=self.strategy_repository,
        )

        self.event_bus = ExecutionEventBus()
        self.trade_listener = TradeListener(
            context=self.context,
            orchestrator=self.execution_orchestrator,
            event_bus=self.event_bus,
            trade_repository=self.trade_repository,
            screenshot_capture_service=self.screenshot_capture_service,
            account_repository=self.account_repository,
        )

        self.diagnostic_orchestrator = DiagnosticOrchestrator()
        self.behavioral_analyzer = BehavioralAnalyzer()
        self.ai_insights_orchestrator = AIInsightsOrchestrator(
            trade_repository=self.trade_repository,
            missed_opportunity_repository=self.missed_opportunity_repository,
            trading_platform_session_repository=self.trading_platform_session_repository,
            behavioral_analyzer=self.behavioral_analyzer,
            calendar_aggregation_engine=self.calendar_aggregation_engine,
            execution_engine=self.execution_engine,
            registry=self.registry,
            account_repository=self.account_repository,
        )
        self.decision_engine = DecisionEngine()
        self.risk_modeling_engine = RiskModelingEngine()

        self.monitoring_registry = MonitoringRegistry()
        self.audit_logger = AuditLogger()
        self.health_monitor = HealthMonitor(
            execution_engine=self.execution_engine,
            monitoring_registry=self.monitoring_registry,
        )

        self.memory_backend = MemoryBackend()
        self.event_store = EventStore(self.memory_backend)
        self.snapshot_store = SnapshotStore(db_path="api_snapshot_store.db")
        self.config_repository = ConfigRepository(db_path="api_config_store.db")

        self.dependency_graph = DependencyGraph()
        self.evaluator = Evaluator()
        self.replay_controller = ReplayController(self.evaluator, self.dependency_graph)
        self.integrity_checker = IntegrityChecker()
        self.recovery_policy = RecoveryPolicy(mode="strict_resume")
        self.recovery_engine = RecoveryEngine(
            event_store=self.event_store,
            snapshot_store=self.snapshot_store,
            config_repository=self.config_repository,
            replay_controller=self.replay_controller,
            integrity_checker=self.integrity_checker,
            recovery_policy=self.recovery_policy,
            execution_orchestrator=self.execution_orchestrator,
        )
        self._started = False

    def startup(self) -> None:
        if self._started:
            return
        try:
            self.broker_integration_service.restore_persisted_integrations()
        except Exception:
            pass
        self.health_monitor.start()
        self._started = True

    def close(self) -> None:
        if self._started:
            self.health_monitor.stop()
            self._started = False

        if hasattr(self, "event_bus") and self.event_bus is not None:
            self.event_bus.shutdown()

        for value in self.__dict__.values():
            if value is self:
                continue
            close_fn = getattr(value, "close", None)
            if callable(close_fn):
                try:
                    close_fn()
                except Exception:
                    pass
                continue

            connection = getattr(value, "_connection", None)
            if connection is not None:
                try:
                    connection.close()
                except Exception:
                    pass


api_registry = APIRegistry()
atexit.register(api_registry.close)
