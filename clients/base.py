from abc import ABC, abstractmethod

class ExchangeClient(ABC):
    @abstractmethod
    def get_price(self, symbol: str) -> float:
        pass
