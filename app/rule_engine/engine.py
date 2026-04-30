from __future__ import annotations

from abc import ABC, abstractmethod


class RuleEngine(ABC):
    @abstractmethod
    def run(self, task_id: str) -> None:
        raise NotImplementedError
