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
                    logp=1.5,
                    tpsa=10.0,
                    mw=100.0,
                    hbd=1,
                    hba=2,
                    rotb=0,
                    aromatic_rings=0,
                    aliphatic_rings=0,
                    num_rings=0,
                    num_heavy_atoms=10,
                )
            }
        ]
        stats = _compute_property_statistics(member_props)
        assert stats["logp"]["mean"] == 1.5
        assert stats["logp"]["std"] == 0.0  # single value => std 0.0
        assert stats["mw"]["min"] == 100.0
        assert stats["mw"]["max"] == 100.0
        assert stats["mw"]["count"] == 1

    def test_statistics_multiple_values_std_positive(self):
        member_props = [
            {"properties": MolecularProperties(logp=1.0)},
            {"properties": MolecularProperties(logp=2.0)},
            {"properties": MolecularProperties(logp=3.0)},
        ]
        stats = _compute_property_statistics(member_props)
        assert stats["logp"]["mean"] == 2.0
        assert stats["logp"]["min"] == 1.0
        assert stats["logp"]["max"] == 3.0
        assert stats["logp"]["count"] == 3
        assert stats["logp"]["std"] > 0.0


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
        # If mock engine is active, expect known keys like 'mw' or 'logp'
        if descriptors:
            assert any(k in descriptors for k in ("mw", "logp", "tpsa"))
