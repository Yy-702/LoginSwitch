from __future__ import annotations

import subprocess


class ProcessLauncher:
    def launch(self, app_path: str) -> None:
        # 使用 shell=False，避免命令注入风险。
        subprocess.Popen([app_path], shell=False)
