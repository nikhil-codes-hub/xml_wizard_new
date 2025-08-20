"""
Template Engine System

This module handles template-based data generation for consistent related data
in the enhanced JSON configuration system. It supports data cycling, computed
fields, template inheritance, and complex data relationships.

Template Features:
- Data consistency: Related fields stay together (name, email, phone)
- Cycling strategies: Sequential, random, once-only
- Computed fields: Calculated values based on other fields
- Template inheritance: Templates can extend other templates
- Field validation: Ensure template data consistency
- Integration: Works with XMLOverrideEngine for XML application

Architecture:
- TemplateEngine: Main template processing engine
- TemplateData: Individual template data container
- ComputedFieldProcessor: Handles calculated field logic
- TemplateCyclingManager: Manages data cycling strategies
- TemplateValidator: Validates template configurations
"""

import json
import random
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from copy import deepcopy
import logging

from .enhanced_json_config import EnhancedJsonConfig


class CyclingStrategy(Enum):
    """Template data cycling strategies."""
    SEQUENTIAL = "sequential"   # Cycle through data in order
    RANDOM = "random"          # Random selection from data
    ONCE = "once"              # Use each item only once
    INFINITE = "infinite"      # Repeat infinitely


@dataclass
class TemplateData:
    """Container for template data with metadata."""
    name: str
    fields: Dict[str, str]
    data: List[Dict[str, Any]]
    cycling: CyclingStrategy = CyclingStrategy.SEQUENTIAL
    computed_fields: Dict[str, Dict] = field(default_factory=dict)
    inheritance: Optional[str] = None
    current_index: int = 0
    used_indices: Set[int] = field(default_factory=set)
    max_uses: Optional[int] = None
    
    def __post_init__(self):
        """Initialize template data after creation."""
        if isinstance(self.cycling, str):
            self.cycling = CyclingStrategy(self.cycling)


@dataclass
class ComputedField:
    """Represents a computed field definition."""
    name: str
    formula: str
    inputs: List[str]
    params: Dict[str, Any] = field(default_factory=dict)
    output_format: Optional[str] = None


class TemplateEngineError(Exception):
    """Raised when template engine operations fail."""
    pass


class TemplateEngine:
    """
    Advanced template engine for consistent data generation.
    
    Manages template data, cycling strategies, computed fields, and
    template inheritance to ensure related data consistency across
    XML generation. Integrates with the enhanced JSON configuration
    system to provide powerful data management capabilities.
    """
    
    def __init__(self, enhanced_config: EnhancedJsonConfig):
        """
        Initialize template engine.
        
        Args:
            enhanced_config: Enhanced JSON configuration instance
        """
        self.config = enhanced_config
        self.logger = logging.getLogger(__name__)
        
        # Template storage
        self.templates: Dict[str, TemplateData] = {}
        self.computed_processors: Dict[str, ComputedField] = {}
        
        # Template resolution state
        self.resolved_templates: Dict[str, List[Dict]] = {}
        self.template_usage: Dict[str, int] = {}
        
        # Random seed for deterministic generation
        if enhanced_config.seed:
            random.seed(enhanced_config.seed)
        
        # Parse and initialize templates
        self._parse_templates()
        self._resolve_inheritance()
        self._setup_computed_fields()
    
    def _parse_templates(self) -> None:
        """Parse template configuration from enhanced config."""
        for template_name, template_config in self.config.templates.items():
            try:
                self._parse_single_template(template_name, template_config)
            except Exception as e:
                self.logger.error(f"Failed to parse template {template_name}: {e}")
    
    def _parse_single_template(self, template_name: str, template_config: Union[Dict, List]) -> None:
        """Parse a single template configuration."""
        if isinstance(template_config, list):
            # Simple list format: [{"field1": "value1"}, ...]
            template_data = TemplateData(
                name=template_name,
                fields={},  # Auto-detect from data
                data=template_config,
                cycling=CyclingStrategy.SEQUENTIAL
            )
            
            # Auto-detect fields from data
            if template_config:
                template_data.fields = {key: "string" for key in template_config[0].keys()}
        
        elif isinstance(template_config, dict):
            # Complex format with metadata
            data = template_config.get('data', [])
            if not data:
                self.logger.warning(f"Template {template_name} has no data")
                return
            
            # Parse cycling strategy
            cycling_str = template_config.get('cycle', 'sequential')
            try:
                cycling = CyclingStrategy(cycling_str)
            except ValueError:
                self.logger.warning(f"Invalid cycling strategy '{cycling_str}' for {template_name}, using sequential")
                cycling = CyclingStrategy.SEQUENTIAL
            
            template_data = TemplateData(
                name=template_name,
                fields=template_config.get('fields', {}),
                data=data,
                cycling=cycling,
                computed_fields=template_config.get('computed', {}),
                inheritance=template_config.get('inheritance'),
                max_uses=template_config.get('max_uses')
            )
            
            # Auto-detect fields if not specified
            if not template_data.fields and data:
                template_data.fields = {key: "string" for key in data[0].keys()}
        
        else:
            raise TemplateEngineError(f"Invalid template format for {template_name}")
        
        self.templates[template_name] = template_data
    
    def _resolve_inheritance(self) -> None:
        """Resolve template inheritance relationships."""
        # Sort templates by dependency order
        resolved_order = self._get_inheritance_order()
        
        for template_name in resolved_order:
            template = self.templates[template_name]
            if template.inheritance:
                self._apply_inheritance(template)
    
    def _get_inheritance_order(self) -> List[str]:
        """Get template resolution order based on inheritance."""
        order = []
        visited = set()
        visiting = set()
        
        def visit(template_name: str):
            if template_name in visiting:
                raise TemplateEngineError(f"Circular inheritance detected: {template_name}")
            if template_name in visited:
                return
            
            visiting.add(template_name)
            template = self.templates.get(template_name)
            if template and template.inheritance:
                visit(template.inheritance)
            
            visiting.remove(template_name)
            visited.add(template_name)
            order.append(template_name)
        
        for template_name in self.templates.keys():
            visit(template_name)
        
        return order
    
    def _apply_inheritance(self, template: TemplateData) -> None:
        """Apply inheritance from parent template."""
        parent_template = self.templates.get(template.inheritance)
        if not parent_template:
            self.logger.warning(f"Parent template '{template.inheritance}' not found for {template.name}")
            return
        
        # Merge fields (child overrides parent)
        merged_fields = parent_template.fields.copy()
        merged_fields.update(template.fields)
        template.fields = merged_fields
        
        # Merge computed fields
        merged_computed = parent_template.computed_fields.copy()
        merged_computed.update(template.computed_fields)
        template.computed_fields = merged_computed
        
        # Inherit data if child has no data
        if not template.data and parent_template.data:
            template.data = deepcopy(parent_template.data)
    
    def _setup_computed_fields(self) -> None:
        """Set up computed field processors for all templates."""
        for template in self.templates.values():
            for field_name, field_config in template.computed_fields.items():
                try:
                    computed_field = self._parse_computed_field(field_name, field_config)
                    self.computed_processors[f"{template.name}.{field_name}"] = computed_field
                except Exception as e:
                    self.logger.error(f"Failed to setup computed field {template.name}.{field_name}: {e}")
    
    def _parse_computed_field(self, field_name: str, field_config: Union[str, Dict]) -> ComputedField:
        """Parse computed field configuration."""
        if isinstance(field_config, str):
            # Simple formula: "DepartureTime + 2h30m"
            return ComputedField(
                name=field_name,
                formula=field_config,
                inputs=self._extract_field_inputs(field_config)
            )
        
        elif isinstance(field_config, dict):
            # Complex configuration
            formula = field_config.get('formula', '')
            inputs = field_config.get('inputs', self._extract_field_inputs(formula))
            
            return ComputedField(
                name=field_name,
                formula=formula,
                inputs=inputs,
                params=field_config.get('params', {}),
                output_format=field_config.get('output_format')
            )
        
        else:
            raise TemplateEngineError(f"Invalid computed field config for {field_name}")
    
    def _extract_field_inputs(self, formula: str) -> List[str]:
        """Extract field names referenced in formula."""
        # Simple extraction - look for field references
        field_pattern = r'\b([A-Z][a-zA-Z]*(?:Time|Date|Amount|Name|ID|Code))\b'
        matches = re.findall(field_pattern, formula)
        return list(set(matches))
    
    def get_template_data(self, template_reference: str) -> Optional[Dict[str, Any]]:
        """
        Get data from template using reference format.
        
        Args:
            template_reference: Reference like "template_name[1]" or "template_name.field"
            
        Returns:
            Template data or None if not found
        """
        try:
            # Parse reference format
            if '[' in template_reference and ']' in template_reference:
                # Array-style: template_name[1]
                match = re.match(r'^(\w+)\[(\d+)\]$', template_reference)
                if match:
                    template_name = match.group(1)
                    index = int(match.group(2)) - 1  # Convert to 0-based
                    return self._get_template_data_by_index(template_name, index)
            
            elif '.' in template_reference:
                # Field-style: template_name.field
                parts = template_reference.split('.', 1)
                template_name = parts[0]
                field_path = parts[1]
                return self._get_template_field_data(template_name, field_path)
            
            else:
                # Simple template name - get next data
                return self._get_next_template_data(template_reference)
        
        except Exception as e:
            self.logger.error(f"Failed to get template data for '{template_reference}': {e}")
            return None
    
    def _get_template_data_by_index(self, template_name: str, index: int) -> Optional[Dict[str, Any]]:
        """Get template data by specific index."""
        template = self.templates.get(template_name)
        if not template or not template.data:
            return None
        
        if 0 <= index < len(template.data):
            data = template.data[index].copy()
            return self._apply_computed_fields(template, data)
        
        return None
    
    def _get_template_field_data(self, template_name: str, field_path: str) -> Optional[Any]:
        """Get specific field data from template."""
        data = self._get_next_template_data(template_name)
        if data and field_path in data:
            return data[field_path]
        return None
    
    def _get_next_template_data(self, template_name: str) -> Optional[Dict[str, Any]]:
        """Get next data item from template based on cycling strategy."""
        template = self.templates.get(template_name)
        if not template or not template.data:
            return None
        
        data_item = None
        
        if template.cycling == CyclingStrategy.SEQUENTIAL:
            data_item = template.data[template.current_index]
            template.current_index = (template.current_index + 1) % len(template.data)
        
        elif template.cycling == CyclingStrategy.RANDOM:
            data_item = random.choice(template.data)
        
        elif template.cycling == CyclingStrategy.ONCE:
            available_indices = [i for i in range(len(template.data)) if i not in template.used_indices]
            if available_indices:
                index = available_indices[0]
                data_item = template.data[index]
                template.used_indices.add(index)
            else:
                return None  # All items used
        
        elif template.cycling == CyclingStrategy.INFINITE:
            data_item = template.data[template.current_index]
            template.current_index = (template.current_index + 1) % len(template.data)
        
        if data_item:
            # Apply computed fields
            data_copy = data_item.copy()
            return self._apply_computed_fields(template, data_copy)
        
        return None
    
    def _apply_computed_fields(self, template: TemplateData, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply computed field calculations to data."""
        for field_name, field_config in template.computed_fields.items():
            try:
                computed_value = self._compute_field_value(field_config, data)
                if computed_value is not None:
                    data[field_name] = computed_value
            except Exception as e:
                self.logger.error(f"Failed to compute field {field_name}: {e}")
        
        return data
    
    def _compute_field_value(self, field_config: Union[str, Dict], data: Dict[str, Any]) -> Any:
        """Compute value for a computed field."""
        if isinstance(field_config, str):
            return self._evaluate_formula(field_config, data)
        
        elif isinstance(field_config, dict):
            formula = field_config.get('formula', '')
            if formula:
                return self._evaluate_formula(formula, data)
        
        return None
    
    def _evaluate_formula(self, formula: str, data: Dict[str, Any]) -> Any:
        """Evaluate a formula with available data."""
        try:
            # Handle common formula patterns
            if ' + ' in formula:
                return self._evaluate_addition_formula(formula, data)
            elif ' - ' in formula:
                return self._evaluate_subtraction_formula(formula, data)
            elif 'concat(' in formula.lower():
                return self._evaluate_concat_formula(formula, data)
            elif 'sum(' in formula.lower():
                return self._evaluate_sum_formula(formula, data)
            else:
                # Simple field reference
                return data.get(formula, formula)
        
        except Exception as e:
            self.logger.error(f"Failed to evaluate formula '{formula}': {e}")
            return None
    
    def _evaluate_addition_formula(self, formula: str, data: Dict[str, Any]) -> Any:
        """Evaluate addition formula like 'DepartureTime + 2h30m'."""
        parts = formula.split(' + ')
        if len(parts) != 2:
            return None
        
        base_field = parts[0].strip()
        addition_part = parts[1].strip()
        
        base_value = data.get(base_field)
        if not base_value:
            return None
        
        # Handle time duration addition
        if 'h' in addition_part or 'm' in addition_part:
            return self._add_time_duration(str(base_value), addition_part)
        
        # Handle numeric addition
        try:
            base_num = float(base_value)
            add_num = float(addition_part)
            return str(base_num + add_num)
        except ValueError:
            return None
    
    def _evaluate_subtraction_formula(self, formula: str, data: Dict[str, Any]) -> Any:
        """Evaluate subtraction formula."""
        parts = formula.split(' - ')
        if len(parts) != 2:
            return None
        
        field1 = parts[0].strip()
        field2 = parts[1].strip()
        
        value1 = data.get(field1)
        value2 = data.get(field2)
        
        if value1 and value2:
            try:
                return str(float(value1) - float(value2))
            except ValueError:
                return None
        
        return None
    
    def _evaluate_concat_formula(self, formula: str, data: Dict[str, Any]) -> str:
        """Evaluate concatenation formula like 'concat(FirstName, " ", LastName)'."""
        # Extract content between parentheses
        match = re.search(r'concat\((.*)\)', formula, re.IGNORECASE)
        if not match:
            return formula
        
        content = match.group(1)
        parts = [part.strip().strip('"\'') for part in content.split(',')]
        
        result_parts = []
        for part in parts:
            if part in data:
                result_parts.append(str(data[part]))
            else:
                result_parts.append(part)
        
        return ''.join(result_parts)
    
    def _evaluate_sum_formula(self, formula: str, data: Dict[str, Any]) -> str:
        """Evaluate sum formula."""
        # Simplified sum implementation
        match = re.search(r'sum\((.*)\)', formula, re.IGNORECASE)
        if not match:
            return formula
        
        content = match.group(1)
        fields = [field.strip() for field in content.split(',')]
        
        total = 0
        for field in fields:
            value = data.get(field, 0)
            try:
                total += float(value)
            except (ValueError, TypeError):
                continue
        
        return str(total)
    
    def _add_time_duration(self, base_time: str, duration: str) -> str:
        """Add duration to time string."""
        try:
            # Parse base time (assume ISO format)
            if 'T' in base_time:
                base_dt = datetime.fromisoformat(base_time.replace('Z', '+00:00'))
            else:
                base_dt = datetime.strptime(base_time, '%Y-%m-%d')
            
            # Parse duration (e.g., "2h30m", "1h", "45m")
            hours = 0
            minutes = 0
            
            hour_match = re.search(r'(\d+)h', duration)
            if hour_match:
                hours = int(hour_match.group(1))
            
            minute_match = re.search(r'(\d+)m', duration)
            if minute_match:
                minutes = int(minute_match.group(1))
            
            # Add duration
            result_dt = base_dt + timedelta(hours=hours, minutes=minutes)
            
            # Return in same format as input
            if 'T' in base_time:
                return result_dt.isoformat()
            else:
                return result_dt.strftime('%Y-%m-%d')
        
        except Exception as e:
            self.logger.error(f"Failed to add duration '{duration}' to time '{base_time}': {e}")
            return base_time
    
    def apply_template_to_elements(self, element_template_map: Dict[str, str]) -> Dict[str, str]:
        """
        Apply template data to elements.
        
        Args:
            element_template_map: Map of element_path -> template_reference
            
        Returns:
            Map of element_path -> resolved_value
        """
        resolved_values = {}
        
        for element_path, template_ref in element_template_map.items():
            template_data = self.get_template_data(template_ref)
            if template_data:
                # For now, convert to JSON string
                # Full implementation would need more sophisticated mapping
                resolved_values[element_path] = json.dumps(template_data)
        
        return resolved_values
    
    def get_template_summary(self) -> Dict[str, Any]:
        """Get summary of template configuration for debugging."""
        return {
            'templates': {
                name: {
                    'fields': template.fields,
                    'data_count': len(template.data),
                    'cycling': template.cycling.value,
                    'computed_fields': len(template.computed_fields),
                    'current_index': template.current_index,
                    'used_count': len(template.used_indices)
                }
                for name, template in self.templates.items()
            },
            'computed_processors': len(self.computed_processors),
            'total_templates': len(self.templates)
        }
    
    def reset_template_state(self, template_name: Optional[str] = None) -> None:
        """Reset template cycling state."""
        if template_name:
            template = self.templates.get(template_name)
            if template:
                template.current_index = 0
                template.used_indices.clear()
        else:
            for template in self.templates.values():
                template.current_index = 0
                template.used_indices.clear()
    
    def validate_templates(self) -> List[str]:
        """Validate template configurations."""
        errors = []
        
        for template_name, template in self.templates.items():
            # Check for empty data
            if not template.data:
                errors.append(f"Template '{template_name}' has no data")
                continue
            
            # Check field consistency
            if template.fields:
                for data_item in template.data:
                    for field_name in template.fields.keys():
                        if field_name not in data_item:
                            errors.append(f"Template '{template_name}' data missing field '{field_name}'")
            
            # Check computed field dependencies
            for computed_field_name, computed_config in template.computed_fields.items():
                if isinstance(computed_config, dict):
                    inputs = computed_config.get('inputs', [])
                    for input_field in inputs:
                        if input_field not in template.fields and input_field not in template.computed_fields:
                            errors.append(f"Computed field '{computed_field_name}' references unknown field '{input_field}'")
        
        return errors
    
    def __repr__(self) -> str:
        """String representation of template engine."""
        return f"TemplateEngine(templates={len(self.templates)}, computed_fields={len(self.computed_processors)})"