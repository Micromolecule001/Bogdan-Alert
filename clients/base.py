from abc import ABC, abstractmethod

class ExchangeClient(ABC):
    @abstractmethod
    def get_price(self, symbol: str) -> float:
        pass

    def get_client(self):
        return None
