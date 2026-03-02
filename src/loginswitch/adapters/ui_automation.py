from __future__ import annotations

import re
import sys
import time
from typing import Any

from loginswitch.models import Profile


class UIAutomationAdapter:
    def __init__(self) -> None:
        self.last_error = ""

    def backend_order(self) -> list[str]:
        return ["win32", "uia"]

    def parse_title_patterns(self, title_re: str) -> list[str]:
        return [item.strip() for item in title_re.split("|") if item.strip()]

    def parse_class_patterns(self, class_re: str) -> list[str]:
        return [item.strip() for item in class_re.split("|") if item.strip()]

    def apply(self, profile: Profile, credential: dict[str, str | None]) -> bool:
        self.last_error = ""
        title_re = profile.adapter_config.get("window_title_re", "系统登录|登录|管理信息系统")
        class_re = profile.adapter_config.get("window_class_re", "#32770|ThunderRT6FormDC")
        timeout = float(profile.adapter_config.get("wait_timeout_sec", 10))
        patterns = self.parse_title_patterns(title_re)
        class_patterns = self.parse_class_patterns(class_re)
        reasons: list[str] = []

        pyw_ok = self._try_with_pywinauto(profile, credential, title_re, timeout, reasons)
        if pyw_ok:
            return True

        native_ok = self._try_with_win32_native(
            profile,
            credential,
            patterns,
            class_patterns,
            timeout,
            reasons,
        )
        if native_ok:
            return True

        self.last_error = "|".join(reasons) if reasons else "unknown_error"
        return False

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

    def _try_with_pywinauto(
        self,
        profile: Profile,
        credential: dict[str, str | None],
        title_re: str,
        timeout: float,
        reasons: list[str],
    ) -> bool:
        try:
            from pywinauto import Desktop
        except ImportError:
            reasons.append("pywinauto_missing")
            return False

        dlg = None
        for backend in self.backend_order():
            dlg = self._wait_window(Desktop(backend=backend), title_re=title_re, timeout=timeout)
            if dlg is not None:
                break
        if dlg is None:
            reasons.append("window_not_found")
            return False

        filled_count = self._fill_fields(dlg, profile, credential)
        if filled_count < 2:
            reasons.append(f"pywinauto_filled_{filled_count}")
            return False

        if profile.login_mode.value == "auto":
            self._click_login(dlg)
        return True

    def _fill_fields(self, dlg: Any, profile: Profile, credential: dict[str, str | None]) -> int:
        filled = 0
        try:
            edits = dlg.descendants(control_type="Edit")
        except Exception:
            edits = []
        if not edits:
            edits = self._fallback_find_by_class(dlg, "Edit")

        if len(edits) >= 1:
            self._safe_set_text(edits[0], profile.env.server)
            filled += 1
        if len(edits) >= 2:
            self._safe_set_text(edits[1], profile.account.user_id)
            filled += 1
        if len(edits) >= 3 and credential.get("password"):
            self._safe_set_text(edits[2], credential["password"])
            filled += 1

        # 角色、网卡在老系统里通常是下拉框，按常见顺序尝试写入。
        try:
            combos = dlg.descendants(control_type="ComboBox")
        except Exception:
            combos = []
        if not combos:
            combos = self._fallback_find_by_class(dlg, "ComboBox")
        if len(combos) >= 1 and profile.account.role:
            self._safe_set_combo(combos[0], profile.account.role)
        if len(combos) >= 2 and profile.account.nic:
            self._safe_set_combo(combos[1], profile.account.nic)
        return filled

    def _click_login(self, dlg: Any) -> None:
        for pattern in ("^登录$", "^Login$"):
            try:
                btn = dlg.child_window(title_re=pattern, control_type="Button")
                if btn.exists(timeout=0.2):
                    btn.click_input()
                    return
            except Exception:
                continue
        try:
            buttons = dlg.descendants(class_name="Button")
        except Exception:
            buttons = []
        for button in buttons:
            try:
                text = button.window_text()
            except Exception:
                text = ""
            if text in ("登录", "Login"):
                try:
                    button.click_input()
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

    def _fallback_find_by_class(self, dlg: Any, class_name: str) -> list[Any]:
        try:
            return dlg.descendants(class_name=class_name)
        except Exception:
            return []

    def _try_with_win32_native(
        self,
        profile: Profile,
        credential: dict[str, str | None],
        title_patterns: list[str],
        class_patterns: list[str],
        timeout: float,
        reasons: list[str],
    ) -> bool:
        if sys.platform != "win32":
            reasons.append("native_not_windows")
            return False

        try:
            import ctypes
            from ctypes import wintypes
        except Exception:
            reasons.append("native_ctypes_unavailable")
            return False

        user32 = ctypes.windll.user32
        hwnd = self._native_wait_main_window(user32, wintypes, title_patterns, class_patterns, timeout)
        if not hwnd:
            reasons.append("native_window_not_found")
            return False

        edits = self._native_enum_children_by_class(user32, wintypes, hwnd, "Edit")
        combos = self._native_enum_children_by_class(user32, wintypes, hwnd, "ComboBox")

        filled = 0
        if len(edits) >= 1 and self._native_set_text(user32, edits[0], profile.env.server, verify=True):
            filled += 1
        if len(edits) >= 2 and self._native_set_text(user32, edits[1], profile.account.user_id, verify=True):
            filled += 1
        if len(edits) >= 3 and credential.get("password"):
            if self._native_set_text(user32, edits[2], str(credential["password"]), verify=False):
                filled += 1

        if len(combos) >= 1 and profile.account.role:
            self._native_set_text(user32, combos[0], profile.account.role, verify=False)
        if len(combos) >= 2 and profile.account.nic:
            self._native_set_text(user32, combos[1], profile.account.nic, verify=False)

        if profile.login_mode.value == "auto":
            self._native_click_login(user32, wintypes, hwnd)

        if filled >= 2:
            return True

        reasons.append(f"native_filled_{filled}")
        reasons.append("tip_try_run_as_admin")
        return False

    def _native_wait_main_window(
        self,
        user32: Any,
        wintypes: Any,
        title_patterns: list[str],
        class_patterns: list[str],
        timeout: float,
    ) -> int:
        end_at = time.time() + timeout
        while time.time() < end_at:
            hwnd = self._native_find_main_window(user32, wintypes, title_patterns, class_patterns)
            if hwnd:
                return hwnd
            time.sleep(0.2)
        return 0

    def _native_find_main_window(
        self,
        user32: Any,
        wintypes: Any,
        title_patterns: list[str],
        class_patterns: list[str],
    ) -> int:
        import ctypes

        found = 0

        @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        def enum_proc(hwnd: int, _lparam: int) -> bool:
            nonlocal found
            if not user32.IsWindowVisible(hwnd):
                return True
            title = self._native_window_text(user32, hwnd)
            cls = self._native_class_name(user32, hwnd)
            if self._title_matches(title, title_patterns) or self._class_matches(cls, class_patterns):
                found = int(hwnd)
                return False
            return True

        user32.EnumWindows(enum_proc, 0)
        return found

    def _native_enum_children_by_class(
        self,
        user32: Any,
        wintypes: Any,
        parent_hwnd: int,
        class_prefix: str,
    ) -> list[int]:
        import ctypes

        handles: list[int] = []
        target = class_prefix.lower()

        @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        def enum_child_proc(hwnd: int, _lparam: int) -> bool:
            cls = self._native_class_name(user32, hwnd).lower()
            if cls.startswith(target):
                handles.append(int(hwnd))
            return True

        user32.EnumChildWindows(parent_hwnd, enum_child_proc, 0)
        return handles

    def _native_window_text(self, user32: Any, hwnd: int) -> str:
        import ctypes

        length = user32.GetWindowTextLengthW(hwnd)
        if length <= 0:
            return ""
        buff = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buff, length + 1)
        return buff.value

    def _native_class_name(self, user32: Any, hwnd: int) -> str:
        import ctypes

        buff = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(hwnd, buff, 256)
        return buff.value

    def _native_set_text(self, user32: Any, hwnd: int, value: str, verify: bool) -> bool:
        import ctypes

        WM_SETTEXT = 0x000C
        user32.SendMessageW(hwnd, WM_SETTEXT, 0, ctypes.c_wchar_p(value))
        if not verify:
            return True
        current = self._native_window_text(user32, hwnd)
        return current == value

    def _native_click_login(self, user32: Any, wintypes: Any, parent_hwnd: int) -> None:
        BM_CLICK = 0x00F5
        button_handles = self._native_enum_children_by_class(user32, wintypes, parent_hwnd, "Button")
        for hwnd in button_handles:
            text = self._native_window_text(user32, hwnd)
            if text in ("登录", "Login"):
                user32.SendMessageW(hwnd, BM_CLICK, 0, 0)
                return

    def _title_matches(self, title: str, patterns: list[str]) -> bool:
        if not title:
            return False
        for pattern in patterns:
            try:
                if re.search(pattern, title, re.IGNORECASE):
                    return True
            except re.error:
                if pattern in title:
                    return True
        return False

    def _class_matches(self, class_name: str, patterns: list[str]) -> bool:
        if not class_name:
            return False
        for pattern in patterns:
            try:
                if re.search(pattern, class_name, re.IGNORECASE):
                    return True
            except re.error:
                if pattern.lower() in class_name.lower():
                    return True
        return False
