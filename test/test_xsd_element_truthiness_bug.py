#!/usr/bin/env python3
"""
Focused unit test to catch the XsdElement truthiness bug.

This test specifically targets the bug where `if not element` was used instead of `if element is None`
in the _is_complex_type_with_simple_content method, causing valid XsdElement objects to be skipped
when their __bool__() method returns False.
"""

import pytest
import os
from utils.xml_generator import XMLGenerator
import xmlschema


class MockXsdElement:
    """Mock XsdElement that always returns False for __bool__ but is not None."""
    
    def __init__(self, local_name, element_type=None):
        self.local_name = local_name
        self.type = element_type
        self.max_occurs = 1
        self.min_occurs = 1
        
    def __bool__(self):
        """Simulate XsdElement.__bool__ returning False - this was the bug."""
        return False
    
    def __nonzero__(self):
        """For Python 2 compatibility."""
        return False


class TestXsdElementTruthinessBug:
    """Test cases specifically targeting the XsdElement truthiness bug."""
    
    def test_simple_choice_element_selection(self):
        """Test choice element selection with simple XSD."""
        test_xsd_path = os.path.join(os.path.dirname(__file__), "test_choice_elements.xsd")
        
        generator = XMLGenerator(test_xsd_path)
        
        # Get the root element and its choice elements
        root_elements = list(generator.schema.elements.keys())
        root_element = generator.schema.elements[root_elements[0]]  # TestRoot
        
        choice_elements = generator._get_choice_elements(root_element)
        
        # Should find exactly 2 choice elements: Success and Error
        assert len(choice_elements) == 2
        choice_names = [elem.local_name for elem in choice_elements]
        assert 'Success' in choice_names
        assert 'Error' in choice_names
        
        # Test choice selection with user preference
        generator.user_choices = {
            'choice_0': {
                'path': 'TestRoot',
                'selected_element': 'Success'
            }
        }
        
        selected = generator._choose_element_from_choices(choice_elements, 'TestRoot')
        assert selected is not None
        assert selected.local_name == 'Success'
    
    def test_is_complex_type_with_simple_content_with_falsy_element(self):
        """Test the _is_complex_type_with_simple_content method with an element that returns False for __bool__."""
        test_xsd_path = os.path.join(os.path.dirname(__file__), "test_choice_elements.xsd")
        generator = XMLGenerator(test_xsd_path)
        
        # Create a mock element that returns False for __bool__ but is not None
        # This mock has a type to test the bug more thoroughly
        class MockType:
            def __init__(self):
                self.is_complex_called = False
                
            def is_complex(self):
                self.is_complex_called = True
                return True
            
        mock_type = MockType()
        mock_element = MockXsdElement("TestElement", mock_type)
        
        # Test the method that had the bug
        # With the bug: `if not element` would be True for mock_element, causing early return False
        # With the fix: `if element is None` would be False for mock_element, allowing proper processing
        result = generator._is_complex_type_with_simple_content(mock_element)
        
        # With the bug (if not element): This would return False immediately due to mock.__bool__() = False
        # With the fix (if element is None): This would proceed to check element.type.is_complex() and return False properly
        
        # The key test: if the bug exists, is_complex() should NOT be called
        # With the bug: `if not element` returns early, is_complex_called remains False
        # Without the bug: `if element is None` allows processing, is_complex_called becomes True
        
        if not mock_type.is_complex_called:
            # Bug detected: method returned early due to truthiness check
            pytest.fail("BUG DETECTED: _is_complex_type_with_simple_content returned early due to 'if not element' instead of 'if element is None'")
        
        assert result == False  # Expected result after proper processing
    
    def test_choice_selection_with_falsy_elements(self):
        """Test that choice selection works correctly even when XsdElement.__bool__ returns False."""
        test_xsd_path = os.path.join(os.path.dirname(__file__), "test_choice_elements.xsd")
        generator = XMLGenerator(test_xsd_path)
        
        # Get real choice elements
        root_elements = list(generator.schema.elements.keys())
        root_element = generator.schema.elements[root_elements[0]]
        real_choice_elements = generator._get_choice_elements(root_element)
        
        # Patch the __bool__ method of choice elements to return False
        original_bool_methods = []
        for elem in real_choice_elements:
            original_bool_methods.append(getattr(elem, '__bool__', None))
            elem.__bool__ = lambda: False
        
        try:
            # Test that choice selection still works
            generator.user_choices = {
                'choice_0': {
                    'path': 'TestRoot',
                    'selected_element': 'Success'
                }
            }
            
            selected = generator._choose_element_from_choices(real_choice_elements, 'TestRoot')
            
            # Should still select the element despite __bool__ returning False
            assert selected is not None
            assert selected.local_name == 'Success'
            
            # Test XML generation still works
            xml_content = generator.generate_dummy_xml_with_choices(generator.user_choices)
            assert 'Success>' in xml_content  # Allow for namespace prefixes like <tns:Success>
            assert xml_content is not None
            
        finally:
            # Restore original __bool__ methods
            for i, elem in enumerate(real_choice_elements):
                if original_bool_methods[i] is not None:
                    elem.__bool__ = original_bool_methods[i]
                elif hasattr(elem, '__bool__'):
                    delattr(elem, '__bool__')
    
    def test_xml_generation_with_complex_choices(self):
        """Test XML generation with the more complex nested choice structure."""
        test_xsd_path = os.path.join(os.path.dirname(__file__), "test_choice_elements.xsd")
        generator = XMLGenerator(test_xsd_path)
        
        # Test with ComplexRoot element that has nested choices
        generator.user_choices = {
            'choice_0': {
                'path': 'ComplexRoot',
                'selected_element': 'DataSection'
            },
            'choice_1': {
                'path': 'ComplexRoot.DataSection',
                'selected_element': 'TypeA'
            }
        }
        
        xml_content = generator.generate_dummy_xml()
        
        # Should contain the selected elements
        assert xml_content is not None
        assert '<?xml version="1.0"' in xml_content
        
        # Verify it's valid XML and contains expected elements
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(xml_content)
            assert root is not None
        except ET.ParseError:
            pytest.fail("Generated XML is not well-formed")
    
    def test_truthiness_bug_specific_scenario(self):
        """Test the exact scenario where the truthiness bug would manifest."""
        test_xsd_path = os.path.join(os.path.dirname(__file__), "test_choice_elements.xsd")
        generator = XMLGenerator(test_xsd_path)
        
        # Load schema and get elements
        root_elements = list(generator.schema.elements.keys())
        
        for root_name in root_elements:
            root_element = generator.schema.elements[root_name]
            
            # Test _is_complex_type_with_simple_content with real elements
            result = generator._is_complex_type_with_simple_content(root_element)
            
            # The method should not fail or behave unexpectedly due to element truthiness
            assert isinstance(result, bool)
            
            # Test with None (should return False)
            result_none = generator._is_complex_type_with_simple_content(None)
            assert result_none == False