"""
Enhanced Configuration UI

This module provides the new user interface for the enhanced JSON configuration
system. It replaces the old Advanced Config tab with a modern, intuitive interface
that supports all the enhanced features including templates, choices, patterns,
and sophisticated override capabilities.

Features:
- Template-based data management UI
- Choice resolution configuration
- Pattern-based override setup
- XPath-aware value assignment
- Real-time validation and preview
- Integration with EnhancedXMLGenerator
"""

import streamlit as st
import json
import io
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import traceback

from utils.enhanced_xml_generator import EnhancedXMLGenerator, GenerationResult
from utils.enhanced_json_config import EnhancedJsonConfig, ConfigValidationError


class EnhancedConfigUI:
    """
    Enhanced Configuration User Interface Manager.
    
    Provides a comprehensive UI for creating and managing enhanced JSON
    configurations with support for all advanced features.
    """
    
    def __init__(self):
        """Initialize the enhanced config UI."""
        self.temp_file_path = None
        self.schema_info = None
        
    def render_enhanced_config_tab(self, temp_file_path: str, schema_analyzer, config_manager):
        """
        Render the new Enhanced Configuration tab.
        
        Args:
            temp_file_path: Path to the temporary XSD file
            schema_analyzer: Schema analyzer instance
            config_manager: Configuration manager instance
        """
        self.temp_file_path = temp_file_path
        
        st.markdown("### 🚀 Enhanced Configuration")
        st.markdown("Create powerful XML configurations with templates, choices, patterns, and advanced overrides.")
        
        # Quick schema analysis for context
        with st.spinner("Analyzing schema for enhanced features..."):
            analysis = self._analyze_schema_for_enhanced_features(schema_analyzer)
            if not analysis['success']:
                st.error(f"Schema analysis failed: {analysis['error']}")
                return
                
        self.schema_info = analysis.get('schema_info', {})
        
        # Main UI layout with tabs for different configuration aspects
        config_tabs = st.tabs([
            "🎯 **Quick Setup**", 
            "📝 **Values & Patterns**", 
            "🔄 **Choices & Logic**", 
            "📊 **Templates & Data**",
            "⚙️ **Advanced Settings**",
            "🧪 **Preview & Test**"
        ])
        
        with config_tabs[0]:
            self._render_quick_setup_tab()
            
        with config_tabs[1]:
            self._render_values_patterns_tab()
            
        with config_tabs[2]:
            self._render_choices_logic_tab()
            
        with config_tabs[3]:
            self._render_templates_data_tab()
            
        with config_tabs[4]:
            self._render_advanced_settings_tab()
            
        with config_tabs[5]:
            self._render_preview_test_tab()
    
    def _analyze_schema_for_enhanced_features(self, schema_analyzer) -> Dict[str, Any]:
        """Analyze schema to identify enhanced configuration opportunities."""
        try:
            # Use existing schema analysis function
            # Import here to avoid circular imports
            import sys
            import importlib
            
            # Try to import the analyze_xsd_schema function
            try:
                xsd_workflow = importlib.import_module('ui.xsd_workflow')
                analyze_xsd_schema = getattr(xsd_workflow, 'analyze_xsd_schema')
                analysis = analyze_xsd_schema(self.temp_file_path, schema_analyzer)
            except (ImportError, AttributeError):
                # Fallback: create a basic analysis structure
                analysis = {
                    'success': True,
                    'schema_info': {
                        'elements_count': 0,
                        'types_count': 0,
                        'choice_elements': [],
                        'unbounded_elements': [],
                        'root_elements': [],
                        'namespace_info': {},
                        'all_elements': []
                    }
                }
            
            if analysis['success']:
                schema_info = analysis['schema_info']
                
                # Enhance with additional analysis for our features
                enhanced_info = {
                    'elements_count': schema_info.get('elements_count', 0),
                    'types_count': schema_info.get('types_count', 0),
                    'choice_elements': schema_info.get('choice_elements', []),
                    'unbounded_elements': schema_info.get('unbounded_elements', []),
                    'root_elements': schema_info.get('root_elements', []),
                    'namespace_info': schema_info.get('namespace_info', {}),
                    
                    # Enhanced analysis for our system
                    'recommended_templates': self._identify_template_opportunities(schema_info),
                    'recommended_patterns': self._identify_pattern_opportunities(schema_info),
                    'suggested_choices': self._identify_choice_opportunities(schema_info)
                }
                
                analysis['schema_info'] = enhanced_info
                
            return analysis
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _identify_template_opportunities(self, schema_info: Dict) -> List[Dict]:
        """Identify elements that would benefit from template data."""
        opportunities = []
        
        # Look for common patterns that suggest template usage
        template_indicators = [
            'passenger', 'traveler', 'customer', 'person', 'user',
            'address', 'contact', 'booking', 'reservation', 'flight',
            'hotel', 'payment', 'card', 'account'
        ]
        
        elements = schema_info.get('all_elements', [])
        for element in elements:
            element_name = element.get('name', '').lower()
            
            for indicator in template_indicators:
                if indicator in element_name:
                    opportunities.append({
                        'element': element['name'],
                        'type': indicator,
                        'description': f"Consider using {indicator} template for consistent data"
                    })
                    break
        
        return opportunities[:10]  # Limit to top 10 suggestions
    
    def _identify_pattern_opportunities(self, schema_info: Dict) -> List[Dict]:
        """Identify elements that would benefit from pattern-based overrides."""
        opportunities = []
        
        # Look for common patterns
        pattern_indicators = {
            'id': 'Unique identifiers (use generate:uuid)',
            'code': 'Codes and references (use generate:code)',
            'date': 'Date fields (use generate:date)',
            'time': 'Time fields (use generate:time)', 
            'amount': 'Monetary amounts (use generate:currency)',
            'price': 'Prices (use generate:currency)',
            'email': 'Email addresses (use generate:email)',
            'phone': 'Phone numbers (use generate:phone)'
        }
        
        elements = schema_info.get('all_elements', [])
        for element in elements:
            element_name = element.get('name', '').lower()
            
            for pattern, description in pattern_indicators.items():
                if pattern in element_name:
                    opportunities.append({
                        'pattern': f"*{pattern.title()}*",
                        'description': description,
                        'example_element': element['name']
                    })
                    break
        
        return opportunities[:8]  # Limit to top 8 suggestions
    
    def _identify_choice_opportunities(self, schema_info: Dict) -> List[Dict]:
        """Identify choice elements for configuration."""
        opportunities = []
        
        choice_elements = schema_info.get('choice_elements', [])
        for choice in choice_elements:
            opportunities.append({
                'element': choice.get('name', 'Unknown'),
                'options': choice.get('options', []),
                'description': f"Choice between {len(choice.get('options', []))} options"
            })
        
        return opportunities
    
    def _render_quick_setup_tab(self):
        """Render quick setup tab for getting started fast."""
        st.markdown("#### 🎯 Quick Configuration Setup")
        st.markdown("Get started quickly with smart defaults and schema-based suggestions.")
        
        # Initialize enhanced config in session state
        if 'enhanced_config_data' not in st.session_state:
            st.session_state['enhanced_config_data'] = self._get_default_enhanced_config()
        
        # Configuration mode selection
        col1, col2 = st.columns([1, 1])
        
        with col1:
            config_mode = st.selectbox(
                "Configuration Style",
                ["Smart Default", "Minimal Setup", "Advanced Custom", "Template-Based"],
                help="Choose how comprehensive you want your configuration to be"
            )
        
        with col2:
            if st.button("🎲 **Auto-Generate Config**", help="Create configuration based on schema analysis"):
                self._auto_generate_config(config_mode)
        
        # Display current configuration overview
        config_data = st.session_state.get('enhanced_config_data', {})
        
        if config_data:
            st.markdown("#### 📊 Current Configuration Overview")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                values_count = len(config_data.get('values', {}))
                st.metric("Values", values_count, help="Direct value assignments")
            
            with col2:
                patterns_count = len(config_data.get('patterns', {}))
                st.metric("Patterns", patterns_count, help="Pattern-based overrides")
            
            with col3:
                choices_count = len(config_data.get('choices', {}))
                st.metric("Choices", choices_count, help="Choice configurations")
            
            with col4:
                templates_count = len(config_data.get('templates', {}))
                st.metric("Templates", templates_count, help="Template definitions")
        
        # Smart suggestions based on schema analysis
        if self.schema_info:
            self._render_smart_suggestions()
    
    def _render_smart_suggestions(self):
        """Render smart configuration suggestions based on schema analysis."""
        st.markdown("#### 💡 Smart Suggestions")
        st.markdown("Based on your schema analysis, here are recommended configurations:")
        
        # Template suggestions
        template_opportunities = self.schema_info.get('recommended_templates', [])
        if template_opportunities:
            with st.expander("📊 **Template Suggestions**", expanded=False):
                for opportunity in template_opportunities[:5]:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**{opportunity['element']}**: {opportunity['description']}")
                    with col2:
                        if st.button(f"Add", key=f"add_template_{opportunity['element']}"):
                            self._add_suggested_template(opportunity)
        
        # Pattern suggestions  
        pattern_opportunities = self.schema_info.get('recommended_patterns', [])
        if pattern_opportunities:
            with st.expander("🎯 **Pattern Suggestions**", expanded=False):
                for opportunity in pattern_opportunities[:5]:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**{opportunity['pattern']}**: {opportunity['description']}")
                        if 'example_element' in opportunity:
                            st.caption(f"Example: {opportunity['example_element']}")
                    with col2:
                        if st.button(f"Add", key=f"add_pattern_{opportunity['pattern']}"):
                            self._add_suggested_pattern(opportunity)
        
        # Choice suggestions
        choice_opportunities = self.schema_info.get('suggested_choices', [])
        if choice_opportunities:
            with st.expander("🔄 **Choice Suggestions**", expanded=False):
                for opportunity in choice_opportunities[:3]:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**{opportunity['element']}**: {opportunity['description']}")
                        if opportunity.get('options'):
                            st.caption(f"Options: {', '.join(opportunity['options'][:3])}...")
                    with col2:
                        if st.button(f"Configure", key=f"config_choice_{opportunity['element']}"):
                            self._configure_suggested_choice(opportunity)
    
    def _render_values_patterns_tab(self):
        """Render values and patterns configuration tab."""
        st.markdown("#### 📝 Values & Patterns Configuration")
        st.markdown("Configure direct value assignments and pattern-based overrides.")
        
        # Initialize if needed
        if 'enhanced_config_data' not in st.session_state:
            st.session_state['enhanced_config_data'] = self._get_default_enhanced_config()
        
        config_data = st.session_state['enhanced_config_data']
        
        # Values section
        st.markdown("##### 🎯 Direct Value Assignments")
        st.markdown("Assign specific values to elements using exact paths or simple names.")
        
        values_expander = st.expander("**Manage Values**", expanded=True)
        with values_expander:
            self._render_values_editor(config_data)
        
        # Patterns section
        st.markdown("##### 🔍 Pattern-Based Overrides")
        st.markdown("Use wildcards and patterns to assign values to multiple elements at once.")
        
        patterns_expander = st.expander("**Manage Patterns**", expanded=True)
        with patterns_expander:
            self._render_patterns_editor(config_data)
    
    def _render_values_editor(self, config_data: Dict):
        """Render the values editor interface."""
        values = config_data.get('values', {})
        
        # Add new value
        st.markdown("**Add New Value Assignment:**")
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            new_path = st.text_input(
                "Element Path",
                placeholder="/Root/Element or Element.Child or SimpleElement",
                help="Absolute path, dot notation, or simple element name"
            )
        
        with col2:
            new_value = st.text_input(
                "Value",
                placeholder="Static value or generate:uuid",
                help="Static value or generator function"
            )
        
        with col3:
            st.write("")  # Spacing
            st.write("")  # Spacing
            if st.button("➕ Add") and new_path and new_value:
                values[new_path] = new_value
                config_data['values'] = values
                st.session_state['enhanced_config_data'] = config_data
                st.rerun()
        
        # Display existing values
        if values:
            st.markdown("**Current Value Assignments:**")
            for i, (path, value) in enumerate(values.items()):
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    edited_path = st.text_input(f"Path", value=path, key=f"value_path_{i}")
                
                with col2:
                    edited_value = st.text_input(f"Value", value=value, key=f"value_value_{i}")
                
                with col3:
                    st.write("")
                    st.write("")
                    if st.button("🗑️", key=f"delete_value_{i}", help="Delete this value"):
                        del values[path]
                        config_data['values'] = values
                        st.session_state['enhanced_config_data'] = config_data
                        st.rerun()
                
                # Update if changed
                if edited_path != path or edited_value != value:
                    if path in values:
                        del values[path]
                    values[edited_path] = edited_value
                    config_data['values'] = values
                    st.session_state['enhanced_config_data'] = config_data
        else:
            st.info("No value assignments configured. Add one above to get started.")
    
    def _render_patterns_editor(self, config_data: Dict):
        """Render the patterns editor interface."""
        patterns = config_data.get('patterns', {})
        
        # Add new pattern
        st.markdown("**Add New Pattern Override:**")
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            new_pattern = st.text_input(
                "Pattern",
                placeholder="*ID, *Amount, *@Currency",
                help="Use * as wildcard. @ for attributes"
            )
        
        with col2:
            new_pattern_value = st.text_input(
                "Value",
                placeholder="generate:uuid, generate:currency",
                help="Value or generator function"
            )
        
        with col3:
            st.write("")
            st.write("")
            if st.button("➕ Add") and new_pattern and new_pattern_value:
                patterns[new_pattern] = new_pattern_value
                config_data['patterns'] = patterns
                st.session_state['enhanced_config_data'] = config_data
                st.rerun()
        
        # Display existing patterns
        if patterns:
            st.markdown("**Current Pattern Overrides:**")
            for i, (pattern, value) in enumerate(patterns.items()):
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    edited_pattern = st.text_input(f"Pattern", value=pattern, key=f"pattern_pattern_{i}")
                
                with col2:
                    edited_pattern_value = st.text_input(f"Value", value=value, key=f"pattern_value_{i}")
                
                with col3:
                    st.write("")
                    st.write("")
                    if st.button("🗑️", key=f"delete_pattern_{i}", help="Delete this pattern"):
                        del patterns[pattern]
                        config_data['patterns'] = patterns
                        st.session_state['enhanced_config_data'] = config_data
                        st.rerun()
                
                # Update if changed
                if edited_pattern != pattern or edited_pattern_value != value:
                    if pattern in patterns:
                        del patterns[pattern]
                    patterns[edited_pattern] = edited_pattern_value
                    config_data['patterns'] = patterns
                    st.session_state['enhanced_config_data'] = config_data
        else:
            st.info("No pattern overrides configured. Add one above to get started.")
    
    def _render_choices_logic_tab(self):
        """Render choices and logic configuration tab."""
        st.markdown("#### 🔄 Choices & Logic Configuration")
        st.markdown("Configure choice selections and conditional logic for dynamic XML generation.")
        
        if 'enhanced_config_data' not in st.session_state:
            st.session_state['enhanced_config_data'] = self._get_default_enhanced_config()
        
        config_data = st.session_state['enhanced_config_data']
        
        # Display available choices from schema
        if self.schema_info and self.schema_info.get('choice_elements'):
            st.markdown("##### 📋 Available Choices from Schema")
            choice_elements = self.schema_info['choice_elements']
            
            for choice in choice_elements[:5]:  # Show first 5
                with st.expander(f"Choice: **{choice.get('name', 'Unknown')}**"):
                    options = choice.get('options', [])
                    if options:
                        st.write(f"**Available options:** {', '.join(options)}")
                        
                        # Quick setup for this choice
                        col1, col2 = st.columns([2, 1])
                        with col1:
                            selected_option = st.selectbox(
                                "Select Option",
                                [""] + options,
                                key=f"quick_choice_{choice['name']}"
                            )
                        with col2:
                            st.write("")
                            if st.button("Configure", key=f"config_quick_choice_{choice['name']}"):
                                if selected_option:
                                    choices = config_data.get('choices', {})
                                    choices[choice['name']] = selected_option
                                    config_data['choices'] = choices
                                    st.session_state['enhanced_config_data'] = config_data
                                    st.success(f"Configured {choice['name']} → {selected_option}")
        
        # Manual choices configuration
        st.markdown("##### ⚙️ Manual Choice Configuration")
        choices_expander = st.expander("**Manage Choices**", expanded=True)
        with choices_expander:
            self._render_choices_editor(config_data)
    
    def _render_choices_editor(self, config_data: Dict):
        """Render the choices editor interface."""
        choices = config_data.get('choices', {})
        
        # Add new choice
        st.markdown("**Add New Choice Configuration:**")
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            new_choice_element = st.text_input(
                "Choice Element",
                placeholder="ChoiceElementName or /Path/To/Choice",
                help="Element name or path containing the choice"
            )
        
        with col2:
            new_choice_selection = st.text_input(
                "Selected Option",
                placeholder="OptionToSelect",
                help="The option to select for this choice"
            )
        
        with col3:
            st.write("")
            st.write("")
            if st.button("➕ Add") and new_choice_element and new_choice_selection:
                choices[new_choice_element] = new_choice_selection
                config_data['choices'] = choices
                st.session_state['enhanced_config_data'] = config_data
                st.rerun()
        
        # Display existing choices
        if choices:
            st.markdown("**Current Choice Configurations:**")
            for i, (element, selection) in enumerate(choices.items()):
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    edited_element = st.text_input(f"Element", value=element, key=f"choice_element_{i}")
                
                with col2:
                    edited_selection = st.text_input(f"Selection", value=selection, key=f"choice_selection_{i}")
                
                with col3:
                    st.write("")
                    st.write("")
                    if st.button("🗑️", key=f"delete_choice_{i}", help="Delete this choice"):
                        del choices[element]
                        config_data['choices'] = choices
                        st.session_state['enhanced_config_data'] = config_data
                        st.rerun()
                
                # Update if changed
                if edited_element != element or edited_selection != selection:
                    if element in choices:
                        del choices[element]
                    choices[edited_element] = edited_selection
                    config_data['choices'] = choices
                    st.session_state['enhanced_config_data'] = config_data
        else:
            st.info("No choice configurations set. Add one above to get started.")
    
    def _render_templates_data_tab(self):
        """Render templates and data configuration tab."""
        st.markdown("#### 📊 Templates & Data Configuration")
        st.markdown("Define template-based data for consistent related information.")
        
        if 'enhanced_config_data' not in st.session_state:
            st.session_state['enhanced_config_data'] = self._get_default_enhanced_config()
        
        config_data = st.session_state['enhanced_config_data']
        
        # Quick template creation
        st.markdown("##### 🚀 Quick Template Creation")
        col1, col2 = st.columns([1, 1])
        
        with col1:
            template_type = st.selectbox(
                "Template Type",
                ["Custom", "Passenger", "Address", "Payment", "Flight", "Hotel"],
                help="Choose a pre-built template or create custom"
            )
        
        with col2:
            if st.button("🎲 **Create Template**", help=f"Create {template_type} template"):
                self._create_quick_template(config_data, template_type)
        
        # Template editor
        st.markdown("##### ⚙️ Template Management")
        templates_expander = st.expander("**Manage Templates**", expanded=True)
        with templates_expander:
            self._render_templates_editor(config_data)
    
    def _render_templates_editor(self, config_data: Dict):
        """Render the templates editor interface."""
        templates = config_data.get('templates', {})
        
        # Add new template
        st.markdown("**Add New Template:**")
        
        with st.form("new_template_form"):
            col1, col2 = st.columns([1, 1])
            
            with col1:
                new_template_name = st.text_input("Template Name", placeholder="passenger_info")
            
            with col2:
                cycle_strategy = st.selectbox("Cycling Strategy", 
                    ["sequential", "random", "once"], 
                    help="How to cycle through template data")
            
            template_data_text = st.text_area(
                "Template Data (JSON Array)",
                placeholder='[{"name": "John Doe", "email": "john@example.com"}, {"name": "Jane Smith", "email": "jane@example.com"}]',
                height=200,
                help="JSON array of data objects"
            )
            
            if st.form_submit_button("➕ Add Template"):
                if new_template_name and template_data_text:
                    try:
                        template_data = json.loads(template_data_text)
                        if not isinstance(template_data, list):
                            st.error("Template data must be a JSON array")
                        else:
                            templates[new_template_name] = {
                                "data": template_data,
                                "cycle": cycle_strategy
                            }
                            config_data['templates'] = templates
                            st.session_state['enhanced_config_data'] = config_data
                            st.success(f"Template '{new_template_name}' added!")
                            st.rerun()
                    except json.JSONDecodeError as e:
                        st.error(f"Invalid JSON: {e}")
        
        # Display existing templates
        if templates:
            st.markdown("**Current Templates:**")
            for template_name, template_config in templates.items():
                with st.expander(f"Template: **{template_name}**"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        data = template_config.get('data', [])
                        st.write(f"**Data items:** {len(data)}")
                        st.write(f"**Cycling:** {template_config.get('cycle', 'sequential')}")
                        
                        if data:
                            st.write("**Sample data:**")
                            st.json(data[0] if len(data) > 0 else {})
                    
                    with col2:
                        if st.button("🗑️ Delete", key=f"delete_template_{template_name}"):
                            del templates[template_name]
                            config_data['templates'] = templates
                            st.session_state['enhanced_config_data'] = config_data
                            st.rerun()
        else:
            st.info("No templates configured. Add one above to get started.")
    
    def _render_advanced_settings_tab(self):
        """Render advanced settings configuration tab."""
        st.markdown("#### ⚙️ Advanced Settings")
        st.markdown("Configure namespaces, generation settings, and other advanced options.")
        
        if 'enhanced_config_data' not in st.session_state:
            st.session_state['enhanced_config_data'] = self._get_default_enhanced_config()
        
        config_data = st.session_state['enhanced_config_data']
        
        # Generation settings
        st.markdown("##### 🎛️ Generation Settings")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            mode = st.selectbox(
                "Generation Mode",
                ["complete", "minimal", "custom"],
                index=0 if config_data.get('mode') == 'complete' else 1 if config_data.get('mode') == 'minimal' else 2,
                help="How comprehensive the generated XML should be"
            )
            config_data['mode'] = mode
        
        with col2:
            seed = st.number_input(
                "Random Seed",
                value=config_data.get('seed', 12345),
                help="Seed for deterministic generation"
            )
            config_data['seed'] = seed
        
        # Namespace configuration
        st.markdown("##### 🏷️ Namespace Configuration")
        
        with st.expander("**Namespace Settings**", expanded=False):
            namespaces = config_data.get('namespaces', {})
            
            # Default namespace
            default_ns = st.text_input(
                "Default Namespace",
                value=namespaces.get('default', ''),
                help="Default namespace URI"
            )
            if default_ns:
                namespaces['default'] = default_ns
            
            # Namespace prefixes
            prefixes = namespaces.get('prefixes', {})
            
            st.markdown("**Namespace Prefixes:**")
            # Add new prefix
            col1, col2, col3 = st.columns([1, 2, 1])
            with col1:
                new_prefix = st.text_input("Prefix", placeholder="ns", key="new_ns_prefix")
            with col2:
                new_uri = st.text_input("URI", placeholder="http://example.com/ns", key="new_ns_uri")
            with col3:
                st.write("")
                st.write("")
                if st.button("➕ Add") and new_prefix and new_uri:
                    prefixes[new_prefix] = new_uri
                    namespaces['prefixes'] = prefixes
                    config_data['namespaces'] = namespaces
                    st.rerun()
            
            # Display existing prefixes
            if prefixes:
                for i, (prefix, uri) in enumerate(prefixes.items()):
                    col1, col2, col3 = st.columns([1, 2, 1])
                    with col1:
                        st.text_input("", value=prefix, disabled=True, key=f"prefix_{i}")
                    with col2:
                        st.text_input("", value=uri, disabled=True, key=f"uri_{i}")
                    with col3:
                        if st.button("🗑️", key=f"delete_ns_{i}"):
                            del prefixes[prefix]
                            namespaces['prefixes'] = prefixes
                            config_data['namespaces'] = namespaces
                            st.rerun()
        
        # Update session state
        st.session_state['enhanced_config_data'] = config_data
    
    def _render_preview_test_tab(self):
        """Render preview and test tab with XML generation."""
        st.markdown("#### 🧪 Preview & Test")
        st.markdown("Preview your configuration and generate XML to test the results.")
        
        config_data = st.session_state.get('enhanced_config_data', {})
        
        # Configuration preview
        st.markdown("##### 📋 Configuration Preview")
        
        with st.expander("**View Complete Configuration**", expanded=False):
            st.json(config_data)
        
        # Configuration validation
        st.markdown("##### ✅ Validation & Testing")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            if st.button("🔍 **Validate Configuration**", use_container_width=True):
                self._validate_enhanced_config(config_data)
        
        with col2:
            if st.button("🚀 **Generate XML**", type="primary", use_container_width=True):
                self._generate_xml_with_enhanced_config(config_data)
        
        # Display validation results
        if 'enhanced_config_validation' in st.session_state:
            validation = st.session_state['enhanced_config_validation']
            if validation['valid']:
                st.success("✅ Configuration is valid!")
                if validation.get('details'):
                    with st.expander("Validation Details"):
                        for detail in validation['details']:
                            st.info(detail)
            else:
                st.error("❌ Configuration validation failed!")
                for error in validation.get('errors', []):
                    st.error(error)
        
        # Display generated XML
        if 'enhanced_generated_xml' in st.session_state:
            result = st.session_state['enhanced_generated_xml']
            
            if isinstance(result, GenerationResult):
                st.markdown("##### 📄 Generated XML")
                
                # Display XML with download option
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.success("✅ XML generation successful!")
                
                with col2:
                    xml_bytes = result.xml_content.encode('utf-8')
                    st.download_button(
                        "💾 Download XML",
                        data=xml_bytes,
                        file_name="enhanced_generated.xml",
                        mime="text/xml"
                    )
                
                # Display XML content
                st.code(result.xml_content, language="xml", line_numbers=True)
                
                # Display generation metadata
                with st.expander("**Generation Metadata**"):
                    summary = result.get_summary()
                    st.json(summary)
            
            elif isinstance(result, dict) and 'error' in result:
                st.error(f"❌ XML generation failed: {result['error']}")
                if 'details' in result:
                    with st.expander("Error Details"):
                        st.text(result['details'])
    
    def _validate_enhanced_config(self, config_data: Dict):
        """Validate the enhanced configuration."""
        try:
            # Create enhanced config instance for validation
            enhanced_config = EnhancedJsonConfig(config_data)
            validation_results = enhanced_config.validate()
            
            st.session_state['enhanced_config_validation'] = {
                'valid': True,
                'details': validation_results if validation_results else ["Configuration is syntactically valid"]
            }
            
        except ConfigValidationError as e:
            st.session_state['enhanced_config_validation'] = {
                'valid': False,
                'errors': [str(e)]
            }
        except Exception as e:
            st.session_state['enhanced_config_validation'] = {
                'valid': False,
                'errors': [f"Unexpected validation error: {str(e)}"]
            }
    
    def _generate_xml_with_enhanced_config(self, config_data: Dict):
        """Generate XML using the enhanced configuration."""
        try:
            # Create enhanced XML generator
            generator = EnhancedXMLGenerator(
                xsd_path=self.temp_file_path,
                json_config_data=config_data
            )
            
            # Generate XML
            result = generator.generate_xml()
            
            st.session_state['enhanced_generated_xml'] = result
            
        except Exception as e:
            error_details = traceback.format_exc()
            st.session_state['enhanced_generated_xml'] = {
                'error': str(e),
                'details': error_details
            }
    
    def _get_default_enhanced_config(self) -> Dict:
        """Get default enhanced configuration structure."""
        return {
            "schema": "auto-detected",
            "mode": "complete",
            "seed": 12345,
            "values": {},
            "patterns": {},
            "choices": {},
            "templates": {},
            "namespaces": {
                "default": "",
                "prefixes": {}
            }
        }
    
    def _auto_generate_config(self, mode: str):
        """Auto-generate configuration based on mode and schema analysis."""
        config_data = self._get_default_enhanced_config()
        
        if mode == "Smart Default" and self.schema_info:
            # Add smart defaults based on schema analysis
            
            # Add suggested patterns
            patterns = {}
            for opportunity in self.schema_info.get('recommended_patterns', [])[:3]:
                if 'generate:' in opportunity['description']:
                    generator = opportunity['description'].split('(use ')[1].split(')')[0]
                    patterns[opportunity['pattern']] = generator
            config_data['patterns'] = patterns
            
            # Add suggested choices
            choices = {}
            for opportunity in self.schema_info.get('suggested_choices', [])[:2]:
                if opportunity.get('options'):
                    choices[opportunity['element']] = opportunity['options'][0]
            config_data['choices'] = choices
            
        elif mode == "Template-Based" and self.schema_info:
            # Create template-based configuration
            self._create_quick_template(config_data, "Passenger")
            
        st.session_state['enhanced_config_data'] = config_data
        st.success(f"✅ Auto-generated {mode} configuration!")
        st.rerun()
    
    def _create_quick_template(self, config_data: Dict, template_type: str):
        """Create a quick template of the specified type."""
        templates = config_data.get('templates', {})
        
        template_definitions = {
            "Passenger": {
                "data": [
                    {"name": "John Doe", "email": "john.doe@example.com", "phone": "+1-555-0123"},
                    {"name": "Jane Smith", "email": "jane.smith@example.com", "phone": "+1-555-0124"},
                    {"name": "Bob Johnson", "email": "bob.johnson@example.com", "phone": "+1-555-0125"}
                ],
                "cycle": "sequential"
            },
            "Address": {
                "data": [
                    {"street": "123 Main St", "city": "New York", "state": "NY", "zip": "10001"},
                    {"street": "456 Oak Ave", "city": "Los Angeles", "state": "CA", "zip": "90210"},
                    {"street": "789 Pine Rd", "city": "Chicago", "state": "IL", "zip": "60601"}
                ],
                "cycle": "sequential"
            },
            "Payment": {
                "data": [
                    {"type": "CREDIT_CARD", "number": "4111111111111111", "cvv": "123"},
                    {"type": "DEBIT_CARD", "number": "5555555555554444", "cvv": "456"},
                    {"type": "PAYPAL", "email": "payment@example.com", "cvv": "789"}
                ],
                "cycle": "random"
            }
        }
        
        if template_type in template_definitions:
            template_name = template_type.lower() + "_template"
            templates[template_name] = template_definitions[template_type]
            config_data['templates'] = templates
            st.session_state['enhanced_config_data'] = config_data
            st.success(f"✅ Created {template_type} template!")
    
    def _add_suggested_template(self, opportunity: Dict):
        """Add a suggested template to the configuration."""
        config_data = st.session_state.get('enhanced_config_data', {})
        templates = config_data.get('templates', {})
        
        # Create a basic template based on the opportunity
        template_name = opportunity['element'].lower() + "_template"
        templates[template_name] = {
            "data": [{"value": "sample_data_1"}, {"value": "sample_data_2"}],
            "cycle": "sequential"
        }
        
        config_data['templates'] = templates
        st.session_state['enhanced_config_data'] = config_data
        st.success(f"✅ Added template for {opportunity['element']}!")
        st.rerun()
    
    def _add_suggested_pattern(self, opportunity: Dict):
        """Add a suggested pattern to the configuration."""
        config_data = st.session_state.get('enhanced_config_data', {})
        patterns = config_data.get('patterns', {})
        
        # Extract generator from description
        if 'generate:' in opportunity['description']:
            generator = opportunity['description'].split('(use ')[1].split(')')[0]
            patterns[opportunity['pattern']] = generator
            
            config_data['patterns'] = patterns
            st.session_state['enhanced_config_data'] = config_data
            st.success(f"✅ Added pattern {opportunity['pattern']}!")
            st.rerun()
    
    def _configure_suggested_choice(self, opportunity: Dict):
        """Configure a suggested choice."""
        config_data = st.session_state.get('enhanced_config_data', {})
        choices = config_data.get('choices', {})
        
        # Use first option as default
        if opportunity.get('options'):
            choices[opportunity['element']] = opportunity['options'][0]
            
            config_data['choices'] = choices  
            st.session_state['enhanced_config_data'] = config_data
            st.success(f"✅ Configured choice for {opportunity['element']}!")
            st.rerun()


# Global instance for use in workflows
enhanced_config_ui = EnhancedConfigUI()