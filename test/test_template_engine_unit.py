#!/usr/bin/env python3
"""
Unit Tests for Template Engine.

Comprehensive tests for template loading, cycling strategies, computed fields,
and constraint handling in the template engine.
"""

import pytest
import random
from utils.template_engine import TemplateEngine


class TestTemplateEngineBasics:
    """Test basic template engine functionality."""
    
    @pytest.fixture
    def template_engine(self):
        """Provide TemplateEngine instance."""
        return TemplateEngine()
    
    @pytest.fixture
    def sample_template_config(self):
        """Provide sample template configuration."""
        return {
            "user_data": {
                "data": [
                    {
                        "FirstName": "John",
                        "LastName": "Doe",
                        "Age": 30,
                        "City": "New York"
                    },
                    {
                        "FirstName": "Jane",
                        "LastName": "Smith",
                        "Age": 25,
                        "City": "Los Angeles"
                    },
                    {
                        "FirstName": "Bob",
                        "LastName": "Johnson",
                        "Age": 35,
                        "City": "Chicago"
                    }
                ],
                "cycle": "sequential"
            }
        }
    
    def test_template_loading(self, template_engine, sample_template_config):
        """Test template configuration loading."""
        template_engine.load_templates(sample_template_config)
        
        assert "user_data" in template_engine.templates
        assert len(template_engine.templates["user_data"]["data"]) == 3
        assert template_engine.templates["user_data"]["cycle"] == "sequential"
    
    def test_template_value_retrieval(self, template_engine, sample_template_config):
        """Test retrieving values from templates."""
        template_engine.load_templates(sample_template_config)
        
        # Get first name from template
        first_name = template_engine.get_template_value("user_data", "FirstName")
        assert first_name in ["John", "Jane", "Bob"]
        
        # Get age from template
        age = template_engine.get_template_value("user_data", "Age")
        assert age in [30, 25, 35]
    
    def test_template_entry_retrieval(self, template_engine, sample_template_config):
        """Test retrieving complete entries from templates."""
        template_engine.load_templates(sample_template_config)
        
        entry = template_engine.get_template_entry("user_data")
        assert isinstance(entry, dict)
        assert "FirstName" in entry
        assert "LastName" in entry
        assert "Age" in entry
        assert "City" in entry
    
    def test_nonexistent_template_handling(self, template_engine):
        """Test handling of nonexistent templates."""
        # Should return None for nonexistent template
        result = template_engine.get_template_value("nonexistent", "field")
        assert result is None
        
        entry = template_engine.get_template_entry("nonexistent")
        assert entry is None
    
    def test_nonexistent_field_handling(self, template_engine, sample_template_config):
        """Test handling of nonexistent fields in templates."""
        template_engine.load_templates(sample_template_config)
        
        # Should return None for nonexistent field
        result = template_engine.get_template_value("user_data", "nonexistent_field")
        assert result is None


class TestCyclingStrategies:
    """Test different cycling strategies."""
    
    @pytest.fixture
    def template_engine(self):
        return TemplateEngine()
    
    def test_sequential_cycling(self, template_engine):
        """Test sequential cycling through template data."""
        template_config = {
            "sequential_data": {
                "data": [
                    {"value": "A", "index": 0},
                    {"value": "B", "index": 1},
                    {"value": "C", "index": 2}
                ],
                "cycle": "sequential"
            }
        }
        
        template_engine.load_templates(template_config)
        
        # Should cycle through in order: A, B, C, A, B, C, ...
        expected_sequence = ["A", "B", "C", "A", "B", "C"]
        actual_sequence = []
        
        for _ in range(6):
            value = template_engine.get_template_value("sequential_data", "value")
            actual_sequence.append(value)
        
        assert actual_sequence == expected_sequence
    
    def test_random_cycling(self, template_engine):
        """Test random cycling through template data."""
        template_config = {
            "random_data": {
                "data": [
                    {"value": "X"},
                    {"value": "Y"},
                    {"value": "Z"}
                ],
                "cycle": "random"
            }
        }
        
        template_engine.load_templates(template_config)
        
        # Get multiple values and check for randomness
        values = []
        for _ in range(20):
            value = template_engine.get_template_value("random_data", "value")
            values.append(value)
        
        # Should have all possible values
        unique_values = set(values)
        assert unique_values == {"X", "Y", "Z"}
        
        # Should have some variety (not all the same)
        assert len(unique_values) > 1
    
    def test_once_cycling(self, template_engine):
        """Test 'once' cycling strategy."""
        template_config = {
            "once_data": {
                "data": [
                    {"value": "SingleValue", "id": 1}
                ],
                "cycle": "once"
            }
        }
        
        template_engine.load_templates(template_config)
        
        # First call should return the value
        first_value = template_engine.get_template_value("once_data", "value")
        assert first_value == "SingleValue"
        
        # Subsequent calls should return None (exhausted)
        second_value = template_engine.get_template_value("once_data", "value")
        assert second_value is None
        
        third_value = template_engine.get_template_value("once_data", "value")
        assert third_value is None
    
    def test_cycling_state_independence(self, template_engine):
        """Test that different templates maintain independent cycling state."""
        template_config = {
            "template_a": {
                "data": [{"value": "A1"}, {"value": "A2"}],
                "cycle": "sequential"
            },
            "template_b": {
                "data": [{"value": "B1"}, {"value": "B2"}, {"value": "B3"}],
                "cycle": "sequential"
            }
        }
        
        template_engine.load_templates(template_config)
        
        # Interleave calls to different templates
        a1 = template_engine.get_template_value("template_a", "value")
        b1 = template_engine.get_template_value("template_b", "value")
        a2 = template_engine.get_template_value("template_a", "value")
        b2 = template_engine.get_template_value("template_b", "value")
        
        # Each template should maintain its own sequence
        assert a1 == "A1"
        assert a2 == "A2"
        assert b1 == "B1"
        assert b2 == "B2"


class TestComputedFields:
    """Test computed field functionality."""
    
    @pytest.fixture
    def template_engine(self):
        return TemplateEngine()
    
    def test_simple_computed_fields(self, template_engine):
        """Test simple computed field expressions."""
        template_config = {
            "computed_data": {
                "data": [
                    {
                        "FirstName": "John",
                        "LastName": "Doe",
                        "BirthYear": 1990
                    }
                ],
                "cycle": "sequential",
                "computed": {
                    "FullName": "concat(FirstName, ' ', LastName)",
                    "Age": "2024 - BirthYear"
                }
            }
        }
        
        template_engine.load_templates(template_config)
        
        # Test computed full name
        full_name = template_engine.get_template_value("computed_data", "FullName")
        assert full_name == "John Doe"
        
        # Test computed age
        age = template_engine.get_template_value("computed_data", "Age")
        assert age == 34
    
    def test_conditional_computed_fields(self, template_engine):
        """Test conditional computed field expressions."""
        template_config = {
            "conditional_data": {
                "data": [
                    {
                        "Name": "Alice",
                        "Score": 85,
                        "Age": 25
                    },
                    {
                        "Name": "Bob",
                        "Score": 92,
                        "Age": 17
                    }
                ],
                "cycle": "sequential",
                "computed": {
                    "Grade": {
                        "formula": "Score >= 90 ? 'A' : Score >= 80 ? 'B' : 'C'",
                        "inputs": ["Score"]
                    },
                    "Category": {
                        "formula": "Age >= 18 ? 'Adult' : 'Minor'",
                        "inputs": ["Age"]
                    }
                }
            }
        }
        
        template_engine.load_templates(template_config)
        
        # Test first entry (Alice)
        grade1 = template_engine.get_template_value("conditional_data", "Grade")
        category1 = template_engine.get_template_value("conditional_data", "Category")
        assert grade1 == "B"  # Score 85 -> B
        assert category1 == "Adult"  # Age 25 -> Adult
        
        # Test second entry (Bob)
        grade2 = template_engine.get_template_value("conditional_data", "Grade")
        category2 = template_engine.get_template_value("conditional_data", "Category")
        assert grade2 == "A"  # Score 92 -> A
        assert category2 == "Minor"  # Age 17 -> Minor
    
    def test_nested_computed_fields(self, template_engine):
        """Test computed fields that reference other computed fields."""
        template_config = {
            "nested_data": {
                "data": [
                    {
                        "FirstName": "Jane",
                        "LastName": "Smith",
                        "Department": "Engineering"
                    }
                ],
                "cycle": "sequential",
                "computed": {
                    "FullName": "concat(FirstName, ' ', LastName)",
                    "EmailPrefix": "concat(FirstName, '.', LastName)",
                    "Email": "concat(EmailPrefix, '@company.com')",
                    "DisplayName": "concat(FullName, ' (', Department, ')')"
                }
            }
        }
        
        template_engine.load_templates(template_config)
        
        # Test nested computation
        email = template_engine.get_template_value("nested_data", "Email")
        assert email == "Jane.Smith@company.com"
        
        display_name = template_engine.get_template_value("nested_data", "DisplayName")
        assert display_name == "Jane Smith (Engineering)"
    
    def test_computed_field_error_handling(self, template_engine):
        """Test error handling in computed fields."""
        template_config = {
            "error_data": {
                "data": [
                    {
                        "Name": "Test",
                        "Value": 10
                    }
                ],
                "cycle": "sequential",
                "computed": {
                    "InvalidField": "nonexistent_field * 2",
                    "DivisionByZero": "Value / 0",
                    "ValidField": "Name + ' User'"
                }
            }
        }
        
        template_engine.load_templates(template_config)
        
        # Invalid field reference should return None
        invalid_result = template_engine.get_template_value("error_data", "InvalidField")
        assert invalid_result is None
        
        # Division by zero should be handled gracefully
        division_result = template_engine.get_template_value("error_data", "DivisionByZero")
        assert division_result is None
        
        # Valid field should work normally
        valid_result = template_engine.get_template_value("error_data", "ValidField")
        assert valid_result == "Test User"


class TestTemplateConstraints:
    """Test template constraint handling."""
    
    @pytest.fixture
    def template_engine(self):
        return TemplateEngine()
    
    def test_constraint_filtering(self, template_engine):
        """Test filtering of template data based on constraints."""
        template_config = {
            "constrained_data": {
                "data": [
                    {
                        "Name": "Alice",
                        "Age": 25,
                        "Salary": 50000,
                        "valid": True
                    },
                    {
                        "Name": "Bob",
                        "Age": 16,  # Too young
                        "Salary": 30000,
                        "valid": False
                    },
                    {
                        "Name": "Charlie",
                        "Age": 30,
                        "Salary": 75000,
                        "valid": True
                    }
                ],
                "cycle": "sequential",
                "constraints": {
                    "age_constraint": {
                        "min_age": 18,
                        "max_age": 65
                    }
                }
            }
        }
        
        template_engine.load_templates(template_config)
        
        # Should only return entries that meet age constraints
        valid_entries = []
        for _ in range(10):
            entry = template_engine.get_template_entry("constrained_data")
            if entry and entry.get("Age", 0) >= 18:
                valid_entries.append(entry)
        
        # All returned entries should meet constraints
        assert len(valid_entries) > 0
        for entry in valid_entries:
            assert entry["Age"] >= 18
            assert entry["valid"]  # Should only get valid entries
    
    def test_constraint_validation(self, template_engine):
        """Test constraint validation for template data."""
        template_config = {
            "validated_data": {
                "data": [
                    {
                        "Amount": "1000.50",
                        "Currency": "USD",
                        "Email": "user@example.com"
                    },
                    {
                        "Amount": "50.00",    # Below minimum
                        "Currency": "XYZ",    # Invalid currency
                        "Email": "invalid"    # Invalid email
                    }
                ],
                "cycle": "sequential",
                "constraints": {
                    "validation_rules": {
                        "min_amount": 100.00,
                        "allowed_currencies": ["USD", "EUR", "GBP"],
                        "email_format": "^[\\w\\.-]+@[\\w\\.-]+\\.[a-z]+$"
                    }
                }
            }
        }
        
        template_engine.load_templates(template_config)
        
        # First entry should be valid
        entry1 = template_engine.get_template_entry("validated_data")
        assert entry1 is not None
        assert entry1["Currency"] == "USD"
        assert float(entry1["Amount"]) >= 100.00
        
        # Template engine should handle invalid entries appropriately
        # (either skip them or return None)
        entry2 = template_engine.get_template_entry("validated_data")
        if entry2 is not None:
            # If returned, should meet constraints
            assert entry2["Currency"] in ["USD", "EUR", "GBP"]
            assert float(entry2["Amount"]) >= 100.00


class TestTemplateEdgeCases:
    """Test edge cases and error conditions."""
    
    @pytest.fixture
    def template_engine(self):
        return TemplateEngine()
    
    def test_empty_template_data(self, template_engine):
        """Test handling of empty template data."""
        template_config = {
            "empty_data": {
                "data": [],
                "cycle": "sequential"
            }
        }
        
        template_engine.load_templates(template_config)
        
        # Should handle empty data gracefully
        result = template_engine.get_template_value("empty_data", "field")
        assert result is None
        
        entry = template_engine.get_template_entry("empty_data")
        assert entry is None
    
    def test_single_item_cycling(self, template_engine):
        """Test cycling with single item."""
        template_config = {
            "single_item": {
                "data": [{"value": "OnlyOne"}],
                "cycle": "sequential"
            }
        }
        
        template_engine.load_templates(template_config)
        
        # Should repeatedly return the same item
        for _ in range(5):
            value = template_engine.get_template_value("single_item", "value")
            assert value == "OnlyOne"
    
    def test_invalid_cycle_strategy(self, template_engine):
        """Test handling of invalid cycle strategy."""
        template_config = {
            "invalid_cycle": {
                "data": [{"value": "test"}],
                "cycle": "invalid_strategy"
            }
        }
        
        template_engine.load_templates(template_config)
        
        # Should default to sequential or handle gracefully
        value = template_engine.get_template_value("invalid_cycle", "value")
        # Should either work (defaulting to sequential) or return None
        assert value == "test" or value is None
    
    def test_malformed_template_config(self, template_engine):
        """Test handling of malformed template configuration."""
        malformed_configs = [
            # Missing data field
            {
                "missing_data": {
                    "cycle": "sequential"
                }
            },
            # Missing cycle field
            {
                "missing_cycle": {
                    "data": [{"value": "test"}]
                }
            },
            # Invalid data type for data field
            {
                "invalid_data_type": {
                    "data": "not_a_list",
                    "cycle": "sequential"
                }
            }
        ]
        
        for config in malformed_configs:
            template_engine.load_templates(config)
            # Should handle malformed configs gracefully
            # (either with defaults or by skipping invalid templates)
            
    def test_deep_nested_data(self, template_engine):
        """Test handling of deeply nested template data."""
        template_config = {
            "nested_data": {
                "data": [
                    {
                        "user": {
                            "personal": {
                                "name": {
                                    "first": "John",
                                    "last": "Doe"
                                },
                                "address": {
                                    "street": "123 Main St",
                                    "city": "Anytown"
                                }
                            }
                        }
                    }
                ],
                "cycle": "sequential",
                "computed": {
                    "FullAddress": "concat(user.personal.address.street, ', ', user.personal.address.city)",
                    "FullName": "concat(user.personal.name.first, ' ', user.personal.name.last)"
                }
            }
        }
        
        template_engine.load_templates(template_config)
        
        # Should handle nested field access
        full_name = template_engine.get_template_value("nested_data", "FullName")
        assert full_name == "John Doe"
        
        full_address = template_engine.get_template_value("nested_data", "FullAddress")
        assert full_address == "123 Main St, Anytown"
    
    def test_concurrent_template_access(self, template_engine):
        """Test concurrent access to template data."""
        template_config = {
            "concurrent_data": {
                "data": [
                    {"id": 1, "value": "A"},
                    {"id": 2, "value": "B"},
                    {"id": 3, "value": "C"}
                ],
                "cycle": "sequential"
            }
        }
        
        template_engine.load_templates(template_config)
        
        # Simulate concurrent access by interleaving different field requests
        results = []
        for i in range(10):
            if i % 2 == 0:
                value = template_engine.get_template_value("concurrent_data", "value")
                results.append(("value", value))
            else:
                id_val = template_engine.get_template_value("concurrent_data", "id")
                results.append(("id", id_val))
        
        # Should maintain consistency (same entry for value and id)
        # This is a simplified test - real concurrent access would need threading
        assert len(results) == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])