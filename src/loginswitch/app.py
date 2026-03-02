from __future__ import annotations

import uuid
from datetime import datetime

try:
    import tkinter as tk
    from tkinter import messagebox, ttk
except ModuleNotFoundError:  # pragma: no cover
    tk = None  # type: ignore[assignment]
    messagebox = None  # type: ignore[assignment]
    ttk = None  # type: ignore[assignment]

from .adapters.detector import detect_with_probe
from .bootstrap import build_services
from .confirm import ProductionConfirmer
from .models import AccountInfo, EnvironmentInfo, LoginMode, Profile


class TkConfirmer(ProductionConfirmer):
    def __init__(self, root: tk.Tk):
        self.root = root

    def confirm_production_auto_login(self, profile: Profile) -> bool:
        return messagebox.askyesno(
            "生产环境确认",
            f"即将自动登录生产环境\n服务器: {profile.env.server}\n账号: {profile.account.user_id}\n\n请确认是否继续。",
            parent=self.root,
        )


class LauncherApp:
    def __init__(self):
        if tk is None or messagebox is None or ttk is None:
            raise RuntimeError("当前 Python 环境未安装 Tk 组件，无法启动图形界面。")
        self.root = tk.Tk()
        self.root.title("LoginSwitch 启动器")
        self.root.geometry("920x520")

        self.profile_store, self.credential_store, self.launcher = build_services()
        self.launcher.confirmer = TkConfirmer(self.root)

        self._build_ui()
        self.refresh_profiles()

    def _build_ui(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        banner = tk.Label(
            self.root,
            text="环境账号快速切换",
            font=("Microsoft YaHei", 18, "bold"),
            fg="#ffffff",
            bg="#1f5f9a",
            pady=12,
        )
        banner.grid(row=0, column=0, sticky="ew")

        container = tk.Frame(self.root)
        container.grid(row=1, column=0, sticky="nsew", padx=12, pady=12)
        container.columnconfigure(0, weight=1)
        container.columnconfigure(1, weight=0)
        container.rowconfigure(0, weight=1)

        self.tree = ttk.Treeview(
            container,
            columns=("env", "server", "user", "mode"),
            show="headings",
            height=16,
        )
        self.tree.heading("env", text="环境")
        self.tree.heading("server", text="服务器")
        self.tree.heading("user", text="用户")
        self.tree.heading("mode", text="登录模式")
        self.tree.column("env", width=100)
        self.tree.column("server", width=260)
        self.tree.column("user", width=120)
        self.tree.column("mode", width=120)
        self.tree.grid(row=0, column=0, sticky="nsew")

        button_frame = tk.Frame(container)
        button_frame.grid(row=0, column=1, sticky="ns", padx=(12, 0))

        tk.Button(button_frame, text="新增", width=14, command=self.open_create_dialog).pack(pady=4)
        tk.Button(button_frame, text="编辑", width=14, command=self.open_edit_dialog).pack(pady=4)
        tk.Button(button_frame, text="删除", width=14, command=self.delete_profile).pack(pady=4)
        tk.Button(button_frame, text="保存密码", width=14, command=self.save_password_for_selected).pack(pady=4)
        tk.Button(button_frame, text="切换并启动", width=14, command=self.switch_and_launch).pack(pady=24)

        self.status_var = tk.StringVar(value="就绪")
        status = tk.Label(self.root, textvariable=self.status_var, anchor="w")
        status.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 8))

    def refresh_profiles(self) -> None:
        for row in self.tree.get_children():
            self.tree.delete(row)
        for profile in self.profile_store.list_profiles():
            mode_text = "自动" if profile.login_mode == LoginMode.AUTO else "手动"
            self.tree.insert(
                "",
                "end",
                iid=profile.id,
                values=(profile.env.label, profile.env.server, profile.account.user_id, mode_text),
                text=profile.name,
            )

    def open_create_dialog(self) -> None:
        self._open_profile_dialog(None)

    def open_edit_dialog(self) -> None:
        profile = self._get_selected_profile()
        if not profile:
            messagebox.showwarning("提示", "请先选择一个配置组")
            return
        self._open_profile_dialog(profile)

    def _open_profile_dialog(self, profile: Profile | None) -> None:
        dialog = tk.Toplevel(self.root)
        dialog.title("配置组")
        dialog.geometry("540x430")
        dialog.transient(self.root)
        dialog.grab_set()

        fields: dict[str, tk.Entry] = {}
        row = 0

        for label, key, default in [
            ("名称", "name", profile.name if profile else ""),
            ("环境标签", "env_label", profile.env.label if profile else "测试"),
            ("服务器", "server", profile.env.server if profile else "127.0.0.1:8000"),
            ("用户ID", "user_id", profile.account.user_id if profile else ""),
            ("角色", "role", profile.account.role if profile else ""),
            ("网卡", "nic", profile.account.nic if profile else ""),
            ("应用路径", "app_path", profile.app_path if profile else ""),
        ]:
            tk.Label(dialog, text=label).grid(row=row, column=0, sticky="e", padx=8, pady=6)
            entry = tk.Entry(dialog, width=42)
            entry.insert(0, default)
            entry.grid(row=row, column=1, sticky="w", padx=8, pady=6)
            fields[key] = entry
            row += 1

        tk.Label(dialog, text="登录模式").grid(row=row, column=0, sticky="e", padx=8, pady=6)
        mode_var = tk.StringVar(
            value=(profile.login_mode.value if profile else LoginMode.MANUAL.value)
        )
        ttk.Combobox(dialog, width=39, textvariable=mode_var, values=["manual", "auto"], state="readonly").grid(
            row=row, column=1, sticky="w", padx=8, pady=6
        )
        row += 1

        def on_save() -> None:
            app_path = fields["app_path"].get().strip()
            adapter_mode, adapter_config = detect_with_probe(app_path)
            now = datetime.now()
            p = Profile(
                id=profile.id if profile else uuid.uuid4().hex,
                name=fields["name"].get().strip(),
                env=EnvironmentInfo(
                    label=fields["env_label"].get().strip(),
                    server=fields["server"].get().strip(),
                ),
                account=AccountInfo(
                    user_id=fields["user_id"].get().strip(),
                    role=fields["role"].get().strip(),
                    nic=fields["nic"].get().strip(),
                ),
                login_mode=LoginMode(mode_var.get()),
                app_path=app_path,
                adapter_mode=adapter_mode,
                adapter_config=adapter_config,
                created_at=profile.created_at if profile else now,
                updated_at=now,
            )
            self.profile_store.upsert(p)
            self.refresh_profiles()
            self.status_var.set(f"已保存配置组: {p.name} ({p.adapter_mode})")
            dialog.destroy()

        tk.Button(dialog, text="保存", width=12, command=on_save).grid(row=row, column=1, sticky="w", padx=8, pady=12)

    def _get_selected_profile(self) -> Profile | None:
        selected = self.tree.selection()
        if not selected:
            return None
        profile_id = selected[0]
        return self.profile_store.get(profile_id)

    def delete_profile(self) -> None:
        profile = self._get_selected_profile()
        if not profile:
            messagebox.showwarning("提示", "请先选择一个配置组")
            return
        self.profile_store.delete(profile.id)
        self.credential_store.delete_credential(profile.id)
        self.refresh_profiles()
        self.status_var.set(f"已删除配置组: {profile.name}")

    def save_password_for_selected(self) -> None:
        profile = self._get_selected_profile()
        if not profile:
            messagebox.showwarning("提示", "请先选择一个配置组")
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("保存凭据")
        dialog.geometry("420x180")
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(dialog, text="用户名").grid(row=0, column=0, padx=8, pady=8, sticky="e")
        username_entry = tk.Entry(dialog, width=32)
        username_entry.insert(0, profile.account.user_id)
        username_entry.grid(row=0, column=1, padx=8, pady=8)

        tk.Label(dialog, text="密码").grid(row=1, column=0, padx=8, pady=8, sticky="e")
        pwd_entry = tk.Entry(dialog, width=32, show="*")
        pwd_entry.grid(row=1, column=1, padx=8, pady=8)

        def save_pwd() -> None:
            ok = self.credential_store.save_credential(
                profile.id,
                username_entry.get().strip(),
                pwd_entry.get(),
            )
            if ok:
                self.status_var.set(f"已保存凭据: {profile.name}")
                dialog.destroy()
            else:
                messagebox.showerror("错误", "保存凭据失败")

        tk.Button(dialog, text="保存", width=12, command=save_pwd).grid(row=2, column=1, padx=8, pady=10, sticky="w")

    def switch_and_launch(self) -> None:
        profile = self._get_selected_profile()
        if not profile:
            messagebox.showwarning("提示", "请先选择一个配置组")
            return

        result = self.launcher.switch_and_launch(profile)
        self.status_var.set(result.message)
        if result.success:
            messagebox.showinfo("完成", result.message)
        else:
            messagebox.showerror("失败", result.message)

    def run(self) -> None:
        self.root.mainloop()


def run_app() -> None:
    LauncherApp().run()
