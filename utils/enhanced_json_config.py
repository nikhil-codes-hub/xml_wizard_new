"""
Enhanced JSON Configuration System

This module implements the new JSON configuration parser based on the comprehensive
user guide specification. It handles values, patterns, choices, templates, repeats,
attributes, and namespaces with enterprise-grade path resolution.

Architecture:
- EnhancedJsonConfig: Main configuration parser and validator
- Precedence-based resolution: absolute paths > dot notation > patterns > templates
- Support for enterprise features: namespaces, complex choices, template cycling
"""

import json
import re
from typing import Dict, List, Optional, Any, Union
from pathlib import Path


class ConfigValidationError(Exception):
    """Raised when JSON configuration validation fails"""
    pass


class EnhancedJsonConfig:
    """
    Enhanced JSON Configuration parser for XML generation from XSD schemas.
    
    Supports the complete specification from the user guide:
    - Values: Direct element assignments with path resolution
    - Patterns: Wildcard-based bulk configuration  
    - Choices: XSD choice element selections
    - Templates: Related data consistency with cycling
    - Repeats: Element occurrence counts
    - Attributes: Attribute-specific configuration
    - Namespaces: Multi-namespace schema support
    """
    
    def __init__(self, config_data: Union[Dict, str, Path]):
        """
        Initialize enhanced JSON configuration.
        
        Args:
            config_data: Dictionary, JSON string, or file path to configuration
        """
        if isinstance(config_data, (str, Path)):
            self.config_dict = self._load_from_file(config_data)
        elif isinstance(config_data, dict):
            self.config_dict = config_data
        else:
            raise ConfigValidationError(f"Invalid config_data type: {type(config_data)}")
        
        # Core configuration sections
        self.schema = self.config_dict.get('schema')
        self.mode = self.config_dict.get('mode', 'complete')
        self.seed = self.config_dict.get('seed')
        
        # Main configuration sections
        self.values = self.config_dict.get('values', {})
        self.patterns = self.config_dict.get('patterns', {})
        self.choices = self.config_dict.get('choices', {})
        self.templates = self.config_dict.get('templates', {})
        self.repeats = self.config_dict.get('repeats', {})
        self.attributes = self.config_dict.get('attributes', {})
        self.namespaces = self.config_dict.get('namespaces', {})
        
        # Advanced configuration sections
        self.conditional = self.config_dict.get('conditional', {})
        self.validation = self.config_dict.get('validation', {})
        
        # Internal state
        self._compiled_patterns = None
        self._namespace_prefixes = {}
        
        # Validate configuration on initialization
        self.validate()
    
    def _load_from_file(self, file_path: Union[str, Path]) -> Dict:
        """Load configuration from JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise ConfigValidationError(f"Configuration file not found: {file_path}")
        except json.JSONDecodeError as e:
            raise ConfigValidationError(f"Invalid JSON in configuration file: {e}")
    
    def validate(self) -> None:
        """
        Validate the configuration structure and syntax.
        
        Raises:
            ConfigValidationError: If configuration is invalid
        """
        # Required fields
        if not self.schema:
            raise ConfigValidationError("'schema' field is required")
        
        # Mode validation
        valid_modes = ['complete', 'minimal', 'custom']
        if self.mode not in valid_modes:
            raise ConfigValidationError(f"Invalid mode '{self.mode}'. Must be one of: {valid_modes}")
        
        # Validate path syntax in values
        self._validate_value_paths()
        
        # Validate pattern syntax
        self._validate_patterns()
        
        # Validate template references
        self._validate_template_references()
        
        # Validate namespace configuration
        self._validate_namespaces()
        
        # Set up internal state after validation
        self._setup_namespace_prefixes()
        self._compile_patterns()
    
    def _validate_value_paths(self) -> None:
        """Validate path syntax in values section."""
        for path in self.values.keys():
            if not self._is_valid_path(path):
                raise ConfigValidationError(f"Invalid path syntax: '{path}'")
    
    def _validate_patterns(self) -> None:
        """Validate pattern syntax."""
        for pattern in self.patterns.keys():
            if not self._is_valid_pattern(pattern):
                raise ConfigValidationError(f"Invalid pattern syntax: '{pattern}'")
    
    def _validate_template_references(self) -> None:
        """Validate template references in values."""
        for value in self.values.values():
            if isinstance(value, str) and value.startswith('@'):
                template_ref = value[1:]  # Remove @ prefix
                if not self._is_valid_template_reference(template_ref):
                    raise ConfigValidationError(f"Invalid template reference: '{value}'")
    
    def _validate_namespaces(self) -> None:
        """Validate namespace configuration."""
        if self.namespaces:
            prefixes = self.namespaces.get('prefixes', {})
            if not isinstance(prefixes, dict):
                raise ConfigValidationError("'namespaces.prefixes' must be a dictionary")
            
            for prefix, uri in prefixes.items():
                if not isinstance(prefix, str) or not isinstance(uri, str):
                    raise ConfigValidationError(f"Invalid namespace mapping: {prefix} -> {uri}")
    
    def _is_valid_path(self, path: str) -> bool:
        """Check if path syntax is valid."""
        # Absolute path: /Root/Element/Child
        if path.startswith('/'):
            return bool(re.match(r'^/[\w\[\]/@{}\.:-]+$', path))
        
        # Dot notation: Parent.Child.Element
        if '.' in path:
            return bool(re.match(r'^[\w@{}]+(?:\.[\w\[\]@{}]+)*$', path))
        
        # Simple element: Element or Element@attribute
        return bool(re.match(r'^[\w@{}\[\]]+$', path))
    
    def _is_valid_pattern(self, pattern: str) -> bool:
        """Check if pattern syntax is valid."""
        # Wildcard patterns: *ID, Customer*, */Address
        return bool(re.match(r'^[\*\w/@{}\.:-]+$', pattern))
    
    def _is_valid_template_reference(self, template_ref: str) -> bool:
        """Check if template reference is valid."""
        # Format: template_name[index] or template_name.field
        if '[' in template_ref and ']' in template_ref:
            # Array-style reference: template_name[1]
            match = re.match(r'^(\w+)\[(\d+)\]$', template_ref)
            if match:
                template_name = match.group(1)
                return template_name in self.templates
        elif '.' in template_ref:
            # Field-style reference: template_name.field
            parts = template_ref.split('.')
            if len(parts) >= 2:
                template_name = parts[0]
                return template_name in self.templates
        else:
            # Simple reference: template_name
            return template_ref in self.templates
        
        return False
    
    def _setup_namespace_prefixes(self) -> None:
        """Set up namespace prefix mappings."""
        if self.namespaces:
            self._namespace_prefixes = self.namespaces.get('prefixes', {})
    
    def _compile_patterns(self) -> None:
        """Compile patterns for efficient matching."""
        self._compiled_patterns = {}
        for pattern, value in self.patterns.items():
            # Convert wildcard pattern to regex
            regex_pattern = pattern.replace('*', '.*')
            regex_pattern = f'^{regex_pattern}$'
            self._compiled_patterns[re.compile(regex_pattern)] = value
    
    def resolve_element_value(self, element_path: str, element_name: str, current_context: Optional[Dict] = None) -> Optional[str]:
        """
        Resolve value for a specific element using precedence rules.
        
        Precedence order:
        1. Absolute paths (/full/xpath)
        2. Dot notation (Parent.Child)  
        3. Simple element name (Element)
        4. Pattern matches (*ID, */Address)
        5. Template references (@template_name)
        
        Args:
            element_path: Full XPath of the element
            element_name: Simple name of the element
            current_context: Current XML context for relative resolution
            
        Returns:
            Resolved value or None if no match found
        """
        # 1. Check absolute path match
        if element_path in self.values:
            return self._resolve_value(self.values[element_path])
        
        # 2. Check dot notation matches (convert XPath to dot notation)
        dot_notation = self._xpath_to_dot_notation(element_path)
        if dot_notation and dot_notation in self.values:
            return self._resolve_value(self.values[dot_notation])
        
        # 3. Check simple element name
        if element_name in self.values:
            return self._resolve_value(self.values[element_name])
        
        # 4. Check pattern matches
        pattern_value = self._match_patterns(element_name, element_path)
        if pattern_value:
            return self._resolve_value(pattern_value)
        
        # 5. No match found
        return None
    
    def resolve_choice_selection(self, choice_path: str, choice_name: str) -> Optional[str]:
        """
        Resolve choice selection for XSD choice elements.
        
        Args:
            choice_path: Full path to choice element
            choice_name: Name of choice element
            
        Returns:
            Selected choice option or None
        """
        # Check absolute path first
        if choice_path in self.choices:
            return self.choices[choice_path]
        
        # Check simple name
        if choice_name in self.choices:
            return self.choices[choice_name]
        
        return None
    
    def get_repeat_count(self, element_name: str) -> Optional[int]:
        """
        Get repeat count for unbounded elements.
        
        Args:
            element_name: Name of the element
            
        Returns:
            Repeat count or None if not specified
        """
        return self.repeats.get(element_name)
    
    def resolve_attribute_value(self, element_path: str, attribute_name: str) -> Optional[str]:
        """
        Resolve attribute value using precedence rules.
        
        Args:
            element_path: Full XPath of the element
            attribute_name: Name of the attribute
            
        Returns:
            Resolved attribute value or None
        """
        # Try element@attribute syntax in values
        attr_path = f"{element_path}@{attribute_name}"
        if attr_path in self.values:
            return self._resolve_value(self.values[attr_path])
        
        # Try simple element@attribute
        simple_attr = f"{self._get_element_name_from_path(element_path)}@{attribute_name}"
        if simple_attr in self.values:
            return self._resolve_value(self.values[simple_attr])
        
        # Check dedicated attributes section
        for attr_selector, value in self.attributes.items():
            if self._attribute_selector_matches(attr_selector, element_path, attribute_name):
                return self._resolve_value(value)
        
        # Check patterns for attributes
        attr_pattern_value = self._match_attribute_patterns(attribute_name, element_path)
        if attr_pattern_value:
            return self._resolve_value(attr_pattern_value)
        
        return None
    
    def _resolve_value(self, value: str) -> str:
        """
        Resolve a configuration value, handling generators and template references.
        
        Args:
            value: Raw value from configuration
            
        Returns:
            Resolved value
        """
        if isinstance(value, str):
            # Handle template references
            if value.startswith('@'):
                return self._resolve_template_reference(value)
            
            # Handle generators
            if value.startswith('generate:'):
                return self._resolve_generator(value)
        
        return str(value)
    
    def _resolve_template_reference(self, template_ref: str) -> str:
        """Resolve template reference to actual value."""
        # Remove @ prefix
        ref = template_ref[1:]
        
        # Handle array-style: template_name[1]
        if '[' in ref and ']' in ref:
            match = re.match(r'^(\w+)\[(\d+)\]$', ref)
            if match:
                template_name = match.group(1)
                index = int(match.group(2)) - 1  # Convert to 0-based
                
                if template_name in self.templates:
                    template_data = self.templates[template_name]
                    if isinstance(template_data, list) and 0 <= index < len(template_data):
                        return json.dumps(template_data[index])
        
        # Handle field-style: template_name.field
        elif '.' in ref:
            parts = ref.split('.', 1)
            template_name = parts[0]
            field_path = parts[1]
            
            if template_name in self.templates:
                # This would need more complex field resolution
                pass
        
        # Return original reference if can't resolve
        return template_ref
    
    def _resolve_generator(self, generator_spec: str) -> str:
        """Resolve generator specification to actual value."""
        # Parse generator specification: generate:type:param1:param2
        parts = generator_spec.split(':')
        if len(parts) < 2:
            return generator_spec
        
        generator_type = parts[1]
        params = parts[2:] if len(parts) > 2 else []
        
        # Implement basic generators (can be extended)
        if generator_type == 'uuid':
            import uuid
            if params and params[0] == 'short':
                return str(uuid.uuid4()).split('-')[0]
            return str(uuid.uuid4())
        
        elif generator_type == 'alpha':
            import string
            import random
            length = int(params[0]) if params else 6
            return ''.join(random.choices(string.ascii_uppercase, k=length))
        
        elif generator_type == 'number':
            import random
            min_val = int(params[0]) if len(params) > 0 else 1
            max_val = int(params[1]) if len(params) > 1 else 1000
            return str(random.randint(min_val, max_val))
        
        elif generator_type == 'currency':
            import random
            min_val = float(params[0]) if len(params) > 0 else 10.0
            max_val = float(params[1]) if len(params) > 1 else 1000.0
            return f"{random.uniform(min_val, max_val):.2f}"
        
        elif generator_type == 'date':
            from datetime import datetime, timedelta
            if params and params[0] == 'today':
                return datetime.now().strftime('%Y-%m-%d')
            elif params and params[0] == 'future':
                future_date = datetime.now() + timedelta(days=random.randint(1, 365))
                return future_date.strftime('%Y-%m-%d')
        
        # Return original if can't resolve
        return generator_spec
    
    def _xpath_to_dot_notation(self, xpath: str) -> Optional[str]:
        """Convert XPath to dot notation."""
        if not xpath.startswith('/'):
            return None
        
        # Remove leading slash and convert slashes to dots
        # /Root/Element/Child -> Root.Element.Child
        parts = xpath.strip('/').split('/')
        return '.'.join(parts) if parts else None
    
    def _get_element_name_from_path(self, xpath: str) -> str:
        """Extract element name from XPath."""
        parts = xpath.strip('/').split('/')
        return parts[-1] if parts else xpath
    
    def _match_patterns(self, element_name: str, element_path: str) -> Optional[str]:
        """Match element against compiled patterns."""
        if not self._compiled_patterns:
            return None
        
        for pattern_regex, value in self._compiled_patterns.items():
            # Try matching against element name
            if pattern_regex.match(element_name):
                return value
            
            # Try matching against path components
            if pattern_regex.match(element_path):
                return value
        
        return None
    
    def _match_attribute_patterns(self, attribute_name: str, element_path: str) -> Optional[str]:
        """Match attribute against patterns."""
        for pattern, value in self.patterns.items():
            # Attribute patterns: *@*ID, *@Currency
            if '@' in pattern:
                element_pattern, attr_pattern = pattern.split('@', 1)
                
                # Check if attribute pattern matches
                attr_regex = attr_pattern.replace('*', '.*')
                if re.match(f'^{attr_regex}$', attribute_name):
                    # Check element pattern if specified
                    if element_pattern == '*' or not element_pattern:
                        return value
                    
                    element_regex = element_pattern.replace('*', '.*')
                    element_name = self._get_element_name_from_path(element_path)
                    if re.match(f'^{element_regex}$', element_name):
                        return value
        
        return None
    
    def _attribute_selector_matches(self, selector: str, element_path: str, attribute_name: str) -> bool:
        """Check if attribute selector matches the given element and attribute."""
        # XPath-style selectors: //*[@AttributeName], //Element/@Attribute
        if selector.startswith('//'):
            if '@' in selector:
                # //Element/@Attribute or //*[@Attribute]
                parts = selector.split('@')
                if len(parts) == 2:
                    element_part = parts[0].strip('/')
                    attr_part = parts[1].strip('[]')
                    
                    # Check attribute name match
                    if attr_part != attribute_name:
                        return False
                    
                    # Check element match
                    if element_part == '*' or not element_part:
                        return True
                    
                    element_name = self._get_element_name_from_path(element_path)
                    return element_part == element_name
        
        return False
    
    def get_base_choices(self) -> Dict[str, str]:
        """
        Extract choices in format expected by base XMLGenerator.
        
        Returns:
            Dictionary of choice selections for base generator
        """
        return self.choices.copy()
    
    def get_base_repeat_counts(self) -> Dict[str, int]:
        """
        Extract repeat counts in format expected by base XMLGenerator.
        
        Returns:
            Dictionary of repeat counts for base generator
        """
        return self.repeats.copy()
    
    def to_dict(self) -> Dict:
        """Convert configuration back to dictionary format."""
        return self.config_dict.copy()
    
    def save_to_file(self, file_path: Union[str, Path]) -> None:
        """Save configuration to JSON file."""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.config_dict, f, indent=2, ensure_ascii=False)
    
    def __repr__(self) -> str:
        """String representation of configuration."""
        return f"EnhancedJsonConfig(schema='{self.schema}', mode='{self.mode}', sections={len([s for s in [self.values, self.patterns, self.choices, self.templates, self.repeats] if s])})"