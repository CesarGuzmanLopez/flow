"""
Tests de Integración con Flows del módulo Chemistry.

Validaciones probadas:
- Vinculación de moléculas a flows
- MoleculeFlow tracking
- Queries por flow
- Metadata consistency
- CASCADE deletion
"""

import pytest
from django.contrib.auth import get_user_model
from django.db import transaction

from chemistry.models import Molecule, MoleculeFlow
from chemistry.services import (
    create_molecule_from_smiles,
)
from chemistry.services.family import create_family_from_smiles

User = get_user_model()


# ============================================================================
# FLOWS BASIC INTEGRATION
# ============================================================================


class TestFlowsBasicIntegration:
    """Test integración básica con flows."""

    @pytest.fixture
    def user(self, db):
        """Create test user."""
        return User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

    @pytest.mark.django_db
    def test_molecule_with_flow_id_in_metadata(self, user):
        """
        >>> mol = create_molecule_from_smiles(
        ...     smiles="CCO",
        ...     created_by=user,
        ...     metadata={"flow_id": "flows.Flow:123"}
        ... )
        >>>
        >>> assert mol.metadata["flow_id"] == "flows.Flow:123"
        >>> assert "source" in mol.metadata
        >>> assert "created_at" in mol.metadata
        """
        mol = create_molecule_from_smiles(
            smiles="CCO",
            created_by=user,
            metadata={"flow_id": "flows.Flow:123", "step": "molecule_creation"},
        )

        assert mol.metadata.get("flow_id") == "flows.Flow:123"
        assert mol.metadata.get("step") == "molecule_creation"

    @pytest.mark.django_db
    def test_family_with_flow_id_in_metadata(self, user):
        """
        >>> family = create_family_from_smiles(
        ...     name="Test",
        ...     smiles_list=["CCO", "CC(C)O"],
        ...     created_by=user,
        ...     metadata={"flow_id": "flows.Flow:456"}
        ... )
        >>>
        >>> assert family.metadata["flow_id"] == "flows.Flow:456"
        """
        family = create_family_from_smiles(
            name="Test Family",
            smiles_list=["CCO", "CC(C)O"],
            created_by=user,
            metadata={"flow_id": "flows.Flow:456"},
        )

        assert family.metadata.get("flow_id") == "flows.Flow:456"


# ============================================================================
# MOLECULEFLOW TRACKING
# ============================================================================


class TestMoleculeFlowTracking:
    """Test tracking de moléculas en MoleculeFlow."""

    @pytest.fixture
    def user(self, db):
        return User.objects.create_user(username="testuser", password="pass123")

    def test_create_moleculeflow_relationship(self, user):
        """
        >>> mol = create_molecule_from_smiles(
        ...     smiles="CCO",
        ...     created_by=user
        ... )
        >>>
        >>> # Simular: flow = Flow.objects.create(...)
        >>> mf = MoleculeFlow.objects.create(
        ...     molecule=mol,
        ...     flow_id=123,  # O flow=flow
        ...     role="generated"
        ... )
        >>>
        >>> assert mf.molecule == mol
        >>> assert mf.role == "generated"
        """
        mol = create_molecule_from_smiles(smiles="CCO", created_by=user)

        # Intentar crear MoleculeFlow (flow debe existir en el proyecto)
        try:
            from flows.models import Flow

            flow = Flow.objects.create(name="Test Flow", owner=user)

            mf = MoleculeFlow.objects.create(
                molecule=mol, flow=flow, role="generated", step_number=1
            )

            assert mf.molecule == mol
            assert mf.role == "generated"
            assert mf.step_number == 1
        except ImportError:
            pytest.skip("Flow model not available")

    def test_moleculeflow_roles(self, user):
        """
        >>> # Roles: input, generated, reference
        >>>
        >>> mol1 = create_molecule_from_smiles(..., created_by=user)  # input
        >>> mol2 = create_molecule_from_smiles(..., created_by=user)  # generated
        >>> mol3 = create_molecule_from_smiles(..., created_by=user)  # reference
        >>>
        >>> MoleculeFlow.objects.create(molecule=mol1, flow=flow, role="input")
        >>> MoleculeFlow.objects.create(molecule=mol2, flow=flow, role="generated")
        >>> MoleculeFlow.objects.create(molecule=mol3, flow=flow, role="reference")
        """
        try:
            from flows.models import Flow

            flow = Flow.objects.create(name="Test Flow", owner=user)

            mol_input = create_molecule_from_smiles(smiles="CCO", created_by=user)

            mol_generated = create_molecule_from_smiles(
                smiles="CC(C)O", created_by=user
            )

            mol_reference = create_molecule_from_smiles(
                smiles="CC(=O)C", created_by=user
            )

            # Create associations with different roles
            MoleculeFlow.objects.create(molecule=mol_input, flow=flow, role="input")

            MoleculeFlow.objects.create(
                molecule=mol_generated, flow=flow, role="generated"
            )

            MoleculeFlow.objects.create(
                molecule=mol_reference, flow=flow, role="reference"
            )

            # Query by role
            input_mols = MoleculeFlow.objects.filter(flow=flow, role="input")
            assert input_mols.count() == 1
            assert input_mols.first().molecule == mol_input

            generated_mols = MoleculeFlow.objects.filter(flow=flow, role="generated")
            assert generated_mols.count() == 1

        except ImportError:
            pytest.skip("Flow model not available")


# ============================================================================
# QUERY TESTS
# ============================================================================


class TestFlowQueries:
    """Test queries de moléculas por flow."""

    @pytest.fixture
    def user(self, db):
        return User.objects.create_user(username="testuser", password="pass123")

    def test_query_molecules_by_flow(self, user):
        """
        >>> # Query: Todas moléculas de un flow
        >>> mols = MoleculeFlow.objects.filter(
        ...     flow_id=123,
        ...     role="generated"
        ... ).values_list("molecule_id", flat=True)
        >>>
        >>> molecules = Molecule.objects.filter(id__in=mols)
        >>> print(f"Count: {molecules.count()}")
        """
        try:
            from flows.models import Flow

            flow = Flow.objects.create(name="Test Flow", owner=user)

            # Create molecules
            mol1 = create_molecule_from_smiles(smiles="CCO", created_by=user)
            mol2 = create_molecule_from_smiles(smiles="CC(C)O", created_by=user)

            # Link to flow
            MoleculeFlow.objects.create(molecule=mol1, flow=flow, role="generated")
            MoleculeFlow.objects.create(molecule=mol2, flow=flow, role="generated")

            # Query
            mol_ids = MoleculeFlow.objects.filter(
                flow=flow, role="generated"
            ).values_list("molecule_id", flat=True)

            molecules = Molecule.objects.filter(id__in=mol_ids)

            assert molecules.count() == 2
            assert mol1 in molecules
            assert mol2 in molecules

        except ImportError:
            pytest.skip("Flow model not available")

    def test_query_molecules_via_metadata_flow_id(self, user):
        """
        >>> # Query: Moléculas con flow_id en metadata
        >>> molecules = Molecule.objects.filter(
        ...     metadata__flow_id__icontains="Flow:123"
        ... )
        """
        mol1 = create_molecule_from_smiles(
            smiles="CCO", created_by=user, metadata={"flow_id": "flows.Flow:123"}
        )

        mol2 = create_molecule_from_smiles(
            smiles="CC(C)O", created_by=user, metadata={"flow_id": "flows.Flow:123"}
        )

        mol3 = create_molecule_from_smiles(
            smiles="CC(=O)C", created_by=user, metadata={"flow_id": "flows.Flow:456"}
        )

        # Query por flow
        molecules = Molecule.objects.filter(metadata__flow_id="flows.Flow:123")

        assert molecules.count() == 2
        assert mol1 in molecules
        assert mol2 in molecules
        assert mol3 not in molecules


# ============================================================================
# CASCADE DELETION TESTS
# ============================================================================


class TestCascadeDeletion:
    """Test CASCADE deletion en MoleculeFlow."""

    @pytest.fixture
    def user(self, db):
        return User.objects.create_user(username="testuser", password="pass123")

    def test_delete_molecule_cascades_to_moleculeflow(self, user):
        """
        >>> mol = create_molecule_from_smiles(
        ...     smiles="CCO",
        ...     created_by=user
        ... )
        >>>
        >>> mf = MoleculeFlow.objects.create(
        ...     molecule=mol,
        ...     flow=flow,
        ...     role="generated"
        ... )
        >>>
        >>> mol.delete()
        >>>
        >>> # MoleculeFlow se eliminó automáticamente
        >>> assert not MoleculeFlow.objects.filter(id=mf.id).exists()
        """
        try:
            from flows.models import Flow

            flow = Flow.objects.create(name="Test Flow", owner=user)

            mol = create_molecule_from_smiles(smiles="CCO", created_by=user)

            mf = MoleculeFlow.objects.create(molecule=mol, flow=flow, role="generated")

            mf_id = mf.id

            # Delete molecule
            mol.delete()

            # MoleculeFlow should be deleted (CASCADE)
            assert not MoleculeFlow.objects.filter(id=mf_id).exists()

        except ImportError:
            pytest.skip("Flow model not available")

    def test_delete_flow_cascades_to_moleculeflow(self, user):
        """
        >>> flow.delete()
        >>>
        >>> # Todos MoleculeFlow de ese flow se eliminan
        >>> assert not MoleculeFlow.objects.filter(flow=flow).exists()
        """
        try:
            from flows.models import Flow

            flow = Flow.objects.create(name="Test Flow", owner=user)

            mol1 = create_molecule_from_smiles(smiles="CCO", created_by=user)
            mol2 = create_molecule_from_smiles(smiles="CC(C)O", created_by=user)

            MoleculeFlow.objects.create(molecule=mol1, flow=flow, role="generated")
            MoleculeFlow.objects.create(molecule=mol2, flow=flow, role="generated")

            flow_id = flow.id

            # Delete flow
            flow.delete()

            # All MoleculeFlow entries deleted
            assert not MoleculeFlow.objects.filter(flow_id=flow_id).exists()

            # Molecules still exist (FK CASCADE on MoleculeFlow, not on Molecule)
            assert Molecule.objects.filter(id=mol1.id).exists()
            assert Molecule.objects.filter(id=mol2.id).exists()

        except ImportError:
            pytest.skip("Flow model not available")


# ============================================================================
# METADATA CONSISTENCY TESTS
# ============================================================================


class TestMetadataConsistency:
    """Test consistencia de metadata vs MoleculeFlow."""

    @pytest.fixture
    def user(self, db):
        return User.objects.create_user(username="testuser", password="pass123")

    def test_metadata_and_moleculeflow_consistency(self, user):
        """
        >>> # metadata['flow_id'] debería coincidir con MoleculeFlow.flow
        >>> mol = create_molecule_from_smiles(
        ...     smiles="CCO",
        ...     created_by=user,
        ...     metadata={"flow_id": "flows.Flow:123"}
        ... )
        >>>
        >>> mf = MoleculeFlow.objects.get(molecule=mol)
        >>>
        >>> # Ambos apuntan al mismo flow
        >>> assert "123" in mol.metadata["flow_id"]
        >>> assert mf.flow.id == 123  # (si es posible parsear)
        """
        try:
            from flows.models import Flow

            flow = Flow.objects.create(name="Test Flow", owner=user)

            mol = create_molecule_from_smiles(
                smiles="CCO",
                created_by=user,
                metadata={"flow_id": f"flows.Flow:{flow.id}"},
            )

            mf = MoleculeFlow.objects.create(molecule=mol, flow=flow, role="generated")

            # Verificar consistencia
            assert str(flow.id) in mol.metadata["flow_id"]
            assert mf.flow.id == flow.id

        except ImportError:
            pytest.skip("Flow model not available")


# ============================================================================
# END-TO-END WORKFLOW TESTS
# ============================================================================


class TestEndToEndWorkflows:
    """Test workflows completos end-to-end."""

    @pytest.fixture
    def user(self, db):
        return User.objects.create_user(username="testuser", password="pass123")

    @pytest.mark.django_db
    def test_workflow_create_molecules_and_family(self, user):
        """
        >>> # Workflow: Input molecules → Create family → Generate properties
        >>>
        >>> flow_id = 123
        >>>
        >>> # STEP 1: Create input molecules
        >>> mol1 = create_molecule_from_smiles(
        ...     smiles="CCO",
        ...     created_by=user,
        ...     metadata={"flow_id": f"flows.Flow:{flow_id}"}
        ... )
        >>>
        >>> # STEP 2: Create family
        >>> family = create_family_from_smiles(
        ...     name="Alcohols",
        ...     smiles_list=["CCO"],
        ...     created_by=user,
        ...     metadata={"flow_id": f"flows.Flow:{flow_id}"}
        ... )
        >>>
        >>> assert family.frozen
        >>> assert "flow_id" in family.metadata
        """
        flow_id = 123

        # STEP 1: Create molecules
        mol1 = create_molecule_from_smiles(
            smiles="CCO",
            created_by=user,
            metadata={"flow_id": f"flows.Flow:{flow_id}", "step": "input_validation"},
        )

        mol2 = create_molecule_from_smiles(
            smiles="CC(C)O",
            created_by=user,
            metadata={"flow_id": f"flows.Flow:{flow_id}", "step": "input_validation"},
        )

        # STEP 2: Create family
        family = create_family_from_smiles(
            name="Primary Alcohols",
            smiles_list=["CCO", "CC(C)O"],
            created_by=user,
            metadata={"flow_id": f"flows.Flow:{flow_id}", "step": "family_generation"},
        )

        # Verify
        assert family.frozen
        assert family.metadata.get("flow_id") == f"flows.Flow:{flow_id}"

        # Verify molecules
        assert mol1.metadata.get("flow_id") == f"flows.Flow:{flow_id}"
        assert mol2.metadata.get("flow_id") == f"flows.Flow:{flow_id}"

    @pytest.mark.django_db
    def test_workflow_with_transaction_rollback(self, user):
        """
        >>> # Workflow que falla: Rollback automático
        >>>
        >>> with pytest.raises(Exception):
        ...     with transaction.atomic():
        ...         mol1 = create_molecule_from_smiles(...)
        ...         mol2 = create_molecule_from_smiles(...)
        ...
        ...         # Error!
        ...         raise Exception("Simulated failure")
        >>>
        >>> # Nada se creó
        >>> assert Molecule.objects.filter(
        ...     metadata__flow_id="flows.Flow:123"
        ... ).count() == 0
        """
        flow_id = 123
        initial_count = Molecule.objects.count()

        with pytest.raises(Exception):
            with transaction.atomic():
                create_molecule_from_smiles(
                    smiles="CCO",
                    created_by=user,
                    metadata={"flow_id": f"flows.Flow:{flow_id}"},
                )

                create_molecule_from_smiles(
                    smiles="CC(C)O",
                    created_by=user,
                    metadata={"flow_id": f"flows.Flow:{flow_id}"},
                )

                # Simulate failure
                raise Exception("Simulated workflow failure")

        # Rollback: No molecules created
        assert Molecule.objects.count() == initial_count


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
