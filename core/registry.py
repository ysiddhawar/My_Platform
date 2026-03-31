from collections import defaultdict
from typing import Callable, Dict, List, Optional


class Registry:
    """
    Institutional Metric Registry

    Features:
    - Deterministic metric storage
    - Dependency graph tracking
    - Hierarchical category support (prefix-based)
    - DAG validation
    - Topological ordering
    """

    def __init__(self):
        self._metrics: Dict[str, Callable] = {}
        self._dependencies: Dict[str, List[str]] = defaultdict(list)
        self._categories: Dict[str, List[str]] = defaultdict(list)

    # -------------------------------------------------
    # REGISTER METRIC
    # -------------------------------------------------

    def register(
        self,
        name: str,
        func: Callable,
        category: Optional[str] = None,
        dependencies: Optional[List[str]] = None,
    ):

        if name in self._metrics:
            raise ValueError(f"[Registry Error] Metric '{name}' already registered")

        self._metrics[name] = func
        self._dependencies[name] = list(dependencies or [])

        if category:
            self._categories[category].append(name)

    # -------------------------------------------------
    # ACCESSORS
    # -------------------------------------------------

    def get(self, name: str) -> Optional[Callable]:
        return self._metrics.get(name)

    def get_dependencies(self, name: str) -> List[str]:
        return self._dependencies.get(name, [])

    def list_metrics(self) -> List[str]:
        return list(self._metrics.keys())

    def get_category_metrics(self, category: str) -> List[str]:
        """
        Supports prefix matching.
        Example:
            category="performance"
            matches:
                performance.core
                performance.rolling
        """
        matched = []
        for cat, metrics in self._categories.items():
            if cat == category or cat.startswith(category + "."):
                matched.extend(metrics)
        return matched

    # -------------------------------------------------
    # DAG VALIDATION
    # -------------------------------------------------

    def validate(self):

        # Dependency existence
        for metric, deps in self._dependencies.items():
            for dep in deps:
                if dep not in self._metrics:
                    raise RuntimeError(
                        f"[Dependency Error] '{metric}' depends on "
                        f"unregistered metric '{dep}'"
                    )

        # Cycle detection
        visited = set()
        stack = set()

        def visit(node):

            if node in stack:
                raise RuntimeError(f"[Cycle Error] Circular dependency at '{node}'")

            if node in visited:
                return

            stack.add(node)
            for dep in self._dependencies[node]:
                visit(dep)
            stack.remove(node)

            visited.add(node)

        for metric in self._metrics:
            visit(metric)

    # -------------------------------------------------
    # EXECUTION ORDER
    # -------------------------------------------------

    def execution_order(self, subset: Optional[List[str]] = None) -> List[str]:

        self.validate()

        visited = set()
        order = []

        targets = subset or list(self._metrics.keys())

        def dfs(node):
            if node in visited:
                return
            visited.add(node)
            for dep in self._dependencies[node]:
                dfs(dep)
            order.append(node)

        for metric in targets:
            dfs(metric)

        return order


# Backward-compatible global registry used by metric modules.
registry = Registry()
