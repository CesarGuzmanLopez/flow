"""
Puertos (interfaces) para la capa de aplicación de flujos.

Define contratos para interacciones con servicios externos (chemistry, etc).
Implementados en infraestructura siguiendo patrón de puertos y adaptadores.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class IChemistryPort(ABC):
    """
    Puerto para interacciones con la app Chemistry.

    Permite que flows/domain/steps dependan de abstracción,
    no de implementación directa de chemistry.services.
    """

    @abstractmethod
    def create_family_from_smiles(
        self, name: str, smiles_list: List[str], created_by: Any
    ) -> Any:
        """
        Crea una familia de moléculas a partir de SMILES.

        Returns:
            Family: Entidad de familia creada
        """
        pass

    @abstractmethod
    def get_family(self, family_id: int) -> Any:
        """Obtiene familia por ID."""
        pass

    @abstractmethod
    def generate_admetsa_properties(
        self, family_id: int, created_by: Any
    ) -> Dict[str, Any]:
        """
        Genera propiedades ADMETSA para una familia.

        Args:
            family_id: ID de la familia
            created_by: Usuario que inicia la generación

        Returns:
            dict con resultados de propiedades
        """
        pass

    @abstractmethod
    def create_molecule_from_smiles(self, smiles: str, created_by: Any) -> Any:
        """Crea moléculas a partir de SMILES."""
        pass
