from __future__ import annotations

from loginswitch.models import Profile


class RegistryAdapter:
    def apply(self, profile: Profile, credential: dict[str, str | None]) -> None:
        # 当前仓库环境可能非 Windows，先保留接口，
        # 在 Windows 运行时可扩展 winreg 实际写入。
        _ = (profile, credential)
