# LoginSwitch

桌面客户端环境与账号快速切换启动器（外部启动器方案）。

## 功能

- 管理“环境 + 账号”配置组
- 自动探测适配模式（`config_file` -> `registry` -> `ui_automation`）
- 一键切换并启动目标客户端
- 支持手动登录/自动登录
- 生产环境自动登录二次确认
- 使用系统凭据库保存密码（不明文落盘）
- 本地审计日志（不含密码）

## 快速开始

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
python -m loginswitch
```

## 本地数据路径

- Windows: `%APPDATA%/LoginSwitch`
- 其他系统: `~/.loginswitch`

包含：

- `profiles.json`：配置组（非敏感）
- `audit.log`：操作审计

## 测试

```bash
source .venv/bin/activate
pytest -q
```

## 说明

- `registry` 与 `ui_automation` 在当前版本先提供稳定接口，便于按项目实际快速扩展。
- 建议上线时优先启用 `config_file` 对接，后续按系统形态补充注册表与控件自动化实现。
