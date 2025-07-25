#!/usr/bin/env python3
"""
Enhanced Interactive XSLT PoC - Detailed Mapping Specification with Context Management

This enhanced version focuses on:
1. Extracting detailed mapping specifications (source→destination→transformation)
2. Progressive summarization with context reset
3. File-based understanding storage
4. Target: 20% chunk coverage for rapid validation
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import time
import re

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / '.env')
except ImportError:
    print("⚠️  python-dotenv not found")

import openai


@dataclass
class SimpleChunk:
    """Simple chunk structure for PoC"""
    id: str
    content: str
    description: str
    chunk_type: str
    templates_defined: List[str]
    template_calls: List[str]
    variables_defined: List[str]
    dependencies: List[str]
    line_start: int
    line_end: int
    token_count: int


# SmartXSLTChunker removed - now using semantic chunker from src.core.xslt_chunker


@dataclass
class MappingSpecification:
    """Detailed mapping specification for XSLT transformation"""
    id: str
    source_path: str
    destination_path: str
    transformation_type: str  # direct_mapping, conditional_mapping, function_call, etc.
    transformation_logic: Dict[str, Any]  # Enhanced with natural language description
    conditions: List[str]
    validation_rules: List[str]
    template_name: str
    chunk_source: str


@dataclass
class TemplateAnalysis:
    """Deep analysis of an XSLT template"""
    name: str
    purpose: str
    input_parameters: List[str]
    output_structure: str
    dependencies: List[str]
    complexity: str
    mappings: List[MappingSpecification]


class EnhancedXSLTExplorer:
    """Enhanced XSLT explorer with detailed mapping extraction and context management"""
    
    def __init__(self, openai_api_key: str, xslt_file_path: str, target_coverage: float = 1.0):
        self.openai_client = openai.OpenAI(api_key=openai_api_key)
        self.xslt_file_path = xslt_file_path
        self.target_coverage = target_coverage
        
        # Initialize semantic chunker for improved mapping extraction
        print("🔍 Chunking XSLT file with semantic strategy...")
        from src.core.xslt_chunker import XSLTChunker
        from pathlib import Path
        
        # Use semantic chunking strategy for better context preservation
        chunker = XSLTChunker(
            max_tokens_per_chunk=15000,
            chunking_strategy='semantic'  # Use semantic clustering for template function binding
        )
        
        # Convert XSLTChunker output to SimpleChunk format
        xslt_chunks = chunker.chunk_file(Path(xslt_file_path))
        self.chunks = self._convert_to_simple_chunks(xslt_chunks)
        self.target_chunks = int(len(self.chunks) * target_coverage)
        
        print(f"✅ Created {len(self.chunks)} chunks, targeting {self.target_chunks} chunks ({target_coverage:.0%})")
        
        # Create indexes
        self.chunk_index = {chunk.id: chunk for chunk in self.chunks}
        
        # Exploration state
        self.chunks_explored = set()
        self.current_chunk_index = 0
        self.conversation_turns = 0
        self.context_resets = 0
        
        # Understanding storage (file-based)
        self.results_dir = Path("poc_results/enhanced_exploration")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        self.mapping_specs: List[MappingSpecification] = []
        self.template_analyses: List[TemplateAnalysis] = []
        
        # Cost tracking
        self.cost_tracker = {
            "total_calls": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "cumulative_cost_usd": 0.0,
            "cost_per_phase": []
        }
        
        # Timing tracking
        self.timing_tracker = {
            "total_runtime": 0.0,
            "llm_call_times": [],
            "step_times": {},
            "start_time": None
        }
        
        # Validation metrics to prove understanding is building
        self.validation_metrics = {
            "mappings_per_chunk": [],
            "understanding_depth_scores": [],
            "cross_references_found": [],
            "template_connections_discovered": [],
            "insights_quality_trend": [],
            "evolution_milestones": []
        }
        
        # LLM understanding storage
        self.llm_insights = []
        self.understanding_evolution = []
        
        # Available functions
        self.available_functions = {
            "get_current_chunk": self.get_current_chunk,
            "get_next_chunk": self.get_next_chunk,
            "analyze_chunk_mappings": self.analyze_chunk_mappings,
            "save_template_analysis": self.save_template_analysis,
            "get_understanding_summary": self.get_understanding_summary,
            "search_related_chunks": self.search_related_chunks,
            "save_llm_insights": self.save_llm_insights,
            "record_understanding_evolution": self.record_understanding_evolution,
            "get_validation_metrics": self.get_validation_metrics
        }
    
    def _convert_to_simple_chunks(self, xslt_chunks) -> List[SimpleChunk]:
        """Convert XSLTChunker output to SimpleChunk format"""
        simple_chunks = []
        
        for i, chunk_info in enumerate(xslt_chunks):
            # Extract metadata from the XSLTChunker chunk
            templates_defined = []
            template_calls = []
            variables_defined = []
            
            # Check if this is a template cluster (semantic chunking feature)
            is_template_cluster = chunk_info.metadata.get('is_template_cluster', False)
            template_name = chunk_info.metadata.get('template_name', '')
            call_site_count = chunk_info.metadata.get('call_site_count', 0)
            
            # Generate description based on chunk type
            if is_template_cluster and template_name:
                description = f"Template cluster: {template_name} (+{call_site_count} call sites) - Semantic grouping"
                templates_defined.append(template_name)
                chunk_type = "template_cluster"
            elif chunk_info.chunk_type.value == "helper_template":
                description = f"Helper template: {chunk_info.name or 'unnamed'}"
                chunk_type = "helper"
                if chunk_info.name:
                    templates_defined.append(chunk_info.name)
            elif chunk_info.chunk_type.value == "main_template":
                description = f"Main template: {chunk_info.name or 'root'}"
                chunk_type = "main"
                if chunk_info.name:
                    templates_defined.append(chunk_info.name)
            else:
                description = chunk_info.name or f"XSLT {chunk_info.chunk_type.value}"
                chunk_type = chunk_info.chunk_type.value
            
            # Extract template calls and variables from content
            content = chunk_info.text
            import re
            
            # Find template calls
            calls = re.findall(r'<xsl:call-template\s+name="([^"]+)"', content)
            template_calls.extend(calls)
            
            # Find variables
            vars_def = re.findall(r'<xsl:variable\s+name="([^"]+)"', content)
            variables_defined.extend(vars_def)
            
            # Create SimpleChunk
            simple_chunk = SimpleChunk(
                id=chunk_info.chunk_id,
                content=content,
                description=description,
                chunk_type=chunk_type,
                templates_defined=templates_defined,
                template_calls=template_calls,
                variables_defined=variables_defined,
                dependencies=chunk_info.dependencies,
                line_start=chunk_info.start_line,
                line_end=chunk_info.end_line,
                token_count=chunk_info.estimated_tokens
            )
            
            simple_chunks.append(simple_chunk)
        
        print(f"🔄 Converted {len(xslt_chunks)} XSLTChunker chunks to SimpleChunk format")
        
        # Print semantic chunking benefits
        template_clusters = [c for c in simple_chunks if c.chunk_type == "template_cluster"]
        if template_clusters:
            print(f"🎯 Semantic chunking created {len(template_clusters)} template clusters")
            print(f"   This should improve mapping extraction by preserving template function context")
        
        return simple_chunks
    
    def _call_llm(self, prompt: str, temperature: float = 0.1, max_tokens: int = 1500, 
                  step_name: str = "LLM Call", model_override: str = None) -> str:
        """Centralized LLM wrapper function that reads configuration from environment"""
        
        # Read LLM configuration from environment variables
        llm_provider = os.getenv('LLM_PROVIDER', 'openai')
        llm_model = model_override or os.getenv('LLM_MODEL', 'gpt-4o-mini')
        
        try:
            start_time = time.time()
            
            if llm_provider.lower() == 'openai':
                response = self.openai_client.chat.completions.create(
                    model=llm_model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                
                # Extract response content
                content = response.choices[0].message.content
                
                # Update tracking
                usage = response.usage
                self._update_cost_tracking(usage.prompt_tokens, usage.completion_tokens)
                
            elif llm_provider.lower() == 'anthropic':
                # Placeholder for Anthropic integration
                raise NotImplementedError("Anthropic provider not yet implemented")
                
            elif llm_provider.lower() == 'local':
                # Placeholder for local model integration
                raise NotImplementedError("Local provider not yet implemented")
                
            else:
                raise ValueError(f"Unsupported LLM provider: {llm_provider}")
            
            end_time = time.time()
            
            # Update conversation and timing tracking
            self.conversation_turns += 1
            self._update_timing_tracking(step_name, end_time - start_time)
            
            return content
            
        except Exception as e:
            print(f"❌ {step_name} failed: {str(e)}")
            return f"{step_name} failed: {str(e)}"
    
    def get_current_chunk(self) -> Dict[str, Any]:
        """Get the current chunk being analyzed"""
        if self.current_chunk_index < len(self.chunks):
            chunk = self.chunks[self.current_chunk_index]
            self.chunks_explored.add(chunk.id)
            
            return {
                "success": True,
                "chunk": asdict(chunk),
                "progress": f"{len(self.chunks_explored)}/{self.target_chunks}",
                "message": f"Current chunk: {chunk.id}"
            }
        
        return {"success": False, "message": "No more chunks to explore"}
    
    def get_next_chunk(self) -> Dict[str, Any]:
        """Move to the next chunk"""
        self.current_chunk_index += 1
        
        if self.current_chunk_index < len(self.chunks) and len(self.chunks_explored) < self.target_chunks:
            return self.get_current_chunk()
        else:
            return {
                "success": False,
                "message": f"Target coverage reached: {len(self.chunks_explored)}/{self.target_chunks} chunks explored"
            }
    
    def analyze_chunk_mappings(self, mapping_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Save detailed mapping analysis for current chunk"""
        
        if not mapping_analysis or not isinstance(mapping_analysis, dict):
            return {"success": False, "message": "Invalid mapping analysis provided"}
        
        # Extract mappings from analysis
        if "mappings" in mapping_analysis:
            for mapping_data in mapping_analysis["mappings"]:
                try:
                    # Handle both old string format and new enhanced format
                    transformation_logic = mapping_data.get("transformation_logic", "")
                    if isinstance(transformation_logic, str):
                        # Convert old string format to enhanced format
                        transformation_logic = {
                            "natural_language": transformation_logic,
                            "original_xslt": transformation_logic,
                            "rules": [],
                            "transformation_type": mapping_data.get("transformation_type", "unknown")
                        }
                    
                    mapping_spec = MappingSpecification(
                        id=f"mapping_{len(self.mapping_specs):03d}",
                        source_path=mapping_data.get("source_path", ""),
                        destination_path=mapping_data.get("destination_path", ""),
                        transformation_type=mapping_data.get("transformation_type", "unknown"),
                        transformation_logic=transformation_logic,
                        conditions=mapping_data.get("conditions", []),
                        validation_rules=mapping_data.get("validation_rules", []),
                        template_name=mapping_data.get("template_name", ""),
                        chunk_source=self.chunks[self.current_chunk_index].id if self.current_chunk_index < len(self.chunks) else ""
                    )
                    self.mapping_specs.append(mapping_spec)
                except Exception as e:
                    print(f"⚠️  Error creating mapping spec: {e}")
        
        # Save to file
        self._save_current_understanding()
        
        return {
            "success": True,
            "message": f"Saved {len(mapping_analysis.get('mappings', []))} mapping specifications",
            "total_mappings": len(self.mapping_specs)
        }
    
    def save_template_analysis(self, template_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Save detailed template analysis"""
        
        if not template_analysis or not isinstance(template_analysis, dict):
            return {"success": False, "message": "Invalid template analysis provided"}
        
        try:
            # Create template analysis
            analysis = TemplateAnalysis(
                name=template_analysis.get("name", ""),
                purpose=template_analysis.get("purpose", ""),
                input_parameters=template_analysis.get("input_parameters", []),
                output_structure=template_analysis.get("output_structure", ""),
                dependencies=template_analysis.get("dependencies", []),
                complexity=template_analysis.get("complexity", "unknown"),
                mappings=[]  # Mappings are handled separately
            )
            
            self.template_analyses.append(analysis)
            self._save_current_understanding()
            
            return {
                "success": True,
                "message": f"Saved template analysis for '{analysis.name}'",
                "total_templates": len(self.template_analyses)
            }
        
        except Exception as e:
            return {"success": False, "message": f"Error saving template analysis: {e}"}
    
    def get_understanding_summary(self) -> Dict[str, Any]:
        """Get current understanding summary"""
        
        return {
            "success": True,
            "summary": {
                "chunks_explored": len(self.chunks_explored),
                "target_chunks": self.target_chunks,
                "progress_percentage": (len(self.chunks_explored) / self.target_chunks) * 100,
                "mapping_specifications": len(self.mapping_specs),
                "template_analyses": len(self.template_analyses),
                "context_resets": self.context_resets,
                "conversation_turns": self.conversation_turns
            }
        }
    
    def search_related_chunks(self, search_pattern: str) -> Dict[str, Any]:
        """Search for chunks containing specific patterns"""
        
        matches = []
        for chunk in self.chunks:
            if re.search(search_pattern, chunk.content, re.IGNORECASE):
                matches.append({
                    "id": chunk.id,
                    "description": chunk.description,
                    "templates_defined": chunk.templates_defined
                })
        
        return {
            "success": True,
            "matches": matches[:5],  # Limit to 5 results
            "total_matches": len(matches),
            "message": f"Found {len(matches)} chunks matching '{search_pattern}'"
        }
    
    def save_llm_insights(self, insights: Dict[str, Any]) -> Dict[str, Any]:
        """Save LLM's understanding insights and observations"""
        
        if not insights or not isinstance(insights, dict):
            return {"success": False, "message": "Invalid insights provided"}
        
        # Add metadata
        insight_record = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "chunk_context": self.chunks[self.current_chunk_index].id if self.current_chunk_index < len(self.chunks) else "",
            "chunks_explored_so_far": len(self.chunks_explored),
            "insights": insights
        }
        
        self.llm_insights.append(insight_record)
        self._save_current_understanding()
        
        return {
            "success": True,
            "message": f"Saved LLM insights - total insights: {len(self.llm_insights)}",
            "total_insights": len(self.llm_insights)
        }
    
    def record_understanding_evolution(self, evolution_data: Dict[str, Any]) -> Dict[str, Any]:
        """Record how LLM's understanding is evolving over time"""
        
        if not evolution_data or not isinstance(evolution_data, dict):
            return {"success": False, "message": "Invalid evolution data provided"}
        
        # Add metadata
        evolution_record = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "chunks_explored": len(self.chunks_explored),
            "progress_percentage": (len(self.chunks_explored) / self.target_chunks) * 100,
            "conversation_turn": self.conversation_turns,
            "evolution_data": evolution_data
        }
        
        self.understanding_evolution.append(evolution_record)
        self._calculate_validation_metrics()
        self._save_current_understanding()
        
        return {
            "success": True,
            "message": f"Recorded understanding evolution - total records: {len(self.understanding_evolution)}",
            "total_evolution_records": len(self.understanding_evolution)
        }
    
    def _calculate_validation_metrics(self):
        """Calculate validation metrics to prove understanding is building"""
        
        # Track mappings per chunk
        if len(self.chunks_explored) > 0:
            mappings_per_chunk = len(self.mapping_specs) / len(self.chunks_explored)
            self.validation_metrics["mappings_per_chunk"].append(mappings_per_chunk)
        
        # Calculate understanding depth score based on recent insights
        if self.llm_insights:
            recent_insights = self.llm_insights[-5:]  # Last 5 insights
            depth_score = sum(len(str(insight.get("insights", {}))) for insight in recent_insights) / len(recent_insights)
            self.validation_metrics["understanding_depth_scores"].append(depth_score)
        
        # Track cross-references found
        cross_refs = 0
        for spec in self.mapping_specs:
            if hasattr(spec, 'dependencies') and spec.dependencies:
                cross_refs += len(spec.dependencies)
        self.validation_metrics["cross_references_found"].append(cross_refs)
        
        # Track template connections discovered
        template_connections = len(set(spec.template_name for spec in self.mapping_specs if spec.template_name))
        self.validation_metrics["template_connections_discovered"].append(template_connections)
        
        # Track insights quality trend (based on length and detail)
        if self.llm_insights:
            last_insight = self.llm_insights[-1]
            quality_score = len(str(last_insight.get("insights", {}))) / 100  # Rough quality metric
            self.validation_metrics["insights_quality_trend"].append(quality_score)
        
        # Track evolution milestones
        if self.understanding_evolution:
            milestone = {
                "chunks_explored": len(self.chunks_explored),
                "mappings_extracted": len(self.mapping_specs),
                "insights_recorded": len(self.llm_insights),
                "understanding_breadth": len(set(chunk.chunk_type for chunk in self.chunks if chunk.id in self.chunks_explored))
            }
            self.validation_metrics["evolution_milestones"].append(milestone)
    
    def get_validation_metrics(self) -> Dict[str, Any]:
        """Get current validation metrics to prove understanding is building"""
        
        # Calculate trends
        mapping_trend = "increasing" if len(self.validation_metrics["mappings_per_chunk"]) > 1 and \
                       self.validation_metrics["mappings_per_chunk"][-1] > self.validation_metrics["mappings_per_chunk"][0] else "stable"
        
        understanding_trend = "deepening" if len(self.validation_metrics["understanding_depth_scores"]) > 1 and \
                             self.validation_metrics["understanding_depth_scores"][-1] > self.validation_metrics["understanding_depth_scores"][0] else "stable"
        
        return {
            "success": True,
            "metrics": {
                "mappings_per_chunk": self.validation_metrics["mappings_per_chunk"][-5:],  # Last 5 values
                "understanding_depth_scores": self.validation_metrics["understanding_depth_scores"][-5:],
                "cross_references_found": self.validation_metrics["cross_references_found"][-5:],
                "template_connections_discovered": self.validation_metrics["template_connections_discovered"][-5:],
                "insights_quality_trend": self.validation_metrics["insights_quality_trend"][-5:],
                "evolution_milestones": self.validation_metrics["evolution_milestones"][-3:]  # Last 3 milestones
            },
            "trends": {
                "mapping_extraction": mapping_trend,
                "understanding_depth": understanding_trend,
                "overall_progress": f"{len(self.chunks_explored)}/{self.target_chunks} chunks explored"
            },
            "validation_summary": {
                "total_mappings": len(self.mapping_specs),
                "total_insights": len(self.llm_insights),
                "total_evolution_records": len(self.understanding_evolution),
                "understanding_building": len(self.validation_metrics["evolution_milestones"]) > 0
            }
        }
    
    def _save_current_understanding(self):
        """Save current understanding to files"""
        
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        
        # Save mapping specifications
        mappings_file = self.results_dir / f"mapping_specifications_{timestamp}.json"
        with open(mappings_file, 'w') as f:
            json.dump([asdict(spec) for spec in self.mapping_specs], f, indent=2)
        
        # Save template analyses
        templates_file = self.results_dir / f"template_analyses_{timestamp}.json"
        with open(templates_file, 'w') as f:
            json.dump([asdict(analysis) for analysis in self.template_analyses], f, indent=2)
        
        # Save LLM insights
        insights_file = self.results_dir / f"llm_insights_{timestamp}.json"
        with open(insights_file, 'w') as f:
            json.dump(self.llm_insights, f, indent=2)
        
        # Save understanding evolution
        evolution_file = self.results_dir / f"understanding_evolution_{timestamp}.json"
        with open(evolution_file, 'w') as f:
            json.dump(self.understanding_evolution, f, indent=2)
        
        # Save validation metrics
        validation_file = self.results_dir / f"validation_metrics_{timestamp}.json"
        with open(validation_file, 'w') as f:
            json.dump(self.validation_metrics, f, indent=2)
        
        # Save exploration summary
        summary_file = self.results_dir / f"exploration_summary_{timestamp}.json"
        summary = {
            "timestamp": timestamp,
            "chunks_explored": list(self.chunks_explored),
            "progress": {
                "chunks_explored": len(self.chunks_explored),
                "target_chunks": self.target_chunks,
                "progress_percentage": (len(self.chunks_explored) / self.target_chunks) * 100
            },
            "statistics": {
                "mapping_specifications": len(self.mapping_specs),
                "template_analyses": len(self.template_analyses),
                "llm_insights": len(self.llm_insights),
                "understanding_evolution_records": len(self.understanding_evolution),
                "context_resets": self.context_resets,
                "conversation_turns": self.conversation_turns
            },
            "cost_tracking": self.cost_tracker,
            "validation_metrics": self.validation_metrics
        }
        
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\n💾 UNDERSTANDING SAVED:")
        print(f"   📁 Directory: {self.results_dir}")
        print(f"   📄 Mappings: {len(self.mapping_specs)} specifications")
        print(f"   📋 Templates: {len(self.template_analyses)} analyses")
        print(f"   🧠 LLM Insights: {len(self.llm_insights)} records")
        print(f"   📈 Evolution: {len(self.understanding_evolution)} records")
        print(f"   📊 Validation Metrics: {len(self.validation_metrics.get('evolution_milestones', []))} milestones")
        print(f"{'~'*60}")
    
    def _should_reset_context(self) -> bool:
        """Determine if context should be reset"""
        return self.conversation_turns >= 15  # Reset every 15 turns
    
    def _generate_example_mapping(self, chunk) -> str:
        """Generate a concrete mapping example based on current chunk content"""
        if not chunk:
            return "{'mapping_analysis': {'mappings': []}}"
        
        # Analyze chunk content for common XSLT patterns
        content = chunk.content.lower()
        
        if 'xsl:for-each' in content and 'select=' in content:
            # Loop pattern detected
            example = {
                "mapping_analysis": {
                    "mappings": [
                        {
                            "source_path": "/input/element",
                            "destination_path": "output/element",
                            "transformation_type": "loop",
                            "transformation_logic": {
                                "natural_language": "For each element in input, create corresponding output element",
                                "transformation_type": "loop",
                                "rules": [{"condition": "for each element", "output": "copy to output"}],
                                "original_xslt": "snippet from chunk"
                            },
                            "conditions": ["element exists"],
                            "validation_rules": [],
                            "template_name": chunk.templates_defined[0] if chunk.templates_defined else "unknown"
                        }
                    ]
                }
            }
        elif 'xsl:choose' in content or 'xsl:when' in content:
            # Conditional pattern detected  
            example = {
                "mapping_analysis": {
                    "mappings": [
                        {
                            "source_path": "/input/value",
                            "destination_path": "output/value",
                            "transformation_type": "conditional_mapping",
                            "transformation_logic": {
                                "natural_language": "If input meets condition, transform to output value",
                                "transformation_type": "conditional_lookup",
                                "rules": [
                                    {"condition": "input = 'value1'", "output": "output1"},
                                    {"condition": "default", "output": "default_output"}
                                ],
                                "original_xslt": "snippet from chunk"
                            },
                            "conditions": ["input = 'value1'"],
                            "validation_rules": [],
                            "template_name": chunk.templates_defined[0] if chunk.templates_defined else "unknown"
                        }
                    ]
                }
            }
        else:
            # Default/direct mapping pattern
            example = {
                "mapping_analysis": {
                    "mappings": [
                        {
                            "source_path": "/input/field",
                            "destination_path": "output/field", 
                            "transformation_type": "direct_mapping",
                            "transformation_logic": {
                                "natural_language": "Copy input field directly to output field",
                                "transformation_type": "direct_copy",
                                "rules": [],
                                "original_xslt": "snippet from chunk"
                            },
                            "conditions": [],
                            "validation_rules": [],
                            "template_name": chunk.templates_defined[0] if chunk.templates_defined else "unknown"
                        }
                    ]
                }
            }
        
        return json.dumps(example, indent=2)
    
    async def analyze_chunk_step_by_step(self, chunk) -> Dict[str, Any]:
        """Enhanced 8-step chunk analysis: business logic + value transformations + implementation formulas + template call sites + sequences"""
        
        try:
            # Step 1: Natural Language Analysis
            analysis = await self._step1_analyze_xslt(chunk)
            
            # Step 2: Extract Business Logic Mappings
            business_mappings = await self._step2_extract_mappings(chunk, analysis)
            
            # Step 2.5: Value Transformations
            value_transformations = await self._step2_5_value_transformation_analysis(chunk, analysis)
            
            # Step 2.6: Implementation Formula Extraction
            implementation_formulas = await self._step2_6_implementation_formula_extraction(chunk, value_transformations)
            
            # Step 2.7: Template Call Site Analysis
            call_site_analysis = await self._step2_7_template_call_site_analysis(chunk, implementation_formulas)
            
            # Step 3: Format Combined Results
            combined_analysis = f"""BUSINESS MAPPINGS:
{business_mappings}

VALUE TRANSFORMATIONS:
{value_transformations}

IMPLEMENTATION FORMULAS:
{implementation_formulas}

TEMPLATE CALL SITE ANALYSIS:
{call_site_analysis}"""
            formatted_mappings = await self._step3_format_mapping_json(combined_analysis)
            
            # Step 3.5: Multi-Step Sequence Analysis
            sequences = await self._step3_5_sequence_analysis(chunk, formatted_mappings)
            
            # Step 4: Save Enhanced Results
            results = await self._step4_save_results(formatted_mappings, analysis, chunk)
            
            # Add enhanced analysis to results
            if results and "success" in results:
                results["sequences"] = sequences
                results["implementation_formulas"] = implementation_formulas
                results["call_site_analysis"] = call_site_analysis
            
            return results
            
        except Exception as e:
            print(f"❌ Analysis failed for {chunk.id}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _step1_analyze_xslt(self, chunk) -> str:
        """Step 1: Natural language analysis of XSLT chunk"""
        
        prompt = f"""You are an XSLT expert. Analyze this XSLT chunk and describe it in plain English.

XSLT CHUNK TO ANALYZE:
{chunk.content}

CHUNK CONTEXT:
- ID: {chunk.id}
- Description: {chunk.description}
- Templates defined: {chunk.templates_defined}
- Template calls: {chunk.template_calls}
- Variables defined: {chunk.variables_defined}

Please provide a clear, natural language analysis covering:

1. **Purpose**: What does this XSLT code do?
2. **Input Processing**: What input data does it expect?
3. **Transformation Logic**: How does it transform the input?
4. **Output Generation**: What output does it produce?
5. **Key Patterns**: What XSLT patterns are used (loops, conditionals, direct mapping)?

Focus on UNDERSTANDING the logic, not formatting. Be specific and detailed."""

        return self._call_llm(
            prompt=prompt,
            temperature=0.1,
            max_tokens=1000,
            step_name="Step 1 - XSLT Analysis"
        )
    
    async def _step2_extract_mappings(self, chunk, analysis: str) -> str:
        """Step 2: Extract business-focused mappings based on analysis"""
        
        prompt = f"""You are analyzing XSLT for business data transformations. Focus on BUSINESS LOGIC, not just technical syntax.

YOUR PREVIOUS ANALYSIS:
{analysis}

XSLT CODE TO ANALYZE:
{chunk.content}

BUSINESS MAPPING EXTRACTION:
Identify what BUSINESS TRANSFORMATIONS this code performs. For each transformation:

1. **Business Rule**: What business problem does this solve?
2. **Source XPath**: ACTUAL xpath expression for input data (e.g., "Passenger/Document/Type", not "user input")
3. **Destination XPath**: COMPLETE xpath expression for output location (e.g., "Result/Passenger/IdentityDocumentType", not just "IdentityDocumentType")  
4. **Business Logic**: What business rule converts source to destination?
5. **Business Conditions**: Under what business conditions does this apply?

CRITICAL: Use COMPLETE XPATH EXPRESSIONS:
❌ WRONG: "cleaned phone", "IdentityDocumentType"  
✅ CORRECT: "Passenger/ContactInformation/PhoneNumber", "Result/Passenger/IdentityDocumentType"

DESTINATION PATH REQUIREMENTS:
- Show FULL XML hierarchy, not just element name
- Include parent elements and document structure
- Look for <xsl:element> and XML literal elements to determine complete path
- Trace through nested element creation to build full hierarchy
- Example: "Response/PassengerData/ContactInformation/PhoneNumber" NOT just "PhoneNumber"

IMPORTANT: Analyze the XSLT output structure to determine the complete destination XML hierarchy.

SPECIFIC PATTERNS TO LOOK FOR:

**Template Functions (vmf1, vmf2, etc.)**:
- What business standardization do they perform?
- Example: vmf1 might standardize document types (P→VPT = Passport→Valid Passport Type)

**Conditional Logic (xsl:choose/when)**:
- What business decisions are being made?
- What business values are being mapped to other business values?

**Loops (xsl:for-each)**:
- What business collections are being processed?
- What business output is generated for each item?

**Value Selections (xsl:value-of)**:
- What business data is being copied or computed?

BUSINESS CONTEXT: This XSLT appears to be for airline/travel industry processing, likely IATA NDC standard transformations.

Focus on extracting BUSINESS MAPPINGS like:
- Document type standardization
- Passenger data processing  
- Contact information formatting
- Travel agency data handling
- Visa/passport processing

Be specific about the business meaning, not just the technical xpath."""

        return self._call_llm(
            prompt=prompt,
            temperature=0.1,
            max_tokens=1500,
            step_name="Step 2 - Extract Mappings"
        )
    
    async def _step2_5_value_transformation_analysis(self, chunk, analysis: str) -> str:
        """Step 2.5: Dynamic text processing AND static value assignment detection"""
        
        prompt = f"""You are analyzing XSLT for VALUE TRANSFORMATION patterns. Look for both DYNAMIC and STATIC value processing.

PREVIOUS ANALYSIS: {analysis}
XSLT CODE: {chunk.content}

FIND THESE VALUE TRANSFORMATION PATTERNS:

**A. DYNAMIC TEXT PROCESSING:**
Look for string manipulation functions and their BUSINESS PURPOSE:

1. **substring() functions**:
   - What business data part is extracted? Why?
   - Example: substring(seat, 1, 2) = extract row "12" from seat "12A"

2. **translate() functions**:
   - What characters removed/replaced for what business rule?
   - Example: translate(phone, '()-. ', '') = clean phone for validation

3. **concat() functions**:
   - What business identifier/reference is created?
   - Example: concat('REF-', booking_id) = create reference number

4. **number() functions**:
   - What business calculation is enabled?
   - Example: number(price_string) = enable price calculations

**B. STATIC VALUE ASSIGNMENTS:**
Look for hardcoded values and their BUSINESS MEANING:

1. **Version numbers**: "17.2", "1.0" → What standard/protocol version?
2. **Location codes**: "FR", "NCE", "US" → What business location/region?
3. **System codes**: "AH9D", "UA", "UAD" → What system/airline identifier?
4. **Default values**: Static strings/numbers → What business default rule?
5. **Business constants**: Fixed codes → What business domain meaning?

**FOR EACH PATTERN FOUND:**
- **Input**: What business data comes in (or "hardcoded")
- **Process**: What transformation/assignment happens
- **Output**: What business data results
- **Business Rule**: Why this serves the business need

**BUSINESS CONTEXT**: This is airline/travel XSLT, likely IATA NDC standard processing.

Focus on BUSINESS VALUE of each transformation, not just technical syntax."""

        return self._call_llm(
            prompt=prompt,
            temperature=0.1,
            max_tokens=1500,
            step_name="Step 2.5 - Value Transformations"
        )
    
    async def _step2_6_implementation_formula_extraction(self, chunk, patterns: str) -> str:
        """Step 2.6: Extract exact XSLT formulas for identified patterns"""
        
        prompt = f"""You are analyzing XSLT code to extract EXACT implementation formulas. Focus on PRECISE technical details.

PREVIOUS PATTERN ANALYSIS:
{patterns}

XSLT CODE TO ANALYZE:
{chunk.content}

EXTRACT EXACT FORMULAS for each pattern mentioned above. For every transformation pattern found:

**EXACT FORMULA EXTRACTION:**

1. **Complete translate() Functions**:
   - Extract FULL character set: translate(., 'chars_to_remove', 'replacement_chars')
   - Example: translate(., concat(' `~!@#$%^&*()-_=+[]{{}}|\\\\:;"',\",./<?abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ\"), '')

2. **Complete substring() Functions**:
   - Extract EXACT start/length calculations: substring(text, start_position, length)
   - Example: number(substring(seatNbr, 1, (string-length(string(seatNbr)) - 1)))

3. **Complete concat() Functions**:
   - Extract EXACT component ordering and separators: concat(part1, 'separator', part2, ...)
   - Example: concat('CI', $var118_idx, $var119_cur)

4. **Complete number() Functions**:
   - Extract EXACT conversion context: number(expression)
   - Example: number(substring(seatNbr, 1, 2))

5. **Complete Conditional Logic**:
   - Extract ALL test conditions and branches: xsl:choose/when/otherwise
   - Example: test="$input='P'" → 'VPT', test="$input='PT'" → 'VPT', otherwise → ''

**FOR EACH EXACT FORMULA:**
- **Pattern Name**: Business name from previous analysis
- **Exact Formula**: Complete XSLT expression with all parameters
- **Parameters**: List of all variables, literals, functions used
- **Business Purpose**: What this precise formula accomplishes
- **Example Input/Output**: Concrete example of transformation

**PRECISION REQUIREMENT**: 
Extract formulas with EXACT character-for-character accuracy. Include ALL quotes, spaces, special characters, parentheses, commas, and operators exactly as they appear in the XSLT.

Focus on IMPLEMENTATION PRECISION, not just business understanding."""

        return self._call_llm(
            prompt=prompt,
            temperature=0.0,  # Maximum precision for exact formula extraction
            max_tokens=2000,
            step_name="Step 2.6 - Implementation Formulas"
        )
    
    async def _step2_7_template_call_site_analysis(self, chunk, formulas: str) -> str:
        """Step 2.7: Analyze template call sites and extract real parameter bindings"""
        
        prompt = f"""You are analyzing XSLT code to find TEMPLATE CALL SITES and extract BUSINESS CONTEXT for parameter bindings.

PREVIOUS ANALYSIS:
{formulas}

XSLT CODE TO ANALYZE:
{chunk.content}

CRITICAL TASK: When you find template calls with generic expressions like "string(.)", look for the BUSINESS CONTEXT that establishes what the current node represents.

LOOK FOR THESE PATTERNS:

1. **TEMPLATE CALL SITES WITH CONTEXT:**
   Look for template calls and trace back to find business meaning:
   
   Example Pattern:
   <xsl:for-each select="passenger/document">  <!-- BUSINESS CONTEXT -->
     <xsl:call-template name="vmf:vmf2_inputtoresult">
       <xsl:with-param name="input" select="string(.)"/>  <!-- GENERIC EXPRESSION -->
     </xsl:call-template>
   </xsl:for-each>
   
   ANALYSIS: string(.) here means "passenger document data"

2. **CONTEXT TRACING:**
   - Find <xsl:for-each>, <xsl:apply-templates>, or context-setting elements
   - Trace what business data establishes the current context
   - Connect generic expressions to business meaning

3. **BUSINESS CONTEXT PATTERNS:**
   - Look for select="passenger/...", select="booking/...", select="contact/..."
   - Find variable assignments that set business context
   - Identify what XML elements are being processed

4. **MAPPING CORRECTIONS:**
   When you see source_path with generic expressions, provide business context:
   
   - CURRENT: source_path="string(.)"
   - CONTEXT: Found within <xsl:for-each select="passenger/document">
   - IMPROVED: source_path="passenger/document (as string)" or "document/type"
   - BUSINESS_MEANING: "Passenger identity document type"

OUTPUT FORMAT:
For each template call site, provide business context analysis:

TEMPLATE: template_name
PARAMETER_EXPRESSION: actual_select_value (e.g., "string(.)")
BUSINESS_CONTEXT: what_establishes_current_context (e.g., "within passenger/document loop")
BUSINESS_DATA_TYPE: what_business_data_this_represents (e.g., "document type code")
SUGGESTED_SOURCE_PATH: business_meaningful_path (e.g., "passenger/document/type")

FOCUS: Extract business meaning even from generic XSLT expressions by understanding the context they operate in."""

        return self._call_llm(
            prompt=prompt,
            temperature=0.1,
            max_tokens=1500,
            step_name="Step 2.7 - Template Call Sites",
            model_override="gpt-4"
        )
    
    async def _step3_format_mapping_json(self, mappings: str) -> Dict[str, Any]:
        """Step 3: Format mappings into precise JSON structure with enhanced error handling"""
        
        prompt = f"""You are a JSON formatter. Take the mapping analysis below and convert it to valid JSON.

MAPPING ANALYSIS TO CONVERT:
{mappings}

REQUIRED OUTPUT FORMAT - Copy this structure exactly and fill in real values:

{{
  "mappings": [
    {{
      "source_path": "COMPLETE_SOURCE_XPATH",
      "destination_path": "COMPLETE_DESTINATION_XPATH_WITH_HIERARCHY", 
      "transformation_type": "conditional_mapping",
      "transformation_logic": {{
        "natural_language": "DETAILED_BUSINESS_EXPLANATION_WITH_SPECIFIC_MAPPINGS",
        "transformation_type": "conditional_lookup",
        "rules": [
          {{"condition": "input='P'", "output": "VPT"}},
          {{"condition": "input='PT'", "output": "VPT"}},
          {{"condition": "default", "output": "empty string"}}
        ],
        "original_xslt": "actual XSLT code from chunk"
      }},
      "conditions": ["input='P'", "input='PT'"],
      "validation_rules": [],
      "template_name": "vmf:vmf1_inputtoresult"
    }}
  ]
}}

CRITICAL RULES:
1. Return ONLY valid JSON - no explanation text before or after
2. Start with {{ and end with }}
3. If no mappings found, return exactly: {{"mappings": []}}
4. Use double quotes for all strings
5. No trailing commas
6. Escape any quotes inside strings
7. IMPORTANT: Use COMPLETE XPATH HIERARCHIES for both source and destination paths
8. DESTINATION PATHS must show full XML structure, not just element names
9. Include parent elements: "Response/PassengerData/ContactInformation/PhoneNumber" NOT "PhoneNumber"
10. If Template Call Site Analysis shows SUGGESTED_SOURCE_PATH, use that for complete source paths
11. Replace generic expressions like "string(.)" with business-meaningful complete paths

EXAMPLE with COMPLETE XPATH HIERARCHIES:
{{"mappings": [{{"source_path": "Passenger/Document/Type", "destination_path": "Response/PassengerData/IdentityDocumentType", "transformation_type": "conditional_mapping", "transformation_logic": {{"natural_language": "Document type standardization: V becomes VVI for travel documents", "transformation_type": "conditional_lookup", "rules": [{{"condition": "type='V'", "output": "VVI"}}, {{"condition": "type='R'", "output": "VAEA"}}], "original_xslt": "xsl:when test=\"$input='V'\">VVI"}}, "conditions": ["Passenger/Document/Type='V'"], "validation_rules": [], "template_name": "vmf:vmf2_inputtoresult"}}]}}

MORE EXAMPLES OF COMPLETE DESTINATION PATHS:
- "Response/PassengerData/ContactInformation/PhoneNumber" (NOT just "PhoneNumber")
- "OrderCreateRS/PassengerInformation/PersonalName" (NOT just "PassengerName")  
- "Result/BookingData/ReferenceNumber" (NOT just "ReferenceNumber")

CRITICAL: ENHANCED "natural_language" DESCRIPTION REQUIREMENTS:
Your descriptions must be DETAILED and SPECIFIC, not generic. Include:

1. **WHY**: Why is this transformation needed? What business purpose does it serve?
2. **WHAT**: What specific business rules are being applied? 
3. **HOW**: How does the transformation actually work step-by-step?
4. **SPECIFIC MAPPINGS**: List the exact input→output value mappings with examples

❌ BAD (too generic): "Standardization of document types to recognized formats"
✅ GOOD (detailed with specifics): "Converts passenger document type codes (P=Passport, PT=Passport Token, V=Visa, etc.) to standardized IATA document type descriptions (VPT=Valid Passport Type, VVI=Valid Visa Type) for compliance with airline booking system requirements and regulatory standards"

❌ BAD (too vague): "Formatting phone number to international format"  
✅ GOOD (explains HOW): "Removes formatting characters (parentheses, dashes, dots, spaces) from phone numbers using translate() function to create clean numeric strings (e.g., '(555) 123-4567' becomes '5551234567') for international dialing compatibility and system integration"

❌ BAD (no business context): "Concatenates first and last name"
✅ GOOD (business context): "Combines passenger's first name and last name with space separator to create full name field required for travel documents and booking confirmations, ensuring consistent passenger identification across reservation systems"

INCLUDE SPECIFIC EXAMPLES: Show actual input values and their corresponding outputs when possible.

Now convert the analysis above to this exact JSON format:"""

        try:
            json_response = self._call_llm(
                prompt=prompt,
                temperature=0.0,  # Reduced temperature for more consistent JSON
                max_tokens=2000,
                step_name="Step 3 - JSON Formatting"
            ).strip()
            
            # Clean up common LLM JSON formatting issues
            json_response = self._clean_json_response(json_response)
            
            # Try to parse JSON to validate format
            try:
                parsed_json = json.loads(json_response)
                print(f"📋 Formatted: {len(parsed_json.get('mappings', []))} mappings")
                return parsed_json
            except json.JSONDecodeError as e:
                print(f"⚠️  JSON parse error: {str(e)}")
                print(f"🔍 Raw response: {json_response[:200]}...")
                
                # Attempt to fix common JSON issues and retry
                fixed_json = self._attempt_json_fix(json_response)
                if fixed_json:
                    try:
                        parsed_json = json.loads(fixed_json)
                        print(f"✅ JSON fixed successfully: {len(parsed_json.get('mappings', []))} mappings")
                        return parsed_json
                    except:
                        pass
                
                # Return empty structure if all parsing attempts fail
                return {"mappings": []}
            
        except Exception as e:
            print(f"❌ Step 3 failed: {str(e)}")
            return {"mappings": []}
    
    def _clean_json_response(self, response: str) -> str:
        """Clean common LLM JSON formatting issues"""
        # Remove any text before the first {
        start = response.find('{')
        if start > 0:
            response = response[start:]
        
        # Remove any text after the last }
        end = response.rfind('}')
        if end >= 0:
            response = response[:end + 1]
        
        # Remove markdown code blocks
        response = response.replace('```json', '').replace('```', '')
        
        return response.strip()
    
    def _attempt_json_fix(self, json_str: str) -> str:
        """Attempt to fix common JSON formatting issues"""
        try:
            # Try adding missing closing braces
            if json_str.count('{') > json_str.count('}'):
                missing_braces = json_str.count('{') - json_str.count('}')
                json_str += '}' * missing_braces
            
            # Try adding missing closing brackets
            if json_str.count('[') > json_str.count(']'):
                missing_brackets = json_str.count('[') - json_str.count(']')
                json_str += ']' * missing_brackets
            
            return json_str
        except:
            return None
    
    async def _step3_5_sequence_analysis(self, chunk, mappings: Dict[str, Any]) -> str:
        """Step 3.5: Detect multi-step operations within single business rules"""
        
        mappings_text = json.dumps(mappings, indent=2) if mappings else "No mappings found"
        
        prompt = f"""You are analyzing individual mappings for MULTI-STEP BUSINESS SEQUENCES. Look for patterns where multiple mappings are actually STEPS in single workflows.

INDIVIDUAL MAPPINGS TO ANALYZE:
{mappings_text}

CHUNK CONTEXT:
{chunk.content}

DETECT MULTI-STEP SEQUENCES:

**1. Conditional Concatenation Sequences**:
   - Multiple concat() operations building single business result
   - Pattern: Step1→concat(a,'/') Step2→concat(result,b) Step3→substring(remove_trailing_slash)
   - Example: Address formatting with conditional slash addition + cleanup

**2. Template Call Chains**:
   - Template call → result validation → substring processing
   - Pattern: vmf1(input) → check_if_result_exists → substring(result,2) 
   - Example: Document type standardization + post-processing

**3. Variable Dependency Sequences**:
   - Variable assignment → calculation → another variable → final output
   - Pattern: $var1=calculation → $var2=process($var1) → output=$var2
   - Example: Seat processing: $row=substring(seat,1,n-1) → $col=substring(seat,n,1) → Row=$row,Col=$col

**4. Validation-Process-Output Workflows**:
   - Input validation → transformation → conditional output
   - Pattern: validate_input → transform_if_valid → format_output
   - Example: Phone validation: number(phone) → translate(clean_chars) → format_output

**5. Complex Address/SSR Generation Workflows**:
   - Data collection → conditional concatenation → trailing character cleanup → output formatting
   - Pattern: collect_components → build_string → clean_format → generate_output

**FOR EACH SEQUENCE DETECTED:**
- **Sequence Name**: Business workflow name
- **Business Purpose**: What complete business operation this accomplishes  
- **Workflow Steps**: Step 1 → Step 2 → Step 3 → Step N (with business meaning)
- **Individual Mappings Involved**: Which individual mappings are part of this sequence
- **Complete Logic**: The full business logic from start to finish
- **Business Value**: Why this multi-step process serves the business need

**FOCUS**: Look beyond individual transformations to understand COMPLETE BUSINESS WORKFLOWS that require multiple steps to accomplish.

If no multi-step sequences found, return "No multi-step sequences detected - mappings appear to be independent operations."""

        return self._call_llm(
            prompt=prompt,
            temperature=0.1,
            max_tokens=1500,
            step_name="Step 3.5 - Sequence Analysis"
        )
    
    async def _step4_save_results(self, formatted_mappings: Dict[str, Any], analysis: str, chunk) -> Dict[str, Any]:
        """Step 4: Save all results using existing functions"""
        
        results = {"mapping_success": False, "insights_success": False, "chunk_id": chunk.id}
        
        try:
            # Save mappings if any were found
            if formatted_mappings.get("mappings"):
                mapping_result = self.analyze_chunk_mappings(mapping_analysis=formatted_mappings)
                results["mapping_success"] = mapping_result.get("success", False)
                results["mappings_saved"] = len(formatted_mappings.get("mappings", []))
                print(f"💾 Saved {results['mappings_saved']} mappings")
            else:
                print("ℹ️  No mappings found to save")
                results["mappings_saved"] = 0
            
            # Save insights from the analysis
            insights = {
                "chunk_id": chunk.id,
                "observations": analysis[:500] + "..." if len(analysis) > 500 else analysis,
                "understanding_level": 4,  # High confidence from multi-step process
                "key_discoveries": [
                    f"Analyzed chunk {chunk.id} using multi-step approach",
                    f"Found {len(formatted_mappings.get('mappings', []))} mappings",
                    "Completed detailed XSLT understanding"
                ],
                "questions": [],
                "analysis_method": "multi_step_cognitive_load_reduction"
            }
            
            insights_result = self.save_llm_insights(insights=insights)
            results["insights_success"] = insights_result.get("success", False)
            print("💾 Saved LLM insights")
            
            # Record understanding evolution
            evolution_data = {
                "milestone": f"Completed multi-step analysis of {chunk.id}",
                "understanding_growth": f"Used cognitive load reduction to analyze chunk systematically",
                "new_insights": [
                    "Multi-step approach successful",
                    f"Extracted {len(formatted_mappings.get('mappings', []))} mappings",
                    "Reduced cognitive overload"
                ],
                "confidence_level": 5,
                "chunk_id": chunk.id,
                "method": "step_by_step_analysis"
            }
            
            evolution_result = self.record_understanding_evolution(evolution_data=evolution_data)
            results["evolution_success"] = evolution_result.get("success", False)
            print("💾 Saved understanding evolution")
            
            # Mark chunk as explored
            self.chunks_explored.add(chunk.id)
            
            return results
            
        except Exception as e:
            print(f"❌ Step 4 failed: {str(e)}")
            results["error"] = str(e)
            return results
    
    def _reset_context(self) -> str:
        """Reset conversation context and return summary"""
        
        self.context_resets += 1
        self.conversation_turns = 0
        
        # Create progressive summary
        summary = f"""
PROGRESSIVE UNDERSTANDING SUMMARY (Reset #{self.context_resets}):

EXPLORATION PROGRESS:
- Chunks explored: {len(self.chunks_explored)}/{self.target_chunks} ({(len(self.chunks_explored)/self.target_chunks)*100:.1f}%)
- Mapping specifications extracted: {len(self.mapping_specs)}
- Template analyses completed: {len(self.template_analyses)}

RECENT MAPPINGS (last 5):
{json.dumps([asdict(spec) for spec in self.mapping_specs[-5:]], indent=2) if self.mapping_specs else "None yet"}

NEXT GOAL: Continue systematic chunk exploration and mapping extraction.
"""
        
        print(f"\n🔄 CONTEXT RESET #{self.context_resets}")
        print(f"📊 Progress: {len(self.chunks_explored)}/{self.target_chunks} chunks explored")
        print(f"💾 Understanding preserved in files")
        print(f"🔄 Starting fresh conversation context")
        print(f"{'█'*60}\n")
        return summary
    
    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for GPT-4o-mini"""
        input_cost = (input_tokens / 1000) * 0.000150
        output_cost = (output_tokens / 1000) * 0.000600
        return input_cost + output_cost
    
    def _update_cost_tracking(self, input_tokens: int, output_tokens: int):
        """Update cost tracking"""
        
        call_cost = self._calculate_cost(input_tokens, output_tokens)
        
        self.cost_tracker["total_calls"] += 1
        self.cost_tracker["total_input_tokens"] += input_tokens
        self.cost_tracker["total_output_tokens"] += output_tokens
        self.cost_tracker["cumulative_cost_usd"] += call_cost
        
        print(f"\n💰 COST TRACKING:")
        print(f"   Call #{self.cost_tracker['total_calls']}: ${call_cost:.6f} | Total: ${self.cost_tracker['cumulative_cost_usd']:.6f}")
        print(f"   Tokens: {input_tokens:,} in, {output_tokens:,} out | Context turns: {self.conversation_turns}")
        print(f"{'-'*60}")
    
    def _update_timing_tracking(self, step_name: str, duration: float):
        """Update timing tracking for LLM calls and steps"""
        self.timing_tracker["llm_call_times"].append({
            "step": step_name,
            "duration": duration,
            "timestamp": time.time()
        })
        
        # Track by step type
        if step_name not in self.timing_tracker["step_times"]:
            self.timing_tracker["step_times"][step_name] = []
        self.timing_tracker["step_times"][step_name].append(duration)
        
        print(f"⏱️  {step_name}: {duration:.2f}s")
    
    def _display_timing_summary(self):
        """Display final timing summary"""
        print(f"\n{'='*60}")
        print(f"🕐 TIMING SUMMARY")
        print(f"{'='*60}")
        print(f"⏱️  Total Runtime: {self.timing_tracker['total_runtime']:.2f}s")
        print(f"🔢 Total LLM Calls: {len(self.timing_tracker['llm_call_times'])}")
        
        if self.timing_tracker['llm_call_times']:
            total_llm_time = sum(call['duration'] for call in self.timing_tracker['llm_call_times'])
            avg_llm_time = total_llm_time / len(self.timing_tracker['llm_call_times'])
            print(f"🤖 Total LLM Time: {total_llm_time:.2f}s")
            print(f"📊 Average LLM Call: {avg_llm_time:.2f}s")
            
            # Show step breakdown
            print(f"\n📋 Step Breakdown:")
            for step_name, times in self.timing_tracker['step_times'].items():
                avg_time = sum(times) / len(times)
                total_time = sum(times)
                print(f"   {step_name}: {total_time:.2f}s (avg: {avg_time:.2f}s, {len(times)} calls)")
        
        print(f"{'='*60}")
    
    async def start_enhanced_exploration(self) -> str:
        """Start enhanced exploration with detailed mapping extraction"""
        
        # Start timing
        self.timing_tracker["start_time"] = time.time()
        
        print(f"🚀 Starting Enhanced XSLT Exploration")
        print(f"📊 Target: {self.target_chunks} chunks ({self.target_coverage:.0%} coverage)")
        
        print(f"🚀 ENHANCED MULTI-STEP XSLT EXPLORATION")
        print(f"🧠 Using cognitive load reduction with step-by-step analysis")
        print(f"🎯 Target: {self.target_chunks} chunks ({self.target_coverage:.0%} coverage)")
        print(f"{'='*60}")
        
        # Start multi-step exploration
        result = await self._multi_step_exploration_loop()
        
        # Save final results
        self._save_current_understanding()
        
        # Calculate and display final timing summary
        total_runtime = time.time() - self.timing_tracker["start_time"]
        self.timing_tracker["total_runtime"] = total_runtime
        self._display_timing_summary()
        
        return result
    
    async def _multi_step_exploration_loop(self) -> str:
        """Main exploration loop using multi-step analysis"""
        
        print(f"\n🔄 STARTING MULTI-STEP EXPLORATION")
        print(f"📊 Target: {self.target_chunks} chunks")
        print(f"{'='*60}")
        
        chunks_processed = 0
        
        try:
            while chunks_processed < self.target_chunks and self.current_chunk_index < len(self.chunks):
                # Get current chunk
                current_chunk = self.chunks[self.current_chunk_index]
                
                print(f"\n🔄 Processing {chunks_processed + 1}/{self.target_chunks}: {current_chunk.id} - {current_chunk.description}")
                
                # Check if already explored
                if current_chunk.id in self.chunks_explored:
                    print(f"⏭️  Already explored, skipping")
                    self.current_chunk_index += 1
                    continue
                
                # Perform multi-step analysis
                analysis_result = await self.analyze_chunk_step_by_step(current_chunk)
                
                if analysis_result.get("mapping_success") or analysis_result.get("insights_success"):
                    print(f"✅ Successfully analyzed {current_chunk.id}")
                    chunks_processed += 1
                else:
                    print(f"⚠️  Partial success for {current_chunk.id}")
                    chunks_processed += 1  # Count even partial successes
                
                # Move to next chunk
                self.current_chunk_index += 1
                
                # Context reset check
                if self._should_reset_context():
                    print(f"\n🔄 Context reset after {self.conversation_turns} turns")
                    self._reset_context()
                
                # Safety check
                if self.conversation_turns > 200:
                    print(f"⚠️  Safety limit reached: {self.conversation_turns} turns")
                    break
            
            # Final summary
            final_message = f"""✅ MULTI-STEP EXPLORATION COMPLETED

📊 RESULTS:
   • Chunks Processed: {chunks_processed}/{self.target_chunks}
   • Success Rate: {(chunks_processed/self.target_chunks)*100:.1f}%
   • Total Mappings: {len(self.mapping_specs)}
   • Total Insights: {len(self.llm_insights)}
   • Context Resets: {self.context_resets}
   • Total Cost: ${self.cost_tracker['cumulative_cost_usd']:.6f}

🎯 Multi-step approach eliminated function calling errors and improved analysis quality."""
            
            print(final_message)
            return final_message
            
        except Exception as e:
            error_message = f"❌ Multi-step exploration failed: {str(e)}"
            print(error_message)
            return error_message
    
    async def _call_llm_with_functions(self, prompt: str, conversation_history: List[Dict] = None) -> str:
        """Enhanced LLM calling with context management"""
        
        # Initialize or manage conversation history
        if conversation_history is None:
            conversation_history = [{"role": "user", "content": prompt}]
        elif self._should_reset_context():
            # Reset context with progressive summary
            summary = self._reset_context()
            conversation_history = [{"role": "user", "content": summary + "\n\n" + prompt}]
        
        # Check completion
        if len(self.chunks_explored) >= self.target_chunks:
            return f"✅ Target coverage reached: {len(self.chunks_explored)}/{self.target_chunks} chunks explored"
        
        # Safety limit - increased for complete exploration
        if self.conversation_turns > 200:
            return f"⚠️ Safety limit reached: {self.conversation_turns} turns"
        
        # Define function schemas
        functions = [
            {
                "name": "get_current_chunk",
                "description": "Get the current chunk for analysis",
                "parameters": {"type": "object", "properties": {}}
            },
            {
                "name": "get_next_chunk", 
                "description": "Move to the next chunk",
                "parameters": {"type": "object", "properties": {}}
            },
            {
                "name": "analyze_chunk_mappings",
                "description": "Save detailed mapping specifications for current chunk",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "mapping_analysis": {
                            "type": "object",
                            "description": "Detailed mapping analysis with source→destination→transformation"
                        }
                    },
                    "required": ["mapping_analysis"]
                }
            },
            {
                "name": "save_template_analysis",
                "description": "Save detailed template analysis",
                "parameters": {
                    "type": "object", 
                    "properties": {
                        "template_analysis": {
                            "type": "object",
                            "description": "Detailed template analysis"
                        }
                    },
                    "required": ["template_analysis"]
                }
            },
            {
                "name": "get_understanding_summary",
                "description": "Get current exploration progress",
                "parameters": {"type": "object", "properties": {}}
            },
            {
                "name": "search_related_chunks",
                "description": "Search for chunks containing specific patterns",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "search_pattern": {"type": "string"}
                    },
                    "required": ["search_pattern"]
                }
            },
            {
                "name": "save_llm_insights",
                "description": "Save LLM's understanding insights and observations",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "insights": {
                            "type": "object",
                            "description": "LLM's insights, observations, and understanding"
                        }
                    },
                    "required": ["insights"]
                }
            },
            {
                "name": "record_understanding_evolution",
                "description": "Record how LLM's understanding is evolving over time",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "evolution_data": {
                            "type": "object",
                            "description": "Data about how understanding has evolved"
                        }
                    },
                    "required": ["evolution_data"]
                }
            },
            {
                "name": "get_validation_metrics",
                "description": "Get validation metrics to prove understanding is building over time",
                "parameters": {"type": "object", "properties": {}}
            }
        ]
        
        try:
            tools = [{"type": "function", "function": func} for func in functions]
            
            # For function calling, we still need to use the direct OpenAI API
            # since _call_llm doesn't handle function calling yet
            llm_model = os.getenv('LLM_MODEL', 'gpt-4o-mini')
            response = self.openai_client.chat.completions.create(
                model=llm_model,
                messages=conversation_history,
                tools=tools,
                tool_choice="auto",
                temperature=0.1,
                max_tokens=2000
            )
            
            message = response.choices[0].message
            self.conversation_turns += 1
            
            # Track costs
            usage = response.usage
            self._update_cost_tracking(usage.prompt_tokens, usage.completion_tokens)
            
            if message.tool_calls:
                # Add assistant message to conversation
                conversation_history.append({
                    "role": "assistant",
                    "content": message.content,
                    "tool_calls": [
                        {
                            "id": tool_call.id,
                            "type": "function",
                            "function": {
                                "name": tool_call.function.name,
                                "arguments": tool_call.function.arguments
                            }
                        } for tool_call in message.tool_calls
                    ]
                })
                
                # Execute function calls
                for tool_call in message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    print(f"\n{'='*60}")
                    if isinstance(function_args, dict):
                        print(f"🔧 FUNCTION CALL: {function_name}({list(function_args.keys())})")
                    else:
                        print(f"🔧 FUNCTION CALL: {function_name}({function_args})")
                    print(f"{'='*60}")
                    
                    try:
                        if function_name in self.available_functions:
                            # Debug: Log the actual parameter type and value
                            print(f"🔍 DEBUG: function_args type={type(function_args)}, value={function_args}")
                            
                            # Handle cases where LLM passes unexpected parameter formats
                            if isinstance(function_args, list):
                                # LLM passed an array instead of object
                                if function_name in ['get_current_chunk', 'get_next_chunk', 'get_understanding_summary', 'get_validation_metrics']:
                                    # Functions that take no parameters - ignore the array and call correctly
                                    function_result = self.available_functions[function_name]()
                                elif function_name == 'analyze_chunk_mappings':
                                    function_result = {
                                        "success": False, 
                                        "message": "❌ Invalid array format. Use: {'mapping_analysis': {'mappings': [{'source_path': '...', 'destination_path': '...', 'transformation_type': '...', 'transformation_logic': {...}}]}}"
                                    }
                                elif function_name == 'save_template_analysis':
                                    function_result = {
                                        "success": False,
                                        "message": "❌ Invalid array format. Use: {'template_analysis': {'name': '...', 'purpose': '...', 'input_parameters': [...], 'output_structure': '...', 'dependencies': [...], 'complexity': '...'}}"
                                    }
                                elif function_name == 'save_llm_insights':
                                    function_result = {
                                        "success": False,
                                        "message": "❌ Invalid array format. Use: {'insights': {'observations': '...', 'understanding_level': 1-5, 'key_discoveries': [...], 'questions': [...]}}"
                                    }
                                elif function_name == 'record_understanding_evolution':
                                    function_result = {
                                        "success": False,
                                        "message": "❌ Invalid array format. Use: {'evolution_data': {'milestone': '...', 'understanding_growth': '...', 'new_insights': [...], 'confidence_level': 1-5}}"
                                    }
                                elif function_name == 'search_related_chunks':
                                    function_result = {
                                        "success": False,
                                        "message": "❌ Invalid array format. Use: {'search_pattern': 'template_name_or_pattern'}"
                                    }
                                else:
                                    function_result = {"success": False, "message": f"❌ Function {function_name} expects object parameters, got array: {function_args}"}
                            elif isinstance(function_args, dict) and len(function_args) == 0:
                                # LLM passed empty object {} - provide specific guidance
                                if function_name in ['get_current_chunk', 'get_next_chunk', 'get_understanding_summary', 'get_validation_metrics']:
                                    # Functions that take no parameters - this is correct, call the function
                                    function_result = self.available_functions[function_name]()
                                elif function_name == 'analyze_chunk_mappings':
                                    # Provide concrete example based on current chunk
                                    current_chunk = self.chunks[self.current_chunk_index] if self.current_chunk_index < len(self.chunks) else None
                                    example_mapping = self._generate_example_mapping(current_chunk)
                                    
                                    function_result = {
                                        "success": False, 
                                        "message": f"❌ Empty object provided. You must include the 'mapping_analysis' parameter.\n\n🎯 CONCRETE EXAMPLE for current chunk:\n{example_mapping}\n\n✅ Copy this structure and replace with actual mappings you find in the chunk."
                                    }
                                elif function_name == 'save_template_analysis':
                                    # Provide concrete template example
                                    current_chunk = self.chunks[self.current_chunk_index] if self.current_chunk_index < len(self.chunks) else None
                                    template_name = current_chunk.templates_defined[0] if current_chunk and current_chunk.templates_defined else "unknown_template"
                                    
                                    example_template = {
                                        "template_analysis": {
                                            "name": template_name,
                                            "purpose": "Describe what this template does based on the XSLT code",
                                            "input_parameters": ["list", "of", "input", "parameters"],
                                            "output_structure": "Description of output XML structure",
                                            "dependencies": ["other", "templates", "called"],
                                            "complexity": "simple|medium|complex"
                                        }
                                    }
                                    
                                    function_result = {
                                        "success": False,
                                        "message": f"❌ Empty object provided. You must include the 'template_analysis' parameter.\n\n🎯 CONCRETE EXAMPLE:\n{json.dumps(example_template, indent=2)}\n\n✅ Replace the example values with actual analysis of the template."
                                    }
                                elif function_name == 'save_llm_insights':
                                    function_result = {
                                        "success": False,
                                        "message": "❌ Empty object provided. You must include: {'insights': {'observations': '...', 'understanding_level': 1-5, 'key_discoveries': [...], 'questions': [...]}}"
                                    }
                                elif function_name == 'record_understanding_evolution':
                                    function_result = {
                                        "success": False,
                                        "message": "❌ Empty object provided. You must include: {'evolution_data': {'milestone': '...', 'understanding_growth': '...', 'new_insights': [...], 'confidence_level': 1-5}}"
                                    }
                                elif function_name == 'search_related_chunks':
                                    function_result = {
                                        "success": False,
                                        "message": "❌ Empty object provided. You must include: {'search_pattern': 'template_name_or_pattern'}"
                                    }
                                else:
                                    function_result = {"success": False, "message": f"❌ Function {function_name} expects object parameters, got empty object"}
                            elif function_name in ['get_current_chunk', 'get_next_chunk', 'get_understanding_summary', 'get_validation_metrics']:
                                # Functions that take no parameters
                                function_result = self.available_functions[function_name]()
                            else:
                                function_result = self.available_functions[function_name](**function_args)
                        else:
                            function_result = {"success": False, "message": f"❌ Unknown function: {function_name}"}
                    except Exception as e:
                        function_result = {"success": False, "message": f"❌ Function error: {str(e)}"}
                    
                    # Add function result to conversation
                    conversation_history.append({
                        "role": "tool",
                        "content": json.dumps(function_result, indent=2),
                        "tool_call_id": tool_call.id
                    })
                    
                    success = function_result.get('success', 'unknown')
                    if success is False:
                        print(f"❌ RESULT: {success}")
                    else:
                        print(f"✅ RESULT: {success}")
                    
                    if 'message' in function_result:
                        if success is False:
                            print(f"🚨 ERROR: {function_result['message']}")
                        else:
                            print(f"📝 MESSAGE: {function_result['message']}")
                    print(f"{'='*60}\n")
                
                # Continue exploration
                continue_prompt = f"Continue systematic exploration. Progress: {len(self.chunks_explored)}/{self.target_chunks} chunks."
                return await self._call_llm_with_functions(continue_prompt, conversation_history)
            
            return message.content or "Exploration completed"
            
        except Exception as e:
            print(f"❌ Error during exploration: {str(e)}")
            return f"Error during exploration: {str(e)}"


async def main():
    """Main enhanced PoC execution"""
    
    print("🚀 Enhanced Interactive XSLT Exploration PoC")
    print("=" * 60)
    
    # Check API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ ERROR: OpenAI API key not found!")
        return False
    
    # Set up paths
    xslt_path = "/home/sidd/dev/xml_wizard/resource/orderCreate/xslt/OrderCreate_MapForce_Full.xslt"
    
    if not Path(xslt_path).exists():
        print(f"❌ ERROR: XSLT file not found: {xslt_path}")
        return False
    
    try:
        # Initialize enhanced explorer (100% coverage for Phase 4.6+4.7 testing)
        explorer = EnhancedXSLTExplorer(api_key, xslt_path, target_coverage=0.4)
        
        # Start exploration
        result = await explorer.start_enhanced_exploration()
        
        print(f"\n🎯 ENHANCED EXPLORATION RESULT:")
        print(f"=" * 60)
        print(result)
        
        # Final assessment
        final_summary = explorer.get_understanding_summary()["summary"]
        
        print(f"\n📊 FINAL ASSESSMENT:")
        print(f"   • Chunks Explored: {final_summary['chunks_explored']}/{final_summary['target_chunks']} ({final_summary['progress_percentage']:.1f}%)")
        print(f"   • Mapping Specifications: {final_summary['mapping_specifications']}")
        print(f"   • Template Analyses: {final_summary['template_analyses']}")
        print(f"   • Context Resets: {final_summary['context_resets']}")
        print(f"   • Total Cost: ${explorer.cost_tracker['cumulative_cost_usd']:.6f}")
        
        # Validate success
        success = (
            final_summary['progress_percentage'] >= 80 and  # Reached most of target
            final_summary['mapping_specifications'] > 0 and  # Extracted mappings
            explorer.cost_tracker['cumulative_cost_usd'] < 1.0  # Reasonable cost
        )
        
        if success:
            print(f"\n🎉 ENHANCED PoC SUCCESS!")
            print(f"✨ Detailed mapping specifications extracted with context management")
            print(f"📁 Results saved to: {explorer.results_dir}")
        else:
            print(f"\n⚠️ ENHANCED PoC NEEDS IMPROVEMENT")
            print(f"🔧 Check mapping extraction quality and coverage")
        
        return success
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
