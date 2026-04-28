from abc import ABC, abstractmethod

class PropertyHandler(ABC):
    @abstractmethod
    def handle(self, prop, context_items, output, generator, adherence):
        """
        Handle generation and population of a specific property type.
        
        Args:
            prop (dict): The property schema dictionary.
            context_items (set): Current items in the context.
            output (dict): The generated output dictionary so far.
            generator (Generator): The main generator instance to access utility methods.
            adherence (float): Rule adherence factor.
        """
        pass
