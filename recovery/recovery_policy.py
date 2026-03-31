from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Dict, Any


class RecoveryPolicyError(Exception):
    pass


@dataclass(frozen=True)
class RecoveryDecision:
    allow_replay: bool
    allow_execution: bool
    require_full_replay: bool
    read_only_mode: bool
    reason: str


class RecoveryPolicy:
    """
    Institutional Recovery Policy Engine

    Responsibilities:
    - Determine recovery behavior
    - Enforce safety thresholds
    - Decide replay strictness
    - Control execution resume permissions
    - Remain deterministic and auditable
    """

    VALID_MODES = {
        "strict_resume",
        "safe_resume",
        "diagnostic_mode",
        "read_only_mode",
        "cold_boot",
    }

    def __init__(self, mode: str = "strict_resume"):

        if mode not in self.VALID_MODES:
            raise RecoveryPolicyError(f"Invalid recovery mode: {mode}")

        self._mode = mode

    # ==========================================================
    # PUBLIC ENTRY
    # ==========================================================

    def evaluate(
        self,
        integrity_report,
        snapshot_available: bool,
        active_config: Optional[Dict[str, Any]],
    ) -> RecoveryDecision:

        if self._mode == "strict_resume":
            return self._strict_mode(
                integrity_report,
                snapshot_available,
                active_config,
            )

        if self._mode == "safe_resume":
            return self._safe_mode(
                integrity_report,
                snapshot_available,
                active_config,
            )

        if self._mode == "diagnostic_mode":
            return self._diagnostic_mode()

        if self._mode == "read_only_mode":
            return self._read_only_mode()

        if self._mode == "cold_boot":
            return self._cold_boot_mode()

        raise RecoveryPolicyError("Unhandled recovery mode")

    # ==========================================================
    # MODE IMPLEMENTATIONS
    # ==========================================================

    def _strict_mode(
        self,
        integrity_report,
        snapshot_available: bool,
        active_config: Optional[Dict[str, Any]],
    ) -> RecoveryDecision:

        if not integrity_report.is_valid:
            return RecoveryDecision(
                allow_replay=False,
                allow_execution=False,
                require_full_replay=False,
                read_only_mode=True,
                reason="Integrity validation failed in strict mode",
            )

        if not snapshot_available:
            return RecoveryDecision(
                allow_replay=True,
                allow_execution=False,
                require_full_replay=True,
                read_only_mode=True,
                reason="Snapshot missing — full replay required",
            )

        if not active_config:
            return RecoveryDecision(
                allow_replay=True,
                allow_execution=False,
                require_full_replay=False,
                read_only_mode=True,
                reason="Active config missing — execution blocked",
            )

        return RecoveryDecision(
            allow_replay=True,
            allow_execution=True,
            require_full_replay=False,
            read_only_mode=False,
            reason="Strict resume approved",
        )

    # ----------------------------------------------------------

    def _safe_mode(
        self,
        integrity_report,
        snapshot_available: bool,
        active_config: Optional[Dict[str, Any]],
    ) -> RecoveryDecision:

        if not integrity_report.is_valid:
            return RecoveryDecision(
                allow_replay=True,
                allow_execution=False,
                require_full_replay=True,
                read_only_mode=True,
                reason="Integrity issues detected — full replay enforced",
            )

        return RecoveryDecision(
            allow_replay=True,
            allow_execution=bool(active_config),
            require_full_replay=not snapshot_available,
            read_only_mode=not bool(active_config),
            reason="Safe resume applied",
        )

    # ----------------------------------------------------------

    def _diagnostic_mode(self) -> RecoveryDecision:

        return RecoveryDecision(
            allow_replay=True,
            allow_execution=False,
            require_full_replay=False,
            read_only_mode=True,
            reason="Diagnostic mode — execution disabled",
        )

    # ----------------------------------------------------------

    def _read_only_mode(self) -> RecoveryDecision:

        return RecoveryDecision(
            allow_replay=True,
            allow_execution=False,
            require_full_replay=False,
            read_only_mode=True,
            reason="Read-only recovery mode",
        )

    # ----------------------------------------------------------

    def _cold_boot_mode(self) -> RecoveryDecision:

        return RecoveryDecision(
            allow_replay=True,
            allow_execution=False,
            require_full_replay=True,
            read_only_mode=True,
            reason="Cold boot — ignoring snapshot",
        )

    # ==========================================================
    # INTROSPECTION
    # ==========================================================

    @property
    def mode(self) -> str:
        return self._mode