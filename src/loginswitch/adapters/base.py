from __future__ import annotations

from typing import Protocol

from loginswitch.models import Profile


class Adapter(Protocol):
    def apply(self, profile: Profile, credential: dict[str, str | None]) -> None:
        ...
