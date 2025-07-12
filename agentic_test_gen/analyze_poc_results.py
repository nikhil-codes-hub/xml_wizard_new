#!/usr/bin/env python3
"""
POC Results Analyzer - Comprehensive Mapping Document Generator

Analyzes the output files from enhanced_interactive_poc.py and creates:
1. On-screen display of all mappings
2. Consolidated comprehensive mapping document
3. Summary statistics and insights
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
import glob

class POCResultsAnalyzer:
    """Analyzes and consolidates POC exploration results"""
    
    def __init__(self, results_dir: str = "poc_results/enhanced_exploration"):
        self.results_dir = Path(results_dir)
        self.all_mappings = []
        self.all_insights = []
        self.all_evolution = []
        self.exploration_summaries = []
        
    def load_all_results(self):
        """Load all result files from the enhanced exploration"""
        
        print("🔍 Loading POC results...")
        
        # Load mapping specifications
        mapping_files = sorted(glob.glob(str(self.results_dir / "mapping_specifications_*.json")))
        for file_path in mapping_files:
            try:
                with open(file_path, 'r') as f:
                    mappings = json.load(f)
                    if mappings:  # Only add non-empty mappings
                        self.all_mappings.extend(mappings)
            except Exception as e:
                print(f"⚠️  Error loading {file_path}: {e}")
        
        # Load LLM insights
        insight_files = sorted(glob.glob(str(self.results_dir / "llm_insights_*.json")))
        for file_path in insight_files:
            try:
                with open(file_path, 'r') as f:
                    insights = json.load(f)
                    if insights:
                        self.all_insights.extend(insights)
            except Exception as e:
                print(f"⚠️  Error loading {file_path}: {e}")
        
        # Load exploration summaries
        summary_files = sorted(glob.glob(str(self.results_dir / "exploration_summary_*.json")))
        for file_path in summary_files:
            try:
                with open(file_path, 'r') as f:
                    summary = json.load(f)
                    self.exploration_summaries.append(summary)
            except Exception as e:
                print(f"⚠️  Error loading {file_path}: {e}")
        
        # Remove duplicates based on mapping ID
        unique_mappings = {}
        for mapping in self.all_mappings:
            mapping_id = mapping.get('id', 'unknown')
            if mapping_id not in unique_mappings:
                unique_mappings[mapping_id] = mapping
        
        self.all_mappings = list(unique_mappings.values())
        
        print(f"✅ Loaded:")
        print(f"   📋 {len(self.all_mappings)} unique mappings")
        print(f"   🧠 {len(self.all_insights)} insights")
        print(f"   📊 {len(self.exploration_summaries)} exploration summaries")
    
    def display_mappings_on_screen(self):
        """Display all mappings in a formatted way on screen"""
        
        print(f"\n{'='*80}")
        print(f"🎯 COMPREHENSIVE XSLT MAPPING ANALYSIS")
        print(f"{'='*80}")
        print(f"📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📋 Total Mappings Found: {len(self.all_mappings)}")
        print(f"{'='*80}")
        
        if not self.all_mappings:
            print("❌ No mappings found in the results!")
            return
        
        # Group mappings by transformation type
        mappings_by_type = {}
        for mapping in self.all_mappings:
            trans_type = mapping.get('transformation_type', 'unknown')
            if trans_type not in mappings_by_type:
                mappings_by_type[trans_type] = []
            mappings_by_type[trans_type].append(mapping)
        
        # Display by category
        for trans_type, mappings in mappings_by_type.items():
            print(f"\n🔄 {trans_type.upper().replace('_', ' ')} ({len(mappings)} mappings)")
            print("-" * 60)
            
            for i, mapping in enumerate(mappings, 1):
                print(f"\n  {i}. {mapping.get('id', 'Unknown ID')}")
                print(f"     📥 Source: {mapping.get('source_path', 'N/A')}")
                print(f"     📤 Destination: {mapping.get('destination_path', 'N/A')}")
                
                # Natural language description
                trans_logic = mapping.get('transformation_logic', {})
                if isinstance(trans_logic, dict):
                    desc = trans_logic.get('natural_language', 'No description')
                    print(f"     💭 Logic: {desc}")
                
                # Conditions
                conditions = mapping.get('conditions', [])
                if conditions:
                    print(f"     🔍 Conditions: {', '.join(conditions)}")
                
                # Source chunk
                chunk_source = mapping.get('chunk_source', 'Unknown')
                print(f"     📦 From Chunk: {chunk_source}")
        
        print(f"\n{'='*80}")
    
    def generate_summary_statistics(self) -> Dict[str, Any]:
        """Generate summary statistics from the analysis"""
        
        # Get latest exploration summary
        latest_summary = self.exploration_summaries[-1] if self.exploration_summaries else {}
        
        # Count mappings by type
        type_counts = {}
        for mapping in self.all_mappings:
            trans_type = mapping.get('transformation_type', 'unknown')
            type_counts[trans_type] = type_counts.get(trans_type, 0) + 1
        
        # Count chunks with mappings
        chunks_with_mappings = set()
        for mapping in self.all_mappings:
            chunk_source = mapping.get('chunk_source')
            if chunk_source:
                chunks_with_mappings.add(chunk_source)
        
        # Calculate mapping extraction rate
        total_chunks = latest_summary.get('progress', {}).get('chunks_explored', 0)
        mapping_rate = len(chunks_with_mappings) / total_chunks if total_chunks > 0 else 0
        
        return {
            "total_mappings": len(self.all_mappings),
            "total_chunks_analyzed": total_chunks,
            "chunks_with_mappings": len(chunks_with_mappings),
            "mapping_extraction_rate": mapping_rate,
            "mappings_by_type": type_counts,
            "total_cost": latest_summary.get('cost_tracking', {}).get('cumulative_cost_usd', 0),
            "total_insights": len(self.all_insights),
            "analysis_date": datetime.now().isoformat()
        }
    
    def create_comprehensive_document(self):
        """Create a comprehensive mapping document and save to file"""
        
        # Generate summary statistics
        stats = self.generate_summary_statistics()
        
        # Create comprehensive document structure
        comprehensive_doc = {
            "metadata": {
                "title": "Comprehensive XSLT Mapping Analysis",
                "generated_date": datetime.now().isoformat(),
                "source": "Enhanced Interactive XSLT Exploration POC",
                "xslt_file": "OrderCreate_MapForce_Full.xslt"
            },
            "summary_statistics": stats,
            "mapping_categories": {},
            "detailed_mappings": self.all_mappings,
            "analysis_insights": {
                "top_transformation_patterns": self._identify_patterns(),
                "complexity_analysis": self._analyze_complexity(),
                "coverage_analysis": self._analyze_coverage()
            }
        }
        
        # Group mappings by type for easier navigation
        for mapping in self.all_mappings:
            trans_type = mapping.get('transformation_type', 'unknown')
            if trans_type not in comprehensive_doc["mapping_categories"]:
                comprehensive_doc["mapping_categories"][trans_type] = []
            comprehensive_doc["mapping_categories"][trans_type].append(mapping)
        
        # Save to file
        output_file = self.results_dir / f"comprehensive_mapping_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(comprehensive_doc, f, indent=2)
        
        print(f"\n💾 COMPREHENSIVE DOCUMENT SAVED:")
        print(f"   📁 File: {output_file}")
        print(f"   📊 Total Mappings: {stats['total_mappings']}")
        print(f"   💰 Total Cost: ${stats['total_cost']:.6f}")
        print(f"   📈 Extraction Rate: {stats['mapping_extraction_rate']:.1%}")
        
        return output_file, comprehensive_doc
    
    def _identify_patterns(self) -> List[Dict[str, Any]]:
        """Identify common transformation patterns"""
        
        patterns = []
        
        # Count transformation types
        type_counts = {}
        for mapping in self.all_mappings:
            trans_type = mapping.get('transformation_type', 'unknown')
            type_counts[trans_type] = type_counts.get(trans_type, 0) + 1
        
        # Sort by frequency
        sorted_types = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)
        
        for trans_type, count in sorted_types:
            patterns.append({
                "pattern": trans_type,
                "frequency": count,
                "percentage": (count / len(self.all_mappings)) * 100 if self.all_mappings else 0
            })
        
        return patterns
    
    def _analyze_complexity(self) -> Dict[str, Any]:
        """Analyze the complexity of transformations"""
        
        complexity_metrics = {
            "simple_mappings": 0,
            "conditional_mappings": 0,
            "loop_mappings": 0,
            "complex_transformations": 0
        }
        
        for mapping in self.all_mappings:
            trans_type = mapping.get('transformation_type', '')
            
            if 'conditional' in trans_type:
                complexity_metrics["conditional_mappings"] += 1
            elif 'loop' in trans_type:
                complexity_metrics["loop_mappings"] += 1
            elif 'direct' in trans_type or 'simple' in trans_type:
                complexity_metrics["simple_mappings"] += 1
            else:
                complexity_metrics["complex_transformations"] += 1
        
        return complexity_metrics
    
    def _analyze_coverage(self) -> Dict[str, Any]:
        """Analyze coverage of the XSLT analysis"""
        
        # Get latest summary for coverage info
        latest_summary = self.exploration_summaries[-1] if self.exploration_summaries else {}
        progress = latest_summary.get('progress', {})
        
        return {
            "chunks_explored": progress.get('chunks_explored', 0),
            "target_chunks": progress.get('target_chunks', 0),
            "completion_percentage": progress.get('progress_percentage', 0),
            "chunks_with_mappings": len(set(m.get('chunk_source') for m in self.all_mappings if m.get('chunk_source'))),
            "mapping_density": len(self.all_mappings) / progress.get('chunks_explored', 1)
        }

def main():
    """Main execution function"""
    
    print("🚀 POC Results Analyzer")
    print("=" * 50)
    
    # Initialize analyzer
    analyzer = POCResultsAnalyzer()
    
    # Load all results
    analyzer.load_all_results()
    
    # Display mappings on screen
    analyzer.display_mappings_on_screen()
    
    # Create comprehensive document
    output_file, doc = analyzer.create_comprehensive_document()
    
    # Show final summary
    stats = doc["summary_statistics"]
    print(f"\n{'='*80}")
    print(f"📋 FINAL ANALYSIS SUMMARY")
    print(f"{'='*80}")
    print(f"✅ Mappings Extracted: {stats['total_mappings']}")
    print(f"📦 Chunks Analyzed: {stats['total_chunks_analyzed']}")
    print(f"💰 Total Cost: ${stats['total_cost']:.6f}")
    print(f"📈 Success Rate: {stats['mapping_extraction_rate']:.1%}")
    print(f"📁 Saved to: {output_file.name}")
    print(f"{'='*80}")

if __name__ == "__main__":
    main()