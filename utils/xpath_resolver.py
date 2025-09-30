"""
XPath Resolver System

This module provides sophisticated path resolution capabilities for the
enhanced JSON configuration system. It handles various path formats,
namespace-aware resolution, and efficient path matching.

Supported Path Formats:
- Absolute paths: /Root/Element/Child
- Dot notation: Parent.Child.Element
- Indexed elements: Element[2], /Root/Element[1]/Child[3]
- Attribute paths: Element@attribute, /Root/Element@attr
- Namespace-qualified: {namespace}Element, {ns}Element@attr
- Pattern paths: *ID, */Address, *@Currency
- Relative paths: ./Child, ../Sibling

Architecture:
- XPathResolver: Main path resolution and matching engine
- PathExpression: Parsed path representation
- NamespaceResolver: Namespace-aware path handling
- PathMatcher: Pattern matching and element finding
"""

import re
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Union, Tuple, Set
from dataclasses import dataclass
from enum import Enum


class PathType(Enum):
    """Types of path expressions supported."""
    ABSOLUTE = "absolute"           # /Root/Element/Child
    DOT_NOTATION = "dot_notation"   # Parent.Child.Element
    SIMPLE = "simple"               # Element
    PATTERN = "pattern"             # *ID, */Address
    ATTRIBUTE = "attribute"         # Element@attr, /Root@attr
    NAMESPACE_QUALIFIED = "ns_qualified"  # {ns}Element


@dataclass
class PathExpression:
    """Parsed representation of a path expression."""
    original: str
    path_type: PathType
    components: List[str]
    attribute: Optional[str] = None
    namespace_prefix: Optional[str] = None
    has_index: bool = False
    indices: List[int] = None
    is_pattern: bool = False
    
    def __post_init__(self):
        if self.indices is None:
            self.indices = []


class XPathResolverError(Exception):
    """Raised when path resolution operations fail."""
    pass


class XPathResolver:
    """
    Advanced path resolution system for JSON configuration.
    
    Provides consistent path parsing, validation, and element finding
    across the enhanced JSON configuration system. Handles various
    path formats with namespace awareness and efficient matching.
    """
    
    def __init__(self, namespace_map: Optional[Dict[str, str]] = None):
        """
        Initialize XPath resolver.
        
        Args:
            namespace_map: Mapping of namespace prefixes to URIs
        """
        self.namespace_map = namespace_map or {}
        self.compiled_patterns = {}
        
        # Path parsing regex patterns
        self.path_patterns = {
            'absolute': re.compile(r'^/[\w\[\]/@{}\.:-]+$'),
            'dot_notation': re.compile(r'^[\w@{}]+(?:\.[\w\[\]@{}]+)*$'),
            'simple': re.compile(r'^[\w@{}\[\]]+$'),
            'namespace': re.compile(r'\{([^}]+)\}(\w+)'),
            'index': re.compile(r'(\w+)\[(\d+)\]'),
            'attribute': re.compile(r'(.+)@(\w+)$'),
            'pattern': re.compile(r'[*]'),
        }
    
    def parse_path(self, path: str) -> PathExpression:
        """
        Parse a path expression into structured components.
        
        Args:
            path: Path expression to parse
            
        Returns:
            Parsed path expression
            
        Raises:
            XPathResolverError: If path syntax is invalid
        """
        if not path or not isinstance(path, str):
            raise XPathResolverError(f"Invalid path: {path}")
        
        original_path = path
        
        # Check for attribute specification
        attribute = None
        if '@' in path:
            path_part, attribute = path.rsplit('@', 1)
            path = path_part
        
        # Check for namespace qualification
        namespace_prefix = None
        if path.startswith('{') and '}' in path:
            ns_match = self.path_patterns['namespace'].match(path)
            if ns_match:
                namespace_prefix = ns_match.group(1)
                path = path[len(ns_match.group(0)):]
        
        # Check for patterns
        is_pattern = '*' in path
        
        # Determine path type
        if path.startswith('/'):
            path_type = PathType.ABSOLUTE
            components = [c for c in path.strip('/').split('/') if c]
        elif '.' in path and not is_pattern:
            path_type = PathType.DOT_NOTATION
            components = path.split('.')
        elif is_pattern:
            path_type = PathType.PATTERN
            components = self._parse_pattern_components(path)
        else:
            path_type = PathType.SIMPLE
            components = [path] if path else []
        
        # Handle special cases
        if attribute:
            path_type = PathType.ATTRIBUTE if path_type == PathType.SIMPLE else path_type
        
        if namespace_prefix:
            path_type = PathType.NAMESPACE_QUALIFIED
        
        # Parse indices in components
        indices = []
        has_index = False
        processed_components = []
        
        for component in components:
            index_match = self.path_patterns['index'].search(component)
            if index_match:
                element_name = index_match.group(1)
                index = int(index_match.group(2))
                processed_components.append(element_name)
                indices.append(index)
                has_index = True
            else:
                processed_components.append(component)
                indices.append(1)  # Default to first occurrence
        
        return PathExpression(
            original=original_path,
            path_type=path_type,
            components=processed_components,
            attribute=attribute,
            namespace_prefix=namespace_prefix,
            has_index=has_index,
            indices=indices,
            is_pattern=is_pattern
        )
    
    def find_elements(self, xml_tree: ET.ElementTree, path_expression: PathExpression) -> List[ET.Element]:
        """
        Find elements in XML tree matching the path expression.
        
        Args:
            xml_tree: XML tree to search
            path_expression: Parsed path expression
            
        Returns:
            List of matching elements
        """
        if path_expression.path_type == PathType.ABSOLUTE:
            return self._find_by_absolute_path(xml_tree, path_expression)
        elif path_expression.path_type == PathType.DOT_NOTATION:
            return self._find_by_dot_notation(xml_tree, path_expression)
        elif path_expression.path_type == PathType.SIMPLE:
            return self._find_by_simple_name(xml_tree, path_expression)
        elif path_expression.path_type == PathType.PATTERN:
            return self._find_by_pattern(xml_tree, path_expression)
        elif path_expression.path_type == PathType.NAMESPACE_QUALIFIED:
            return self._find_by_namespace(xml_tree, path_expression)
        else:
            return []
    
    def resolve_path(self, xml_tree: ET.ElementTree, path: str) -> List[ET.Element]:
        """
        Resolve a path string to matching elements.
        
        Args:
            xml_tree: XML tree to search
            path: Path string to resolve
            
        Returns:
            List of matching elements
        """
        try:
            path_expr = self.parse_path(path)
            return self.find_elements(xml_tree, path_expr)
        except Exception as e:
            raise XPathResolverError(f"Failed to resolve path '{path}': {e}") from e
    
    def match_pattern(self, element_name: str, pattern: str) -> bool:
        """
        Check if element name matches a pattern.
        
        Args:
            element_name: Name of element to check
            pattern: Pattern to match against
            
        Returns:
            True if pattern matches
        """
        # Compile pattern if not already cached
        if pattern not in self.compiled_patterns:
            regex_pattern = pattern.replace('*', '.*')
            self.compiled_patterns[pattern] = re.compile(f'^{regex_pattern}$')
        
        return bool(self.compiled_patterns[pattern].match(element_name))
    
    def get_element_path(self, element: ET.Element, root: ET.Element) -> str:
        """
        Get the absolute path of an element within a tree.
        
        Args:
            element: Element to get path for
            root: Root element of the tree
            
        Returns:
            Absolute path string
        """
        if element is root:
            return f"/{self._get_local_name(root.tag)}"
        
        # Build path by traversing up the tree
        path_components = []
        current = element
        
        # We need to traverse up to build the path
        # This is a simplified implementation
        element_name = self._get_local_name(current.tag)
        path_components.insert(0, element_name)
        
        # For a complete implementation, we'd need parent references
        # For now, return a basic path
        return "/" + "/".join(path_components)
    
    def _find_by_absolute_path(self, xml_tree: ET.ElementTree, path_expr: PathExpression) -> List[ET.Element]:
        """Find elements by absolute path."""
        root = xml_tree.getroot()
        current_elements = [root]
        
        # Skip root component if it matches
        components = path_expr.components[:]
        if components and self._get_local_name(root.tag) == components[0]:
            components = components[1:]
        
        # Traverse each component
        for i, component in enumerate(components):
            next_elements = []
            target_index = path_expr.indices[i] if i < len(path_expr.indices) else 1
            
            for element in current_elements:
                matching_children = []
                for child in element:
                    if self._get_local_name(child.tag) == component:
                        matching_children.append(child)
                
                # Apply index if specified
                if path_expr.has_index and target_index <= len(matching_children):
                    next_elements.append(matching_children[target_index - 1])
                else:
                    next_elements.extend(matching_children)
            
            current_elements = next_elements
            if not current_elements:
                break
        
        return current_elements
    
    def _find_by_dot_notation(self, xml_tree: ET.ElementTree, path_expr: PathExpression) -> List[ET.Element]:
        """Find elements by dot notation path."""
        # Convert dot notation to absolute path and reuse logic
        absolute_path = '/' + '/'.join(path_expr.components)
        absolute_expr = PathExpression(
            original=absolute_path,
            path_type=PathType.ABSOLUTE,
            components=path_expr.components,
            attribute=path_expr.attribute,
            namespace_prefix=path_expr.namespace_prefix,
            has_index=path_expr.has_index,
            indices=path_expr.indices,
            is_pattern=path_expr.is_pattern
        )
        return self._find_by_absolute_path(xml_tree, absolute_expr)
    
    def _find_by_simple_name(self, xml_tree: ET.ElementTree, path_expr: PathExpression) -> List[ET.Element]:
        """Find elements by simple name throughout the tree."""
        if not path_expr.components:
            return []
        
        element_name = path_expr.components[0]
        matching_elements = []
        
        def find_recursive(element):
            if self._get_local_name(element.tag) == element_name:
                matching_elements.append(element)
            for child in element:
                find_recursive(child)
        
        find_recursive(xml_tree.getroot())
        return matching_elements
    
    def _find_by_pattern(self, xml_tree: ET.ElementTree, path_expr: PathExpression) -> List[ET.Element]:
        """Find elements by pattern matching."""
        matching_elements = []
        pattern = path_expr.components[0] if path_expr.components else '*'
        
        def find_recursive(element):
            element_name = self._get_local_name(element.tag)
            if self.match_pattern(element_name, pattern):
                matching_elements.append(element)
            for child in element:
                find_recursive(child)
        
        find_recursive(xml_tree.getroot())
        return matching_elements
    
    def _find_by_namespace(self, xml_tree: ET.ElementTree, path_expr: PathExpression) -> List[ET.Element]:
        """Find elements by namespace-qualified name."""
        # This is a simplified implementation
        # Full namespace support would require more sophisticated handling
        return self._find_by_simple_name(xml_tree, path_expr)
    
    def _parse_pattern_components(self, pattern_path: str) -> List[str]:
        """Parse pattern path into components."""
        if '/' in pattern_path:
            return [c for c in pattern_path.strip('/').split('/') if c]
        elif '.' in pattern_path:
            return pattern_path.split('.')
        else:
            return [pattern_path]
    
    def _get_local_name(self, tag: str) -> str:
        """Extract local name from potentially namespaced tag."""
        if '}' in tag:
            return tag.split('}')[1]
        return tag
    
    def validate_path_syntax(self, path: str) -> bool:
        """
        Validate path syntax without parsing.
        
        Args:
            path: Path to validate
            
        Returns:
            True if syntax is valid
        """
        try:
            self.parse_path(path)
            return True
        except XPathResolverError:
            return False
    
    def normalize_path(self, path: str) -> str:
        """
        Normalize a path to standard format.
        
        Args:
            path: Path to normalize
            
        Returns:
            Normalized path string
        """
        try:
            path_expr = self.parse_path(path)
            
            # Rebuild path in normalized format
            if path_expr.path_type == PathType.ABSOLUTE:
                normalized = '/' + '/'.join(path_expr.components)
            elif path_expr.path_type == PathType.DOT_NOTATION:
                normalized = '.'.join(path_expr.components)
            else:
                normalized = path_expr.original
            
            # Add indices if present
            if path_expr.has_index:
                components = normalized.split('/' if normalized.startswith('/') else '.')
                for i, index in enumerate(path_expr.indices):
                    if i < len(components) and index != 1:
                        components[i] = f"{components[i]}[{index}]"
                
                separator = '/' if normalized.startswith('/') else '.'
                normalized = separator.join(components)
                if normalized.startswith('/'):
                    normalized = '/' + normalized.lstrip('/')
            
            # Add attribute if present
            if path_expr.attribute:
                normalized = f"{normalized}@{path_expr.attribute}"
            
            # Add namespace if present
            if path_expr.namespace_prefix:
                normalized = f"{{{path_expr.namespace_prefix}}}{normalized}"
            
            return normalized
            
        except XPathResolverError:
            return path  # Return original if can't normalize
    
    def get_path_precedence(self, path: str) -> int:
        """
        Get precedence score for path (higher = higher precedence).
        
        Args:
            path: Path to score
            
        Returns:
            Precedence score
        """
        try:
            path_expr = self.parse_path(path)
            
            # Precedence order: absolute > dot_notation > simple > pattern
            precedence_map = {
                PathType.ABSOLUTE: 1000,
                PathType.DOT_NOTATION: 800,
                PathType.SIMPLE: 600,
                PathType.ATTRIBUTE: 400,
                PathType.PATTERN: 200,
                PathType.NAMESPACE_QUALIFIED: 900
            }
            
            base_score = precedence_map.get(path_expr.path_type, 0)
            
            # Bonus for specificity
            component_bonus = len(path_expr.components) * 50
            index_bonus = 100 if path_expr.has_index else 0
            attribute_bonus = 150 if path_expr.attribute else 0
            
            return base_score + component_bonus + index_bonus + attribute_bonus
            
        except XPathResolverError:
            return 0
    
    def __repr__(self) -> str:
        """String representation of resolver."""
        return f"XPathResolver(namespaces={len(self.namespace_map)}, patterns_cached={len(self.compiled_patterns)})"