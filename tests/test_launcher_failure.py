from dataclasses import dataclass

from loginswitch.launcher import LauncherService
from loginswitch.models import AccountInfo, EnvironmentInfo, LoginMode, Profile


@dataclass
class FakeCreds:
    def load_credential(self, profile_id: str):
        return {"username": "qa01", "password": "pwd"}


class FailAdapter:
    def apply(self, profile, credential):
        return False


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
    def confirm_production_auto_login(self, profile):
        return True


def test_switch_and_launch_fail_when_adapter_apply_failed() -> None:
    proc = FakeProcess()
    audit = FakeAudit()

    service = LauncherService(
        credential_store=FakeCreds(),
        adapters={"ui_automation": FailAdapter()},
        process_launcher=proc,
        audit_logger=audit,
        confirmer=FakeConfirm(),
    )

    profile = Profile(
        id="p-fail",
        name="测试账号",
        env=EnvironmentInfo(label="测试", server="127.0.0.1:8000"),
        account=AccountInfo(user_id="qa01", role="QA", nic="AA"),
        login_mode=LoginMode.MANUAL,
        app_path="client.exe",
        adapter_mode="ui_automation",
        adapter_config={},
    )

    result = service.switch_and_launch(profile)

    assert result.success is False
    assert "回填失败" in result.message
    assert any(event == "switch_failed" for event, _ in audit.events)
