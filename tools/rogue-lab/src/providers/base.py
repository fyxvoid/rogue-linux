from abc import ABC, abstractmethod

class LabProvider(ABC):
    """
    Abstract Base Class for Rogue Lab Cloud Providers.
    All providers (AWS, Azure, Docker) must implement this interface.
    """

    @abstractmethod
    def provision_lab(self, lab_id: str, config: dict) -> dict:
        """
        Provision the lab infrastructure.
        Returns: dict containing 'ip', 'status', 'id'
        """
        pass

    @abstractmethod
    def terminate_lab(self, instance_id: str) -> bool:
        """
        Terminate and cleanup the lab infrastructure.
        """
        pass

    @abstractmethod
    def get_status(self, instance_id: str) -> str:
        """
        Get the current status of the lab (PROVISIONING, RUNNING, TERMINATED).
        """
        pass
