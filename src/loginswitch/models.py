from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class LoginMode(str, Enum):
    MANUAL = "manual"
    AUTO = "auto"


@dataclass
class EnvironmentInfo:
    label: str
    server: str


@dataclass
class AccountInfo:
    user_id: str
    role: str
    nic: str


@dataclass
class Profile:
    id: str
    name: str
    env: EnvironmentInfo
    account: AccountInfo
    login_mode: LoginMode
    app_path: str
    adapter_mode: str
    adapter_config: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "env": {
                "label": self.env.label,
                "server": self.env.server,
            },
            "account": {
                "userId": self.account.user_id,
                "role": self.account.role,
                "nic": self.account.nic,
            },
            "loginMode": self.login_mode.value,
            "appPath": self.app_path,
            "adapterMode": self.adapter_mode,
            "adapterConfig": self.adapter_config,
            "createdAt": self.created_at.isoformat(),
            "updatedAt": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Profile":
        return cls(
            id=data["id"],
            name=data["name"],
            env=EnvironmentInfo(
                label=data["env"]["label"],
                server=data["env"]["server"],
            ),
            account=AccountInfo(
                user_id=data["account"]["userId"],
                role=data["account"]["role"],
                nic=data["account"]["nic"],
            ),
            login_mode=LoginMode(data["loginMode"]),
            app_path=data["appPath"],
            adapter_mode=data["adapterMode"],
            adapter_config=data.get("adapterConfig", {}),
            created_at=_parse_datetime(data.get("createdAt")),
            updated_at=_parse_datetime(data.get("updatedAt")),
        )


@dataclass
class SwitchResult:
    success: bool
    message: str


def _parse_datetime(raw: str | None) -> datetime:
    if not raw:
        return datetime.now()
    return datetime.fromisoformat(raw)
