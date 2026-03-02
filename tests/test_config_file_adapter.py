from pathlib import Path

from loginswitch.adapters.config_file import ConfigFileAdapter
from loginswitch.models import AccountInfo, EnvironmentInfo, LoginMode, Profile


def build_profile(path: Path) -> Profile:
    return Profile(
        id="p1",
        name="测试",
        env=EnvironmentInfo(label="测试", server="192.168.170.154:8090"),
        account=AccountInfo(user_id="6150", role="", nic="6C-3C-8C-47-D6-03"),
        login_mode=LoginMode.MANUAL,
        app_path="C:/npserver/npserver.exe",
        adapter_mode="config_file",
        adapter_config={
            "path": str(path),
            "format": "properties",
            "keyMap": {"server": "ip", "userId": "userid", "nic": "mac"},
        },
    )


def test_properties_write_and_preserve_unknown_fields(tmp_path: Path) -> None:
    path = tmp_path / "sysclient.properties"
    path.write_text(
        "authunit=abc\n"
        "copyright=xyz\n"
        "ip=192.168.9.120:8000\n"
        "mac=OLD-MAC\n"
        "userid=200000901\n",
        encoding="utf-8",
    )

    adapter = ConfigFileAdapter()
    profile = build_profile(path)
    adapter.apply(profile, {"username": "6150", "password": None})

    content = path.read_text(encoding="utf-8")
    assert "authunit=abc" in content
    assert "copyright=xyz" in content
    assert "ip=192.168.170.154:8090" in content
    assert "mac=6C-3C-8C-47-D6-03" in content
    assert "userid=6150" in content
