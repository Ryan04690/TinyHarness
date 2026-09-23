from abc import ABC, abstractmethod

class ModelProvider(ABC):

    @abstractmethod #该方法是抽象方法，子类必须实现
    def generate(self,messages,tools=None):
        pass