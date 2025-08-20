"""
Choice Resolver System

This module handles complex choice resolution for XSD choice elements in the
enhanced JSON configuration system. It supports simple selections, conditional
choices, nested choice hierarchies, and validation.

Supported Choice Features:
- Simple choice selections: "ChoiceElement": "SelectedOption"
- Path-specific choices: "/Root/Choice": "Option"
- Conditional choices: Based on other element values
- Nested choice handling: Multiple choice levels
- Choice validation: Ensure valid selections
- Unselected element removal: Clean up XML structure

Architecture:
- ChoiceResolver: Main choice resolution engine
- ConditionalChoiceEvaluator: Handles conditional choice logic
- ChoiceValidator: Validates choice selections against XSD
- ChoiceApplicator: Applies choices to XML structure
"""

import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Any, Union, Tuple, Set
from dataclasses import dataclass
from enum import Enum
import re
import logging

from .enhanced_json_config import EnhancedJsonConfig
from .xpath_resolver import XPathResolver, PathExpression


class ChoiceType(Enum):
    """Types of choice configurations."""
    SIMPLE = "simple"           # "ChoiceElement": "SelectedOption"
    PATH_SPECIFIC = "path_specific"  # "/Root/Choice": "Option"
    CONDITIONAL = "conditional"  # Based on conditions
    NESTED = "nested"           # Multiple choice levels


@dataclass
class ChoiceSelection:
    """Represents a choice selection with context."""
    choice_path: str
    choice_element: str
    selected_option: str
    choice_type: ChoiceType
    condition: Optional[Dict] = None
    context: Optional[Dict] = None


@dataclass
class ChoiceCondition:
    """Represents a conditional choice rule."""
    field_path: str
    operator: str
    value: Any
    choice_selection: str


class ChoiceResolverError(Exception):
    """Raised when choice resolution operations fail."""
    pass


class ChoiceResolver:
    """
    Advanced choice resolution system for XSD choice elements.
    
    Handles complex choice scenarios including conditional selections,
    nested choices, and path-specific choice resolution. Integrates
    with the base XMLGenerator and XMLOverrideEngine for complete
    choice handling throughout the XML generation process.
    """
    
    def __init__(self, enhanced_config: EnhancedJsonConfig, xpath_resolver: Optional[XPathResolver] = None):
        """
        Initialize choice resolver.
        
        Args:
            enhanced_config: Enhanced JSON configuration instance
            xpath_resolver: XPath resolver for path operations
        """
        self.config = enhanced_config
        self.xpath_resolver = xpath_resolver or XPathResolver()
        self.logger = logging.getLogger(__name__)
        
        # Choice resolution state
        self.resolved_choices: Dict[str, ChoiceSelection] = {}
        self.conditional_choices: List[ChoiceCondition] = []
        self.nested_choices: Dict[str, List[str]] = {}
        
        # XML context for conditional evaluation
        self.xml_context: Optional[ET.ElementTree] = None
        self.element_values: Dict[str, str] = {}
        
        # Parse choice configuration
        self._parse_choice_configuration()
    
    def _parse_choice_configuration(self) -> None:
        """Parse choice configuration from enhanced config."""
        for choice_path, choice_config in self.config.choices.items():
            try:
                if isinstance(choice_config, str):
                    # Simple choice: "ChoiceElement": "SelectedOption"
                    self._add_simple_choice(choice_path, choice_config)
                    
                elif isinstance(choice_config, dict):
                    # Complex choice with conditions
                    self._add_conditional_choice(choice_path, choice_config)
                    
                else:
                    self.logger.warning(f"Invalid choice configuration for {choice_path}: {choice_config}")
                    
            except Exception as e:
                self.logger.error(f"Failed to parse choice {choice_path}: {e}")
    
    def _add_simple_choice(self, choice_path: str, selected_option: str) -> None:
        """Add a simple choice selection."""
        # Determine choice type based on path format
        if choice_path.startswith('/'):
            choice_type = ChoiceType.PATH_SPECIFIC
        else:
            choice_type = ChoiceType.SIMPLE
        
        choice_selection = ChoiceSelection(
            choice_path=choice_path,
            choice_element=self._extract_choice_element(choice_path),
            selected_option=selected_option,
            choice_type=choice_type
        )
        
        self.resolved_choices[choice_path] = choice_selection
    
    def _add_conditional_choice(self, choice_path: str, choice_config: Dict) -> None:
        """Add a conditional choice with evaluation rules."""
        conditions = choice_config.get('conditions', [])
        default_choice = choice_config.get('default')
        
        # Parse conditions
        for condition in conditions:
            if_clause = condition.get('if')
            choose_clause = condition.get('choose')
            
            if if_clause and choose_clause:
                choice_condition = self._parse_condition(if_clause, choose_clause, choice_path)
                if choice_condition:
                    self.conditional_choices.append(choice_condition)
        
        # Add default choice if specified
        if default_choice:
            choice_selection = ChoiceSelection(
                choice_path=choice_path,
                choice_element=self._extract_choice_element(choice_path),
                selected_option=default_choice,
                choice_type=ChoiceType.CONDITIONAL,
                condition={'type': 'default'}
            )
            self.resolved_choices[f"{choice_path}_default"] = choice_selection
    
    def _parse_condition(self, if_clause: str, choose_clause: str, choice_path: str) -> Optional[ChoiceCondition]:
        """Parse a conditional choice rule."""
        try:
            # Parse condition: "TotalAmount > 1000", "CustomerType == 'Business'"
            condition_patterns = [
                r'(\S+)\s*(>|<|>=|<=|==|!=)\s*(.+)',  # Comparison operators
                r'(\S+)\s+in\s+\[(.+)\]',             # In operator
                r'(\S+)\s+matches\s+(.+)'             # Pattern matching
            ]
            
            for pattern in condition_patterns:
                match = re.match(pattern, if_clause.strip())
                if match:
                    if '>' in if_clause or '<' in if_clause or '==' in if_clause or '!=' in if_clause:
                        field_path = match.group(1)
                        operator = match.group(2)
                        value = match.group(3).strip('\'"')
                    elif ' in ' in if_clause:
                        field_path = match.group(1)
                        operator = 'in'
                        value = [v.strip('\'" ') for v in match.group(2).split(',')]
                    elif ' matches ' in if_clause:
                        field_path = match.group(1)
                        operator = 'matches'
                        value = match.group(2).strip('\'"')
                    else:
                        continue
                    
                    return ChoiceCondition(
                        field_path=field_path,
                        operator=operator,
                        value=value,
                        choice_selection=choose_clause
                    )
            
            self.logger.warning(f"Could not parse condition: {if_clause}")
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to parse condition '{if_clause}': {e}")
            return None
    
    def _extract_choice_element(self, choice_path: str) -> str:
        """Extract choice element name from path."""
        if choice_path.startswith('/'):
            # Extract last component from absolute path
            components = choice_path.strip('/').split('/')
            return components[-1] if components else choice_path
        else:
            # Simple element name
            return choice_path
    
    def resolve_choices_for_xml(self, xml_tree: ET.ElementTree) -> Dict[str, str]:
        """
        Resolve all choices for the given XML tree.
        
        Args:
            xml_tree: XML tree to resolve choices for
            
        Returns:
            Dictionary of resolved choices for base XMLGenerator
        """
        self.xml_context = xml_tree
        self._extract_element_values()
        
        resolved = {}
        
        # Process simple choices first
        for choice_path, choice_selection in self.resolved_choices.items():
            if choice_selection.choice_type in [ChoiceType.SIMPLE, ChoiceType.PATH_SPECIFIC]:
                resolved[choice_selection.choice_element] = choice_selection.selected_option
        
        # Process conditional choices
        for condition in self.conditional_choices:
            if self._evaluate_condition(condition):
                choice_element = self._extract_choice_element(condition.field_path)
                resolved[choice_element] = condition.choice_selection
        
        return resolved
    
    def apply_choices_to_xml(self, xml_tree: ET.ElementTree) -> ET.ElementTree:
        """
        Apply choice selections to XML tree by removing unselected elements.
        
        Args:
            xml_tree: XML tree to modify
            
        Returns:
            Modified XML tree with choices applied
        """
        self.xml_context = xml_tree
        
        # Find and remove unselected choice elements
        for choice_path, choice_selection in self.resolved_choices.items():
            try:
                self._apply_single_choice(xml_tree, choice_selection)
            except Exception as e:
                self.logger.error(f"Failed to apply choice {choice_path}: {e}")
        
        # Apply conditional choices
        for condition in self.conditional_choices:
            try:
                if self._evaluate_condition(condition):
                    self._apply_conditional_choice(xml_tree, condition)
            except Exception as e:
                self.logger.error(f"Failed to apply conditional choice: {e}")
        
        return xml_tree
    
    def _apply_single_choice(self, xml_tree: ET.ElementTree, choice_selection: ChoiceSelection) -> None:
        """Apply a single choice selection to XML tree."""
        # Find choice elements in the tree
        if choice_selection.choice_type == ChoiceType.PATH_SPECIFIC:
            choice_elements = self.xpath_resolver.resolve_path(xml_tree, choice_selection.choice_path)
        else:
            choice_elements = self.xpath_resolver.resolve_path(xml_tree, choice_selection.choice_element)
        
        for choice_element in choice_elements:
            # Find parent element containing the choice
            parent = self._find_choice_parent(choice_element)
            if parent is not None:
                # Remove unselected options
                self._remove_unselected_options(parent, choice_selection.selected_option)
    
    def _apply_conditional_choice(self, xml_tree: ET.ElementTree, condition: ChoiceCondition) -> None:
        """Apply a conditional choice selection."""
        # This is a simplified implementation
        # Full conditional choice application would require more sophisticated logic
        choice_elements = self.xpath_resolver.resolve_path(xml_tree, condition.field_path)
        
        for choice_element in choice_elements:
            parent = self._find_choice_parent(choice_element)
            if parent is not None:
                self._remove_unselected_options(parent, condition.choice_selection)
    
    def _find_choice_parent(self, element: ET.Element) -> Optional[ET.Element]:
        """Find the parent element that contains choice options."""
        # This would need to traverse up the tree to find the choice container
        # For now, return the element itself as a placeholder
        return element
    
    def _remove_unselected_options(self, parent: ET.Element, selected_option: str) -> None:
        """Remove unselected choice options from parent element."""
        children_to_remove = []
        
        for child in parent:
            child_name = self._get_local_name(child.tag)
            if child_name != selected_option:
                # Check if this child is part of a choice group
                # This is simplified - full implementation would need XSD analysis
                children_to_remove.append(child)
        
        # Remove unselected children
        for child in children_to_remove:
            try:
                parent.remove(child)
            except Exception as e:
                self.logger.warning(f"Could not remove choice element {child.tag}: {e}")
    
    def _extract_element_values(self) -> None:
        """Extract element values from XML for conditional evaluation."""
        if not self.xml_context:
            return
        
        self.element_values = {}
        
        def extract_recursive(element, path_components):
            element_name = self._get_local_name(element.tag)
            current_path = '/'.join(path_components + [element_name])
            
            # Store element text value
            if element.text and element.text.strip():
                self.element_values[current_path] = element.text.strip()
                self.element_values[element_name] = element.text.strip()  # Simple name too
            
            # Store attribute values
            for attr_name, attr_value in element.attrib.items():
                attr_path = f"{current_path}@{attr_name}"
                self.element_values[attr_path] = attr_value
                self.element_values[f"{element_name}@{attr_name}"] = attr_value
            
            # Recurse to children
            for child in element:
                extract_recursive(child, path_components + [element_name])
        
        root = self.xml_context.getroot()
        root_name = self._get_local_name(root.tag)
        extract_recursive(root, [])
    
    def _evaluate_condition(self, condition: ChoiceCondition) -> bool:
        """Evaluate a conditional choice condition."""
        try:
            # Get value for the field
            field_value = self.element_values.get(condition.field_path)
            if field_value is None:
                # Try simple field name
                simple_name = condition.field_path.split('/')[-1]
                field_value = self.element_values.get(simple_name)
            
            if field_value is None:
                return False
            
            # Evaluate condition based on operator
            if condition.operator == '==':
                return str(field_value) == str(condition.value)
            elif condition.operator == '!=':
                return str(field_value) != str(condition.value)
            elif condition.operator == '>':
                return float(field_value) > float(condition.value)
            elif condition.operator == '<':
                return float(field_value) < float(condition.value)
            elif condition.operator == '>=':
                return float(field_value) >= float(condition.value)
            elif condition.operator == '<=':
                return float(field_value) <= float(condition.value)
            elif condition.operator == 'in':
                return str(field_value) in condition.value
            elif condition.operator == 'matches':
                return bool(re.search(condition.value, str(field_value)))
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to evaluate condition {condition.field_path} {condition.operator} {condition.value}: {e}")
            return False
    
    def _get_local_name(self, tag: str) -> str:
        """Extract local name from potentially namespaced tag."""
        if '}' in tag:
            return tag.split('}')[1]
        return tag
    
    def validate_choices(self, available_choices: Dict[str, List[str]]) -> List[str]:
        """
        Validate choice selections against available options.
        
        Args:
            available_choices: Dict of choice element -> available options
            
        Returns:
            List of validation error messages
        """
        errors = []
        
        for choice_path, choice_selection in self.resolved_choices.items():
            choice_element = choice_selection.choice_element
            selected_option = choice_selection.selected_option
            
            if choice_element in available_choices:
                available_options = available_choices[choice_element]
                if selected_option not in available_options:
                    errors.append(
                        f"Invalid choice for {choice_element}: '{selected_option}' "
                        f"not in available options: {available_options}"
                    )
        
        return errors
    
    def get_choice_summary(self) -> Dict[str, Any]:
        """Get summary of resolved choices for debugging."""
        return {
            'simple_choices': len([c for c in self.resolved_choices.values() 
                                 if c.choice_type in [ChoiceType.SIMPLE, ChoiceType.PATH_SPECIFIC]]),
            'conditional_choices': len(self.conditional_choices),
            'total_resolved': len(self.resolved_choices),
            'resolved_choices': {
                path: {
                    'element': choice.choice_element,
                    'selected': choice.selected_option,
                    'type': choice.choice_type.value
                }
                for path, choice in self.resolved_choices.items()
            }
        }
    
    def get_base_generator_choices(self) -> Dict[str, str]:
        """
        Get choices in format expected by base XMLGenerator.
        
        Returns:
            Dictionary of choice selections for base generator
        """
        base_choices = {}
        
        for choice_selection in self.resolved_choices.values():
            if choice_selection.choice_type in [ChoiceType.SIMPLE, ChoiceType.PATH_SPECIFIC]:
                base_choices[choice_selection.choice_element] = choice_selection.selected_option
        
        return base_choices
    
    def __repr__(self) -> str:
        """String representation of choice resolver."""
        return f"ChoiceResolver(choices={len(self.resolved_choices)}, conditions={len(self.conditional_choices)})"