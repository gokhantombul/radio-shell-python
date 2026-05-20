import os
import psutil
import platform
from typing import Dict, Any
from src.radio.player import AudioPlayer


class SystemService:
    def __init__(self, player: AudioPlayer):
        self.player = player
        self.process = psutil.Process(os.getpid())

    def get_memory_info(self) -> Dict[str, Any]:
        """Returns memory usage of the current process and its children (like ffplay)."""
        # Main process memory
        main_mem = self.process.memory_info().rss

        # Child processes memory (ffplay)
        children_mem = 0
        children_list = []

        for child in self.process.children(recursive=True):
            try:
                name = child.name()
                mem = child.memory_info().rss
                children_mem += mem
                children_list.append({"name": name, "memory": mem})
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        return {
            "main_process": main_mem,
            "children_processes": children_list,
            "total_children_memory": children_mem,
            "total_memory": main_mem + children_mem
        }

    def get_system_stats(self) -> Dict[str, Any]:
        """Returns general system information."""
        return {
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "virtual_memory": psutil.virtual_memory()._asdict(),
            "os": f"{platform.system()} {platform.release()}",
            "python_version": platform.python_version()
        }

    def format_bytes(self, n: int) -> str:
        """Converts bytes to human readable string."""
        nf = float(n)
        for unit in ['B', 'KB', 'MB', 'GB']:
            if nf < 1024:
                return f"{nf:.2f} {unit}"
            nf /= 1024
        return f"{nf:.2f} TB"
