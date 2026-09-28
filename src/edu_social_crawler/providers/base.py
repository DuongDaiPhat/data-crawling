from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator

from ..models import RawItem


class ProviderError(RuntimeError):
    pass


class Provider(ABC):
    name: str

    @abstractmethod
    def collect(self) -> Iterator[RawItem]:
        raise NotImplementedError
