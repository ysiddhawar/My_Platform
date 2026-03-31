# API_CONTRACTS

Base URL prefix: `/api/v1`

This contract is strict and maps directly to the API layer in `api/`.

## 1) Trade Ingestion Pipeline

Endpoint: `POST /api/v1/trade-ingestion/events`

Request schema:
```json
{
  "event_id": "string",
  "type": "PRE_TRADE_REQUEST | TRADE_FILLED | TRADE_CLOSED",
  "payload": {}
}
```

Response schema:
```json
{
  "status": "ok",
  "result": {}
}
```

Internal modules triggered:
- `connectors.trade_listener.TradeListener.on_broker_event`
- `execution_tools.execution_orchestrator.ExecutionOrchestrator.execute_trade` (for `PRE_TRADE_REQUEST`)
- `connectors.execution_event_bus.ExecutionEventBus.emit`

Example payload:
```json
{
  "event_id": "evt-1001",
  "type": "PRE_TRADE_REQUEST",
  "payload": {
    "account_balance": 100000,
    "entry_price": 100.5,
    "stop_loss_price": 98.0,
    "symbol": "AAPL",
    "side": "buy",
    "slippage_cost": 1.2,
    "spread": 0.04,
    "volatility": 0.2,
    "open_positions": 2,
    "correlation_exposure": 0.35
  }
}
```

## 2) Metric Computation Pipeline

Endpoint: `POST /api/v1/metrics/run`

Request schema:
```json
{
  "category": "string | null",
  "metrics_subset": ["string"] | null,
  "data": {},
  "phase": "research"
}
```

Response schema:
```json
{
  "results": {},
  "errors": {},
  "metadata": {}
}
```

Internal modules triggered:
- `load_metrics.load_all` (preloaded in API registry)
- `core.execution_engine.ExecutionEngine.run`
- `core.registry.registry` for dependency ordering/validation

Example payload:
```json
{
  "category": "performance",
  "data": {
    "returns": [0.01, -0.02, 0.03, 0.005]
  },
  "phase": "research"
}
```

## 3) AI Diagnostic Pipeline

Endpoint: `POST /api/v1/ai-diagnostic/run`

Request schema:
```json
{
  "structured_metrics": {
    "journal": {}, "performance": {}, "risk": {}, "distributions": {},
    "regimes": {}, "robustness": {}, "portfolio": {}, "capital": {},
    "risk_control": {}, "stress": {}, "survival": {}
  },
  "governance_tier": "string",
  "percentiles": {"metric": 0.5} | null,
  "zscores": {"metric": 1.2} | null,
  "behavioral_signals": {} | null,
  "metadata": {} | null
}
```

Response schema:
```json
{
  "diagnosis": {}
}
```

Internal modules triggered:
- `ai.diagnostic_orchestrator.DiagnosticOrchestrator.run`
- `ai.metric_interpreter.MetricInterpreter.interpret`
- `ai.behavioral_interpreter.BehavioralInterpreter.interpret` (optional)

Example payload:
```json
{
  "structured_metrics": {
    "journal": {}, "performance": {"net_sharpe": 1.1}, "risk": {"max_drawdown": 0.12},
    "distributions": {}, "regimes": {}, "robustness": {}, "portfolio": {},
    "capital": {}, "risk_control": {}, "stress": {}, "survival": {}
  },
  "governance_tier": "TIER_2"
}
```

## 4) Decision Engine Pipeline

Endpoint: `POST /api/v1/decisions/evaluate`

Request schema:
```json
{
  "structured_data": {},
  "base_capital": 100000.0,
  "ai_diagnosis": {} | null
}
```

Response schema:
```json
{
  "decision": {}
}
```

Internal modules triggered:
- `decisions.decision_engine.DecisionEngine.evaluate`
- `decisions.governance_levels.GovernanceLevels.classify`
- `decisions.capital_governor.CapitalGovernor.generate_advisory`
- `decisions.strategy_approval.StrategyApproval.evaluate`
- `decisions.deployment_validator.DeploymentValidator.evaluate`

Example payload:
```json
{
  "structured_data": {
    "performance": {"net_sharpe": 1.2},
    "risk": {"max_drawdown": 0.1}
  },
  "base_capital": 250000
}
```

## 5) Execution Tools Pipeline

Endpoint A: `POST /api/v1/execution-tools/execute-trade`

Request schema:
```json
{
  "account_balance": 100000,
  "entry_price": 101,
  "stop_loss_price": 99,
  "symbol": "AAPL",
  "side": "buy",
  "slippage_cost": 0.8,
  "spread": 0.03,
  "volatility": 0.18,
  "open_positions": 1,
  "correlation_exposure": 0.2
}
```

Response schema:
```json
{
  "result": {
    "status": "approved | rejected",
    "position_size": 123.45,
    "reason": "string"
  }
}
```

Endpoint B: `POST /api/v1/execution-tools/update-config`

Request schema:
```json
{
  "config": {
    "position_sizer": {},
    "risk_line_manager": {},
    "slippage_guard": {}
  }
}
```

Response schema:
```json
{
  "status": "updated"
}
```

Internal modules triggered:
- `execution_tools.execution_orchestrator.ExecutionOrchestrator.execute_trade`
- `execution_tools.position_sizer.PositionSizer.calculate_position_size`
- `execution_tools.risk_line_manager.RiskLineManager.is_trade_allowed`
- `execution_tools.slippage_guard.SlippageGuard.is_execution_allowed`
- `core.execution_engine.ExecutionEngine.process_event`

Example payload:
```json
{
  "account_balance": 50000,
  "entry_price": 50,
  "stop_loss_price": 48,
  "symbol": "MSFT",
  "side": "buy"
}
```

## 6) Risk Modeling Pipeline

Endpoint: `POST /api/v1/risk-modeling/analyze`

Request schema:
```json
{
  "metrics": {},
  "returns": [0.01, -0.01, 0.02],
  "initial_equity": 100000
}
```

Response schema:
```json
{
  "report": {
    "regime_probabilities": {},
    "scenario_summary": {},
    "drawdown_forecast": {},
    "ruin_forecast": {},
    "tail_risk": {}
  }
}
```

Internal modules triggered:
- `risk_modeling.risk_modeling_engine.RiskModelingEngine.analyze`
- `risk_modeling.regime_probability_model.RegimeProbabilityModel.estimate`
- `risk_modeling.forward_scenario_engine.ForwardScenarioEngine.simulate`
- `risk_modeling.forward_drawdown_estimator.ForwardDrawdownEstimator.estimate`
- `risk_modeling.forward_ruin_probability.ForwardRuinProbability.estimate`
- `risk_modeling.tail_scenario_simulator.TailScenarioSimulator.simulate`

Example payload:
```json
{
  "metrics": {
    "risk": {"max_drawdown": 0.12},
    "regimes": {},
    "survival": {},
    "robustness": {},
    "portfolio": {}
  },
  "returns": [0.002, -0.001, 0.003, -0.004, 0.001],
  "initial_equity": 100000
}
```

## 7) Visualization Pipeline

Endpoint A: `POST /api/v1/visualization/performance-dashboard`

Request schema:
```json
{
  "timestamps": ["t1", "t2"],
  "equity_curve": [100000, 100500],
  "drawdown": [0.0, -0.01],
  "rolling_sharpe": [1.1, 1.2]
}
```

Endpoint B: `POST /api/v1/visualization/portfolio-dashboard`

Request schema:
```json
{
  "timestamps": ["t1", "t2"],
  "portfolio_values": [100000, 100200],
  "symbols": ["AAPL", "MSFT"],
  "exposures": [0.6, 0.4],
  "assets": ["AAPL", "MSFT"],
  "correlation_matrix": [[1.0, 0.3], [0.3, 1.0]]
}
```

Response schema (both):
```json
{
  "dashboard": {}
}
```

Internal modules triggered:
- `visualization.performance_dashboard.PerformanceDashboard`
- `visualization.portfolio_dashboard.PortfolioDashboard`
- `visualization.charts.*` chart exporters

Example payload:
```json
{
  "timestamps": ["2026-03-06T10:00:00Z", "2026-03-06T11:00:00Z"],
  "equity_curve": [100000, 100800],
  "drawdown": [0.0, -0.003],
  "rolling_sharpe": [1.0, 1.15]
}
```

## 8) Monitoring Pipeline

Endpoint A: `POST /api/v1/monitoring/anomaly`

Request schema:
```json
{
  "event": {}
}
```

Endpoint B: `POST /api/v1/monitoring/audit-log`

Request schema:
```json
{
  "category": "string",
  "component": "string",
  "event_type": "string",
  "details": {},
  "severity": "info|low|medium|high|critical",
  "metadata": {}
}
```

Endpoint C: `GET /api/v1/monitoring/snapshot`

Response schema:
```json
{
  "status": "ok",
  "data": {
    "monitoring_registry": {},
    "health_status": {},
    "audit_stats": {}
  }
}
```

Internal modules triggered:
- `monitoring.monitoring_registry.MonitoringRegistry`
- `monitoring.health_monitor.HealthMonitor.get_status`
- `observability.audit_logger.AuditLogger`

Example payload:
```json
{
  "category": "execution",
  "component": "execution_orchestrator",
  "event_type": "trade_approved",
  "details": {"symbol": "AAPL"},
  "severity": "info",
  "metadata": {"run_id": "r-1"}
}
```

## 9) Recovery Pipeline

Endpoint: `POST /api/v1/recovery/run`

Request schema:
```json
{
  "account_id": "string | null"
}
```

Response schema:
```json
{
  "result": {
    "integrity_valid": true,
    "integrity_errors": [],
    "integrity_warnings": [],
    "recovery_mode": "string",
    "execution_allowed": false,
    "read_only_mode": true,
    "reason": "string",
    "context_metadata": {}
  }
}
```

Internal modules triggered:
- `recovery.recovery_engine.RecoveryEngine.recover`
- `persistence_layer.snapshot_store.SnapshotStore.load_latest_snapshot`
- `persistence_layer.event_store.EventStore.load_events`
- `recovery.integrity_checker.IntegrityChecker.validate`
- `recovery.recovery_policy.RecoveryPolicy.evaluate`
- `recovery.replay_controller.ReplayController.replay`

Example payload:
```json
{
  "account_id": "ACC-001"
}
```

## 10) Governance / Configuration Update Pipeline

Endpoint A: `POST /api/v1/governance-config/update`

Request schema:
```json
{
  "account_id": "string",
  "config": {},
  "source": "api"
}
```

Response schema:
```json
{
  "status": "updated",
  "config_version": 1
}
```

Endpoint B: `GET /api/v1/governance-config/active/{account_id}`

Response schema:
```json
{
  "status": "ok",
  "active_config": {}
}
```

Internal modules triggered:
- `persistence_layer.config_repository.ConfigRepository.create_new_version`
- `persistence_layer.config_repository.ConfigRepository.activate_version`
- `persistence_layer.config_repository.ConfigRepository.get_active_config`
- `execution_tools.execution_orchestrator.ExecutionOrchestrator.update_config`

Example payload:
```json
{
  "account_id": "ACC-001",
  "config": {
    "position_sizer": {"max_risk_percent": 0.8},
    "risk_line_manager": {"max_daily_drawdown": 0.03},
    "slippage_guard": {"max_spread": 0.2}
  },
  "source": "risk_committee"
}
```

---

## Shared Server Entry

- Server file: `api/server/api_server.py`
- Router registration: `api/server/api_router.py`
- Service registry/container: `api/server/api_registry.py`
- Start command:

```bash
uvicorn api.server.api_server:app
```
