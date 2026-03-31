from __future__ import annotations

from typing import Dict, List, Set, Callable, Any
from threading import RLock


class DependencyGraphError(Exception):
    pass


class DependencyGraph:
    """
    Institutional Directed Acyclic Dependency Graph (DAG)

    Responsibilities:
    - Register nodes
    - Register event bindings
    - Maintain execution order
    - Prevent circular dependencies
    - Provide deterministic traversal
    - Support recovery replay
    """

    def __init__(self):

        self._lock = RLock()

        # node_name -> callable
        self._nodes: Dict[str, Callable] = {}

        # node_name -> set(dependency_node_names)
        self._edges: Dict[str, Set[str]] = {}

        # event_type -> list(node_names)
        self._event_bindings: Dict[str, List[str]] = {}

    # ==========================================================
    # NODE REGISTRATION
    # ==========================================================

    def register_node(
        self,
        name: str,
        handler: Callable,
        depends_on: List[str] | None = None,
    ):

        with self._lock:

            if name in self._nodes:
                raise DependencyGraphError(f"Node '{name}' already registered")

            self._nodes[name] = handler
            self._edges[name] = set(depends_on or [])

            self._validate_no_cycle()

    # ==========================================================
    # EVENT BINDING
    # ==========================================================

    def bind_event(
        self,
        event_type: str,
        node_name: str,
    ):

        with self._lock:

            if node_name not in self._nodes:
                raise DependencyGraphError(
                    f"Cannot bind unknown node '{node_name}'"
                )

            self._event_bindings.setdefault(event_type, [])
            self._event_bindings[event_type].append(node_name)

    # ==========================================================
    # RETRIEVE ORDERED NODES FOR EVENT
    # ==========================================================

    def get_nodes_for_event(self, event_type: str) -> List[Callable]:

        with self._lock:

            node_names = self._event_bindings.get(event_type, [])

            ordered = self._topological_sort(node_names)

            return [self._nodes[name] for name in ordered]

    # ==========================================================
    # TOPOLOGICAL SORT
    # ==========================================================

    def _topological_sort(self, target_nodes: List[str]) -> List[str]:

        visited: Set[str] = set()
        temp_mark: Set[str] = set()
        result: List[str] = []

        def visit(node: str):

            if node in temp_mark:
                raise DependencyGraphError("Circular dependency detected")

            if node not in visited:
                temp_mark.add(node)

                for dep in self._edges.get(node, []):
                    if dep in target_nodes:
                        visit(dep)

                temp_mark.remove(node)
                visited.add(node)
                result.append(node)

        for node in target_nodes:
            visit(node)

        return result

    # ==========================================================
    # CYCLE VALIDATION
    # ==========================================================

    def _validate_no_cycle(self):

        all_nodes = list(self._nodes.keys())
        self._topological_sort(all_nodes)

    # ==========================================================
    # INTROSPECTION
    # ==========================================================

    def list_nodes(self) -> List[str]:
        return list(self._nodes.keys())

    def list_event_bindings(self) -> Dict[str, List[str]]:
        return dict(self._event_bindings)