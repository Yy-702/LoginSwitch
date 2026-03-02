from dataclasses import dataclass

from loginswitch.launcher import LauncherService
from loginswitch.models import AccountInfo, EnvironmentInfo, LoginMode, Profile


@dataclass
class FakeCreds:
    password: str = "pwd"

    def load_credential(self, profile_id: str):
        return {"username": "qa01", "password": self.password}


class FakeAdapter:
    def __init__(self):
        self.applied = False

    def apply(self, profile, credential):
        self.applied = True


class FakeProcess:
    def __init__(self):
        self.called = False

    def launch(self, app_path: str):
        self.called = True


class FakeAudit:
    def __init__(self):
        self.events = []

    def write(self, event: str, payload: dict):
        self.events.append((event, payload))


class FakeConfirm:
    def __init__(self, allow: bool):
        self.allow = allow

    def confirm_production_auto_login(self, profile):
        return self.allow


def test_switch_and_launch_manual_success() -> None:
    adapter = FakeAdapter()
    proc = FakeProcess()
    audit = FakeAudit()

    service = LauncherService(
        credential_store=FakeCreds(),
        adapters={"config_file": adapter},
        process_launcher=proc,
        audit_logger=audit,
        confirmer=FakeConfirm(True),
    )

    profile = Profile(
        id="p1",
        name="测试账号",
        env=EnvironmentInfo(label="测试", server="127.0.0.1:8000"),
        account=AccountInfo(user_id="qa01", role="QA", nic="AA"),
        login_mode=LoginMode.MANUAL,
        app_path="client.exe",
        adapter_mode="config_file",
        adapter_config={},
    )

    result = service.switch_and_launch(profile)

    assert result.success is True
    assert adapter.applied is True
    assert proc.called is True
    assert audit.events[-1][0] == "switch_success"


def test_switch_and_launch_blocks_prod_auto_without_confirm() -> None:
    adapter = FakeAdapter()
    proc = FakeProcess()
    audit = FakeAudit()

    service = LauncherService(
        credential_store=FakeCreds(),
        adapters={"config_file": adapter},
        process_launcher=proc,
        audit_logger=audit,
        confirmer=FakeConfirm(False),
    )

    profile = Profile(
        id="p2",
        name="生产账号",
        env=EnvironmentInfo(label="生产", server="192.168.1.1:8000"),
        account=AccountInfo(user_id="admin", role="管理员", nic="AA"),
        login_mode=LoginMode.AUTO,
        app_path="client.exe",
        adapter_mode="config_file",
        adapter_config={},
    )

    result = service.switch_and_launch(profile)

    assert result.success is False
    assert "取消" in result.message
    assert proc.called is False
