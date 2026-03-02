from pathlib import Path

from loginswitch.models import AccountInfo, EnvironmentInfo, LoginMode, Profile
from loginswitch.storage import ProfileStore


def build_profile(profile_id: str) -> Profile:
    return Profile(
        id=profile_id,
        name="测试-qa",
        env=EnvironmentInfo(label="测试", server="127.0.0.1:8000"),
        account=AccountInfo(user_id="qa01", role="QA", nic="AA-BB-CC"),
        login_mode=LoginMode.MANUAL,
        app_path=r"C:\\app\\client.exe",
        adapter_mode="config_file",
        adapter_config={"path": "a.ini"},
    )


def test_profile_store_roundtrip(tmp_path: Path) -> None:
    store = ProfileStore(tmp_path / "profiles.json")
    p = build_profile("p1")

    store.upsert(p)
    loaded = store.get("p1")

    assert loaded is not None
    assert loaded.name == "测试-qa"
    assert loaded.account.user_id == "qa01"


def test_profile_store_delete(tmp_path: Path) -> None:
    store = ProfileStore(tmp_path / "profiles.json")
    p = build_profile("p2")

    store.upsert(p)
    store.delete("p2")

    assert store.get("p2") is None
