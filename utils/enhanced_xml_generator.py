"""
Enhanced XML Generator

This module provides the main integration layer that combines the base XML
generation system with the enhanced JSON configuration capabilities. It serves
as the unified interface for generating XML with advanced configuration features.

Architecture:
- EnhancedXMLGenerator: Main integration class
- Combines base XMLGenerator with enhanced JSON config
- Orchestrates choice resolution, template application, and override processing
- Provides unified interface for UI and API integration
- Handles error cases and fallbacks gracefully

Integration Flow:
1. Parse enhanced JSON configuration
2. Resolve choices for base generator
3. Generate base XML using proven XMLGenerator
4. Apply overrides using XMLOverrideEngine
5. Return enhanced XML with comprehensive metadata
"""

import logging
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Any, Union, Tuple
from pathlib import Path
from datetime import datetime

# Import existing base components
from .xml_generator import XMLGenerator
from .type_generators import TypeGeneratorFactory

# Import new enhanced components
from .enhanced_json_config import EnhancedJsonConfig, ConfigValidationError
from .xml_override_engine import XMLOverrideEngine, XMLOverrideEngineError
from .xpath_resolver import XPathResolver, XPathResolverError
from .choice_resolver import ChoiceResolver, ChoiceResolverError
from .template_engine import TemplateEngine, TemplateEngineError


class EnhancedXMLGeneratorError(Exception):
    """Raised when enhanced XML generation fails."""
    pass


class GenerationResult:
    """Container for generation results with metadata."""
    
    def __init__(self, xml_content: str, metadata: Dict[str, Any]):
        self.xml_content = xml_content
        self.metadata = metadata
        self.timestamp = datetime.now()
    
    def __str__(self) -> str:
        return self.xml_content
    
    def get_summary(self) -> Dict[str, Any]:
        """Get generation summary."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'xml_length': len(self.xml_content),
            'lines': len(self.xml_content.splitlines()),
            'metadata': self.metadata
        }


class EnhancedXMLGenerator:
    """
    Enhanced XML Generator with JSON configuration support.
    
    This class serves as the main integration point for the enhanced JSON
    configuration system. It combines the proven base XMLGenerator with
    advanced configuration capabilities including choice resolution,
    template processing, and sophisticated override management.
    
    Key Features:
    - Preserves reliability of base XML generation
    - Adds powerful JSON configuration capabilities
    - Graceful fallback to base generation on errors
    - Comprehensive error handling and logging
    - Detailed generation metadata and debugging info
    """
    
    def __init__(self, xsd_path: Union[str, Path], json_config_data: Optional[Union[Dict, str, Path]] = None):
        """
        Initialize Enhanced XML Generator.
        
        Args:
            xsd_path: Path to XSD schema file
            json_config_data: Enhanced JSON configuration (dict, JSON string, or file path)
            
        Raises:
            EnhancedXMLGeneratorError: If initialization fails
        """
        self.xsd_path = Path(xsd_path)
        self.logger = logging.getLogger(__name__)
        
        # Initialize base generator (always works)
        try:
            self.base_generator = XMLGenerator(str(self.xsd_path))
            self.logger.info(f"Base XMLGenerator initialized for {self.xsd_path.name}")
        except Exception as e:
            raise EnhancedXMLGeneratorError(f"Failed to initialize base generator: {e}") from e
        
        # Initialize enhanced components (optional)
        self.enhanced_config: Optional[EnhancedJsonConfig] = None
        self.xpath_resolver: Optional[XPathResolver] = None
        self.choice_resolver: Optional[ChoiceResolver] = None
        self.template_engine: Optional[TemplateEngine] = None
        self.override_engine: Optional[XMLOverrideEngine] = None
        
        # Generation state
        self.last_result: Optional[GenerationResult] = None
        self.generation_errors: List[str] = []
        self.fallback_used = False
        
        # Initialize enhanced configuration if provided
        if json_config_data:
            self._initialize_enhanced_config(json_config_data)
    
    def _initialize_enhanced_config(self, json_config_data: Union[Dict, str, Path]) -> None:
        """Initialize enhanced configuration components."""
        try:
            # Parse enhanced JSON configuration
            self.enhanced_config = EnhancedJsonConfig(json_config_data)
            self.logger.info(f"Enhanced JSON config loaded: {self.enhanced_config.schema}")
            
            # Initialize supporting components
            self.xpath_resolver = XPathResolver(
                namespace_map=self.enhanced_config.namespaces.get('prefixes', {})
            )
            
            self.choice_resolver = ChoiceResolver(
                enhanced_config=self.enhanced_config,
                xpath_resolver=self.xpath_resolver
            )
            
            self.template_engine = TemplateEngine(
                enhanced_config=self.enhanced_config
            )
            
            self.override_engine = XMLOverrideEngine(
                enhanced_config=self.enhanced_config
            )
            
            self.logger.info("Enhanced configuration components initialized successfully")
            
        except ConfigValidationError as e:
            self.logger.error(f"Configuration validation failed: {e}")
            self.generation_errors.append(f"Config validation: {e}")
            self._reset_enhanced_components()
            
        except Exception as e:
            self.logger.error(f"Failed to initialize enhanced config: {e}")
            self.generation_errors.append(f"Enhanced config initialization: {e}")
            self._reset_enhanced_components()
    
    def _reset_enhanced_components(self) -> None:
        """Reset enhanced components to None (fallback to base generation)."""
        self.enhanced_config = None
        self.xpath_resolver = None
        self.choice_resolver = None
        self.template_engine = None
        self.override_engine = None
    
    def generate_xml(self, 
                    mode: Optional[str] = None,
                    additional_choices: Optional[Dict[str, str]] = None,
                    additional_repeats: Optional[Dict[str, int]] = None) -> GenerationResult:
        """
        Generate XML with enhanced configuration support.
        
        Args:
            mode: Generation mode override ('complete', 'minimal', 'custom')
            additional_choices: Additional choice selections (UI overrides)
            additional_repeats: Additional repeat counts (UI overrides)
            
        Returns:
            GenerationResult with XML content and metadata
            
        Raises:
            EnhancedXMLGeneratorError: If generation fails completely
        """
        self.generation_errors.clear()
        self.fallback_used = False
        
        try:
            if self.enhanced_config and self.override_engine:
                # Enhanced generation path
                return self._generate_enhanced_xml(mode, additional_choices, additional_repeats)
            else:
                # Base generation path
                return self._generate_base_xml(mode, additional_choices, additional_repeats)
                
        except Exception as e:
            self.logger.error(f"XML generation failed: {e}")
            
            # Try fallback to base generation
            if not self.fallback_used and self.enhanced_config:
                self.logger.info("Attempting fallback to base generation")
                try:
                    return self._generate_base_xml(mode, additional_choices, additional_repeats)
                except Exception as fallback_error:
                    self.logger.error(f"Fallback generation also failed: {fallback_error}")
                    raise EnhancedXMLGeneratorError(f"Both enhanced and fallback generation failed: {e}") from e
            else:
                raise EnhancedXMLGeneratorError(f"XML generation failed: {e}") from e
    
    def _generate_enhanced_xml(self, 
                              mode: Optional[str],
                              additional_choices: Optional[Dict[str, str]],
                              additional_repeats: Optional[Dict[str, int]]) -> GenerationResult:
        """Generate XML using enhanced configuration."""
        start_time = datetime.now()
        
        # Determine generation mode
        effective_mode = mode or self.enhanced_config.mode
        
        # Step 1: Resolve choices for base generator
        base_choices = self._resolve_base_choices(additional_choices)
        
        # Step 2: Resolve repeat counts for base generator
        base_repeats = self._resolve_base_repeats(additional_repeats)
        
        # Step 3: Generate base XML using proven XMLGenerator
        try:
            base_xml = self.base_generator.generate_dummy_xml_with_options(
                selected_choices=base_choices,
                unbounded_counts=base_repeats,
                generation_mode=effective_mode
            )
            self.logger.info("Base XML generated successfully")
        except Exception as e:
            raise EnhancedXMLGeneratorError(f"Base XML generation failed: {e}") from e
        
        # Step 4: Apply enhanced overrides
        try:
            enhanced_xml = self.override_engine.apply_overrides(base_xml)
            self.logger.info("Enhanced overrides applied successfully")
        except XMLOverrideEngineError as e:
            self.logger.warning(f"Override application failed, using base XML: {e}")
            self.generation_errors.append(f"Override application: {e}")
            enhanced_xml = base_xml
        
        # Step 5: Apply choice-based element removal
        try:
            if self.choice_resolver:
                xml_tree = ET.fromstring(enhanced_xml)
                xml_tree_with_choices = self.choice_resolver.apply_choices_to_xml(ET.ElementTree(xml_tree))
                enhanced_xml = ET.tostring(xml_tree_with_choices.getroot(), encoding='unicode')
                self.logger.info("Choice-based element removal applied")
        except Exception as e:
            self.logger.warning(f"Choice application failed: {e}")
            self.generation_errors.append(f"Choice application: {e}")
        
        # Step 6: Create result with metadata
        generation_time = datetime.now() - start_time
        metadata = self._create_enhanced_metadata(
            mode=effective_mode,
            base_choices=base_choices,
            base_repeats=base_repeats,
            generation_time=generation_time
        )
        
        result = GenerationResult(enhanced_xml, metadata)
        self.last_result = result
        
        return result
    
    def _generate_base_xml(self,
                          mode: Optional[str],
                          additional_choices: Optional[Dict[str, str]],
                          additional_repeats: Optional[Dict[str, int]]) -> GenerationResult:
        """Generate XML using base generator only."""
        self.fallback_used = True
        start_time = datetime.now()
        
        # Use provided choices and repeats or defaults
        choices = additional_choices or {}
        repeats = additional_repeats or {}
        effective_mode = mode or 'complete'
        
        try:
            xml_content = self.base_generator.generate_dummy_xml_with_options(
                selected_choices=choices,
                unbounded_counts=repeats,
                generation_mode=effective_mode
            )
            self.logger.info("Base XML generated successfully (fallback mode)")
        except Exception as e:
            raise EnhancedXMLGeneratorError(f"Base XML generation failed: {e}") from e
        
        # Create result with basic metadata
        generation_time = datetime.now() - start_time
        metadata = self._create_base_metadata(
            mode=effective_mode,
            choices=choices,
            repeats=repeats,
            generation_time=generation_time
        )
        
        result = GenerationResult(xml_content, metadata)
        self.last_result = result
        
        return result
    
    def _resolve_base_choices(self, additional_choices: Optional[Dict[str, str]]) -> Dict[str, str]:
        """Resolve choices for base XMLGenerator."""
        choices = {}
        
        # Add choices from enhanced config
        if self.choice_resolver:
            try:
                config_choices = self.choice_resolver.get_base_generator_choices()
                choices.update(config_choices)
                self.logger.debug(f"Added {len(config_choices)} choices from config")
            except Exception as e:
                self.logger.warning(f"Failed to resolve config choices: {e}")
                self.generation_errors.append(f"Choice resolution: {e}")
        
        # Add additional choices (UI overrides)
        if additional_choices:
            choices.update(additional_choices)
            self.logger.debug(f"Added {len(additional_choices)} additional choices")
        
        return choices
    
    def _resolve_base_repeats(self, additional_repeats: Optional[Dict[str, int]]) -> Dict[str, int]:
        """Resolve repeat counts for base XMLGenerator."""
        repeats = {}
        
        # Add repeats from enhanced config
        if self.enhanced_config:
            config_repeats = self.enhanced_config.get_base_repeat_counts()
            repeats.update(config_repeats)
            self.logger.debug(f"Added {len(config_repeats)} repeat counts from config")
        
        # Add additional repeats (UI overrides)
        if additional_repeats:
            repeats.update(additional_repeats)
            self.logger.debug(f"Added {len(additional_repeats)} additional repeat counts")
        
        return repeats
    
    def _create_enhanced_metadata(self,
                                 mode: str,
                                 base_choices: Dict[str, str],
                                 base_repeats: Dict[str, int],
                                 generation_time) -> Dict[str, Any]:
        """Create comprehensive metadata for enhanced generation."""
        metadata = {
            'generation_type': 'enhanced',
            'mode': mode,
            'schema': str(self.xsd_path),
            'config_schema': self.enhanced_config.schema if self.enhanced_config else None,
            'generation_time_ms': generation_time.total_seconds() * 1000,
            'fallback_used': self.fallback_used,
            'errors': self.generation_errors.copy(),
            
            # Choice information
            'choices': {
                'base_choices': base_choices,
                'choice_summary': self.choice_resolver.get_choice_summary() if self.choice_resolver else {}
            },
            
            # Template information
            'templates': {
                'template_summary': self.template_engine.get_template_summary() if self.template_engine else {}
            },
            
            # Override information
            'overrides': {
                'override_summary': self.override_engine.get_override_summary() if self.override_engine else {}
            },
            
            # Base generator information
            'base': {
                'choices_used': base_choices,
                'repeats_used': base_repeats
            }
        }
        
        return metadata
    
    def _create_base_metadata(self,
                             mode: str,
                             choices: Dict[str, str],
                             repeats: Dict[str, int],
                             generation_time) -> Dict[str, Any]:
        """Create basic metadata for base generation."""
        return {
            'generation_type': 'base',
            'mode': mode,
            'schema': str(self.xsd_path),
            'generation_time_ms': generation_time.total_seconds() * 1000,
            'fallback_used': self.fallback_used,
            'errors': self.generation_errors.copy(),
            'base': {
                'choices_used': choices,
                'repeats_used': repeats
            }
        }
    
    def validate_configuration(self) -> Dict[str, List[str]]:
        """
        Validate the enhanced configuration.
        
        Returns:
            Dictionary of validation results by component
        """
        validation_results = {
            'config': [],
            'choices': [],
            'templates': [],
            'overall': []
        }
        
        if not self.enhanced_config:
            validation_results['overall'].append("No enhanced configuration loaded")
            return validation_results
        
        try:
            # Validate enhanced config
            self.enhanced_config.validate()
            validation_results['config'].append("Configuration syntax valid")
        except ConfigValidationError as e:
            validation_results['config'].append(f"Configuration error: {e}")
        
        # Validate templates
        if self.template_engine:
            template_errors = self.template_engine.validate_templates()
            if template_errors:
                validation_results['templates'].extend(template_errors)
            else:
                validation_results['templates'].append("All templates valid")
        
        # Validate choices (would need schema analysis for complete validation)
        if self.choice_resolver:
            choice_summary = self.choice_resolver.get_choice_summary()
            total_choices = choice_summary.get('total_resolved', 0)
            if total_choices > 0:
                validation_results['choices'].append(f"{total_choices} choices configured")
            else:
                validation_results['choices'].append("No choices configured")
        
        # Overall status
        error_count = sum(len(errors) for errors in validation_results.values() 
                         if any('error' in error.lower() for error in errors))
        if error_count == 0:
            validation_results['overall'].append("Configuration validation successful")
        else:
            validation_results['overall'].append(f"Configuration has {error_count} validation errors")
        
        return validation_results
    
    def get_generation_summary(self) -> Dict[str, Any]:
        """Get summary of last generation for debugging."""
        if not self.last_result:
            return {'status': 'No generation performed yet'}
        
        summary = self.last_result.get_summary()
        summary.update({
            'enhanced_config_loaded': self.enhanced_config is not None,
            'components_initialized': {
                'xpath_resolver': self.xpath_resolver is not None,
                'choice_resolver': self.choice_resolver is not None,
                'template_engine': self.template_engine is not None,
                'override_engine': self.override_engine is not None
            },
            'generation_errors': self.generation_errors,
            'fallback_used': self.fallback_used
        })
        
        return summary
    
    def supports_enhanced_features(self) -> bool:
        """Check if enhanced features are available."""
        return self.enhanced_config is not None and self.override_engine is not None
    
    def get_config_schema(self) -> Optional[str]:
        """Get the schema file specified in configuration."""
        return self.enhanced_config.schema if self.enhanced_config else None
    
    def __repr__(self) -> str:
        """String representation of enhanced generator."""
        enhanced_status = "enabled" if self.enhanced_config else "disabled"
        return f"EnhancedXMLGenerator(schema='{self.xsd_path.name}', enhanced={enhanced_status})"