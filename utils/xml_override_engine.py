"""
XML Override Engine

This module applies JSON configuration overrides to base-generated XML.
It takes complete, valid XML from the base XMLGenerator and enhances it
according to the EnhancedJsonConfig specifications.

Architecture:
- XMLOverrideEngine: Main override application engine
- Applies overrides in precedence order: values, patterns, templates, attributes
- Preserves XML structure while enhancing content
- Handles namespaces, XPath resolution, and complex data types
"""

import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Any, Union, Tuple
from pathlib import Path
import re
import logging

from .enhanced_json_config import EnhancedJsonConfig


class XMLOverrideEngineError(Exception):
    """Raised when XML override operations fail"""
    pass


class XMLOverrideEngine:
    """
    Applies JSON configuration overrides to base-generated XML.
    
    This engine takes complete, valid XML from the base XMLGenerator and
    applies targeted enhancements based on EnhancedJsonConfig specifications.
    
    Key Features:
    - Preserves XML structure and validity
    - Applies overrides in correct precedence order
    - Handles complex XPath resolution
    - Supports namespace-aware operations
    - Maintains attribute and element text content
    """
    
    def __init__(self, enhanced_config: EnhancedJsonConfig):
        """
        Initialize XML Override Engine.
        
        Args:
            enhanced_config: Enhanced JSON configuration instance
        """
        self.config = enhanced_config
        self.logger = logging.getLogger(__name__)
        
        # XML processing state
        self.xml_tree = None
        self.root = None
        self.namespace_map = {}
        self.element_index = {}  # For indexed element access
        
        # Override tracking
        self.applied_overrides = {
            'values': [],
            'patterns': [],
            'templates': [],
            'attributes': []
        }
    
    def apply_overrides(self, base_xml: Union[str, ET.Element, ET.ElementTree]) -> str:
        """
        Apply all JSON configuration overrides to base XML.
        
        Args:
            base_xml: Base XML as string, Element, or ElementTree
            
        Returns:
            Enhanced XML as string
            
        Raises:
            XMLOverrideEngineError: If override application fails
        """
        try:
            # Parse base XML
            self._parse_base_xml(base_xml)
            
            # Build element index for efficient lookups
            self._build_element_index()
            
            # Apply overrides in precedence order
            self._apply_value_overrides()
            self._apply_pattern_overrides()
            self._apply_template_overrides()
            self._apply_attribute_overrides()
            self._apply_namespace_prefixes()
            
            # Convert back to string
            return self._tree_to_string()
            
        except Exception as e:
            raise XMLOverrideEngineError(f"Failed to apply overrides: {e}") from e
    
    def _parse_base_xml(self, base_xml: Union[str, ET.Element, ET.ElementTree]) -> None:
        """Parse base XML into ElementTree structure."""
        if isinstance(base_xml, str):
            try:
                self.root = ET.fromstring(base_xml)
                self.xml_tree = ET.ElementTree(self.root)
            except ET.ParseError as e:
                raise XMLOverrideEngineError(f"Invalid XML: {e}")
                
        elif isinstance(base_xml, ET.Element):
            self.root = base_xml
            self.xml_tree = ET.ElementTree(self.root)
            
        elif isinstance(base_xml, ET.ElementTree):
            self.xml_tree = base_xml
            self.root = base_xml.getroot()
            
        else:
            raise XMLOverrideEngineError(f"Unsupported XML type: {type(base_xml)}")
        
        # Extract namespace mappings
        self._extract_namespaces()
    
    def _extract_namespaces(self) -> None:
        """Extract namespace mappings from XML."""
        # Get namespaces from root element
        for prefix, uri in ET._namespace_map.items():
            if prefix:  # Skip default namespace
                self.namespace_map[prefix] = uri
        
        # Also check root element attributes for namespace declarations
        for attr_name, attr_value in self.root.attrib.items():
            if attr_name.startswith('xmlns:'):
                prefix = attr_name[6:]  # Remove 'xmlns:' prefix
                self.namespace_map[prefix] = attr_value
            elif attr_name == 'xmlns':
                self.namespace_map[''] = attr_value  # Default namespace
    
    def _build_element_index(self) -> None:
        """Build index of elements for efficient XPath-like lookups."""
        self.element_index = {}
        
        def index_element(element, path_components):
            # Build full path
            element_name = self._get_local_name(element.tag)
            current_path = '/'.join(path_components + [element_name])
            
            # Count siblings with same name for indexing
            parent_path = '/'.join(path_components) if path_components else ''
            sibling_count = self.element_index.get(f"{parent_path}_count_{element_name}", 0) + 1
            self.element_index[f"{parent_path}_count_{element_name}"] = sibling_count
            
            # Store element with indexed path
            indexed_path = f"{current_path}[{sibling_count}]"
            self.element_index[current_path] = self.element_index.get(current_path, [])
            self.element_index[current_path].append(element)
            self.element_index[indexed_path] = element
            
            # Recurse to children
            for child in element:
                index_element(child, path_components + [element_name])
        
        # Start indexing from root
        root_name = self._get_local_name(self.root.tag)
        self.element_index[f'/{root_name}'] = [self.root]
        self.element_index[f'/{root_name}[1]'] = self.root
        
        for child in self.root:
            index_element(child, [root_name])
    
    def _apply_value_overrides(self) -> None:
        """Apply explicit value overrides from configuration."""
        for path, value in self.config.values.items():
            elements = self._find_elements_by_path(path)
            
            for element in elements:
                if '@' in path:
                    # Attribute override
                    attr_name = path.split('@')[-1]
                    resolved_value = self.config._resolve_value(value)
                    element.set(attr_name, resolved_value)
                    self.applied_overrides['values'].append(f"{path} = {resolved_value}")
                else:
                    # Element text override
                    resolved_value = self.config._resolve_value(value)
                    element.text = resolved_value
                    self.applied_overrides['values'].append(f"{path} = {resolved_value}")
    
    def _apply_pattern_overrides(self) -> None:
        """Apply pattern-based overrides to matching elements."""
        for pattern, value in self.config.patterns.items():
            matching_elements = self._find_elements_by_pattern(pattern)
            
            for element, element_path in matching_elements:
                if '@' in pattern:
                    # Attribute pattern
                    attr_pattern = pattern.split('@')[-1]
                    for attr_name in element.attrib.keys():
                        if self._pattern_matches(attr_pattern, attr_name):
                            resolved_value = self.config._resolve_value(value)
                            element.set(attr_name, resolved_value)
                            self.applied_overrides['patterns'].append(f"{element_path}@{attr_name} = {resolved_value}")
                else:
                    # Element pattern
                    resolved_value = self.config._resolve_value(value)
                    element.text = resolved_value
                    self.applied_overrides['patterns'].append(f"{element_path} = {resolved_value}")
    
    def _apply_template_overrides(self) -> None:
        """Apply template-based data overrides."""
        # This is a simplified implementation
        # Full template engine will be implemented in Phase 2.2
        for path, value in self.config.values.items():
            if isinstance(value, str) and value.startswith('@'):
                elements = self._find_elements_by_path(path)
                
                for element in elements:
                    template_data = self.config._resolve_template_reference(value)
                    if template_data and template_data != value:
                        # For now, just set as text content
                        # Full template resolution will be enhanced later
                        element.text = template_data
                        self.applied_overrides['templates'].append(f"{path} = {template_data}")
    
    def _apply_attribute_overrides(self) -> None:
        """Apply dedicated attribute overrides."""
        for attr_selector, value in self.config.attributes.items():
            matching_elements = self._find_elements_by_attribute_selector(attr_selector)
            
            for element, attr_name in matching_elements:
                resolved_value = self.config._resolve_value(value)
                element.set(attr_name, resolved_value)
                element_path = self._get_element_path(element)
                self.applied_overrides['attributes'].append(f"{element_path}@{attr_name} = {resolved_value}")
    
    def _apply_namespace_prefixes(self) -> None:
        """Apply namespace prefixes to elements based on configuration."""
        if not self.config.namespaces:
            return
        
        # This is a placeholder for namespace handling
        # Full namespace support will be enhanced based on requirements
        pass
    
    def _find_elements_by_path(self, path: str) -> List[ET.Element]:
        """Find elements matching the given path specification."""
        elements = []
        
        # Handle absolute paths
        if path.startswith('/'):
            # Remove attribute part if present
            element_path = path.split('@')[0]
            if element_path in self.element_index:
                result = self.element_index[element_path]
                if isinstance(result, list):
                    elements.extend(result)
                else:
                    elements.append(result)
        
        # Handle dot notation
        elif '.' in path and not path.startswith('@'):
            xpath_path = '/' + path.replace('.', '/')
            element_path = xpath_path.split('@')[0]
            if element_path in self.element_index:
                result = self.element_index[element_path]
                if isinstance(result, list):
                    elements.extend(result)
                else:
                    elements.append(result)
        
        # Handle simple element names
        else:
            element_name = path.split('@')[0]
            # Find all elements with this name
            for indexed_path, element_or_list in self.element_index.items():
                if indexed_path.endswith(f'/{element_name}') or indexed_path.endswith(f'/{element_name}[1]'):
                    if isinstance(element_or_list, list):
                        elements.extend(element_or_list)
                    else:
                        elements.append(element_or_list)
        
        return elements
    
    def _find_elements_by_pattern(self, pattern: str) -> List[Tuple[ET.Element, str]]:
        """Find elements matching the given pattern."""
        matching_elements = []
        
        # Convert wildcard pattern to regex
        if '@' in pattern:
            # Attribute pattern handling
            element_pattern, attr_pattern = pattern.split('@', 1)
            element_regex = element_pattern.replace('*', '.*') if element_pattern else '.*'

            for path, element_or_list in self.element_index.items():
                # Skip counter entries (they contain "_count_" in the key)
                if '_count_' in str(path):
                    continue

                elements = element_or_list if isinstance(element_or_list, list) else [element_or_list]

                for element in elements:
                    # Skip if element is not an ET.Element (could be int counter)
                    if not isinstance(element, ET.Element):
                        continue

                    element_name = self._get_local_name(element.tag)
                    if re.match(f'^{element_regex}$', element_name) or element_pattern == '*':
                        matching_elements.append((element, path))
        else:
            # Element pattern
            element_regex = pattern.replace('*', '.*')

            for path, element_or_list in self.element_index.items():
                # Skip counter entries (they contain "_count_" in the key)
                if '_count_' in str(path):
                    continue

                elements = element_or_list if isinstance(element_or_list, list) else [element_or_list]

                for element in elements:
                    # Skip if element is not an ET.Element (could be int counter)
                    if not isinstance(element, ET.Element):
                        continue

                    element_name = self._get_local_name(element.tag)
                    if re.match(f'^{element_regex}$', element_name):
                        matching_elements.append((element, path))
        
        return matching_elements
    
    def _find_elements_by_attribute_selector(self, selector: str) -> List[Tuple[ET.Element, str]]:
        """Find elements matching XPath-style attribute selector."""
        matching_elements = []
        
        # Parse selector: //*[@AttributeName] or //Element/@Attribute
        if selector.startswith('//'):
            if '@' in selector:
                parts = selector.split('@')
                element_part = parts[0].strip('/')
                attr_part = parts[1].strip('[]')
                
                for path, element_or_list in self.element_index.items():
                    elements = element_or_list if isinstance(element_or_list, list) else [element_or_list]
                    
                    for element in elements:
                        element_name = self._get_local_name(element.tag)
                        
                        # Check element match
                        element_matches = (element_part == '*' or 
                                         element_part == '' or 
                                         element_part == element_name)
                        
                        if element_matches and attr_part in element.attrib:
                            matching_elements.append((element, attr_part))
        
        return matching_elements
    
    def _pattern_matches(self, pattern: str, text: str) -> bool:
        """Check if pattern matches text."""
        regex_pattern = pattern.replace('*', '.*')
        return bool(re.match(f'^{regex_pattern}$', text))
    
    def _get_local_name(self, tag: str) -> str:
        """Extract local name from potentially namespaced tag."""
        if '}' in tag:
            return tag.split('}')[1]
        return tag
    
    def _get_element_path(self, element: ET.Element) -> str:
        """Get the full path of an element in the tree."""
        # This is a simplified implementation
        # A full implementation would traverse up the tree
        element_name = self._get_local_name(element.tag)
        
        # Try to find the path in our index
        for path, indexed_element in self.element_index.items():
            if isinstance(indexed_element, ET.Element) and indexed_element is element:
                return path
            elif isinstance(indexed_element, list) and element in indexed_element:
                return path
        
        return element_name
    
    def _tree_to_string(self) -> str:
        """Convert ElementTree back to XML string."""
        # Register namespaces for proper output
        for prefix, uri in self.namespace_map.items():
            if prefix:  # Don't register empty prefix
                ET.register_namespace(prefix, uri)
        
        return ET.tostring(self.root, encoding='unicode', xml_declaration=True)
    
    def get_override_summary(self) -> Dict[str, List[str]]:
        """Get summary of applied overrides for debugging."""
        return self.applied_overrides.copy()
    
    def __repr__(self) -> str:
        """String representation of override engine."""
        total_overrides = sum(len(overrides) for overrides in self.applied_overrides.values())
        return f"XMLOverrideEngine(config='{self.config.schema}', overrides_applied={total_overrides})"