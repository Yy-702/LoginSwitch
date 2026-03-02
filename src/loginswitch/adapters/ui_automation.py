from __future__ import annotations

from loginswitch.models import Profile


class UIAutomationAdapter:
    def apply(self, profile: Profile, credential: dict[str, str | None]) -> None:
        # 预留 UI 自动化接入点，可替换为 pywinauto/win32api 实现。
        _ = (profile, credential)
