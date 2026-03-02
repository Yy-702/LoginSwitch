from __future__ import annotations

from .models import Profile


class ProductionConfirmer:
    def confirm_production_auto_login(self, profile: Profile) -> bool:
        # 默认允许，GUI 层可覆盖为弹窗确认。
        return True
