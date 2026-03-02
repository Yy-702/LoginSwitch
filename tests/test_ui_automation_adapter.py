from loginswitch.adapters.ui_automation import UIAutomationAdapter


def test_backend_order_prioritizes_win32() -> None:
    adapter = UIAutomationAdapter()
    assert adapter.backend_order() == ["win32", "uia"]
