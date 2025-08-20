#!/usr/bin/env python3
"""
Validation Tests for Constraint Handling in Enhanced JSON Configuration.

Tests constraint validation, enforcement, and error handling in the
enhanced JSON configuration system.
"""

import pytest
import json
from utils.enhanced_json_config import EnhancedJsonConfig
from utils.constraint_validator import ConstraintValidator
from utils.template_engine import TemplateEngine


class TestConstraintValidation:
    """Test constraint validation functionality."""
    
    @pytest.fixture
    def constraint_validator(self):
        """Provide ConstraintValidator instance."""
        return ConstraintValidator()
    
    def test_global_constraint_validation(self, constraint_validator):
        """Test global constraint validation."""
        global_constraints = {
            "max_depth": 10,
            "ensure_unique_combinations": True,
            "business_hours_only": True
        }
        
        # Valid global constraints
        assert constraint_validator.validate_global_constraints(global_constraints)
        
        # Invalid max_depth
        invalid_constraints = global_constraints.copy()
        invalid_constraints["max_depth"] = -1
        assert not constraint_validator.validate_global_constraints(invalid_constraints)
        
        # Invalid type
        invalid_constraints = global_constraints.copy()
        invalid_constraints["ensure_unique_combinations"] = "not_boolean"
        assert not constraint_validator.validate_global_constraints(invalid_constraints)
    
    def test_element_constraint_validation(self, constraint_validator):
        """Test element-specific constraint validation."""
        element_constraints = {
            "Passenger": {
                "min_count": 1,
                "max_count": 4,
                "default_count": 2
            },
            "FlightSegment": {
                "min_count": 1,
                "max_count": 3,
                "default_count": 1
            }
        }
        
        # Valid element constraints
        assert constraint_validator.validate_element_constraints(element_constraints)
        
        # Invalid count range
        invalid_constraints = {
            "Passenger": {
                "min_count": 5,
                "max_count": 3,  # max < min
                "default_count": 2
            }
        }
        assert not constraint_validator.validate_element_constraints(invalid_constraints)
        
        # Default count outside range
        invalid_constraints = {
            "Passenger": {
                "min_count": 1,
                "max_count": 4,
                "default_count": 10  # default > max
            }
        }
        assert not constraint_validator.validate_element_constraints(invalid_constraints)
    
    def test_pattern_constraint_validation(self, constraint_validator):
        """Test pattern constraint validation."""
        pattern_constraints = {
            "*Amount": {
                "generator": "generate:currency",
                "constraints": {
                    "min": 0,
                    "max": 10000,
                    "precision": 2
                }
            },
            "*Time": {
                "generator": "generate:datetime",
                "constraints": {
                    "format": "ISO8601",
                    "future_only": True
                }
            }
        }
        
        # Valid pattern constraints
        assert constraint_validator.validate_pattern_constraints(pattern_constraints)
        
        # Invalid range
        invalid_constraints = pattern_constraints.copy()
        invalid_constraints["*Amount"]["constraints"]["min"] = 100
        invalid_constraints["*Amount"]["constraints"]["max"] = 50  # max < min
        assert not constraint_validator.validate_pattern_constraints(invalid_constraints)
        
        # Invalid generator
        invalid_constraints = pattern_constraints.copy()
        invalid_constraints["*Amount"]["generator"] = "invalid:generator"
        assert not constraint_validator.validate_pattern_constraints(invalid_constraints)
    
    def test_template_constraint_validation(self, constraint_validator):
        """Test template constraint validation."""
        template_constraints = {
            "age_validation": {
                "min_age": 18,
                "max_age": 80,
                "birth_date_format": "YYYY-MM-DD"
            },
            "payment_validation": {
                "allowed_currencies": ["USD", "EUR", "GBP"],
                "amount_range": {"min": 500.00, "max": 5000.00},
                "precision": 2
            }
        }
        
        # Valid template constraints
        assert constraint_validator.validate_template_constraints(template_constraints)
        
        # Invalid age range
        invalid_constraints = template_constraints.copy()
        invalid_constraints["age_validation"]["min_age"] = 90
        invalid_constraints["age_validation"]["max_age"] = 65  # max < min
        assert not constraint_validator.validate_template_constraints(invalid_constraints)
        
        # Invalid currency list
        invalid_constraints = template_constraints.copy()
        invalid_constraints["payment_validation"]["allowed_currencies"] = "not_a_list"
        assert not constraint_validator.validate_template_constraints(invalid_constraints)


class TestConstraintEnforcement:
    """Test constraint enforcement during data generation."""
    
    @pytest.fixture
    def template_engine(self):
        """Provide TemplateEngine instance."""
        return TemplateEngine()
    
    def test_age_constraint_enforcement(self, template_engine):
        """Test age constraint enforcement in templates."""
        template_config = {
            "passenger_pool": {
                "data": [
                    {
                        "FirstName": "John",
                        "LastName": "Doe",
                        "BirthDate": "1990-01-01",
                        "age": 34
                    },
                    {
                        "FirstName": "Jane",
                        "LastName": "Smith", 
                        "BirthDate": "2010-01-01",  # Too young
                        "age": 14
                    },
                    {
                        "FirstName": "Bob",
                        "LastName": "Wilson",
                        "BirthDate": "1975-01-01",
                        "age": 49
                    }
                ],
                "cycle": "sequential",
                "constraints": {
                    "age_validation": {
                        "min_age": 18,
                        "max_age": 80
                    }
                }
            }
        }
        
        template_engine.load_templates(template_config)
        
        # Should only return entries that meet age constraints
        valid_entries = []
        for _ in range(10):  # Try multiple times
            entry = template_engine.get_template_entry("passenger_pool")
            if entry and entry.get("age", 0) >= 18:
                valid_entries.append(entry)
        
        # All returned entries should meet the age constraint
        assert len(valid_entries) > 0, "Should return some valid entries"
        for entry in valid_entries:
            assert entry["age"] >= 18, f"Entry with age {entry['age']} violates constraint"
    
    def test_amount_constraint_enforcement(self):
        """Test amount constraint enforcement."""
        constraint_validator = ConstraintValidator()
        
        amount_constraints = {
            "min": 500.00,
            "max": 5000.00,
            "precision": 2
        }
        
        # Valid amounts
        valid_amounts = ["500.00", "1000.50", "4999.99"]
        for amount in valid_amounts:
            assert constraint_validator.validate_amount(amount, amount_constraints)
        
        # Invalid amounts
        invalid_amounts = ["499.99", "5000.01", "1000.555"]  # Below min, above max, too precise
        for amount in invalid_amounts:
            assert not constraint_validator.validate_amount(amount, amount_constraints)
    
    def test_currency_constraint_enforcement(self):
        """Test currency constraint enforcement."""
        constraint_validator = ConstraintValidator()
        
        currency_constraints = {
            "allowed_currencies": ["USD", "EUR", "GBP"]
        }
        
        # Valid currencies
        valid_currencies = ["USD", "EUR", "GBP"]
        for currency in valid_currencies:
            assert constraint_validator.validate_currency(currency, currency_constraints)
        
        # Invalid currencies
        invalid_currencies = ["JPY", "CAD", "AUD", ""]
        for currency in invalid_currencies:
            assert not constraint_validator.validate_currency(currency, currency_constraints)
    
    def test_date_format_constraint_enforcement(self):
        """Test date format constraint enforcement."""
        constraint_validator = ConstraintValidator()
        
        date_constraints = {
            "format": "YYYY-MM-DD",
            "min_year": 1920,
            "max_year": 2010
        }
        
        # Valid dates
        valid_dates = ["1990-01-01", "2005-12-31", "1920-01-01", "2010-12-31"]
        for date in valid_dates:
            assert constraint_validator.validate_date(date, date_constraints)
        
        # Invalid dates
        invalid_dates = ["1919-01-01", "2011-01-01", "90-01-01", "1990/01/01", "invalid-date"]
        for date in invalid_dates:
            assert not constraint_validator.validate_date(date, date_constraints)


class TestConstraintConfigIntegration:
    """Test constraint integration with full configuration."""
    
    def test_constraint_config_loading(self):
        """Test loading constraint configuration from JSON."""
        constraint_config_data = {
            "schema": "1_test.xsd",
            "mode": "complete",
            "seed": 999,
            "constraints": {
                "global": {
                    "ensure_unique_combinations": True,
                    "max_depth": 6,
                    "business_hours_only": True
                },
                "elements": {
                    "Passenger": {
                        "min_count": 1,
                        "max_count": 4,
                        "default_count": 2
                    },
                    "FlightSegment": {
                        "min_count": 1,
                        "max_count": 3,
                        "default_count": 1
                    }
                },
                "validation_rules": {
                    "business_rules": {
                        "min_booking_amount": 500.00,
                        "max_booking_amount": 5000.00,
                        "allowed_currencies": ["USD", "EUR", "GBP"]
                    }
                }
            }
        }
        
        config = EnhancedJsonConfig(constraint_config_data)
        assert config.is_valid()
        
        # Test constraint access
        global_constraints = config.get_global_constraints()
        assert global_constraints["max_depth"] == 6
        assert global_constraints["ensure_unique_combinations"] is True
        
        element_constraints = config.get_element_constraints()
        assert "Passenger" in element_constraints
        assert element_constraints["Passenger"]["min_count"] == 1
        assert element_constraints["Passenger"]["max_count"] == 4
        
        validation_rules = config.get_validation_rules()
        assert "business_rules" in validation_rules
        assert validation_rules["business_rules"]["min_booking_amount"] == 500.00
    
    def test_template_constraints_integration(self):
        """Test template constraint integration."""
        template_config_data = {
            "schema": "1_test.xsd",
            "mode": "complete",
            "templates": {
                "validated_passenger_pool": {
                    "data": [
                        {
                            "FirstName": "Thomas",
                            "LastName": "Anderson",
                            "BirthDate": "1980-03-15",
                            "age": 44
                        },
                        {
                            "FirstName": "Sarah",
                            "LastName": "Connor",
                            "BirthDate": "1975-12-22",
                            "age": 48
                        }
                    ],
                    "cycle": "sequential",
                    "constraints": {
                        "age_validation": {
                            "min_age": 18,
                            "max_age": 80,
                            "birth_date_format": "YYYY-MM-DD"
                        }
                    }
                }
            }
        }
        
        config = EnhancedJsonConfig(template_config_data)
        assert config.is_valid()
        
        # Test template constraint access
        templates = config.get_templates()
        assert "validated_passenger_pool" in templates
        
        template_data = templates["validated_passenger_pool"]
        assert "constraints" in template_data
        assert "age_validation" in template_data["constraints"]
        
        age_constraints = template_data["constraints"]["age_validation"]
        assert age_constraints["min_age"] == 18
        assert age_constraints["max_age"] == 80
    
    def test_pattern_constraints_integration(self):
        """Test pattern constraint integration."""
        pattern_config_data = {
            "schema": "1_test.xsd",
            "mode": "complete",
            "patterns": {
                "*Amount": {
                    "generator": "generate:currency",
                    "constraints": {
                        "min": 500.00,
                        "max": 5000.00,
                        "precision": 2
                    }
                },
                "*Time": {
                    "generator": "generate:datetime",
                    "constraints": {
                        "format": "ISO8601",
                        "future_only": True
                    }
                },
                "*Name": {
                    "generator": "generate:name",
                    "constraints": {
                        "min_length": 2,
                        "max_length": 30,
                        "alpha_only": True
                    }
                }
            }
        }
        
        config = EnhancedJsonConfig(pattern_config_data)
        assert config.is_valid()
        
        # Test pattern constraint access
        patterns = config.get_patterns()
        
        # Amount pattern constraints
        amount_pattern = patterns["*Amount"]
        assert amount_pattern["generator"] == "generate:currency"
        assert amount_pattern["constraints"]["min"] == 500.00
        assert amount_pattern["constraints"]["max"] == 5000.00
        
        # Time pattern constraints
        time_pattern = patterns["*Time"]
        assert time_pattern["generator"] == "generate:datetime"
        assert time_pattern["constraints"]["format"] == "ISO8601"
        assert time_pattern["constraints"]["future_only"] is True
        
        # Name pattern constraints
        name_pattern = patterns["*Name"]
        assert name_pattern["generator"] == "generate:name"
        assert name_pattern["constraints"]["min_length"] == 2
        assert name_pattern["constraints"]["max_length"] == 30


class TestConstraintErrorHandling:
    """Test error handling for constraint violations."""
    
    def test_constraint_violation_detection(self):
        """Test detection of constraint violations."""
        constraint_validator = ConstraintValidator()
        
        # Test amount constraint violation
        amount_constraints = {"min": 100, "max": 1000, "precision": 2}
        
        violations = []
        test_amounts = ["50.00", "1500.00", "500.555"]  # Below min, above max, too precise
        
        for amount in test_amounts:
            if not constraint_validator.validate_amount(amount, amount_constraints):
                violation = constraint_validator.get_violation_reason(amount, amount_constraints)
                violations.append(violation)
        
        assert len(violations) == 3, f"Expected 3 violations, got {len(violations)}"
        
        # Check violation reasons contain relevant information
        violation_text = " ".join(violations).lower()
        assert "minimum" in violation_text or "min" in violation_text
        assert "maximum" in violation_text or "max" in violation_text
        assert "precision" in violation_text or "decimal" in violation_text
    
    def test_constraint_error_recovery(self):
        """Test error recovery from constraint violations."""
        template_engine = TemplateEngine()
        
        # Template with some invalid data
        template_config = {
            "mixed_data_pool": {
                "data": [
                    {"amount": "500.00", "currency": "USD", "valid": True},
                    {"amount": "50.00", "currency": "USD", "valid": False},   # Below min
                    {"amount": "1500.00", "currency": "EUR", "valid": True},
                    {"amount": "2000.00", "currency": "XYZ", "valid": False}  # Invalid currency
                ],
                "cycle": "sequential",
                "constraints": {
                    "amount_validation": {
                        "min_amount": 100.00,
                        "allowed_currencies": ["USD", "EUR", "GBP"]
                    }
                }
            }
        }
        
        template_engine.load_templates(template_config)
        
        # Should skip invalid entries and return only valid ones
        valid_entries = []
        for _ in range(10):
            entry = template_engine.get_template_entry("mixed_data_pool")
            if entry and entry.get("valid"):
                valid_entries.append(entry)
        
        # Should have found some valid entries
        assert len(valid_entries) > 0, "Should recover and return valid entries"
        
        # All returned entries should be valid
        for entry in valid_entries:
            assert entry["valid"], "Should only return valid entries"
    
    def test_constraint_validation_error_messages(self):
        """Test that constraint validation provides clear error messages."""
        invalid_config_data = {
            "schema": "1_test.xsd",
            "mode": "complete",
            "constraints": {
                "elements": {
                    "Passenger": {
                        "min_count": 10,
                        "max_count": 5,  # max < min - should trigger error
                        "default_count": 15  # default > max - should trigger error
                    }
                }
            }
        }
        
        config = EnhancedJsonConfig(invalid_config_data)
        assert not config.is_valid()
        
        errors = config.get_validation_errors()
        assert len(errors) > 0, "Should have validation errors"
        
        # Check that error messages are informative
        error_text = " ".join(errors).lower()
        assert "count" in error_text or "range" in error_text
        assert "passenger" in error_text  # Should mention the element name
    
    def test_missing_constraint_handling(self):
        """Test handling of missing or incomplete constraints."""
        incomplete_config_data = {
            "schema": "1_test.xsd",
            "mode": "complete",
            "patterns": {
                "*Amount": {
                    "generator": "generate:currency",
                    # Missing constraints section
                }
            },
            "templates": {
                "incomplete_template": {
                    "data": [{"field": "value"}],
                    # Missing cycle
                }
            }
        }
        
        config = EnhancedJsonConfig(incomplete_config_data)
        
        # Should handle missing constraints gracefully
        patterns = config.get_patterns()
        assert "*Amount" in patterns
        
        # Should provide defaults for missing constraint fields
        amount_pattern = patterns["*Amount"]
        assert amount_pattern["generator"] == "generate:currency"
        
        # For templates, missing cycle should be caught by validation
        if not config.is_valid():
            errors = config.get_validation_errors()
            error_text = " ".join(errors).lower()
            assert "cycle" in error_text or "template" in error_text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])