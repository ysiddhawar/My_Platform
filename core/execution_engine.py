import time
from typing import List, Optional, Callable
from core.context import ExecutionContext


class ExecutionEngine:
    """
    Institutional DAG Execution Engine

    Features:
    - Deterministic dependency resolution
    - Optional pre/post hooks
    - Governance-ready execution
    - Fail-fast mode
    """

    def __init__(self, fail_fast: bool = False):
        self.fail_fast = fail_fast
        self._events = []

    # -------------------------------------------------
    # EXECUTION
    # -------------------------------------------------

    def run(
        self,
        data: dict,
        registry,
        category: Optional[str] = None,
        metrics_subset: Optional[List[str]] = None,
        parent: Optional[ExecutionContext] = None,
        phase: str = "research",
        entity=None,
        pre_hooks: Optional[List[Callable]] = None,
        post_hooks: Optional[List[Callable]] = None,
    ) -> ExecutionContext:

        context = ExecutionContext(data=data, phase=phase, entity=entity)

        if parent is not None:
            context._cache = parent._cache.copy()

        # -----------------------------------------
        # Metric Selection
        # -----------------------------------------

        if metrics_subset:
            metrics = metrics_subset
        elif category:
            metrics = registry.get_category_metrics(category)
        else:
            metrics = registry.list_metrics()

        ordered = registry.execution_order(metrics)

        # -----------------------------------------
        # Pre-hooks (future discipline integration)
        # -----------------------------------------

        for hook in pre_hooks or []:
            hook(context)

        # -----------------------------------------
        # Execute Metrics
        # -----------------------------------------

        for name in ordered:

            func = registry.get(name)
            if not func:
                continue

            start = time.perf_counter()

            try:
                result = func(context)
                context.set_result(name, result)

            except Exception as e:
                context.set_error(name, e)
                if self.fail_fast:
                    raise e
                context.set_result(name, None)

            finally:
                context.set_cache(
                    f"{name}_exec_time",
                    time.perf_counter() - start,
                )

        # -----------------------------------------
        # Post-hooks
        # -----------------------------------------

        for hook in post_hooks or []:
            hook(context)

        context.finalize()
        return context

    def process_event(self, event):
        """
        Compatibility hook for components that use an event-driven interface.
        """
        self._events.append(event)

    def get_events(self):
        return list(self._events)
