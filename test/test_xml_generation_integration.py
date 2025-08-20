#!/usr/bin/env python3
"""
Integration Tests for XML Generation with Enhanced JSON Configurations.

Tests the complete flow from JSON configuration to XML generation,
validating that all components work together correctly.
"""

import pytest
import json
import os
import tempfile
from pathlib import Path
from lxml import etree
from utils.enhanced_json_config import EnhancedJsonConfig
from utils.enhanced_xml_generator import EnhancedXMLGenerator
from services.xml_validator import XMLValidator


class TestXMLGenerationIntegration:
    """Test integration between JSON configs and XML generation."""
    
    @pytest.fixture
    def test_schema_path(self):
        """Provide path to test schema."""
        return "resource/test_xsd/1_test.xsd"
    
    @pytest.fixture
    def config_directory(self):
        """Provide path to configuration directory."""
        return Path("resource/test_JSON_for_test_xsd")
    
    @pytest.fixture
    def temp_output_dir(self):
        """Create temporary directory for output files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    def test_business_config_xml_generation(self, test_schema_path, config_directory):
        """Test XML generation from business configuration."""
        if not os.path.exists(test_schema_path):
            pytest.skip(f"Test schema not found: {test_schema_path}")
        
        business_config_path = config_directory / "1_xsd_travel_booking_business_config.json"
        if not business_config_path.exists():
            pytest.skip("Business config not found")
        
        with open(business_config_path, 'r') as f:
            config_data = json.load(f)
        
        config = EnhancedJsonConfig(config_data)
        assert config.is_valid(), f"Config validation failed: {config.get_validation_errors()}"
        
        generator = EnhancedXMLGenerator(test_schema_path)
        xml_content = generator.generate_with_config(config)
        
        # Basic XML validation
        assert xml_content is not None
        assert len(xml_content) > 100
        assert '<?xml version="1.0"' in xml_content
        assert '<TravelBooking' in xml_content
        assert '</TravelBooking>' in xml_content
        
        # Verify business-specific content
        assert 'TB-004-2024' in xml_content  # Booking ID from config
        assert 'Corporate Card' in xml_content  # Payment method from config
        assert '4320.75' in xml_content  # Amount from config
        
        # Verify choice selection (PickupLocation for business config)
        assert '<PickupLocation>' in xml_content or 'PickupLocation' in xml_content
        
        print("✅ Business config XML generation successful")
    
    def test_family_config_xml_generation(self, test_schema_path, config_directory):
        """Test XML generation from family configuration."""
        if not os.path.exists(test_schema_path):
            pytest.skip(f"Test schema not found: {test_schema_path}")
        
        family_config_path = config_directory / "1_xsd_travel_booking_family_config.json"
        if not family_config_path.exists():
            pytest.skip("Family config not found")
        
        with open(family_config_path, 'r') as f:
            config_data = json.load(f)
        
        config = EnhancedJsonConfig(config_data)
        generator = EnhancedXMLGenerator(test_schema_path)
        xml_content = generator.generate_with_config(config)
        
        # Verify family-specific content
        assert 'Davis' in xml_content  # Family name from template
        assert 'Robert' in xml_content  # Father's name from template
        assert 'Lisa' in xml_content  # Mother's name from template
        
        # Should use DeliveryAddress choice
        assert '<DeliveryAddress>' in xml_content or 'DeliveryAddress' in xml_content
        
        print("✅ Family config XML generation successful")
    
    def test_minimalistic_config_xml_generation(self, test_schema_path, config_directory):
        """Test XML generation from minimalistic configuration."""
        if not os.path.exists(test_schema_path):
            pytest.skip(f"Test schema not found: {test_schema_path}")
        
        minimal_config_path = config_directory / "1_xsd_travel_booking_minimalistic_config.json"
        if not minimal_config_path.exists():
            pytest.skip("Minimalistic config not found")
        
        with open(minimal_config_path, 'r') as f:
            config_data = json.load(f)
        
        config = EnhancedJsonConfig(config_data)
        generator = EnhancedXMLGenerator(test_schema_path)
        xml_content = generator.generate_with_config(config)
        
        # Verify minimal mode produces valid XML with generated data
        assert xml_content is not None
        assert '<TravelBooking' in xml_content
        
        # Should contain generated values (UUIDs for IDs, etc.)
        # The exact values will be generated, so we check for patterns
        assert 'PassengerID=' in xml_content or '<PassengerID>' in xml_content
        assert 'SegmentID=' in xml_content or '<SegmentID>' in xml_content
        
        print("✅ Minimalistic config XML generation successful")
    
    def test_constraint_config_xml_generation(self, test_schema_path, config_directory):
        """Test XML generation from constraint configuration."""
        if not os.path.exists(test_schema_path):
            pytest.skip(f"Test schema not found: {test_schema_path}")
        
        constraint_config_path = config_directory / "1_xsd_travel_booking_constraint_config.json"
        if not constraint_config_path.exists():
            pytest.skip("Constraint config not found")
        
        with open(constraint_config_path, 'r') as f:
            config_data = json.load(f)
        
        config = EnhancedJsonConfig(config_data)
        generator = EnhancedXMLGenerator(test_schema_path)
        xml_content = generator.generate_with_config(config)
        
        # Verify constraint-specific content
        assert 'Thomas' in xml_content or 'Sarah' in xml_content  # Template passenger names
        assert 'CONST-BK-001' in xml_content  # Specific booking ID
        assert 'ValidatedCard' in xml_content or 'SecureTransfer' in xml_content  # Payment methods
        
        # Verify amounts are within constraint range (500-5000)
        # This is more complex to validate without parsing, but we check for presence
        assert 'Amount>' in xml_content or 'Amount=' in xml_content
        
        print("✅ Constraint config XML generation successful")
    
    def test_template_data_integration(self, test_schema_path, config_directory):
        """Test that template data is correctly integrated into XML."""
        if not os.path.exists(test_schema_path):
            pytest.skip(f"Test schema not found: {test_schema_path}")
        
        # Test dependent config which has advanced template usage
        dependent_config_path = config_directory / "1_xsd_travel_booking_dependent_config.json"
        if not dependent_config_path.exists():
            pytest.skip("Dependent config not found")
        
        with open(dependent_config_path, 'r') as f:
            config_data = json.load(f)
        
        config = EnhancedJsonConfig(config_data)
        generator = EnhancedXMLGenerator(test_schema_path)
        xml_content = generator.generate_with_config(config)
        
        # Verify template passenger data
        assert 'Taylor' in xml_content or 'Jamie' in xml_content  # Template names
        assert 'Williams' in xml_content or 'Martinez' in xml_content  # Template surnames
        assert 'Non-Binary' in xml_content or 'Female' in xml_content  # Template genders
        
        # Verify template flight data
        assert 'SFO' in xml_content or 'HNL' in xml_content  # Template airports
        
        print("✅ Template data integration successful")
    
    def test_choice_resolution_integration(self, test_schema_path, config_directory):
        """Test that choice resolution works correctly in XML generation."""
        if not os.path.exists(test_schema_path):
            pytest.skip(f"Test schema not found: {test_schema_path}")
        
        # Test configs with different choice selections
        test_configs = [
            ("1_xsd_travel_booking_pickup_config.json", "PickupLocation"),
            ("1_xsd_travel_booking_delivery_config.json", "DeliveryAddress"),
            ("1_xsd_travel_booking_single_domestic_config.json", "DeliveryAddress")
        ]
        
        for config_filename, expected_choice in test_configs:
            config_path = config_directory / config_filename
            if not config_path.exists():
                continue
            
            with open(config_path, 'r') as f:
                config_data = json.load(f)
            
            config = EnhancedJsonConfig(config_data)
            generator = EnhancedXMLGenerator(test_schema_path)
            xml_content = generator.generate_with_config(config)
            
            # Verify the expected choice appears in XML
            choice_found = f"<{expected_choice}>" in xml_content or f"{expected_choice}>" in xml_content
            assert choice_found, f"Expected choice '{expected_choice}' not found in XML from {config_filename}"
            
            print(f"✅ Choice '{expected_choice}' correctly resolved in {config_filename}")
    
    def test_pattern_generation_integration(self, test_schema_path, config_directory):
        """Test that pattern-based generation works in XML output."""
        if not os.path.exists(test_schema_path):
            pytest.skip(f"Test schema not found: {test_schema_path}")
        
        # Test global overrides config which uses extensive patterns
        global_config_path = config_directory / "1_xsd_travel_booking_global_overrides_config.json"
        if not global_config_path.exists():
            pytest.skip("Global overrides config not found")
        
        with open(global_config_path, 'r') as f:
            config_data = json.load(f)
        
        config = EnhancedJsonConfig(config_data)
        generator = EnhancedXMLGenerator(test_schema_path)
        xml_content = generator.generate_with_config(config)
        
        # Verify pattern-based content
        # *ID pattern should generate IDs
        assert 'PassengerID=' in xml_content or '<PassengerID>' in xml_content
        assert 'SegmentID=' in xml_content or '<SegmentID>' in xml_content
        
        # *Name pattern should generate names
        assert '<FirstName>' in xml_content and '</FirstName>' in xml_content
        assert '<LastName>' in xml_content and '</LastName>' in xml_content
        
        # *Airport pattern should generate airport codes
        assert '<DepartureAirport>' in xml_content
        assert '<ArrivalAirport>' in xml_content
        
        print("✅ Pattern generation integration successful")
    
    def test_xml_validation_against_schema(self, test_schema_path, config_directory):
        """Test that generated XML validates against the XSD schema."""
        if not os.path.exists(test_schema_path):
            pytest.skip(f"Test schema not found: {test_schema_path}")
        
        validator = XMLValidator()
        successful_validations = 0
        total_configs = 0
        
        for config_file in config_directory.glob("1_xsd_*.json"):
            total_configs += 1
            
            try:
                with open(config_file, 'r') as f:
                    config_data = json.load(f)
                
                config = EnhancedJsonConfig(config_data)
                generator = EnhancedXMLGenerator(test_schema_path)
                xml_content = generator.generate_with_config(config)
                
                # Validate against schema
                is_valid, errors, warnings = validator.validate_xml_string(xml_content, test_schema_path)
                
                if is_valid:
                    successful_validations += 1
                    print(f"✅ {config_file.name}: Generated XML validates against schema")
                else:
                    print(f"❌ {config_file.name}: Validation failed - {len(errors)} errors")
                    for error in errors[:3]:  # Show first 3 errors
                        print(f"   - {error}")
                
            except Exception as e:
                print(f"❌ {config_file.name}: Exception during validation - {e}")
        
        # At least 70% of configs should generate valid XML
        success_rate = successful_validations / total_configs if total_configs > 0 else 0
        assert success_rate >= 0.7, f"Too many validation failures: {successful_validations}/{total_configs} passed"
        
        print(f"✅ XML validation success rate: {successful_validations}/{total_configs} ({success_rate:.1%})")
    
    def test_namespace_handling_integration(self, test_schema_path, config_directory):
        """Test that namespace handling works correctly in generated XML."""
        if not os.path.exists(test_schema_path):
            pytest.skip(f"Test schema not found: {test_schema_path}")
        
        # Test config with namespace configuration
        global_config_path = config_directory / "1_xsd_travel_booking_global_overrides_config.json"
        if not global_config_path.exists():
            pytest.skip("Global overrides config not found")
        
        with open(global_config_path, 'r') as f:
            config_data = json.load(f)
        
        config = EnhancedJsonConfig(config_data)
        generator = EnhancedXMLGenerator(test_schema_path)
        xml_content = generator.generate_with_config(config)
        
        # Verify namespace declarations
        assert 'xmlns=' in xml_content or 'xmlns:' in xml_content
        
        # Verify default namespace if specified
        if hasattr(config, 'namespaces') and config.namespaces:
            default_ns = config.namespaces.get('default')
            if default_ns:
                assert default_ns in xml_content
        
        print("✅ Namespace handling integration successful")
    
    def test_error_handling_in_integration(self, test_schema_path, config_directory):
        """Test error handling during integration flow."""
        if not os.path.exists(test_schema_path):
            pytest.skip(f"Test schema not found: {test_schema_path}")
        
        # Test with invalid schema path
        try:
            generator = EnhancedXMLGenerator("nonexistent_schema.xsd")
            # Should handle this gracefully or raise appropriate exception
        except Exception as e:
            assert "schema" in str(e).lower() or "file" in str(e).lower()
        
        # Test with invalid config
        invalid_config_data = {"invalid": "config"}
        invalid_config = EnhancedJsonConfig(invalid_config_data)
        
        if not invalid_config.is_valid():
            # This should be handled gracefully
            generator = EnhancedXMLGenerator(test_schema_path)
            try:
                xml_content = generator.generate_with_config(invalid_config)
                # If it doesn't raise an exception, it should produce some output
                assert xml_content is not None
            except Exception as e:
                # Exception is acceptable for invalid config
                assert "config" in str(e).lower() or "validation" in str(e).lower()
        
        print("✅ Error handling integration successful")
    
    def test_performance_with_large_configs(self, test_schema_path, config_directory):
        """Test performance with configurations that generate large XML."""
        if not os.path.exists(test_schema_path):
            pytest.skip(f"Test schema not found: {test_schema_path}")
        
        # Create a config that should generate a reasonably large XML
        large_config_data = {
            "schema": "1_test.xsd",
            "mode": "complete",
            "seed": 12345,
            "templates": {
                "large_passenger_pool": {
                    "data": [
                        {
                            "FirstName": f"Passenger{i}",
                            "LastName": f"Surname{i}",
                            "Gender": "Male" if i % 2 == 0 else "Female",
                            "BirthDate": f"19{80 + (i % 40):02d}-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}",
                            "PassengerID": f"PAX-{i:04d}"
                        }
                        for i in range(50)  # 50 passengers
                    ],
                    "cycle": "sequential"
                }
            },
            "choices": {
                "TravelBooking": "DeliveryAddress"
            }
        }
        
        config = EnhancedJsonConfig(large_config_data)
        generator = EnhancedXMLGenerator(test_schema_path)
        
        import time
        start_time = time.time()
        xml_content = generator.generate_with_config(config)
        end_time = time.time()
        
        generation_time = end_time - start_time
        
        # Verify the XML was generated
        assert xml_content is not None
        assert len(xml_content) > 1000  # Should be reasonably large
        
        # Performance should be reasonable (less than 10 seconds)
        assert generation_time < 10.0, f"Generation took too long: {generation_time:.2f} seconds"
        
        print(f"✅ Large config performance test successful: {generation_time:.2f}s")


class TestConfigToXMLConsistency:
    """Test consistency between config settings and generated XML."""
    
    @pytest.fixture
    def test_schema_path(self):
        return "resource/test_xsd/1_test.xsd"
    
    def test_value_consistency(self, test_schema_path):
        """Test that explicit values in config appear in XML."""
        if not os.path.exists(test_schema_path):
            pytest.skip(f"Test schema not found: {test_schema_path}")
        
        config_data = {
            "schema": "1_test.xsd",
            "mode": "complete",
            "values": {
                "/TravelBooking/BookingID": "TEST-BOOKING-001",
                "PaymentMethod": "Test Card",
                "Amount": "1234.56",
                "Currency": "EUR"
            },
            "choices": {
                "TravelBooking": "DeliveryAddress"
            }
        }
        
        config = EnhancedJsonConfig(config_data)
        generator = EnhancedXMLGenerator(test_schema_path)
        xml_content = generator.generate_with_config(config)
        
        # Verify all explicit values appear in XML
        assert "TEST-BOOKING-001" in xml_content
        assert "Test Card" in xml_content
        assert "1234.56" in xml_content
        assert "EUR" in xml_content
        
        print("✅ Value consistency test successful")
    
    def test_seed_consistency(self, test_schema_path):
        """Test that the same seed produces consistent XML."""
        if not os.path.exists(test_schema_path):
            pytest.skip(f"Test schema not found: {test_schema_path}")
        
        config_data = {
            "schema": "1_test.xsd",
            "mode": "complete",
            "seed": 42,
            "patterns": {
                "*ID": "generate:uuid",
                "*Amount": "generate:currency"
            }
        }
        
        config = EnhancedJsonConfig(config_data)
        generator = EnhancedXMLGenerator(test_schema_path)
        
        # Generate XML twice with same seed
        xml_content1 = generator.generate_with_config(config)
        xml_content2 = generator.generate_with_config(config)
        
        # Should be identical due to seed
        assert xml_content1 == xml_content2, "Same seed should produce identical XML"
        
        print("✅ Seed consistency test successful")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])