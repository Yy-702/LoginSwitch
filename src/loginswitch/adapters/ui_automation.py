from __future__ import annotations

import time
from typing import Any

from loginswitch.models import Profile


class UIAutomationAdapter:
    def apply(self, profile: Profile, credential: dict[str, str | None]) -> None:
        try:
            from pywinauto import Desktop
        except ImportError:
            return

        title_re = profile.adapter_config.get("window_title_re", "系统登录|登录|管理信息系统")
        timeout = float(profile.adapter_config.get("wait_timeout_sec", 10))

        dlg = self._wait_window(Desktop(backend="uia"), title_re=title_re, timeout=timeout)
        if dlg is None:
            return

        self._fill_fields(dlg, profile, credential)
        if profile.login_mode.value == "auto":
            self._click_login(dlg)

    def _wait_window(self, desktop: Any, title_re: str, timeout: float):
        end_at = time.time() + timeout
        while time.time() < end_at:
            try:
                dlg = desktop.window(title_re=title_re)
                if dlg.exists(timeout=0.2):
                    return dlg
            except Exception:
                pass
            time.sleep(0.2)
        return None

    def _fill_fields(self, dlg: Any, profile: Profile, credential: dict[str, str | None]) -> None:
        try:
            edits = dlg.descendants(control_type="Edit")
        except Exception:
            edits = []

        if len(edits) >= 1:
            self._safe_set_text(edits[0], profile.env.server)
        if len(edits) >= 2:
            self._safe_set_text(edits[1], profile.account.user_id)
        if len(edits) >= 3 and credential.get("password"):
            self._safe_set_text(edits[2], credential["password"])

        # 角色、网卡在老系统里通常是下拉框，按常见顺序尝试写入。
        try:
            combos = dlg.descendants(control_type="ComboBox")
        except Exception:
            combos = []
        if len(combos) >= 1 and profile.account.role:
            self._safe_set_combo(combos[0], profile.account.role)
        if len(combos) >= 2 and profile.account.nic:
            self._safe_set_combo(combos[1], profile.account.nic)

    def _click_login(self, dlg: Any) -> None:
        for pattern in ("^登录$", "^Login$"):
            try:
                btn = dlg.child_window(title_re=pattern, control_type="Button")
                if btn.exists(timeout=0.2):
                    btn.click_input()
                    return
            except Exception:
                continue

    def _safe_set_text(self, element: Any, value: str) -> None:
        try:
            element.set_edit_text(value)
        except Exception:
            try:
                element.click_input()
                element.type_keys("^a{BACKSPACE}", set_foreground=False)
                element.type_keys(value, with_spaces=True, set_foreground=False)
            except Exception:
                pass

    def _safe_set_combo(self, element: Any, value: str) -> None:
        try:
            element.select(value)
            return
        except Exception:
            pass

        try:
            edit = element.child_window(control_type="Edit")
            self._safe_set_text(edit, value)
        except Exception:
            pass
