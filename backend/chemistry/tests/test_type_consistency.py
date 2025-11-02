"""
Type safety validation tests for chemistry engine implementations.

This module validates that all chemistry engine implementations
return the exact types specified in the interface.
"""

import pytest

from chemistry.providers.interface import ChemEngineInterface

# Import implementations
from chemistry.providers.mock_chem import MockChemEngine
from chemistry.type_definitions import (
    InvalidSmilesError,
    MolecularProperties,
    MolecularPropertiesDict,
    PropertyCalculationError,
    StructureIdentifiers,
    StructureIdentifiersDict,
    SubstitutionGenerationError,
    SubstitutionResult,
)

try:
    from chemistry.providers.rdkit_chem import RDKitChemEngine

    RDKIT_AVAILABLE = True
except ImportError:
    RDKIT_AVAILABLE = False


class TestChemEngineTypeConsistency:
    """Test that all chemistry engines return consistent types."""

    def setup_method(self):
        """Set up test engines."""
        self.mock_engine = MockChemEngine()
        if RDKIT_AVAILABLE:
            self.rdkit_engine = RDKitChemEngine()

        # Test molecules
        self.valid_smiles = "CCO"  # ethanol
        self.invalid_smiles = "invalid_smiles_string"

    def get_engines(self):
        """Get available engines for testing."""
        engines = [("Mock", self.mock_engine)]
        if RDKIT_AVAILABLE:
            engines.append(("RDKit", self.rdkit_engine))
        return engines

    def test_smiles_to_inchi_return_types(self):
        """Test smiles_to_inchi returns correct types."""
        for engine_name, engine in self.get_engines():
            # Test dataclass return
            result_dc = engine.smiles_to_inchi(self.valid_smiles, return_dataclass=True)
            assert isinstance(result_dc, StructureIdentifiers), (
                f"{engine_name}: Expected StructureIdentifiers, got {type(result_dc)}"
            )
            assert isinstance(result_dc.inchi, str), (
                f"{engine_name}: inchi should be str"
            )
            assert isinstance(result_dc.inchikey, str), (
                f"{engine_name}: inchikey should be str"
            )
            assert isinstance(result_dc.canonical_smiles, str), (
                f"{engine_name}: canonical_smiles should be str"
            )
            assert result_dc.molecular_formula is None or isinstance(
                result_dc.molecular_formula, str
            ), f"{engine_name}: molecular_formula should be str or None"

            # Test dict return
            result_dict = engine.smiles_to_inchi(
                self.valid_smiles, return_dataclass=False
            )
            assert isinstance(result_dict, dict), (
                f"{engine_name}: Expected dict, got {type(result_dict)}"
            )
            assert "inchi" in result_dict, f"{engine_name}: Missing 'inchi' key"
            assert "inchikey" in result_dict, f"{engine_name}: Missing 'inchikey' key"
            assert "canonical_smiles" in result_dict, (
                f"{engine_name}: Missing 'canonical_smiles' key"
            )

            # Test conversion between formats
            converted = StructureIdentifiers.from_dict(result_dict)
            reconverted = converted.to_dict()
            assert "inchi" in reconverted, f"{engine_name}: Conversion failed"
            assert "inchikey" in reconverted, f"{engine_name}: Conversion failed"
            assert "canonical_smiles" in reconverted, (
                f"{engine_name}: Conversion failed"
            )

    def test_calculate_properties_return_types(self):
        """Test calculate_properties returns correct types."""
        for engine_name, engine in self.get_engines():
            # Test dataclass return
            result_dc = engine.calculate_properties(
                self.valid_smiles, return_dataclass=True
            )
            assert isinstance(result_dc, MolecularProperties), (
                f"{engine_name}: Expected MolecularProperties, got {type(result_dc)}"
            )

            # Check that all numeric fields are float or None
            for field_name in [
                "mol_wt",
                "log_p",
                "tpsa",
                "hba",
                "hbd",
                "rotatable_bonds",
            ]:
                field_value = getattr(result_dc, field_name)
                assert field_value is None or isinstance(field_value, (int, float)), (
                    f"{engine_name}: {field_name} should be numeric or None, got {type(field_value)}"
                )

            # Test dict return
            result_dict = engine.calculate_properties(
                self.valid_smiles, return_dataclass=False
            )
            assert isinstance(result_dict, dict), (
                f"{engine_name}: Expected dict, got {type(result_dict)}"
            )

            # Check that all values are numeric
            for key, value in result_dict.items():
                assert isinstance(value, (int, float)), (
                    f"{engine_name}: Property '{key}' should be numeric, got {type(value)}"
                )

            # Test conversion between formats
            converted = MolecularProperties.from_dict(result_dict)
            reconverted = converted.to_dict()
            assert isinstance(reconverted, dict), f"{engine_name}: Conversion failed"

    def test_generate_substitutions_return_types(self):
        """Test generate_substitutions returns correct types."""
        for engine_name, engine in self.get_engines():
            count = 3

            # Test dataclass return
            result_dc = engine.generate_substitutions(
                self.valid_smiles, count=count, return_dataclass=True
            )
            assert isinstance(result_dc, SubstitutionResult), (
                f"{engine_name}: Expected SubstitutionResult, got {type(result_dc)}"
            )
            assert isinstance(result_dc.substitutions, list), (
                f"{engine_name}: substitutions should be list"
            )
            assert all(isinstance(s, str) for s in result_dc.substitutions), (
                f"{engine_name}: All substitutions should be strings"
            )
            assert len(result_dc.substitutions) <= count, (
                f"{engine_name}: Too many substitutions returned"
            )
            assert result_dc.original_smiles == self.valid_smiles, (
                f"{engine_name}: Original SMILES mismatch"
            )
            assert result_dc.count_requested == count, f"{engine_name}: Count mismatch"

            # Test list return
            result_list = engine.generate_substitutions(
                self.valid_smiles, count=count, return_dataclass=False
            )
            assert isinstance(result_list, list), (
                f"{engine_name}: Expected list, got {type(result_list)}"
            )
            assert all(isinstance(s, str) for s in result_list), (
                f"{engine_name}: All substitutions should be strings"
            )
            assert len(result_list) <= count, (
                f"{engine_name}: Too many substitutions returned"
            )

            # Test conversion
            converted_list = result_dc.to_list()
            assert isinstance(converted_list, list), f"{engine_name}: Conversion failed"
            assert converted_list == result_dc.substitutions, (
                f"{engine_name}: Conversion mismatch"
            )

    def test_invalid_smiles_handling(self):
        """Test that invalid SMILES strings raise appropriate errors."""
        # Only test RDKit for this since it has real validation
        if RDKIT_AVAILABLE:
            engine = self.rdkit_engine

            with pytest.raises(InvalidSmilesError):
                engine.smiles_to_inchi(self.invalid_smiles)

            with pytest.raises(InvalidSmilesError):
                engine.calculate_properties(self.invalid_smiles)

            with pytest.raises(InvalidSmilesError):
                engine.generate_substitutions(self.invalid_smiles)

    def test_invalid_parameters(self):
        """Test that invalid parameters raise appropriate errors."""
        for engine_name, engine in self.get_engines():
            # Test negative count
            with pytest.raises(ValueError):
                engine.generate_substitutions(self.valid_smiles, count=0)

            with pytest.raises(ValueError):
                engine.generate_substitutions(self.valid_smiles, count=-1)

    def test_interface_compliance(self):
        """Test that all engines implement the interface correctly."""
        for engine_name, engine in self.get_engines():
            assert isinstance(engine, ChemEngineInterface), (
                f"{engine_name}: Does not implement ChemEngineInterface"
            )

            # Check all required methods exist
            assert hasattr(engine, "smiles_to_inchi"), (
                f"{engine_name}: Missing smiles_to_inchi method"
            )
            assert hasattr(engine, "calculate_properties"), (
                f"{engine_name}: Missing calculate_properties method"
            )
            assert hasattr(engine, "generate_substitutions"), (
                f"{engine_name}: Missing generate_substitutions method"
            )

            # Test default parameters work
            result1 = engine.smiles_to_inchi(self.valid_smiles)
            assert isinstance(result1, StructureIdentifiers), (
                f"{engine_name}: Default should return dataclass"
            )

            result2 = engine.calculate_properties(self.valid_smiles)
            assert isinstance(result2, MolecularProperties), (
                f"{engine_name}: Default should return dataclass"
            )

            result3 = engine.generate_substitutions(self.valid_smiles)
            assert isinstance(result3, SubstitutionResult), (
                f"{engine_name}: Default should return dataclass"
            )

    def test_data_consistency_between_formats(self):
        """Test that dataclass and dict formats contain equivalent data."""
        for engine_name, engine in self.get_engines():
            # Test smiles_to_inchi
            dc_result = engine.smiles_to_inchi(self.valid_smiles, return_dataclass=True)
            dict_result = engine.smiles_to_inchi(
                self.valid_smiles, return_dataclass=False
            )

            converted_dc = StructureIdentifiers.from_dict(dict_result)

            assert dc_result.inchi == converted_dc.inchi, (
                f"{engine_name}: InChI mismatch"
            )
            assert dc_result.inchikey == converted_dc.inchikey, (
                f"{engine_name}: InChI Key mismatch"
            )
            assert dc_result.canonical_smiles == converted_dc.canonical_smiles, (
                f"{engine_name}: Canonical SMILES mismatch"
            )

            # Test calculate_properties
            dc_props = engine.calculate_properties(
                self.valid_smiles, return_dataclass=True
            )
            dict_props = engine.calculate_properties(
                self.valid_smiles, return_dataclass=False
            )

            converted_dc_props = MolecularProperties.from_dict(dict_props)

            # Check that key properties match (if they exist)
            if dc_props.log_p is not None and "LogP" in dict_props:
                assert abs(dc_props.log_p - converted_dc_props.log_p) < 1e-6, (
                    f"{engine_name}: LogP mismatch"
                )

            # Test generate_substitutions
            dc_subs = engine.generate_substitutions(
                self.valid_smiles, return_dataclass=True
            )
            list_subs = engine.generate_substitutions(
                self.valid_smiles, return_dataclass=False
            )

            assert dc_subs.substitutions == list_subs, (
                f"{engine_name}: Substitutions list mismatch"
            )


def test_type_validation_imports() -> None:
    """Test that all type imports work correctly."""
    # This test ensures the module structure is correct
    assert StructureIdentifiers is not None
    assert StructureIdentifiersDict is not None
    assert MolecularProperties is not None
    assert MolecularPropertiesDict is not None
    assert SubstitutionResult is not None
    assert InvalidSmilesError is not None
    assert PropertyCalculationError is not None
    assert SubstitutionGenerationError is not None


if __name__ == "__main__":
    # Run basic tests if script is executed directly
    test_suite = TestChemEngineTypeConsistency()
    test_suite.setup_method()

    print("Running type consistency tests...")

    try:
        test_suite.test_smiles_to_inchi_return_types()
        print("✓ smiles_to_inchi type tests passed")

        test_suite.test_calculate_properties_return_types()
        print("✓ calculate_properties type tests passed")

        test_suite.test_generate_substitutions_return_types()
        print("✓ generate_substitutions type tests passed")

        test_suite.test_interface_compliance()
        print("✓ Interface compliance tests passed")

        test_suite.test_data_consistency_between_formats()
        print("✓ Data consistency tests passed")

        test_suite.test_invalid_parameters()
        print("✓ Invalid parameters tests passed")

        print("\n🎉 All type consistency tests passed!")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        raise
