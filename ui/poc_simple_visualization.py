"""
Simple POC Mapping Visualization

Clean, table-focused visualization of XSLT mapping specifications for BAs and Devs.
Designed to be LLM-consumable and export-friendly.
"""

import streamlit as st
import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Import POC analyzer
poc_analyzer_available = False
try:
    import sys
    
    # Add agentic_test_gen to path for imports
    agentic_path = Path(__file__).parent.parent / "agentic_test_gen"
    if agentic_path.exists():
        sys.path.insert(0, str(agentic_path))
        from analyze_poc_results import POCResultsAnalyzer
        poc_analyzer_available = True
except ImportError:
    poc_analyzer_available = False


def get_available_poc_results() -> List[Dict[str, Any]]:
    """Get list of available POC result directories."""
    agentic_path = Path(__file__).parent.parent / "agentic_test_gen"
    poc_results_path = agentic_path / "poc_results"
    
    available_results = []
    
    if not poc_results_path.exists():
        return available_results
    
    # Look for enhanced_exploration_v* AND enhanced_exploration directories
    search_patterns = [
        "enhanced_exploration_v*",  # Versioned results (v1, v2, v3, etc.)
        "enhanced_exploration"      # Non-versioned results
    ]
    
    for pattern in search_patterns:
        for result_dir in poc_results_path.glob(pattern):
            if result_dir.is_dir():
                # Get basic info about this result set
                mapping_files = list(result_dir.glob("mapping_specifications_*.json"))
                summary_files = list(result_dir.glob("exploration_summary_*.json"))
                
                if mapping_files:
                    # Get the latest summary for metadata
                    latest_summary = None
                    total_mappings = 0
                    
                    if summary_files:
                        latest_summary_file = max(summary_files, key=lambda f: f.stat().st_mtime)
                        try:
                            with open(latest_summary_file, 'r') as f:
                                latest_summary = json.load(f)
                                # Try to get total mappings from summary
                                total_mappings = latest_summary.get('statistics', {}).get('mapping_specifications', 0)
                        except:
                            pass
                    
                    # If no summary or no mapping count, estimate from files
                    if total_mappings == 0:
                        # Quick estimation by checking one mapping file
                        try:
                            with open(mapping_files[0], 'r') as f:
                                sample_mappings = json.load(f)
                                if isinstance(sample_mappings, list):
                                    # Estimate total based on files and sample size
                                    total_mappings = len(sample_mappings) * len(mapping_files)
                        except:
                            total_mappings = len(mapping_files)  # Fallback estimate
                    
                    result_info = {
                        'name': result_dir.name,
                        'path': str(result_dir),
                        'mapping_files_count': len(mapping_files),
                        'estimated_mappings': total_mappings,
                        'last_modified': datetime.fromtimestamp(result_dir.stat().st_mtime),
                        'summary': latest_summary,
                        'has_summary': latest_summary is not None
                    }
                    available_results.append(result_info)
    
    # Sort by last modified (newest first)
    available_results.sort(key=lambda x: x['last_modified'], reverse=True)
    
    return available_results


def load_poc_mappings(results_dir: str) -> Dict[str, Any]:
    """Load POC mappings from a specific results directory."""
    if not poc_analyzer_available:
        return {'error': 'POC analyzer not available'}
    
    try:
        # Use the POC analyzer to load results
        analyzer = POCResultsAnalyzer(results_dir)
        analyzer.load_all_results()
        
        # Generate summary statistics
        stats = analyzer.generate_summary_statistics()
        
        return {
            'mappings': analyzer.all_mappings,
            'statistics': stats,
            'analyzer': analyzer
        }
    except Exception as e:
        return {'error': f'Failed to load POC results: {str(e)}'}


def process_mappings_for_table(mappings: List[Dict]) -> pd.DataFrame:
    """Convert POC mappings to a clean table format."""
    
    table_data = []
    
    for mapping in mappings:
        # Extract core information
        input_field = mapping.get('source_path', '')
        output_field = mapping.get('destination_path', '')
        
        # Get transformation details
        trans_logic = mapping.get('transformation_logic', {})
        description = trans_logic.get('natural_language', 'No description') if isinstance(trans_logic, dict) else 'No description'
        xslt_code = trans_logic.get('original_xslt', '') if isinstance(trans_logic, dict) else ''
        
        # Process conditions into readable format
        conditions = mapping.get('conditions', [])
        when_clause = 'Always'
        if conditions:
            if len(conditions) == 1:
                when_clause = f"When {conditions[0]}"
            elif len(conditions) <= 3:
                when_clause = f"When {' OR '.join(conditions)}"
            else:
                when_clause = f"When {conditions[0]} (+ {len(conditions)-1} more)"
        
        # Get template name (clean format)
        template_name = mapping.get('template_name', '')
        if template_name.startswith('vmf:'):
            template_name = template_name[4:]  # Remove vmf: prefix
        
        # Show full data without truncation
        input_display = input_field
        output_display = output_field  
        description_display = description
        xslt_display = xslt_code
        
        # Categorize transformation type
        trans_type = mapping.get('transformation_type', 'unknown')
        category = categorize_transformation(trans_type)
        
        table_data.append({
            'ID': mapping.get('id', ''),
            'Input': input_display,
            'Output': output_display,
            'Description': description_display,
            'XSLT Code': xslt_display,
            'When': when_clause,
            'Template': template_name,
            'Category': category,
            # Keep full data for expansion/export
            'Input_Full': input_field,
            'Output_Full': output_field,
            'Description_Full': description,
            'XSLT_Full': xslt_code,
            'Conditions_Full': conditions,
            'Type_Full': trans_type
        })
    
    return pd.DataFrame(table_data)


def categorize_transformation(trans_type: str) -> str:
    """Categorize transformation types into simple groups."""
    type_lower = trans_type.lower()
    
    if 'conditional' in type_lower:
        return 'Conditional'
    elif 'text' in type_lower or 'processing' in type_lower:
        return 'Text Processing'
    elif 'static' in type_lower:
        return 'Static Value'
    elif 'hierarchical' in type_lower:
        return 'Hierarchical'
    elif 'value' in type_lower:
        return 'Value Transform'
    else:
        return 'Other'


def render_mapping_table(df: pd.DataFrame):
    """Render the main mapping table with filtering and search."""
    
    st.markdown("#### 📋 XSLT Mapping Specifications")
    
    # Quick stats row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Mappings", len(df))
    with col2:
        unique_categories = df['Category'].nunique()
        st.metric("Categories", unique_categories)
    with col3:
        with_conditions = len(df[df['When'] != 'Always'])
        st.metric("Conditional", with_conditions)
    with col4:
        with_xslt = len(df[df['XSLT Code'] != ''])
        st.metric("With XSLT", with_xslt)
    
    # Filters row
    col_filter1, col_filter2, col_filter3 = st.columns(3)
    
    with col_filter1:
        # Category filter
        categories = ['All'] + sorted(df['Category'].unique().tolist())
        selected_category = st.selectbox("Category:", categories)
    
    with col_filter2:
        # Template filter
        templates = ['All'] + sorted([t for t in df['Template'].unique() if t])
        selected_template = st.selectbox("Template:", templates)
    
    with col_filter3:
        # Search box
        search_term = st.text_input("🔍 Search:", placeholder="Search input, output, or description...")
    
    # Apply filters
    filtered_df = df.copy()
    
    if selected_category != 'All':
        filtered_df = filtered_df[filtered_df['Category'] == selected_category]
    
    if selected_template != 'All':
        filtered_df = filtered_df[filtered_df['Template'] == selected_template]
    
    if search_term:
        search_mask = (
            filtered_df['Input_Full'].str.contains(search_term, case=False, na=False) |
            filtered_df['Output_Full'].str.contains(search_term, case=False, na=False) |
            filtered_df['Description_Full'].str.contains(search_term, case=False, na=False)
        )
        filtered_df = filtered_df[search_mask]
    
    st.info(f"Showing {len(filtered_df)} of {len(df)} mappings")
    
    # Display table with core columns  
    display_columns = ['Input', 'Output', 'Description', 'XSLT Code', 'When', 'Template']
    
    if len(filtered_df) > 0:
        # Use streamlit's native dataframe display with selection
        selection = st.dataframe(
            filtered_df[display_columns],
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
            column_config={
                "Description": st.column_config.TextColumn(
                    "Description",
                    width="large",
                    help="Complete business description"
                ),
                "XSLT Code": st.column_config.TextColumn(
                    "XSLT Code", 
                    width="large",
                    help="Complete XSLT transformation code"
                ),
                "Input": st.column_config.TextColumn(
                    "Input",
                    width="medium",
                    help="Source data path"
                ),
                "Output": st.column_config.TextColumn(
                    "Output",
                    width="medium", 
                    help="Destination data path"
                )
            }
        )
        
        # Show details for selected row
        if selection['selection']['rows']:
            selected_idx = selection['selection']['rows'][0]
            selected_row = filtered_df.iloc[selected_idx]
            
            st.markdown("---")
            st.markdown("#### 🔍 Selected Mapping Details")
            
            col_detail1, col_detail2 = st.columns([2, 1])
            
            with col_detail1:
                st.markdown("**Full Input:**")
                st.code(selected_row['Input_Full'], language="text")
                
                st.markdown("**Full Output:**")
                st.code(selected_row['Output_Full'], language="xml")
                
                st.markdown("**Complete Description:**")
                st.write(selected_row['Description_Full'])
                
                if selected_row['XSLT_Full']:
                    st.markdown("**Complete XSLT Code:**")
                    st.code(selected_row['XSLT_Full'], language="xml")
            
            with col_detail2:
                st.markdown("**Metadata:**")
                st.markdown(f"**ID:** {selected_row['ID']}")
                st.markdown(f"**Template:** {selected_row['Template']}")
                st.markdown(f"**Category:** {selected_row['Category']}")
                st.markdown(f"**Type:** {selected_row['Type_Full']}")
                
                if selected_row['Conditions_Full']:
                    st.markdown("**Conditions:**")
                    for condition in selected_row['Conditions_Full']:
                        st.markdown(f"• {condition}")
    else:
        st.warning("No mappings match your current filters.")


def render_export_options(df: pd.DataFrame):
    """Render simple export options."""
    
    st.markdown("#### 💾 Export Options")
    
    col_exp1, col_exp2, col_exp3 = st.columns(3)
    
    with col_exp1:
        if st.button("📊 **Export Table CSV**", use_container_width=True):
            # Export the main display columns plus full data
            export_df = df[['ID', 'Input_Full', 'Output_Full', 'Description_Full', 
                          'XSLT_Full', 'When', 'Template', 'Category', 'Type_Full']].copy()
            
            # Rename columns for clarity
            export_df.columns = ['ID', 'Input', 'Output', 'Description', 'XSLT_Code', 
                               'Conditions', 'Template', 'Category', 'Type']
            
            csv_string = export_df.to_csv(index=False)
            
            st.download_button(
                label="💾 Download CSV",
                data=csv_string,
                file_name=f"xslt_mappings_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    
    with col_exp2:
        if st.button("🤖 **LLM-Ready Export**", use_container_width=True):
            # Create LLM-optimized format
            llm_data = []
            for _, row in df.iterrows():
                llm_entry = {
                    "mapping_id": row['ID'],
                    "input": row['Input_Full'],
                    "output": row['Output_Full'],
                    "transformation_description": row['Description_Full'],
                    "xslt_implementation": row['XSLT_Full'],
                    "conditions": row['Conditions_Full'],
                    "template_function": row['Template'],
                    "category": row['Category']
                }
                llm_data.append(llm_entry)
            
            llm_json = json.dumps({
                "xslt_mappings": llm_data,
                "metadata": {
                    "total_mappings": len(df),
                    "export_date": datetime.now().isoformat(),
                    "format": "llm_consumable"
                }
            }, indent=2)
            
            st.download_button(
                label="💾 Download LLM JSON",
                data=llm_json,
                file_name=f"xslt_mappings_llm_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    
    with col_exp3:
        if st.button("📋 **Summary Report**", use_container_width=True):
            # Create summary report
            summary = {
                "overview": {
                    "total_mappings": len(df),
                    "categories": df['Category'].value_counts().to_dict(),
                    "templates": df['Template'].value_counts().to_dict(),
                    "conditional_mappings": len(df[df['When'] != 'Always']),
                    "static_mappings": len(df[df['When'] == 'Always'])
                },
                "sample_mappings": df.head(5)[['Input_Full', 'Output_Full', 'Description_Full']].to_dict('records')
            }
            
            summary_json = json.dumps(summary, indent=2)
            
            st.download_button(
                label="💾 Download Summary",
                data=summary_json,
                file_name=f"xslt_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )


def render_simple_poc_visualization():
    """Render the simplified POC mapping visualization."""
    
    st.markdown('<div class="main-header">POC Mapping Visualization</div>', unsafe_allow_html=True)
    st.markdown('**Simple table view of XSLT mapping specifications - Perfect for BAs, Devs, and LLM consumption**')
    
    # Check if POC analyzer is available
    if not poc_analyzer_available:
        st.error("🚫 POC analyzer not available. Please check the agentic_test_gen installation.")
        return
    
    # Get available POC results
    available_results = get_available_poc_results()
    
    if not available_results:
        st.warning("⚠️ No POC results found. Please run the Enhanced XSLT POC first using `python agentic_test_gen/xslt_mapping_extractor_poc.py`")
        st.info("""
        **Expected directory structure:**
        ```
        agentic_test_gen/poc_results/
        ├── enhanced_exploration/          # Basic results
        ├── enhanced_exploration_v1/       # Version 1 results  
        ├── enhanced_exploration_v2/       # Version 2 results
        └── enhanced_exploration_v3/       # Version 3 results (latest)
        ```
        """)
        return
    
    # Show available results summary
    st.info(f"**Found {len(available_results)} POC result sets** - showing newest first")
    
    # Simple results selector
    st.markdown("### 📁 Select POC Results")
    
    # Enhanced display with mapping estimates and metadata
    result_options = []
    for result in available_results:
        name = result['name']
        date = result['last_modified'].strftime('%Y-%m-%d %H:%M')
        mappings = result['estimated_mappings']
        files = result['mapping_files_count']
        
        # Add status indicators
        status_indicators = []
        if result['has_summary']:
            status_indicators.append("📊")
        if 'v3' in name:
            status_indicators.append("🚀")  # Latest version
        elif 'v' in name:
            status_indicators.append("📋")  # Versioned
        else:
            status_indicators.append("📁")  # Basic
        
        status = "".join(status_indicators)
        label = f"{status} {name} - {mappings} mappings ({files} files) - {date}"
        result_options.append(label)
    
    selected_result_idx = st.selectbox(
        "Choose POC result set:",
        range(len(result_options)),
        format_func=lambda x: result_options[x],
        help="🚀 = Latest, 📊 = Has summary data, 📋 = Versioned, 📁 = Basic"
    )
    
    selected_result = available_results[selected_result_idx]
    
    # Display selected result info
    st.markdown("#### 📋 Selected Result Details")
    col_meta1, col_meta2, col_meta3 = st.columns(3)
    
    with col_meta1:
        st.metric("Result Set", selected_result['name'])
        st.metric("Files Found", selected_result['mapping_files_count'])
    
    with col_meta2:
        st.metric("Estimated Mappings", selected_result['estimated_mappings'])
        st.metric("Generated", selected_result['last_modified'].strftime('%Y-%m-%d %H:%M'))
    
    with col_meta3:
        summary_status = "✅ Available" if selected_result['has_summary'] else "❌ Missing"
        st.metric("Summary Data", summary_status)
        
        # Determine analysis version
        if selected_result['summary'] and 'enhanced_analysis_version' in selected_result['summary'].get('statistics', {}):
            version = selected_result['summary']['statistics']['enhanced_analysis_version']
            st.metric("Analysis Version", version)
        elif 'v3' in selected_result['name']:
            st.metric("Analysis Version", "Phase 4.6+4.7 (Latest)")
        else:
            st.metric("Analysis Version", "Legacy")
    
    # Load POC data
    with st.spinner("Loading POC mapping data..."):
        poc_data = load_poc_mappings(selected_result['path'])
    
    if 'error' in poc_data:
        st.error(f"Failed to load POC data: {poc_data['error']}")
        st.info(f"""
        **Troubleshooting:**
        - Verify the directory exists: `{selected_result['path']}`
        - Check file permissions for mapping_specifications_*.json files
        - Ensure agentic_test_gen environment is properly installed
        """)
        return
    
    mappings = poc_data['mappings']
    statistics = poc_data['statistics']
    
    if not mappings:
        st.warning("No mappings found in the selected POC results.")
        return
    
    # Convert to table format
    with st.spinner("Processing mappings for table display..."):
        df = process_mappings_for_table(mappings)
    
    # Store in session state
    st.session_state['poc_table_df'] = df
    st.session_state['poc_statistics'] = statistics
    
    # Create simple tabs
    tab1, tab2 = st.tabs(["📋 **Mapping Table**", "💾 **Export**"])
    
    with tab1:
        render_mapping_table(df)
    
    with tab2:
        render_export_options(df)
    
    # Simple footer with key stats
    st.markdown("---")
    col_footer1, col_footer2, col_footer3 = st.columns(3)
    
    with col_footer1:
        st.markdown(f"**📊 Total:** {len(mappings)} mappings")
    with col_footer2:
        cost = statistics.get('total_cost', 0)
        st.markdown(f"**💰 Cost:** ${cost:.6f}")
    with col_footer3:
        version = statistics.get('enhanced_analysis_version', 'Unknown')
        if 'Phase 4' in version:
            st.markdown("**✅ Enhanced** (Phase 4.6+4.7)")
        else:
            st.markdown("**⚠️ Legacy** version")


def check_simple_poc_availability():
    """Check if simple POC visualization is available."""
    return poc_analyzer_available