#!/usr/bin/env python3
"""
Analyze JSON configuration coverage to identify missing features for comprehensive testing.
"""

import json
from pathlib import Path

def analyze_config_coverage():
    """Analyze what JSON config features are missing from our test configs."""
    
    print("🔍 ANALYZING JSON CONFIGURATION COVERAGE")
    print("="*80)
    
    # Define all possible JSON configuration features from the schema
    all_features = {
        "metadata": {
            "required": ["name", "schema_name"],
            "optional": ["description", "created", "version"]
        },
        "generation_settings": {
            "available": [
                "mode", "global_repeat_count", "max_depth", 
                "include_comments", "deterministic_seed", "ensure_unique_combinations"
            ]
        },
        "element_configs": {
            "available": [
                "choices", "repeat_count", "include_optional", "custom_values",
                "selection_strategy", "data_context", "template_source", 
                "relationship", "constraints", "ensure_unique"
            ]
        },
        "smart_relationships": {
            "strategies": ["consistent_persona", "dependent_values", "constraint_based"],
            "properties": ["fields", "strategy", "ensure_unique", "constraints", "depends_on"]
        },
        "data_contexts": {
            "types": ["simple_arrays", "nested_objects", "templates", "inheritance"]
        },
        "global_overrides": {
            "available": [
                "default_string_length", "use_realistic_data", "preserve_structure", 
                "namespace_prefixes"
            ]
        },
        "selection_strategies": ["random", "sequential", "seeded", "template"],
        "generation_modes": ["Minimalistic", "Complete", "Custom"]
    }
    
    # Load our existing configs
    config_dir = Path("resource/test_JSON_for_test_xsd")
    configs = {}
    
    for config_file in config_dir.glob("*.json"):
        with open(config_file, 'r') as f:
            configs[config_file.name] = json.load(f)
    
    print(f"📋 Analyzing {len(configs)} existing configurations...\n")
    
    # Track what features are used
    used_features = {
        "metadata_fields": set(),
        "generation_settings": set(),
        "element_config_properties": set(),
        "selection_strategies": set(),
        "smart_relationship_strategies": set(),
        "generation_modes": set(),
        "data_context_types": set(),
        "global_overrides": set()
    }
    
    # Analyze each config
    for config_name, config_data in configs.items():
        print(f"📄 {config_name}:")
        
        # Metadata
        metadata = config_data.get("metadata", {})
        used_features["metadata_fields"].update(metadata.keys())
        
        # Generation settings
        gen_settings = config_data.get("generation_settings", {})
        used_features["generation_settings"].update(gen_settings.keys())
        used_features["generation_modes"].add(gen_settings.get("mode"))
        
        # Element configs
        element_configs = config_data.get("element_configs", {})
        for element_name, element_config in element_configs.items():
            used_features["element_config_properties"].update(element_config.keys())
            if "selection_strategy" in element_config:
                used_features["selection_strategies"].add(element_config["selection_strategy"])
        
        # Smart relationships
        smart_relationships = config_data.get("smart_relationships", {})
        for rel_name, rel_config in smart_relationships.items():
            if "strategy" in rel_config:
                used_features["smart_relationship_strategies"].add(rel_config["strategy"])
        
        # Global overrides
        global_overrides = config_data.get("global_overrides", {})
        used_features["global_overrides"].update(global_overrides.keys())
        
        # Data contexts (analyze structure)
        data_contexts = config_data.get("data_contexts", {})
        for context_name, context_data in data_contexts.items():
            if isinstance(context_data, list) and context_data and isinstance(context_data[0], dict):
                used_features["data_context_types"].add("templates")
            elif isinstance(context_data, dict) and any(isinstance(v, dict) for v in context_data.values()):
                used_features["data_context_types"].add("nested_objects")
            elif isinstance(context_data, list):
                used_features["data_context_types"].add("simple_arrays")
            elif isinstance(context_data, dict):
                used_features["data_context_types"].add("simple_objects")
        
        print(f"  Mode: {gen_settings.get('mode', 'Not set')}")
        print(f"  Smart Relationships: {list(smart_relationships.keys())}")
        print(f"  Data Contexts: {list(data_contexts.keys())}")
        print()
    
    # Report missing features
    print("🚨 MISSING FEATURES ANALYSIS")
    print("="*80)
    
    missing_features = []
    
    # Check metadata
    missing_metadata = set(all_features["metadata"]["optional"]) - used_features["metadata_fields"]
    if missing_metadata:
        missing_features.append(f"Metadata fields: {missing_metadata}")
    
    # Check generation settings
    missing_gen_settings = set(all_features["generation_settings"]["available"]) - used_features["generation_settings"]
    if missing_gen_settings:
        missing_features.append(f"Generation settings: {missing_gen_settings}")
    
    # Check element config properties
    missing_element_props = set(all_features["element_configs"]["available"]) - used_features["element_config_properties"]
    if missing_element_props:
        missing_features.append(f"Element config properties: {missing_element_props}")
    
    # Check selection strategies
    missing_strategies = set(all_features["selection_strategies"]) - used_features["selection_strategies"]
    if missing_strategies:
        missing_features.append(f"Selection strategies: {missing_strategies}")
    
    # Check smart relationship strategies
    missing_rel_strategies = set(all_features["smart_relationships"]["strategies"]) - used_features["smart_relationship_strategies"]
    if missing_rel_strategies:
        missing_features.append(f"Smart relationship strategies: {missing_rel_strategies}")
    
    # Check generation modes
    missing_modes = set(all_features["generation_modes"]) - used_features["generation_modes"]
    if missing_modes:
        missing_features.append(f"Generation modes: {missing_modes}")
    
    # Check global overrides
    missing_overrides = set(all_features["global_overrides"]["available"]) - used_features["global_overrides"]
    if missing_overrides:
        missing_features.append(f"Global overrides: {missing_overrides}")
    
    if missing_features:
        print("❌ MISSING FEATURES:")
        for i, feature in enumerate(missing_features, 1):
            print(f"  {i}. {feature}")
    else:
        print("✅ All major features are covered!")
    
    print(f"\n📊 COVERAGE SUMMARY")
    print("="*80)
    print(f"✅ Used metadata fields: {used_features['metadata_fields']}")
    print(f"✅ Used generation settings: {used_features['generation_settings']}")
    print(f"✅ Used element properties: {used_features['element_config_properties']}")
    print(f"✅ Used selection strategies: {used_features['selection_strategies']}")
    print(f"✅ Used relationship strategies: {used_features['smart_relationship_strategies']}")
    print(f"✅ Used generation modes: {used_features['generation_modes']}")
    print(f"✅ Used data context types: {used_features['data_context_types']}")
    print(f"✅ Used global overrides: {used_features['global_overrides']}")
    
    # Suggest additional test configs
    print(f"\n💡 RECOMMENDED ADDITIONAL TEST CONFIGS")
    print("="*80)
    
    recommendations = []
    
    if "random" in missing_strategies:
        recommendations.append("Random selection strategy config")
    if "seeded" in missing_strategies:
        recommendations.append("Seeded random strategy config")
    if "dependent_values" in missing_rel_strategies:
        recommendations.append("Dependent values relationship config")
    if "constraint_based" in missing_rel_strategies:
        recommendations.append("Constraint-based relationship config")
    if "Custom" in missing_modes:
        recommendations.append("Custom generation mode config")
    if "Minimalistic" in missing_modes:
        recommendations.append("Minimalistic generation mode config")
    if "custom_values" in missing_element_props:
        recommendations.append("Custom values without data context config")
    if "include_optional" in missing_element_props:
        recommendations.append("Optional elements inclusion config")
    if "constraints" in missing_element_props:
        recommendations.append("Element constraints config")
    if "ensure_unique" in missing_element_props:
        recommendations.append("Ensure unique values config")
    if missing_overrides:
        recommendations.append("Global overrides comprehensive config")
    
    if recommendations:
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. {rec}")
    else:
        print("✅ Current configs provide good coverage!")
    
    return missing_features, recommendations

if __name__ == "__main__":
    missing_features, recommendations = analyze_config_coverage()
    
    print(f"\n🎯 CONCLUSION")
    print("="*80)
    if missing_features:
        print(f"❌ {len(missing_features)} feature categories need additional test coverage")
        print(f"💡 {len(recommendations)} additional test configs recommended for comprehensive testing")
    else:
        print("✅ Current configuration coverage is comprehensive!")
    print("\nUse this analysis to create additional test configurations for complete coverage.")