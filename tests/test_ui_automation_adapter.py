from loginswitch.adapters.ui_automation import UIAutomationAdapter


def test_backend_order_prioritizes_win32() -> None:
    adapter = UIAutomationAdapter()
    assert adapter.backend_order() == ["win32", "uia"]


def test_parse_title_patterns() -> None:
    adapter = UIAutomationAdapter()
    patterns = adapter.parse_title_patterns("系统登录|广州医药.*管理信息系统| Login ")
    assert patterns == ["系统登录", "广州医药.*管理信息系统", "Login"]
