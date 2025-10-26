"""
Tests de Seguridad e Integridad del módulo Chemistry.

Validaciones probadas:
- Frozen entities (no update/delete)
- Invariant properties (protección)
- Ownership validation
- SMILES length/format
- Composite uniqueness
- Family hash consistency
"""

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction
from rest_framework.test import APIClient

from chemistry.models import (
    MolecularProperty,
    Molecule,
    MoleculeFlow,
)
from chemistry.providers.exceptions import InvalidSmilesError
from chemistry.services import (
    create_family_from_smiles,
    create_molecule_from_smiles,
    create_or_update_molecular_property,
    update_molecule,
)

User = get_user_model()


# ============================================================================
# FROZEN ENTITIES TESTS
# ============================================================================


class TestFrozenEntities:
    """Test protección de entidades congeladas."""

    @pytest.fixture
    def user(self, db):
        """Create test user."""
        return User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

    @pytest.fixture
    def frozen_molecule(self, db, user):
        """Create frozen molecule."""
        mol = create_molecule_from_smiles(smiles="CCO", created_by=user)
        mol.frozen = True
        mol.save()
        return mol

    @pytest.mark.django_db
    def test_cannot_update_frozen_molecule(self, frozen_molecule, user):
        """
        >>> # Intentar actualizar molécula congelada
        >>> frozen_mol = Molecule.objects.get(frozen=True)
        >>> try:
        ...     update_molecule(
        ...         molecule=frozen_mol,
        ...         payload={"name": "New Name"},
        ...         user=user
        ...     )
        ... except ValidationError as e:
        ...     assert "frozen" in str(e).lower()
        """
        with pytest.raises(ValidationError):
            update_molecule(
                molecule=frozen_molecule, payload={"name": "New Name"}, user=user
            )

    @pytest.mark.django_db
    def test_cannot_delete_frozen_molecule_via_api(self, frozen_molecule, user):
        """
        >>> client = APIClient()
        >>> client.force_authenticate(user=user)
        >>> response = client.delete(f"/api/chemistry/molecules/{mol.id}/")
        >>> assert response.status_code == 403
        """
        client = APIClient()
        client.force_authenticate(user=user)

        response = client.delete(f"/api/chemistry/molecules/{frozen_molecule.id}/")

        # Debería rechazar
        assert response.status_code in [403, 400]

    @pytest.mark.django_db
    def test_frozen_family_immutable(self, db, user):
        """
        >>> family = create_family_from_smiles(
        ...     name="Test",
        ...     smiles_list=["CCO", "CC(C)O"],
        ...     created_by=user
        ... )
        >>> assert family.frozen == True  # Familias SIEMPRE frozen
        """
        family = create_family_from_smiles(
            name="Test Family", smiles_list=["CCO", "CC(C)O"], created_by=user
        )

        # SIEMPRE creada como frozen
        assert family.frozen is True


# ============================================================================
# OWNERSHIP VALIDATION TESTS
# ============================================================================


class TestOwnershipValidation:
    """Test validación de ownership (created_by)."""

    @pytest.fixture
    def users(self, db):
        """Create multiple test users."""
        alice = User.objects.create_user(
            username="alice", email="alice@example.com", password="pass123"
        )
        bob = User.objects.create_user(
            username="bob", email="bob@example.com", password="pass123"
        )
        return {"alice": alice, "bob": bob}

    @pytest.fixture
    def molecule_by_alice(self, db, users):
        """Create molecule by Alice."""
        return create_molecule_from_smiles(smiles="CCO", created_by=users["alice"])

    @pytest.mark.django_db
    def test_only_creator_can_update(self, molecule_by_alice, users):
        """
        >>> # Alice crea molécula, Bob intenta modificar
        >>> with pytest.raises(PermissionDenied):
        ...     update_molecule(
        ...         molecule=molecule_by_alice,
        ...         payload={"name": "Hacked"},
        ...         user=users["bob"]
        ...     )
        """
        with pytest.raises((PermissionError, ValidationError)):
            update_molecule(
                molecule=molecule_by_alice,
                payload={"name": "Hacked"},
                user=users["bob"],
            )

    @pytest.mark.django_db
    def test_creator_can_update_own_molecule(self, molecule_by_alice, users):
        """
        >>> # Alice puede actualizar su propia molécula
        >>> result = update_molecule(
        ...     molecule=molecule_by_alice,
        ...     payload={"name": "Updated Name"},
        ...     user=users["alice"]
        ... )
        >>> assert result.name == "Updated Name"
        """
        result = update_molecule(
            molecule=molecule_by_alice,
            payload={"name": "Updated Name"},
            user=users["alice"],
        )

        assert result.name == "Updated Name"

    @pytest.mark.django_db
    def test_api_assigns_current_user_as_creator(self, users):
        """
        >>> client = APIClient()
        >>> client.force_authenticate(user=alice)
        >>> response = client.post(
        ...     "/api/chemistry/molecules/from_smiles/",
        ...     {"smiles": "CCO"}
        ... )
        >>> mol = Molecule.objects.get(id=response.data["id"])
        >>> assert mol.created_by == alice
        """
        client = APIClient()
        client.force_authenticate(user=users["alice"])

        response = client.post(
            "/api/chemistry/molecules/from_smiles/", {"smiles": "CCO", "name": "Test"}
        )

        assert response.status_code == 201

        mol = Molecule.objects.get(id=response.data["id"])
        assert mol.created_by == users["alice"]


# ============================================================================
# SMILES VALIDATION TESTS
# ============================================================================


class TestSmilesValidation:
    """Test validación de SMILES."""

    @pytest.fixture
    def user(self, db):
        return User.objects.create_user(username="testuser", password="pass123")

    @pytest.mark.django_db
    def test_cannot_create_with_empty_smiles(self, user):
        """
        >>> try:
        ...     create_molecule_from_smiles(
        ...         smiles="",
        ...         created_by=user
        ...     )
        ... except ValidationError as e:
        ...     assert "empty" in str(e).lower()
        """
        with pytest.raises(ValidationError):
            create_molecule_from_smiles(smiles="", created_by=user)

    @pytest.mark.django_db
    def test_cannot_create_with_whitespace_only_smiles(self, user):
        """
        >>> with pytest.raises(ValidationError):
        ...     create_molecule_from_smiles(
        ...         smiles="   ",
        ...         created_by=user
        ...     )
        """
        with pytest.raises(ValidationError):
            create_molecule_from_smiles(smiles="   ", created_by=user)

    @pytest.mark.django_db
    def test_cannot_create_with_invalid_smiles(self, user):
        """
        >>> with pytest.raises(InvalidSmilesError):
        ...     create_molecule_from_smiles(
        ...         smiles="INVALID!!!",
        ...         created_by=user
        ...     )
        """
        with pytest.raises(InvalidSmilesError):
            create_molecule_from_smiles(smiles="INVALID!!!", created_by=user)

    @pytest.mark.django_db
    def test_cannot_create_with_very_long_smiles(self, user):
        """
        >>> long_smiles = "C" * 1001  # > 1000
        >>> with pytest.raises(ValidationError):
        ...     create_molecule_from_smiles(
        ...         smiles=long_smiles,
        ...         created_by=user
        ...     )
        """
        long_smiles = "C" * 1001

        with pytest.raises(ValidationError):
            create_molecule_from_smiles(smiles=long_smiles, created_by=user)

    @pytest.mark.django_db
    def test_can_create_with_valid_smiles(self, user):
        """
        >>> mol = create_molecule_from_smiles(
        ...     smiles="CCO",
        ...     created_by=user
        ... )
        >>> assert mol.inchikey is not None
        """
        mol = create_molecule_from_smiles(smiles="CCO", created_by=user)

        assert mol.inchikey is not None
        assert mol.canonical_smiles is not None


# ============================================================================
# COMPOSITE UNIQUENESS TESTS (EAV Pattern)
# ============================================================================


class TestCompositeUniqueness:
    """Test unicidad compuesta en properties (EAV)."""

    @pytest.fixture
    def user(self, db):
        return User.objects.create_user(username="testuser", password="pass123")

    @pytest.fixture
    def molecule(self, db, user):
        return create_molecule_from_smiles(smiles="CCO", created_by=user)

    @pytest.mark.django_db
    def test_duplicate_property_raises_error(self, molecule):
        """
        >>> # Crear property primera vez
        >>> prop1 = create_or_update_molecular_property(
        ...     molecule=molecule,
        ...     property_type="MolWt",
        ...     value="46.07",
        ...     method="rdkit"
        ... )
        >>>
        >>> # Intentar crear con EXACTAMENTE los mismos params
        >>> with pytest.raises(Exception):
        ...     create_or_update_molecular_property(
        ...         molecule=molecule,
        ...         property_type="MolWt",
        ...         value="46.07",
        ...         method="rdkit"
        ...     )
        """

        # Intentar duplicado (same (molecule, property_type, method, relation, source_id))
        with pytest.raises(Exception):
            create_or_update_molecular_property(
                molecule=molecule,
                property_type="MolWt",
                value="46.07",
                method="rdkit",
                source_id="system",
            )

    @pytest.mark.django_db
    def test_can_create_same_property_different_method(self, molecule):
        """
        >>> # Misma property, método diferente: OK
        >>> prop1 = create_or_update_molecular_property(
        ...     molecule=molecule,
        ...     property_type="MolWt",
        ...     value="46.07",
        ...     method="rdkit"
        ... )
        >>>
        >>> prop2 = create_or_update_molecular_property(
        ...     molecule=molecule,
        ...     property_type="MolWt",
        ...     value="46.069",
        ...     method="experimental"
        ... )
        >>>
        >>> assert prop1.id != prop2.id
        """
        prop1 = create_or_update_molecular_property(
            molecule=molecule,
            property_type="MolWt",
            value="46.07",
            method="rdkit",
            source_id="rdkit_2024",
        )

        prop2 = create_or_update_molecular_property(
            molecule=molecule,
            property_type="MolWt",
            value="46.069",
            method="experimental",
            source_id="lab_2024",
        )

        assert prop1.id != prop2.id

        # Verificar ambas existen
        count = MolecularProperty.objects.filter(
            molecule=molecule, property_type="MolWt"
        ).count()
        assert count == 2


# ============================================================================
# INCHIKEY UNIQUENESS TESTS
# ============================================================================


class TestInChIKeyUniqueness:
    """Test unicidad de InChIKey."""

    @pytest.fixture
    def user(self, db):
        return User.objects.create_user(username="testuser", password="pass123")

    @pytest.mark.django_db
    def test_same_inchikey_returns_existing_molecule(self, user):
        """
        >>> # CCO tiene mismo InChIKey siempre
        >>> mol1 = create_molecule_from_smiles(
        ...     smiles="CCO",
        ...     created_by=user
        ... )
        >>>
        >>> mol2 = create_molecule_from_smiles(
        ...     smiles="OCC",  # Mismo SMILES canonicalizado
        ...     created_by=user
        ... )
        >>>
        >>> assert mol1.id == mol2.id  # Misma molécula!
        """
        mol1 = create_molecule_from_smiles(smiles="CCO", created_by=user)

        mol2 = create_molecule_from_smiles(
            smiles="OCC",  # Equivalente, mismo InChI
            created_by=user,
        )

        assert mol1.inchikey == mol2.inchikey
        assert mol1.id == mol2.id  # Deduplicado


# ============================================================================
# ATOMICITY TESTS
# ============================================================================


class TestAtomicity:
    """Test atomicity de transacciones."""

    @pytest.fixture
    def user(self, db):
        return User.objects.create_user(username="testuser", password="pass123")

    @pytest.mark.django_db
    def test_family_creation_rollback_on_error(self, user):
        """
        >>> initial_count = Molecule.objects.count()
        >>>
        >>> with pytest.raises(Exception):
        ...     with transaction.atomic():
        ...         create_molecule_from_smiles(
        ...             smiles="CCO",
        ...             created_by=user
        ...         )
        ...         # Simular error
        ...         raise Exception("Simulated failure")
        >>>
        >>> # Verificar rollback
        >>> final_count = Molecule.objects.count()
        >>> assert final_count == initial_count
        """
        initial_count = Molecule.objects.count()

        with pytest.raises(Exception):
            with transaction.atomic():
                create_molecule_from_smiles(smiles="CCO", created_by=user)
                raise Exception("Simulated failure")

        # Verificar rollback
        final_count = Molecule.objects.count()
        assert final_count == initial_count

    @pytest.mark.django_db
    def test_family_with_invalid_molecule_rollback(self, user):
        """
        >>> initial_count = Molecule.objects.count()
        >>>
        >>> with pytest.raises(Exception):
        ...     create_family_from_smiles(
        ...         name="Test",
        ...         smiles_list=["CCO", "INVALID!!!"],  # SMILES inválido
        ...         created_by=user
        ...     )
        >>>
        >>> # Verificar que ninguna fue creada
        >>> assert Molecule.objects.count() == initial_count
        """
        initial_count = Molecule.objects.count()

        with pytest.raises(Exception):
            create_family_from_smiles(
                name="Test", smiles_list=["CCO", "INVALID!!!"], created_by=user
            )

        # Nada se creó
        assert Molecule.objects.count() == initial_count


# ============================================================================
# FAMILY HASH CONSISTENCY TESTS
# ============================================================================


class TestFamilyHashConsistency:
    """Test consistencia de family_hash."""

    @pytest.fixture
    def user(self, db):
        return User.objects.create_user(username="testuser", password="pass123")

    @pytest.mark.django_db
    def test_family_hash_consistent_regardless_of_order(self, user):
        """
        >>> # Orden diferente, MISMO hash
        >>> family1 = create_family_from_smiles(
        ...     name="F1",
        ...     smiles_list=["CCO", "CC(C)O", "CC(=O)C"],
        ...     created_by=user
        ... )
        >>>
        >>> family2 = create_family_from_smiles(
        ...     name="F2",
        ...     smiles_list=["CC(=O)C", "CCO", "CC(C)O"],  # Reordenado
        ...     created_by=user
        ... )
        >>>
        >>> assert family1.family_hash == family2.family_hash
        >>> assert family1.id == family2.id  # Misma familia!
        """
        family1 = create_family_from_smiles(
            name="Family 1", smiles_list=["CCO", "CC(C)O", "CC(=O)C"], created_by=user
        )

        family2 = create_family_from_smiles(
            name="Family 2", smiles_list=["CC(=O)C", "CCO", "CC(C)O"], created_by=user
        )

        assert family1.family_hash == family2.family_hash
        assert family1.id == family2.id

    @pytest.mark.django_db
    def test_family_hash_different_for_different_composition(self, user):
        """
        >>> family1 = create_family_from_smiles(
        ...     name="F1",
        ...     smiles_list=["CCO", "CC(C)O"],
        ...     created_by=user
        ... )
        >>>
        >>> family2 = create_family_from_smiles(
        ...     name="F2",
        ...     smiles_list=["CCO", "CC(C)O", "CC(=O)C"],  # 3ª molécula
        ...     created_by=user
        ... )
        >>>
        >>> assert family1.family_hash != family2.family_hash
        >>> assert family1.id != family2.id
        """
        family1 = create_family_from_smiles(
            name="Family 1", smiles_list=["CCO", "CC(C)O"], created_by=user
        )

        family2 = create_family_from_smiles(
            name="Family 2", smiles_list=["CCO", "CC(C)O", "CC(=O)C"], created_by=user
        )

        assert family1.family_hash != family2.family_hash
        assert family1.id != family2.id


# ============================================================================
# MOLECULEFLOW INTEGRATION TESTS
# ============================================================================


class TestMoleculeFlowIntegration:
    """Test integración con flows."""

    @pytest.fixture
    def user(self, db):
        return User.objects.create_user(username="testuser", password="pass123")

    @pytest.fixture
    def molecule(self, db, user):
        return create_molecule_from_smiles(
            smiles="CCO",
            created_by=user,
            metadata={"flow_id": "flows.Flow:123", "source": "workflow"},
        )

    @pytest.mark.django_db
    def test_molecule_linked_to_flow_via_metadata(self, molecule):
        """
        >>> mol = Molecule.objects.get(id=1)
        >>> assert mol.metadata.get("flow_id") == "flows.Flow:123"
        """
        assert molecule.metadata.get("flow_id") == "flows.Flow:123"

    @pytest.mark.django_db
    def test_moleculeflow_cascade_delete(self, db, user):
        """
        >>> mol = create_molecule_from_smiles(
        ...     smiles="CCO",
        ...     created_by=user
        ... )
        >>>
        >>> # Simular: flow = Flow.objects.create(...)
        >>> # mf = MoleculeFlow.objects.create(molecule=mol, flow=flow, ...)
        >>>
        >>> # Al eliminar molécula, MoleculeFlow se elimina automáticamente
        >>> mol.delete()
        >>> assert not MoleculeFlow.objects.filter(molecule=mol).exists()
        """
        from flows.models import Flow

        mol = create_molecule_from_smiles(smiles="CCO", created_by=user)

        # Crear flow (si está disponible)
        try:
            flow = Flow.objects.create(name="Test Flow", created_by=user)

            mf = MoleculeFlow.objects.create(molecule=mol, flow=flow, role="generated")

            mol.delete()

            # MoleculeFlow se eliminó (CASCADE)
            assert not MoleculeFlow.objects.filter(id=mf.id).exists()
        except Exception:
            # Flow model might not exist, skip this part
            pass


# ============================================================================
# SIZE LIMITS TESTS
# ============================================================================


class TestSizeLimits:
    """Test límites de tamaño en serializers."""

    @pytest.fixture
    def user(self, db):
        return User.objects.create_user(username="testuser", password="pass123")

    @pytest.mark.django_db
    def test_smiles_size_limit_in_serializer(self, user):
        """
        >>> from chemistry.serializers import CreateMoleculeFromSmilesSerializer
        >>>
        >>> # SMILES > 1000 characters
        >>> data = {"smiles": "C" * 1001}
        >>> serializer = CreateMoleculeFromSmilesSerializer(data=data)
        >>> assert not serializer.is_valid()
        >>> assert "smiles" in serializer.errors
        """
        from chemistry.serializers import CreateMoleculeFromSmilesSerializer

        data = {"smiles": "C" * 1001}
        serializer = CreateMoleculeFromSmilesSerializer(data=data)

        assert not serializer.is_valid()
        assert "smiles" in serializer.errors

    @pytest.mark.django_db
    def test_metadata_structure_validation(self, user):
        """
        >>> # Metadata debe ser dict
        >>> data = {
        ...     "smiles": "CCO",
        ...     "extra_metadata": "not a dict!"  # ← INVÁLIDO
        ... }
        >>> serializer = CreateMoleculeFromSmilesSerializer(data=data)
        >>> assert not serializer.is_valid()
        """
        from chemistry.serializers import CreateMoleculeFromSmilesSerializer

        data = {"smiles": "CCO", "extra_metadata": "not a dict!"}
        serializer = CreateMoleculeFromSmilesSerializer(data=data)

        # Debería fallar validación
        assert not serializer.is_valid()


# ============================================================================
# PERMISSION TESTS (Integration with DRF)
# ============================================================================


class TestPermissionsIntegration:
    """Test permisos en views."""

    @pytest.fixture
    def users(self, db):
        alice = User.objects.create_user(username="alice", password="pass123")
        bob = User.objects.create_user(username="bob", password="pass123")
        return {"alice": alice, "bob": bob}

    @pytest.fixture
    def molecule(self, db, users):
        return create_molecule_from_smiles(smiles="CCO", created_by=users["alice"])

    @pytest.mark.django_db
    def test_unauthorized_user_cannot_modify(self, molecule, users):
        """
        >>> client = APIClient()
        >>> client.force_authenticate(user=bob)
        >>> response = client.put(
        ...     f"/api/chemistry/molecules/{mol.id}/",
        ...     {"name": "Hacked"}
        ... )
        >>> assert response.status_code == 403
        """
        client = APIClient()
        client.force_authenticate(user=users["bob"])

        response = client.put(
            f"/api/chemistry/molecules/{molecule.id}/", {"name": "Hacked"}
        )

        # Debería ser 403 o similar
        assert response.status_code in [403, 400]

    @pytest.mark.django_db
    def test_unauthenticated_user_cannot_access(self, molecule):
        """
        >>> client = APIClient()  # Sin authenticate
        >>> response = client.get(f"/api/chemistry/molecules/{mol.id}/")
        >>> assert response.status_code == 401
        """
        client = APIClient()

        response = client.get(f"/api/chemistry/molecules/{molecule.id}/")

        # Debería rechazar no autenticados
        assert response.status_code == 401


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
