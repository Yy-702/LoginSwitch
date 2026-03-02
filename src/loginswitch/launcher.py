from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .models import LoginMode, Profile, SwitchResult


@dataclass
class LauncherService:
    credential_store: object
    adapters: Mapping[str, object]
    process_launcher: object
    audit_logger: object
    confirmer: object

    def switch_and_launch(self, profile: Profile) -> SwitchResult:
        credential = self.credential_store.load_credential(profile.id)

        if self._is_prod_auto(profile):
            ok = self.confirmer.confirm_production_auto_login(profile)
            if not ok:
                self.audit_logger.write(
                    "switch_blocked",
                    {"profileId": profile.id, "reason": "production_auto_cancelled"},
                )
                return SwitchResult(False, "已取消生产环境自动登录")

        adapter = self.adapters.get(profile.adapter_mode)
        if adapter is None:
            msg = f"不支持的适配模式: {profile.adapter_mode}"
            self.audit_logger.write("switch_failed", {"profileId": profile.id, "message": msg})
            return SwitchResult(False, msg)

        adapter.apply(profile, credential)
        self.process_launcher.launch(profile.app_path)
        self.audit_logger.write(
            "switch_success",
            {
                "profileId": profile.id,
                "adapterMode": profile.adapter_mode,
                "loginMode": profile.login_mode.value,
                "env": profile.env.label,
            },
        )
        return SwitchResult(True, "切换成功，已启动客户端")

    @staticmethod
    def _is_prod_auto(profile: Profile) -> bool:
        return profile.login_mode == LoginMode.AUTO and profile.env.label == "生产"
