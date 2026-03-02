from __future__ import annotations

import json
from pathlib import Path

from .models import Profile


class ProfileStore:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def list_profiles(self) -> list[Profile]:
        data = self._load_json()
        return [Profile.from_dict(item) for item in data.get("profiles", [])]

    def get(self, profile_id: str) -> Profile | None:
        for profile in self.list_profiles():
            if profile.id == profile_id:
                return profile
        return None

    def upsert(self, profile: Profile) -> None:
        profiles = self.list_profiles()
        replaced = False
        for index, current in enumerate(profiles):
            if current.id == profile.id:
                profiles[index] = profile
                replaced = True
                break
        if not replaced:
            profiles.append(profile)
        self._save_profiles(profiles)

    def delete(self, profile_id: str) -> None:
        profiles = [p for p in self.list_profiles() if p.id != profile_id]
        self._save_profiles(profiles)

    def _load_json(self) -> dict:
        if not self.path.exists():
            return {"profiles": []}
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _save_profiles(self, profiles: list[Profile]) -> None:
        payload = {"profiles": [p.to_dict() for p in profiles]}
        self.path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
