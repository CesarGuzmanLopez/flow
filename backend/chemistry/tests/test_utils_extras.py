"""
Additional utility tests for the Chemistry module.

Covers:
- Statistics computation helper for family member properties
- Provider utility to enrich SMILES with structure + descriptors
"""

from django.test import TestCase, override_settings

from chemistry.providers import utils as provider_utils
from chemistry.services.utils import _compute_property_statistics
from chemistry.types import MolecularProperties


class TestComputePropertyStatistics(TestCase):
    def test_statistics_single_value_std_zero(self):
        # One member with numeric properties
        member_props = [
            {
                "properties": MolecularProperties(
                    log_p=1.5,
                    tpsa=10.0,
                    mol_wt=100.0,
                    hbd=1.0,
                    hba=2.0,
                    rotatable_bonds=0.0,
                )
            }
        ]
        stats = _compute_property_statistics(member_props)
        assert stats["LogP"]["mean"] == 1.5
        assert stats["LogP"]["std"] == 0.0  # single value => std 0.0
        assert stats["MolWt"]["min"] == 100.0
        assert stats["MolWt"]["max"] == 100.0
        assert stats["MolWt"]["count"] == 1

    def test_statistics_multiple_values_std_positive(self):
        member_props = [
            {"properties": MolecularProperties(log_p=1.0)},
            {"properties": MolecularProperties(log_p=2.0)},
            {"properties": MolecularProperties(log_p=3.0)},
        ]
        stats = _compute_property_statistics(member_props)
        assert stats["LogP"]["mean"] == 2.0
        assert stats["LogP"]["min"] == 1.0
        assert stats["LogP"]["max"] == 3.0
        assert stats["LogP"]["count"] == 3
        assert stats["LogP"]["std"] > 0.0


@override_settings(CHEM_ENGINE="mock")
class TestProviderEnrichSmiles(TestCase):
    def test_enrich_smiles_structure_and_descriptors(self):
        structure, descriptors = provider_utils.enrich_smiles("C")
        # Structure keys present (non-strict depending on engine)
        assert isinstance(structure, dict)
        assert (
            "inchi" in structure
            or "inchikey" in structure
            or "canonical_smiles" in structure
        )
        # Descriptors as dict, may be empty if provider failed; mock should return values
        assert isinstance(descriptors, dict)
        # If mock engine is active, expect known keys like 'MolWt' or 'LogP'
        if descriptors:
            assert any(k in descriptors for k in ("MolWt", "LogP", "TPSA", "PSA"))
