#!/usr/bin/env python3
"""
Unit Tests for EnhancedJsonConfig Parser.

Focused unit tests for the EnhancedJsonConfig class including validation,
field parsing, and error handling.
"""

import pytest
import json
from utils.enhanced_json_config import EnhancedJsonConfig


class TestEnhancedJsonConfigParsing:
    """Test parsing of enhanced JSON configuration format."""
    
    def test_minimal_valid_config(self):
        """Test parsing minimal valid configuration."""
        config_data = {
            "schema": "test.xsd",
            "mode": "minimal"
        }
        
        config = EnhancedJsonConfig(config_data)
        assert config.is_valid()
        assert config.schema == "test.xsd"
        assert config.mode == "minimal"
        assert config.seed is None  # Optional field
    
    def test_complete_valid_config(self):
        """Test parsing complete valid configuration with all fields."""
        config_data = {
            "schema": "test.xsd",
            "mode": "complete",
            "seed": 12345,
            "values": {
                "/root/element": "test_value",
                "simple_element": "another_value"
            },
            "patterns": {
                "*ID": "generate:uuid",
                "*Amount": {
                    "generator": "generate:currency",
                    "constraints": {
                        "min": 0,
                        "max": 1000
                    }
                }
            },
            "choices": {
                "ChoiceElement": "OptionA",
                "ConditionalChoice": {
                    "conditions": [
                        {
                            "if": "Amount > 100",
                            "choose": "OptionB"
                        }
                    ],
                    "default": "OptionA"
                }
            },
            "templates": {
                "user_data": {
                    "data": [
                        {"name": "John", "age": 30},
                        {"name": "Jane", "age": 25}
                    ],
                    "cycle": "sequential",
                    "computed": {
                        "full_name": "concat(name, ' User')"
                    }
                }
            },
            "constraints": {
                "global": {
                    "max_depth": 10
                },
                "elements": {
                    "TestElement": {
                        "min_count": 1,
                        "max_count": 5
                    }
                }
            },
            "namespaces": {
                "default": "http://example.com/test",
                "prefixes": {
                    "test": "http://example.com/test"
                }
            }
        }
        
        config = EnhancedJsonConfig(config_data)
        assert config.is_valid()
        assert config.schema == "test.xsd"
        assert config.mode == "complete"
        assert config.seed == 12345
        assert len(config.values) == 2
        assert len(config.patterns) == 2
        assert len(config.choices) == 2
        assert len(config.templates) == 1
        assert "global" in config.constraints
        assert "elements" in config.constraints
        assert config.namespaces["default"] == "http://example.com/test"
    
    def test_invalid_config_missing_required_fields(self):
        """Test validation fails for missing required fields."""
        # Missing schema
        config_data = {"mode": "minimal"}
        config = EnhancedJsonConfig(config_data)
        assert not config.is_valid()
        errors = config.get_validation_errors()
        assert any("schema" in error.lower() for error in errors)
        
        # Missing mode
        config_data = {"schema": "test.xsd"}
        config = EnhancedJsonConfig(config_data)
        assert not config.is_valid()
        errors = config.get_validation_errors()
        assert any("mode" in error.lower() for error in errors)
    
    def test_invalid_mode_values(self):
        """Test validation fails for invalid mode values."""
        invalid_modes = ["invalid", "MINIMAL", "Complete", "custom_mode", ""]
        
        for invalid_mode in invalid_modes:
            config_data = {
                "schema": "test.xsd",
                "mode": invalid_mode
            }
            config = EnhancedJsonConfig(config_data)
            assert not config.is_valid(), f"Mode '{invalid_mode}' should be invalid"
            errors = config.get_validation_errors()
            assert any("mode" in error.lower() for error in errors)
    
    def test_pattern_validation(self):
        """Test pattern field validation."""
        # Valid patterns
        valid_config = {
            "schema": "test.xsd",
            "mode": "complete",
            "patterns": {
                "*ID": "generate:uuid",
                "*Name": "generate:name",
                "*Amount": {
                    "generator": "generate:currency",
                    "constraints": {"min": 0}
                }
            }
        }
        config = EnhancedJsonConfig(valid_config)
        assert config.is_valid()
        
        # Invalid pattern - doesn't start with *
        invalid_config = {
            "schema": "test.xsd", 
            "mode": "complete",
            "patterns": {
                "ID": "generate:uuid"  # Missing *
            }
        }
        config = EnhancedJsonConfig(invalid_config)
        assert not config.is_valid()
        errors = config.get_validation_errors()
        assert any("pattern" in error.lower() for error in errors)
    
    def test_choice_validation(self):
        """Test choice field validation."""
        # Valid simple choice
        valid_config = {
            "schema": "test.xsd",
            "mode": "complete",
            "choices": {
                "Element": "OptionA"
            }
        }
        config = EnhancedJsonConfig(valid_config)
        assert config.is_valid()
        
        # Valid conditional choice
        valid_config["choices"] = {
            "Element": {
                "conditions": [
                    {"if": "field == 'value'", "choose": "OptionA"}
                ],
                "default": "OptionB"
            }
        }
        config = EnhancedJsonConfig(valid_config)
        assert config.is_valid()
        
        # Invalid conditional choice - missing 'if'
        invalid_config = {
            "schema": "test.xsd",
            "mode": "complete", 
            "choices": {
                "Element": {
                    "conditions": [
                        {"choose": "OptionA"}  # Missing 'if'
                    ]
                }
            }
        }
        config = EnhancedJsonConfig(invalid_config)
        assert not config.is_valid()
        errors = config.get_validation_errors()
        assert any("condition" in error.lower() for error in errors)
    
    def test_template_validation(self):
        """Test template field validation."""
        # Valid template
        valid_config = {
            "schema": "test.xsd",
            "mode": "complete",
            "templates": {
                "test_template": {
                    "data": [{"field": "value"}],
                    "cycle": "sequential"
                }
            }
        }
        config = EnhancedJsonConfig(valid_config)
        assert config.is_valid()
        
        # Invalid template - missing data
        invalid_config = {
            "schema": "test.xsd",
            "mode": "complete",
            "templates": {
                "test_template": {
                    "cycle": "sequential"  # Missing data
                }
            }
        }
        config = EnhancedJsonConfig(invalid_config)
        assert not config.is_valid()
        errors = config.get_validation_errors()
        assert any("template" in error.lower() and "data" in error.lower() for error in errors)
        
        # Invalid template - invalid cycle
        invalid_config = {
            "schema": "test.xsd",
            "mode": "complete",
            "templates": {
                "test_template": {
                    "data": [{"field": "value"}],
                    "cycle": "invalid_cycle"
                }
            }
        }
        config = EnhancedJsonConfig(invalid_config)
        assert not config.is_valid()
        errors = config.get_validation_errors()
        assert any("cycle" in error.lower() for error in errors)
    
    def test_field_access_methods(self):
        """Test field access methods and default values."""
        config_data = {
            "schema": "test.xsd",
            "mode": "complete",
            "seed": 12345,
            "values": {"key": "value"}
        }
        
        config = EnhancedJsonConfig(config_data)
        
        # Test field access
        assert config.get_schema() == "test.xsd"
        assert config.get_mode() == "complete"
        assert config.get_seed() == 12345
        assert config.get_values() == {"key": "value"}
        
        # Test defaults for missing fields
        assert config.get_patterns() == {}
        assert config.get_choices() == {}
        assert config.get_templates() == {}
        assert config.get_constraints() == {}
        assert config.get_namespaces() == {}
    
    def test_constraint_validation(self):
        """Test constraint field validation."""
        # Valid constraints
        valid_config = {
            "schema": "test.xsd",
            "mode": "complete",
            "constraints": {
                "global": {
                    "max_depth": 10,
                    "ensure_unique": True
                },
                "elements": {
                    "Element": {
                        "min_count": 1,
                        "max_count": 5
                    }
                },
                "validation_rules": {
                    "amount_range": {"min": 0, "max": 1000}
                }
            }
        }
        config = EnhancedJsonConfig(valid_config)
        assert config.is_valid()
        
        # Test constraint access
        global_constraints = config.get_global_constraints()
        assert global_constraints["max_depth"] == 10
        
        element_constraints = config.get_element_constraints()
        assert "Element" in element_constraints
        assert element_constraints["Element"]["min_count"] == 1
    
    def test_namespace_validation(self):
        """Test namespace field validation."""
        # Valid namespaces
        valid_config = {
            "schema": "test.xsd",
            "mode": "complete",
            "namespaces": {
                "default": "http://example.com/default",
                "prefixes": {
                    "prefix1": "http://example.com/prefix1",
                    "prefix2": "http://example.com/prefix2"
                }
            }
        }
        config = EnhancedJsonConfig(valid_config)
        assert config.is_valid()
        
        # Test namespace access
        default_ns = config.get_default_namespace()
        assert default_ns == "http://example.com/default"
        
        prefixes = config.get_namespace_prefixes()
        assert "prefix1" in prefixes
        assert prefixes["prefix1"] == "http://example.com/prefix1"
    
    def test_json_serialization_roundtrip(self):
        """Test that config can be serialized and deserialized correctly."""
        original_config_data = {
            "schema": "test.xsd",
            "mode": "complete",
            "seed": 12345,
            "values": {"key": "value"},
            "patterns": {"*ID": "generate:uuid"},
            "choices": {"Element": "OptionA"},
            "templates": {
                "test": {
                    "data": [{"field": "value"}],
                    "cycle": "sequential"
                }
            }
        }
        
        # Create config from data
        config = EnhancedJsonConfig(original_config_data)
        assert config.is_valid()
        
        # Serialize to JSON and back
        json_str = json.dumps(original_config_data)
        loaded_data = json.loads(json_str)
        
        # Create new config from loaded data
        new_config = EnhancedJsonConfig(loaded_data)
        assert new_config.is_valid()
        
        # Verify data integrity
        assert config.schema == new_config.schema
        assert config.mode == new_config.mode
        assert config.seed == new_config.seed
        assert config.values == new_config.values
        assert config.patterns == new_config.patterns
        assert config.choices == new_config.choices


class TestEnhancedJsonConfigEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_empty_config(self):
        """Test handling of empty configuration."""
        config = EnhancedJsonConfig({})
        assert not config.is_valid()
        errors = config.get_validation_errors()
        assert len(errors) >= 2  # Missing schema and mode
    
    def test_none_config(self):
        """Test handling of None configuration."""
        config = EnhancedJsonConfig(None)
        assert not config.is_valid() 
        errors = config.get_validation_errors()
        assert any("configuration data" in error.lower() for error in errors)
    
    def test_non_dict_config(self):
        """Test handling of non-dictionary configuration."""
        invalid_configs = ["string", 123, [], True]
        
        for invalid_config in invalid_configs:
            config = EnhancedJsonConfig(invalid_config)
            assert not config.is_valid()
            errors = config.get_validation_errors()
            assert any("dictionary" in error.lower() for error in errors)
    
    def test_deeply_nested_templates(self):
        """Test handling of deeply nested template structures."""
        config_data = {
            "schema": "test.xsd",
            "mode": "complete",
            "templates": {
                "nested_template": {
                    "data": [
                        {
                            "level1": {
                                "level2": {
                                    "level3": {
                                        "deep_field": "deep_value"
                                    }
                                }
                            }
                        }
                    ],
                    "cycle": "sequential",
                    "computed": {
                        "deep_access": "level1.level2.level3.deep_field"
                    }
                }
            }
        }
        
        config = EnhancedJsonConfig(config_data)
        assert config.is_valid()
        
        # Test template access
        templates = config.get_templates()
        assert "nested_template" in templates
        template_data = templates["nested_template"]["data"][0]
        assert template_data["level1"]["level2"]["level3"]["deep_field"] == "deep_value"
    
    def test_large_template_data(self):
        """Test handling of large template datasets."""
        large_data = [{"id": i, "value": f"value_{i}"} for i in range(1000)]
        
        config_data = {
            "schema": "test.xsd",
            "mode": "complete",
            "templates": {
                "large_template": {
                    "data": large_data,
                    "cycle": "random"
                }
            }
        }
        
        config = EnhancedJsonConfig(config_data)
        assert config.is_valid()
        
        templates = config.get_templates()
        assert len(templates["large_template"]["data"]) == 1000
    
    def test_unicode_and_special_characters(self):
        """Test handling of unicode and special characters."""
        config_data = {
            "schema": "test.xsd",
            "mode": "complete",
            "values": {
                "unicode_field": "测试数据 🎯",
                "special_chars": "Value with \"quotes\" and 'apostrophes'",
                "symbols": "Value with symbols: @#$%^&*()"
            },
            "templates": {
                "unicode_template": {
                    "data": [
                        {"name": "José García", "city": "São Paulo"},
                        {"name": "王小明", "city": "北京"},
                        {"name": "Müller", "city": "München"}
                    ],
                    "cycle": "sequential"
                }
            }
        }
        
        config = EnhancedJsonConfig(config_data)
        assert config.is_valid()
        
        # Verify unicode data is preserved
        values = config.get_values()
        assert values["unicode_field"] == "测试数据 🎯"
        
        templates = config.get_templates()
        template_data = templates["unicode_template"]["data"]
        assert template_data[0]["name"] == "José García"
        assert template_data[1]["name"] == "王小明"
        assert template_data[2]["name"] == "Müller"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])