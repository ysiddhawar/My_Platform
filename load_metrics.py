import importlib
import importlib.util
import pkgutil
from typing import Iterable, Optional


# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------

DEFAULT_METRIC_PACKAGES = (
    "metrics",
    "portfolio",
    "robustness",
    "capital",
    "risk_control",
    "stress",
    "survival",
)

BASE_PACKAGE_CANDIDATES = ("", "My_Platform")


# ---------------------------------------------------------
# PACKAGE RESOLUTION
# ---------------------------------------------------------

def _resolve_package(sub_package: str) -> str:
    """
    Resolve package dynamically across possible base paths.
    """
    for base in BASE_PACKAGE_CANDIDATES:
        full = f"{base}.{sub_package}" if base else sub_package
        try:
            if importlib.util.find_spec(full) is not None:
                return full
        except ModuleNotFoundError:
            continue

    raise ModuleNotFoundError(
        f"[load_metrics] Could not resolve package '{sub_package}'"
    )


# ---------------------------------------------------------
# MODULE IMPORTER
# ---------------------------------------------------------

def _auto_import(sub_package: str):
    """
    Recursively import all modules inside a package.
    Registration side-effects happen during import.
    """
    full_package = _resolve_package(sub_package)
    package = importlib.import_module(full_package)

    if not hasattr(package, "__path__"):
        return

    for _, module_name, _ in pkgutil.walk_packages(
        package.__path__,
        prefix=full_package + "."
    ):
        importlib.import_module(module_name)


# ---------------------------------------------------------
# LOADERS
# ---------------------------------------------------------

def load_metrics(packages: Optional[Iterable[str]] = None):
    """
    Load metric-producing packages only.

    Parameters
    ----------
    packages : Iterable[str]
        Custom list of packages to load.
        If None → loads DEFAULT_METRIC_PACKAGES.
    """
    target_packages = packages or DEFAULT_METRIC_PACKAGES

    for sub_package in target_packages:
        _auto_import(sub_package)


def load_core_only():
    """
    Load minimal metric layer for lightweight execution.
    Useful for fast evaluation or testing.
    """
    load_metrics(packages=("metrics",))


def load_full():
    """
    Explicit full load.
    """
    load_metrics(packages=DEFAULT_METRIC_PACKAGES)


def load_all():
    """
    Backward-compatible alias used by legacy tests/callers.
    """
    load_full()
