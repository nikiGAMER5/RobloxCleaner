"""Process detection and termination utility for Roblox instances."""

from __future__ import annotations

import time
from typing import List, Tuple

import psutil

from app.utils.logger import get_logger

ROBLOX_PROCESS_NAMES = {
    "robloxplayerbeta.exe",
    "robloxplayerlauncher.exe",
    "robloxstudiobeta.exe",
    "robloxstudio.exe",
    "robloxcrashhandler.exe",
    "robloxservice.exe",
    "robloxplayerinstaller.exe",
    "robloxstudioinstaller.exe",
}


class RobloxProcessManager:
    """Detects and manages running Roblox desktop processes."""

    def __init__(self) -> None:
        self.logger = get_logger()

    @staticmethod
    def get_running_roblox_processes() -> List[psutil.Process]:
        """Find all currently active Roblox processes."""
        found = []
        for proc in psutil.process_iter(["pid", "name"]):
            try:
                name = proc.info.get("name")
                if name and name.lower() in ROBLOX_PROCESS_NAMES:
                    found.append(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        return found

    @classmethod
    def is_roblox_running(cls) -> bool:
        """Check if any Roblox process is currently executing."""
        return len(cls.get_running_roblox_processes()) > 0

    def terminate_roblox(self, timeout_sec: float = 3.0) -> Tuple[int, int, str]:
        """Gracefully terminate running Roblox processes, forcing kill if necessary.

        Returns:
            (terminated_count, failed_count, message)
        """
        processes = self.get_running_roblox_processes()
        if not processes:
            return 0, 0, "Kein laufender Roblox-Prozess gefunden."

        terminated_count = 0
        failed_count = 0

        self.logger.info(f"Beende {len(processes)} aktive Roblox-Prozesse...")

        for proc in processes:
            try:
                proc_name = proc.name()
                pid = proc.pid
                self.logger.info(f"Beende Prozess: {proc_name} (PID: {pid})")

                proc.terminate()
            except (psutil.NoSuchProcess, psutil.AccessDenied) as exc:
                self.logger.warning(f"Konnte Prozess nicht beenden: {exc}")

        gone, alive = psutil.wait_procs(processes, timeout=timeout_sec)
        terminated_count += len(gone)

        for proc in alive:
            try:
                self.logger.warning(f"Erzwinge Schließen von: {proc.name()} (PID: {proc.pid})")
                proc.kill()
                terminated_count += 1
            except Exception as exc:
                failed_count += 1
                self.logger.error(f"Fehler beim Schließen von PID {proc.pid}: {exc}")

        msg = f"{terminated_count} Roblox-Prozess(e) erfolgreich beendet."
        if failed_count > 0:
            msg += f" {failed_count} Prozess(e) konnten nicht beendet werden."

        self.logger.info(msg)
        return terminated_count, failed_count, msg
