#!/usr/bin/env python3
"""
Unit Tests for Choice Resolution.

Comprehensive tests for choice resolution logic including simple choices,
conditional choices, context evaluation, and error handling.
"""

import pytest
from utils.choice_resolver import ChoiceResolver


class TestSimpleChoiceResolution:
    """Test simple choice resolution functionality."""
    
    @pytest.fixture
    def choice_resolver(self):
        """Provide ChoiceResolver instance."""
        return ChoiceResolver()
    
    def test_simple_string_choice(self, choice_resolver):
        """Test simple string choice resolution."""
        choices = {
            "TravelBooking": "PickupLocation"
        }
        context = {}
        
        result = choice_resolver.resolve_choice("TravelBooking", choices, context)
        assert result == "PickupLocation"
    
    def test_multiple_simple_choices(self, choice_resolver):
        """Test multiple simple choices."""
        choices = {
            "TravelBooking": "PickupLocation",
            "PaymentMethod": "CreditCard",
            "DeliveryOption": "Express"
        }
        context = {}
        
        # Test each choice
        result1 = choice_resolver.resolve_choice("TravelBooking", choices, context)
        assert result1 == "PickupLocation"
        
        result2 = choice_resolver.resolve_choice("PaymentMethod", choices, context)
        assert result2 == "CreditCard"
        
        result3 = choice_resolver.resolve_choice("DeliveryOption", choices, context)
        assert result3 == "Express"
    
    def test_nonexistent_choice_element(self, choice_resolver):
        """Test handling of nonexistent choice elements."""
        choices = {
            "TravelBooking": "PickupLocation"
        }
        context = {}
        
        # Should return None for nonexistent choice element
        result = choice_resolver.resolve_choice("NonexistentElement", choices, context)
        assert result is None
    
    def test_empty_choices_config(self, choice_resolver):
        """Test handling of empty choices configuration."""
        choices = {}
        context = {}
        
        result = choice_resolver.resolve_choice("TravelBooking", choices, context)
        assert result is None


class TestConditionalChoiceResolution:
    """Test conditional choice resolution functionality."""
    
    @pytest.fixture
    def choice_resolver(self):
        return ChoiceResolver()
    
    def test_simple_conditional_choice(self, choice_resolver):
        """Test simple conditional choice resolution."""
        choices = {
            "TravelBooking": {
                "conditions": [
                    {
                        "if": "Amount > 1000",
                        "choose": "PickupLocation"
                    }
                ],
                "default": "DeliveryAddress"
            }
        }
        
        # Test condition that evaluates to true
        context = {"Amount": 1500}
        result = choice_resolver.resolve_choice("TravelBooking", choices, context)
        assert result == "PickupLocation"
        
        # Test condition that evaluates to false
        context = {"Amount": 500}
        result = choice_resolver.resolve_choice("TravelBooking", choices, context)
        assert result == "DeliveryAddress"
    
    def test_multiple_conditional_choices(self, choice_resolver):
        """Test multiple conditional choices."""
        choices = {
            "TravelBooking": {
                "conditions": [
                    {
                        "if": "Amount > 5000",
                        "choose": "PremiumPickup"
                    },
                    {
                        "if": "Amount > 1000",
                        "choose": "PickupLocation"
                    },
                    {
                        "if": "Amount > 100",
                        "choose": "StandardDelivery"
                    }
                ],
                "default": "BasicDelivery"
            }
        }
        
        # Test premium condition
        context = {"Amount": 6000}
        result = choice_resolver.resolve_choice("TravelBooking", choices, context)
        assert result == "PremiumPickup"
        
        # Test pickup condition
        context = {"Amount": 2000}
        result = choice_resolver.resolve_choice("TravelBooking", choices, context)
        assert result == "PickupLocation"
        
        # Test standard condition
        context = {"Amount": 500}
        result = choice_resolver.resolve_choice("TravelBooking", choices, context)
        assert result == "StandardDelivery"
        
        # Test default fallback
        context = {"Amount": 50}
        result = choice_resolver.resolve_choice("TravelBooking", choices, context)
        assert result == "BasicDelivery"
    
    def test_complex_conditional_expressions(self, choice_resolver):
        """Test complex conditional expressions."""
        choices = {
            "TravelBooking": {
                "conditions": [
                    {
                        "if": "Amount > 1000 && PaymentMethod == 'CreditCard'",
                        "choose": "PremiumPickup"
                    },
                    {
                        "if": "Amount > 500 || Currency == 'EUR'",
                        "choose": "PickupLocation"
                    },
                    {
                        "if": "CustomerType == 'Business' && Amount > 100",
                        "choose": "BusinessDelivery"
                    }
                ],
                "default": "StandardDelivery"
            }
        }
        
        # Test AND condition (both true)
        context = {"Amount": 1500, "PaymentMethod": "CreditCard"}
        result = choice_resolver.resolve_choice("TravelBooking", choices, context)
        assert result == "PremiumPickup"
        
        # Test AND condition (one false)
        context = {"Amount": 1500, "PaymentMethod": "DebitCard"}
        result = choice_resolver.resolve_choice("TravelBooking", choices, context)
        assert result == "PickupLocation"  # Falls through to next condition
        
        # Test OR condition (first true)
        context = {"Amount": 800, "Currency": "USD"}
        result = choice_resolver.resolve_choice("TravelBooking", choices, context)
        assert result == "PickupLocation"
        
        # Test OR condition (second true)
        context = {"Amount": 200, "Currency": "EUR"}
        result = choice_resolver.resolve_choice("TravelBooking", choices, context)
        assert result == "PickupLocation"
        
        # Test business condition
        context = {"CustomerType": "Business", "Amount": 300}
        result = choice_resolver.resolve_choice("TravelBooking", choices, context)
        assert result == "BusinessDelivery"
    
    def test_string_comparison_conditions(self, choice_resolver):
        """Test string comparison in conditions."""
        choices = {
            "ServiceLevel": {
                "conditions": [
                    {
                        "if": "CustomerType == 'VIP'",
                        "choose": "VIPService"
                    },
                    {
                        "if": "CustomerType == 'Business'",
                        "choose": "BusinessService"
                    },
                    {
                        "if": "Region == 'Europe'",
                        "choose": "EuropeanService"
                    }
                ],
                "default": "StandardService"
            }
        }
        
        # Test VIP customer
        context = {"CustomerType": "VIP"}
        result = choice_resolver.resolve_choice("ServiceLevel", choices, context)
        assert result == "VIPService"
        
        # Test Business customer
        context = {"CustomerType": "Business"}
        result = choice_resolver.resolve_choice("ServiceLevel", choices, context)
        assert result == "BusinessService"
        
        # Test European region
        context = {"Region": "Europe"}
        result = choice_resolver.resolve_choice("ServiceLevel", choices, context)
        assert result == "EuropeanService"
        
        # Test default fallback
        context = {"CustomerType": "Individual", "Region": "Americas"}
        result = choice_resolver.resolve_choice("ServiceLevel", choices, context)
        assert result == "StandardService"
    
    def test_numeric_comparison_conditions(self, choice_resolver):
        """Test numeric comparison operators in conditions."""
        choices = {
            "ShippingMethod": {
                "conditions": [
                    {
                        "if": "Weight >= 50",
                        "choose": "FreightShipping"
                    },
                    {
                        "if": "Weight <= 1",
                        "choose": "EnvelopeShipping"
                    },
                    {
                        "if": "Distance < 100",
                        "choose": "LocalDelivery"
                    },
                    {
                        "if": "Distance >= 1000",
                        "choose": "LongDistanceShipping"
                    }
                ],
                "default": "StandardShipping"
            }
        }
        
        # Test >= condition
        context = {"Weight": 75}
        result = choice_resolver.resolve_choice("ShippingMethod", choices, context)
        assert result == "FreightShipping"
        
        # Test <= condition
        context = {"Weight": 0.5}
        result = choice_resolver.resolve_choice("ShippingMethod", choices, context)
        assert result == "EnvelopeShipping"
        
        # Test < condition
        context = {"Weight": 5, "Distance": 50}
        result = choice_resolver.resolve_choice("ShippingMethod", choices, context)
        assert result == "LocalDelivery"
        
        # Test >= condition for distance
        context = {"Weight": 5, "Distance": 1500}
        result = choice_resolver.resolve_choice("ShippingMethod", choices, context)
        assert result == "LongDistanceShipping"
        
        # Test default
        context = {"Weight": 10, "Distance": 500}
        result = choice_resolver.resolve_choice("ShippingMethod", choices, context)
        assert result == "StandardShipping"


class TestChoiceContextHandling:
    """Test context handling in choice resolution."""
    
    @pytest.fixture
    def choice_resolver(self):
        return ChoiceResolver()
    
    def test_missing_context_variables(self, choice_resolver):
        """Test handling of missing context variables."""
        choices = {
            "TravelBooking": {
                "conditions": [
                    {
                        "if": "NonexistentVariable > 100",
                        "choose": "PickupLocation"
                    }
                ],
                "default": "DeliveryAddress"
            }
        }
        
        context = {"Amount": 1000}  # Missing NonexistentVariable
        
        # Should fallback to default when variable is missing
        result = choice_resolver.resolve_choice("TravelBooking", choices, context)
        assert result == "DeliveryAddress"
    
    def test_null_context_values(self, choice_resolver):
        """Test handling of null context values."""
        choices = {
            "ServiceType": {
                "conditions": [
                    {
                        "if": "SpecialCode != null",
                        "choose": "SpecialService"
                    }
                ],
                "default": "StandardService"
            }
        }
        
        # Test with null value
        context = {"SpecialCode": None}
        result = choice_resolver.resolve_choice("ServiceType", choices, context)
        assert result == "StandardService"
        
        # Test with non-null value
        context = {"SpecialCode": "VIP123"}
        result = choice_resolver.resolve_choice("ServiceType", choices, context)
        assert result == "SpecialService"
    
    def test_nested_context_variables(self, choice_resolver):
        """Test handling of nested context variables."""
        choices = {
            "DeliveryMethod": {
                "conditions": [
                    {
                        "if": "Customer.Type == 'Premium'",
                        "choose": "PremiumDelivery"
                    },
                    {
                        "if": "Order.Priority == 'Urgent'",
                        "choose": "ExpressDelivery"
                    }
                ],
                "default": "StandardDelivery"
            }
        }
        
        # Test nested customer type
        context = {
            "Customer": {"Type": "Premium", "Region": "US"},
            "Order": {"Priority": "Normal", "Value": 500}
        }
        result = choice_resolver.resolve_choice("DeliveryMethod", choices, context)
        assert result == "PremiumDelivery"
        
        # Test nested order priority
        context = {
            "Customer": {"Type": "Standard", "Region": "EU"},
            "Order": {"Priority": "Urgent", "Value": 200}
        }
        result = choice_resolver.resolve_choice("DeliveryMethod", choices, context)
        assert result == "ExpressDelivery"
        
        # Test default fallback
        context = {
            "Customer": {"Type": "Standard", "Region": "US"},
            "Order": {"Priority": "Normal", "Value": 100}
        }
        result = choice_resolver.resolve_choice("DeliveryMethod", choices, context)
        assert result == "StandardDelivery"
    
    def test_context_type_conversion(self, choice_resolver):
        """Test automatic type conversion in context evaluation."""
        choices = {
            "PricingTier": {
                "conditions": [
                    {
                        "if": "Amount > 1000",
                        "choose": "PremiumTier"
                    }
                ],
                "default": "StandardTier"
            }
        }
        
        # Test with string that can be converted to number
        context = {"Amount": "1500"}
        result = choice_resolver.resolve_choice("PricingTier", choices, context)
        assert result == "PremiumTier"
        
        # Test with actual number
        context = {"Amount": 1500}
        result = choice_resolver.resolve_choice("PricingTier", choices, context)
        assert result == "PremiumTier"
        
        # Test with string that results in false condition
        context = {"Amount": "500"}
        result = choice_resolver.resolve_choice("PricingTier", choices, context)
        assert result == "StandardTier"


class TestChoiceResolutionErrorHandling:
    """Test error handling in choice resolution."""
    
    @pytest.fixture
    def choice_resolver(self):
        return ChoiceResolver()
    
    def test_malformed_conditional_choice(self, choice_resolver):
        """Test handling of malformed conditional choices."""
        malformed_choices = [
            # Missing 'if' field
            {
                "TravelBooking": {
                    "conditions": [
                        {
                            "choose": "PickupLocation"
                        }
                    ],
                    "default": "DeliveryAddress"
                }
            },
            # Missing 'choose' field
            {
                "TravelBooking": {
                    "conditions": [
                        {
                            "if": "Amount > 1000"
                        }
                    ],
                    "default": "DeliveryAddress"
                }
            },
            # Invalid condition syntax
            {
                "TravelBooking": {
                    "conditions": [
                        {
                            "if": "Amount > > 1000",  # Invalid syntax
                            "choose": "PickupLocation"
                        }
                    ],
                    "default": "DeliveryAddress"
                }
            }
        ]
        
        context = {"Amount": 1500}
        
        for choices in malformed_choices:
            # Should fallback to default or return None gracefully
            result = choice_resolver.resolve_choice("TravelBooking", choices, context)
            assert result == "DeliveryAddress" or result is None
    
    def test_missing_default_choice(self, choice_resolver):
        """Test handling when default choice is missing."""
        choices = {
            "TravelBooking": {
                "conditions": [
                    {
                        "if": "Amount > 10000",  # Very high threshold
                        "choose": "PickupLocation"
                    }
                ]
                # No default specified
            }
        }
        
        context = {"Amount": 1000}  # Doesn't meet condition
        
        # Should return None when no condition matches and no default
        result = choice_resolver.resolve_choice("TravelBooking", choices, context)
        assert result is None
    
    def test_invalid_condition_expressions(self, choice_resolver):
        """Test handling of invalid condition expressions."""
        choices = {
            "ServiceLevel": {
                "conditions": [
                    {
                        "if": "undefined_function(Amount)",
                        "choose": "SpecialService"
                    },
                    {
                        "if": "Amount ++ 100",  # Invalid operator
                        "choose": "AnotherService"
                    }
                ],
                "default": "StandardService"
            }
        }
        
        context = {"Amount": 1000}
        
        # Should handle invalid expressions gracefully and fall back to default
        result = choice_resolver.resolve_choice("ServiceLevel", choices, context)
        assert result == "StandardService"
    
    def test_circular_condition_references(self, choice_resolver):
        """Test handling of circular references in conditions."""
        choices = {
            "ServiceA": {
                "conditions": [
                    {
                        "if": "ServiceB == 'TypeX'",
                        "choose": "ServiceTypeA"
                    }
                ],
                "default": "DefaultA"
            },
            "ServiceB": {
                "conditions": [
                    {
                        "if": "ServiceA == 'TypeY'",
                        "choose": "ServiceTypeB"
                    }
                ],
                "default": "DefaultB"
            }
        }
        
        context = {}
        
        # Should handle circular references without infinite loops
        result1 = choice_resolver.resolve_choice("ServiceA", choices, context)
        result2 = choice_resolver.resolve_choice("ServiceB", choices, context)
        
        # Should resolve to defaults
        assert result1 == "DefaultA"
        assert result2 == "DefaultB"


class TestChoiceResolutionPerformance:
    """Test performance aspects of choice resolution."""
    
    @pytest.fixture
    def choice_resolver(self):
        return ChoiceResolver()
    
    def test_large_number_of_conditions(self, choice_resolver):
        """Test performance with large number of conditions."""
        # Create choice with many conditions
        conditions = []
        for i in range(100):
            conditions.append({
                "if": f"Value == {i}",
                "choose": f"Option{i}"
            })
        
        choices = {
            "LargeChoice": {
                "conditions": conditions,
                "default": "DefaultOption"
            }
        }
        
        # Test with matching condition (should be fast)
        context = {"Value": 50}
        result = choice_resolver.resolve_choice("LargeChoice", choices, context)
        assert result == "Option50"
        
        # Test with non-matching condition (should still be reasonable)
        context = {"Value": 999}
        result = choice_resolver.resolve_choice("LargeChoice", choices, context)
        assert result == "DefaultOption"
    
    def test_complex_context_evaluation(self, choice_resolver):
        """Test performance with complex context evaluation."""
        choices = {
            "ComplexChoice": {
                "conditions": [
                    {
                        "if": "((Amount > 1000 && Type == 'Premium') || (Amount > 2000 && Type == 'Standard')) && Region != 'Restricted'",
                        "choose": "ComplexOption"
                    }
                ],
                "default": "SimpleOption"
            }
        }
        
        # Test multiple evaluations
        test_contexts = [
            {"Amount": 1500, "Type": "Premium", "Region": "US"},
            {"Amount": 2500, "Type": "Standard", "Region": "EU"},
            {"Amount": 500, "Type": "Premium", "Region": "US"},
            {"Amount": 1500, "Type": "Premium", "Region": "Restricted"},
        ]
        
        expected_results = ["ComplexOption", "ComplexOption", "SimpleOption", "SimpleOption"]
        
        for context, expected in zip(test_contexts, expected_results):
            result = choice_resolver.resolve_choice("ComplexChoice", choices, context)
            assert result == expected
    
    def test_repeated_choice_resolution(self, choice_resolver):
        """Test performance of repeated choice resolution."""
        choices = {
            "RepeatedChoice": {
                "conditions": [
                    {
                        "if": "Amount > 1000",
                        "choose": "HighValue"
                    }
                ],
                "default": "LowValue"
            }
        }
        
        context = {"Amount": 1500}
        
        # Resolve the same choice many times
        results = []
        for _ in range(1000):
            result = choice_resolver.resolve_choice("RepeatedChoice", choices, context)
            results.append(result)
        
        # All results should be consistent
        assert all(result == "HighValue" for result in results)
        assert len(set(results)) == 1  # All results are the same


if __name__ == "__main__":
    pytest.main([__file__, "-v"])