# GUÍA DE EXTENSIÓN - Chemistry Module

Documentación para desarrolladores externos que deseen extender el módulo chemistry con nuevos providers, engines o funcionalidades.

## Tabla de Contenidos

1. [Arquitectura General](#arquitectura-general)
2. [Crear un PropertyProvider Custom](#crear-un-propertyprovider-custom)
3. [Crear un ChemEngine Custom](#crear-un-chemengine-custom)
4. [Registrar en Factory](#registrar-en-factory)
5. [Testing](#testing)
6. [Best Practices](#best-practices)

---

## ARQUITECTURA GENERAL

### Hexagonal Architecture (Ports & Adapters)

```
┌─────────────────────────────────────┐
│ API Layer (Views)                   │
│ - REST endpoints                    │
│ - Request/Response serialization    │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│ Application Services                │
│ - create_molecule_from_smiles       │
│ - create_family_from_smiles         │
│ - generate_properties_for_family    │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│ PORTS (Abstracciones)               │
│ - ChemEngineInterface (Protocol)    │
│ - PropertyProviderInterface (ABC)   │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│ ADAPTERS (Implementaciones)         │
│ - RDKitChemEngine                   │
│ - MockChemEngine                    │
│ - RDKitPropertyProvider             │
│ - ManualPropertyProvider            │
│ - CustomProviders ← TÚ AQUÍ          │
└─────────────────────────────────────┘
```

### Patrón de Dependencia

```
                  Factory (Registry pattern)
                         ↑
                         │
API Views ────→ Services ────→ PropertyProviders
                         │
                         └───→ ChemEngines
```

---

## CREAR UN PROPERTYPROVIDER CUSTOM

### Paso 1: Entender la Interfaz

```python
from chemistry.providers.interfaces import (
    AbstractPropertyProvider,
    PropertyInfo,
    PropertyProviderInfo,
)

class MyCustomProvider(AbstractPropertyProvider):
    """
    Template Method pattern: Solo implementa 3 métodos:
    1. _initialize_metadata() → PropertyProviderInfo
    2. _initialize_properties() → Dict[str, PropertyInfo]
    3. _calculate_properties_impl() → Dict[str, Any]
    """
```

### Paso 2: Definir Metadata

```python
def _initialize_metadata(self) -> PropertyProviderInfo:
    """
    >>> provider = MyCustomProvider()
    >>> info = provider.get_metadata()
    >>> print(info.name)
    my_custom
    """
    return PropertyProviderInfo(
        name="my_custom",
        display_name="My Custom Provider",
        is_computational=False,  # True si usa RDKit/complejos
        requires_external_data=True,  # True si necesita entrada user
        supported_categories=["admet", "physics"],
        description="Custom implementation for..."
    )
```

### Paso 3: Definir Propiedades

```python
def _initialize_properties(self) -> Dict[str, PropertyInfo]:
    """
    >>> provider = MyCustomProvider()
    >>> props = provider.get_properties()
    >>> print(list(props.keys()))
    ['MolWt', 'LogP', 'TPSA']
    """
    return {
        "MolWt": PropertyInfo(
            name="MolWt",
            description="Molecular weight",
            units="g/mol",
            value_type="float",
            range_min=0,
            range_max=2000
        ),
        "LogP": PropertyInfo(
            name="LogP",
            description="Lipophilicity",
            units="",
            value_type="float",
            range_min=-10,
            range_max=10
        ),
        # ... más propiedades
    }
```

### Paso 4: Implementar Cálculo

```python
def _calculate_properties_impl(
    self,
    smiles: str,
    properties_data: Dict[str, Any] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Implementación del algoritmo.

    >>> provider = MyCustomProvider()
    >>> result = provider.calculate_properties(
    ...     smiles="CCO",
    ...     properties_data={"MolWt": {"value": 46.07}}
    ... )
    >>> assert "MolWt" in result
    """

    if not properties_data:
        return {}

    validated = {}

    for prop_name, prop_data in properties_data.items():
        if prop_name not in self._properties:
            continue  # Skip unknown

        prop_info = self._properties[prop_name]
        value = prop_data.get("value")

        # VALIDAR RANGO
        if prop_info.range_min is not None and value < prop_info.range_min:
            raise ValueError(f"{prop_name}: value too low")

        if prop_info.range_max is not None and value > prop_info.range_max:
            raise ValueError(f"{prop_name}: value too high")

        # GUARDAR CON SOURCE
        validated[prop_name] = {
            "value": value,
            "units": prop_data.get("units", ""),
            "source": "my_custom",  # ← Identificar origen
            "method": "custom_algorithm"
        }

    return validated
```

### Ejemplo Completo: Predictor Bayesiano

```python
# chemistry/providers/bayesian_provider.py

from typing import Dict, Any
from chemistry.providers.interfaces import (
    AbstractPropertyProvider,
    PropertyInfo,
    PropertyProviderInfo,
)
import pickle

class BayesianPropertyProvider(AbstractPropertyProvider):
    """
    Provider usando modelos Bayesianos pre-entrenados.

    Caso de uso:
    - Empresas quieren usar modelos internos
    - Más rápido que RDKit, menos preciso
    - No requiere licencia de RDKit

    >>> provider = BayesianPropertyProvider()
    >>> provider.calculate_properties(
    ...     smiles="CCO",
    ...     model_file="/path/to/bayes_model.pkl"
    ... )
    """

    def _initialize_metadata(self) -> PropertyProviderInfo:
        return PropertyProviderInfo(
            name="bayesian",
            display_name="Bayesian Models",
            is_computational=True,
            requires_external_data=False,
            supported_categories=["admet"],
            description="Fast predictions using Bayesian models"
        )

    def _initialize_properties(self) -> Dict[str, PropertyInfo]:
        return {
            "MolWt": PropertyInfo(
                name="MolWt",
                description="Molecular weight (Bayesian prediction)",
                units="g/mol",
                value_type="float",
                range_min=10,
                range_max=1000
            ),
            "LogP": PropertyInfo(
                name="LogP",
                description="LogP (Bayesian prediction)",
                units="",
                value_type="float",
                range_min=-5,
                range_max=8
            ),
            "TPSA": PropertyInfo(
                name="TPSA",
                description="Topological PSA (Bayesian prediction)",
                units="Ų",
                value_type="float",
                range_min=0,
                range_max=300
            ),
        }

    def _calculate_properties_impl(
        self,
        smiles: str,
        properties_data: Dict[str, Any] = None,
        model_file: str = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Usar modelo guardado para predicciones.

        >>> result = provider.calculate_properties(
        ...     smiles="CCO",
        ...     model_file="/models/bayes_admet.pkl"
        ... )
        """

        if not model_file:
            raise ValueError("model_file parameter required")

        # Cargar modelo
        try:
            with open(model_file, 'rb') as f:
                model = pickle.load(f)
        except Exception as e:
            raise RuntimeError(f"Cannot load model: {e}")

        # Convertir SMILES a descriptores
        # (Usar método que esté disponible, ej. rdkit)
        try:
            from rdkit.Chem import MolFromSmiles, Descriptors
            mol = MolFromSmiles(smiles)
            if mol is None:
                raise ValueError(f"Invalid SMILES: {smiles}")

            # Calcular descriptores
            desc = self._compute_descriptors(mol)
        except Exception as e:
            raise ValueError(f"Cannot compute descriptors: {e}")

        # Predecir propiedades
        predictions = {}
        for prop_name in ["MolWt", "LogP", "TPSA"]:
            try:
                # Simulado: model.predict(desc)
                pred_value = model.predict([desc])[0]

                predictions[prop_name] = {
                    "value": float(pred_value),
                    "units": self._properties[prop_name].units,
                    "source": "bayesian",
                    "method": "bayesian_model",
                    "confidence": 0.85  # Metadata extra
                }
            except Exception:
                continue

        return predictions

    def _compute_descriptors(self, mol):
        """Extract descriptors from molecule."""
        from rdkit.Chem import Descriptors
        return [
            Descriptors.MolWt(mol),
            Descriptors.LogP(mol),
            Descriptors.TPSA(mol),
            # ... más descriptores
        ]
```

---

## CREAR UN CHEMENGINE CUSTOM

### Interfaz a Implementar

```python
from typing import Protocol

class ChemEngineInterface(Protocol):
    """
    Protocol: Define qué debe implementar un motor de química.

    Protocolos (Structural Subtyping):
    - No requiere heredar
    - Solo implementar estos 3 métodos
    """

    def smiles_to_inchi(self, smiles: str) -> StructureIdentifiers:
        """Convert SMILES to InChI/InChIKey."""
        ...

    def calculate_properties(self, smiles: str) -> MolecularProperties:
        """Calculate basic properties."""
        ...

    def generate_substitutions(self, smiles: str) -> SubstitutionResult:
        """Generate substitution variants."""
        ...
```

### Paso 1: Crear la Clase

```python
# chemistry/providers/custom_engine.py

from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class StructureIdentifiers:
    """Output de smiles_to_inchi."""
    inchi: str
    inchikey: str
    canonical_smiles: str
    molecular_formula: str

class MyCustomChemEngine:
    """
    Motor de química personalizado.

    >>> engine = MyCustomChemEngine()
    >>> result = engine.smiles_to_inchi("CCO")
    >>> print(result.inchikey)
    LFQSCWFLJHTTHZ-UHFFFAOYSA-N
    """

    def smiles_to_inchi(self, smiles: str) -> StructureIdentifiers:
        """
        Convertir SMILES a estructura canónica.

        Tu implementación puede:
        1. Usar RDKit
        2. Usar OpenBabel
        3. Llamar API externa
        4. Usar base de datos pre-calculada
        """

        # Ejemplo: Usar RDKit
        from rdkit.Chem import MolToInchi, MolToInchiKey, MolFromSmiles

        mol = MolFromSmiles(smiles)
        if mol is None:
            raise InvalidSmilesError(f"Cannot parse: {smiles}")

        return StructureIdentifiers(
            inchi=MolToInchi(mol),
            inchikey=MolToInchiKey(mol),
            canonical_smiles=smiles,  # Ya es canónico
            molecular_formula=self._get_formula(mol)
        )

    def calculate_properties(self, smiles: str):
        """Calcular propiedades básicas."""
        # Tu lógica aquí
        pass

    def generate_substitutions(self, smiles: str):
        """Generar variantes."""
        # Tu lógica aquí
        pass
```

### Paso 2: Registrar Motor

```python
# En factory.py o provision.py

from chemistry.providers.custom_engine import MyCustomChemEngine

# Opción 1: Usar por defecto
_engine = MyCustomChemEngine()

# Opción 2: Selector de motor
def get_engine(engine_type: str = "rdkit"):
    if engine_type == "rdkit":
        return RDKitChemEngine()
    elif engine_type == "my_custom":
        return MyCustomChemEngine()
    elif engine_type == "mock":
        return MockChemEngine()
    else:
        raise ValueError(f"Unknown engine: {engine_type}")

# Opción 3: Inyección de dependencia
def create_molecule_from_smiles(
    *,
    smiles: str,
    engine: ChemEngineInterface = None,
    **kwargs
):
    if engine is None:
        engine = get_engine("rdkit")

    structure = engine.smiles_to_inchi(smiles)
    # ...
```

---

## REGISTRAR EN FACTORY

### Patrón Registry

```python
# chemistry/providers/factory.py

from chemistry.providers.custom_provider import BayesianPropertyProvider
from chemistry.providers.bayesian_engine import BayesianChemEngine

class PropertyProviderFactory:
    def __init__(self, registry=None):
        self._registry = registry or PropertyProviderRegistry()
        self._setup_default_providers()

    def _setup_default_providers(self):
        """Register built-in providers."""
        from chemistry.providers.property_providers import (
            RDKitProvider,
            ManualProvider,
            RandomProvider,
        )

        self._registry.register("rdkit", RDKitProvider())
        self._registry.register("manual", ManualProvider())
        self._registry.register("random", RandomProvider())

        # ← AGREGAR TUS PROVIDERS
        self._registry.register("bayesian", BayesianPropertyProvider())
```

### Uso en Servicios

```python
# chemistry/services/properties.py

def create_or_update_molecular_property(
    *,
    molecule,
    property_type: str,
    value: str,
    method: str = "unknown",
    relation: str = "exact",
    source_id: str = "system",
    provider: str = "rdkit",  # ← Parámetro nuevo
    **kwargs
):
    """Create or update property using specified provider."""

    # Obtener provider del factory
    factory = PropertyProviderFactory()
    prov = factory.get_provider(provider)

    # Usar provider
    props = prov.calculate_properties(
        smiles=molecule.smiles,
        properties_data=kwargs.get("properties_data")
    )

    # Guardar resultados
    for prop_name, prop_info in props.items():
        MolecularProperty.objects.update_or_create(
            molecule=molecule,
            property_type=prop_name,
            method=provider,
            defaults={
                "value": prop_info["value"],
                "units": prop_info["units"],
                "source_id": provider
            }
        )
```

### Uso en API

```python
# chemistry/views/molecules.py

class MoleculePropertyViewSet(viewsets.ModelViewSet):
    def calculate_properties(self, request, pk=None):
        """
        POST /api/molecules/{id}/properties/calculate/

        Body:
        {
            "provider": "bayesian",  # ← Especificar provider
            "model_file": "/models/model.pkl"
        }
        """
        molecule = self.get_object()

        provider = request.data.get("provider", "rdkit")

        # Usar provider especificado
        from chemistry.services import create_or_update_molecular_property

        result = create_or_update_molecular_property(
            molecule=molecule,
            property_type=request.data.get("property_type"),
            value=request.data.get("value"),
            provider=provider
        )

        return Response({"status": "calculated", "result": result})
```

---

## TESTING

### Test de Provider Custom

```python
# chemistry/tests/test_my_custom_provider.py

import pytest
from chemistry.providers.custom_provider import MyCustomProvider

class TestMyCustomProvider:
    @pytest.fixture
    def provider(self):
        return MyCustomProvider()

    def test_metadata(self, provider):
        """Verificar metadata."""
        info = provider.get_metadata()
        assert info.name == "my_custom"
        assert not info.is_computational

    def test_calculate_properties(self, provider):
        """Verificar cálculo."""
        result = provider.calculate_properties(
            smiles="CCO",
            properties_data={
                "MolWt": {"value": 46.07, "units": "g/mol"}
            }
        )

        assert "MolWt" in result
        assert result["MolWt"]["source"] == "my_custom"

    def test_validation(self, provider):
        """Verificar validación de rangos."""
        with pytest.raises(ValueError):
            provider.calculate_properties(
                smiles="CCO",
                properties_data={
                    "MolWt": {"value": -10, "units": "g/mol"}  # OUT OF RANGE
                }
            )
```

### Test de Integración

```python
# chemistry/tests/test_custom_provider_integration.py

from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()

def test_calculate_properties_with_custom_provider():
    """Test uso desde API."""
    client = APIClient()
    user = User.objects.create_user("testuser", password="pass")
    client.force_authenticate(user=user)

    from chemistry.services import create_molecule_from_smiles
    mol = create_molecule_from_smiles(
        smiles="CCO",
        created_by=user
    )

    # Request with custom provider
    response = client.post(
        f"/api/chemistry/molecules/{mol.id}/properties/calculate/",
        {
            "provider": "bayesian",
            "model_file": "/models/model.pkl"
        }
    )

    assert response.status_code == 200
    assert "result" in response.json()
```

---

## BEST PRACTICES

### 1. Validar Entrada

```python
def _calculate_properties_impl(self, smiles, **kwargs):
    # ✅ BIEN
    if not smiles or not smiles.strip():
        raise ValueError("SMILES cannot be empty")

    if len(smiles) > 1000:
        raise ValueError("SMILES too long")

    # ❌ MAL
    # No validar, dejar que falle silenciosamente
```

### 2. Usar Metadata Estándar

```python
# ✅ BIEN
validated[prop_name] = {
    "value": value,
    "units": prop_info.units,
    "source": self.get_metadata().name,  # ← Identificar origen
    "method": "my_algorithm"
}

# ❌ MAL
validated[prop_name] = value  # No hay contexto
```

### 3. Manejar Errores Explícitamente

```python
# ✅ BIEN
try:
    result = expensive_computation(smiles)
except ComputationError as e:
    raise PropertyCalculationError(f"Computation failed: {e}")

# ❌ MAL
try:
    result = expensive_computation(smiles)
except:
    return {}  # Silent failure
```

### 4. Documentar con REPL

```python
def calculate_properties(self, smiles, **kwargs):
    """
    >>> provider = MyProvider()
    >>> result = provider.calculate_properties(
    ...     smiles="CCO",
    ...     properties_data={"MolWt": {"value": 46.07}}
    ... )
    >>> assert "MolWt" in result
    """
```

### 5. Usar Type Hints

```python
# ✅ BIEN
def calculate_properties(
    self,
    smiles: str,
    properties_data: Dict[str, Any] = None
) -> Dict[str, Any]:
    ...

# ❌ MAL
def calculate_properties(self, smiles, properties_data):
    ...
```

### 6. Seguir Arquitectura Hexagonal

```
┌──────────────────────────┐
│ API (ViewSet)            │ ← REST endpoint
└────────────┬─────────────┘
             │
┌────────────▼─────────────┐
│ Service                  │ ← Business logic (aquí va tu código)
└────────────┬─────────────┘
             │
┌────────────▼─────────────┐
│ Port (Interface)         │ ← PropertyProviderInterface
└────────────┬─────────────┘
             │
┌────────────▼─────────────┐
│ Adapter (Tu Provider)    │ ← MyCustomProvider
└──────────────────────────┘
```

### 7. Evitar Lógica en Views

```python
# ✅ BIEN
class MoleculeViewSet:
    def create(self, request):
        # Delegar a servicio
        mol = create_molecule_from_smiles(
            smiles=request.data['smiles'],
            created_by=request.user
        )
        return Response(MoleculeSerializer(mol).data, status=201)

# ❌ MAL
class MoleculeViewSet:
    def create(self, request):
        # Lógica en view
        mol = Molecule(
            smiles=request.data['smiles'],
            ...
        )
        mol.save()
        return Response(...)
```

---

## CHECKLIST DE EXTENSIÓN

Antes de enviar tu provider:

- [ ] Implementé los 3 métodos requeridos
- [ ] Validé entrada (SMILES, rangos, etc.)
- [ ] Manejo errores explícitamente
- [ ] Agregué docstrings con ejemplos >>>
- [ ] Usé type hints en todas las funciones
- [ ] Seguí patrón Template Method
- [ ] Registré en PropertyProviderRegistry
- [ ] Escribí tests (mínimo 5 casos)
- [ ] Test de error handling
- [ ] Test de integración con servicios
- [ ] Sin lógica en views (solo servicios)
- [ ] Metadata tiene fields estándar
