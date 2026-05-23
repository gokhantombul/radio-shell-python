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
        # Use a short interval for the first call or repeated calls
        cpu = psutil.cpu_percent(interval=0.1)
        
        # Get virtual memory info safely
        try:
            vmem = psutil.virtual_memory()._asdict()
        except Exception:
            vmem = {"total": 0, "available": 0, "percent": 0, "used": 0, "free": 0}

        return {
            "cpu_percent": cpu,
            "virtual_memory": vmem,
            "os": f"{platform.system()} {platform.release()}",
            "python_version": platform.python_version()
        }

    def get_web_info(self) -> Dict[str, Any]:
        """Returns a summary of system information for the web interface."""
        mem = self.get_memory_info()
        stats = self.get_system_stats()
        
        # Calculate total memory usage in MB for the web UI
        total_mem_mb = round(mem["total_memory"] / 1024 / 1024, 2)
        
        return {
            "os": stats["os"],
            "python_version": stats["python_version"],
            "memory_usage_mb": total_mem_mb,
            "cpu_percent": stats["cpu_percent"]
        }

    def format_bytes(self, n: int) -> str:
        """Converts bytes to human readable string."""
        nf = float(n)
        for unit in ['B', 'KB', 'MB', 'GB']:
            if nf < 1024:
                return f"{nf:.2f} {unit}"
            nf /= 1024
        return f"{nf:.2f} TB"
