from abc import ABC, abstractmethod

class ModelProvider(ABC):

    @abstractmethod # This method is abstract, and subclasses have to implement it.
    def generate(self,messages,tools=None):
        pass