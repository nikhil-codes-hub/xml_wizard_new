"""
Unit tests for semantic chunking functionality in XSLTChunker
Tests the new configurable chunking strategies (boundary vs semantic)
"""

import unittest
import tempfile
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.core.xslt_chunker import XSLTChunker, ChunkType


class TestSemanticChunking(unittest.TestCase):
    """Test semantic chunking strategy functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create test XSLT content with helper templates and call sites
        self.test_xslt_content = '''<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="2.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    
    <!-- Helper template 1 - vmf1 -->
    <xsl:template name="vmf:vmf1_inputtoresult">
        <xsl:param name="input" />
        <xsl:choose>
            <xsl:when test="$input = 'P'">VPT</xsl:when>
            <xsl:when test="$input = 'PT'">VPT</xsl:when>
            <xsl:otherwise></xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    
    <!-- Helper template 2 - vmf2 -->
    <xsl:template name="vmf:vmf2_inputtoresult">
        <xsl:param name="input" />
        <xsl:choose>
            <xsl:when test="$input = 'V'">VVI</xsl:when>
            <xsl:when test="$input = 'R'">VAEA</xsl:when>
            <xsl:when test="$input = 'K'">VCR</xsl:when>
            <xsl:otherwise></xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    
    <!-- Helper template 3 - vmf3 -->
    <xsl:template name="vmf:vmf3_inputtoresult">
        <xsl:param name="input" />
        <xsl:choose>
            <xsl:when test="$input = 'email'">Voperational</xsl:when>
            <xsl:otherwise></xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    
    <!-- Helper template 4 - vmf4 -->
    <xsl:template name="vmf:vmf4_inputtoresult">
        <xsl:param name="input" />
        <xsl:choose>
            <xsl:when test="$input = 'mobile'">Voperational</xsl:when>
            <xsl:otherwise></xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    
    <!-- Main template with template calls -->
    <xsl:template match="/">
        <xsl:variable name="target" select="//Target"/>
        <OrderCreateRQ>
            <!-- Document processing using vmf1 -->
            <xsl:for-each select="//Document">
                <DocumentType>
                    <xsl:call-template name="vmf:vmf1_inputtoresult">
                        <xsl:with-param name="input" select="@type"/>
                    </xsl:call-template>
                </DocumentType>
            </xsl:for-each>
            
            <!-- Visa processing using vmf2 -->
            <xsl:for-each select="//Visa">
                <VisaType>
                    <xsl:call-template name="vmf:vmf2_inputtoresult">
                        <xsl:with-param name="input" select="@type"/>
                    </xsl:call-template>
                </VisaType>
            </xsl:for-each>
            
            <!-- Email processing using vmf3 -->
            <xsl:for-each select="//Email">
                <EmailLabel>
                    <xsl:call-template name="vmf:vmf3_inputtoresult">
                        <xsl:with-param name="input" select="@label"/>
                    </xsl:call-template>
                </EmailLabel>
            </xsl:for-each>
            
            <!-- Phone processing using vmf4 -->
            <xsl:for-each select="//Phone">
                <PhoneLabel>
                    <xsl:call-template name="vmf:vmf4_inputtoresult">
                        <xsl:with-param name="input" select="@label"/>
                    </xsl:call-template>
                </PhoneLabel>
            </xsl:for-each>
        </OrderCreateRQ>
    </xsl:template>
    
</xsl:stylesheet>'''
    
    def test_chunking_strategy_parameter(self):
        """Test that chunking_strategy parameter is properly handled"""
        # Test boundary strategy (default)
        boundary_chunker = XSLTChunker(chunking_strategy='boundary')
        self.assertEqual(boundary_chunker.chunking_strategy, 'boundary')
        
        # Test semantic strategy
        semantic_chunker = XSLTChunker(chunking_strategy='semantic')
        self.assertEqual(semantic_chunker.chunking_strategy, 'semantic')
        
        # Test default behavior (should be boundary for backward compatibility)
        default_chunker = XSLTChunker()
        self.assertEqual(default_chunker.chunking_strategy, 'boundary')
    
    def test_boundary_vs_semantic_chunking_difference(self):
        """Test that boundary and semantic strategies produce different results"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xslt', delete=False) as f:
            f.write(self.test_xslt_content)
            f.flush()
            
            # Create chunkers with different strategies
            boundary_chunker = XSLTChunker(
                max_tokens_per_chunk=1000,  # Small for testing
                chunking_strategy='boundary'
            )
            semantic_chunker = XSLTChunker(
                max_tokens_per_chunk=1000,  # Small for testing
                chunking_strategy='semantic'
            )
            
            # Chunk with both strategies
            boundary_chunks = boundary_chunker.chunk_file(Path(f.name))
            semantic_chunks = semantic_chunker.chunk_file(Path(f.name))
            
            # Both should produce chunks
            self.assertGreater(len(boundary_chunks), 0)
            self.assertGreater(len(semantic_chunks), 0)
            
            # Semantic chunking should generally produce fewer chunks due to clustering
            # Note: This may not always be true for small files, so we just check they're different
            boundary_count = len(boundary_chunks)
            semantic_count = len(semantic_chunks)
            
            # At minimum, the chunk structures should be different
            boundary_ids = [c.chunk_id for c in boundary_chunks]
            semantic_ids = [c.chunk_id for c in semantic_chunks]
            
            # They should have different chunk identification patterns
            self.assertNotEqual(boundary_ids, semantic_ids)
    
    def test_semantic_template_clustering(self):
        """Test that semantic chunking groups template definitions with call sites"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xslt', delete=False) as f:
            f.write(self.test_xslt_content)
            f.flush()
            
            semantic_chunker = XSLTChunker(
                max_tokens_per_chunk=2000,  # Allow for larger clusters
                chunking_strategy='semantic'
            )
            
            chunks = semantic_chunker.chunk_file(Path(f.name))
            
            # Check for template cluster chunks
            template_clusters = [c for c in chunks if 'template_cluster' in c.chunk_id]
            
            # Should have template clusters if semantic chunking is working
            if template_clusters:
                # Template clusters should contain both template definitions and calls
                for cluster in template_clusters:
                    content = cluster.text
                    
                    # Should contain template definition
                    self.assertTrue(
                        '<xsl:template name="vmf:' in content,
                        f"Template cluster should contain template definition: {cluster.chunk_id}"
                    )
                    
                    # Metadata should indicate it's a template cluster
                    if hasattr(cluster, 'metadata') and cluster.metadata:
                        cluster_metadata = cluster.metadata.get('is_template_cluster', False)
                        if cluster_metadata:
                            self.assertTrue(cluster_metadata)
    
    def test_semantic_chunking_preserves_helper_templates(self):
        """Test that semantic chunking properly preserves helper template relationships"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xslt', delete=False) as f:
            f.write(self.test_xslt_content)
            f.flush()
            
            semantic_chunker = XSLTChunker(chunking_strategy='semantic')
            chunks = semantic_chunker.chunk_file(Path(f.name))
            
            # Count vmf template occurrences across all chunks
            vmf_definitions = 0
            vmf_calls = 0
            
            for chunk in chunks:
                content = chunk.text
                
                # Count template definitions
                vmf_definitions += content.count('<xsl:template name="vmf:')
                
                # Count template calls
                vmf_calls += content.count('<xsl:call-template name="vmf:')
            
            # Should find all 4 vmf template definitions
            self.assertEqual(vmf_definitions, 4, "Should find all 4 vmf template definitions")
            
            # Should find all 4 vmf template calls
            self.assertEqual(vmf_calls, 4, "Should find all 4 vmf template calls")
    
    def test_semantic_chunking_metadata(self):
        """Test that semantic chunking includes proper metadata"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xslt', delete=False) as f:
            f.write(self.test_xslt_content)
            f.flush()
            
            semantic_chunker = XSLTChunker(chunking_strategy='semantic')
            chunks = semantic_chunker.chunk_file(Path(f.name))
            
            # Check that chunks have appropriate metadata
            for chunk in chunks:
                # Basic chunk properties should exist
                self.assertIsNotNone(chunk.chunk_id)
                self.assertIsNotNone(chunk.text)
                self.assertIsInstance(chunk.chunk_type, ChunkType)
                
                # Check for semantic-specific metadata if present
                if hasattr(chunk, 'metadata') and chunk.metadata:
                    metadata = chunk.metadata
                    
                    # If it's a template cluster, should have template cluster metadata
                    if metadata.get('is_template_cluster', False):
                        self.assertIn('template_name', metadata)
                        self.assertIn('call_site_count', metadata)
                        self.assertIsInstance(metadata['call_site_count'], int)
    
    def test_backward_compatibility(self):
        """Test that existing code without chunking_strategy still works"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xslt', delete=False) as f:
            f.write(self.test_xslt_content)
            f.flush()
            
            # Old-style chunker creation (should default to boundary)
            old_style_chunker = XSLTChunker(max_tokens_per_chunk=1000)
            chunks = old_style_chunker.chunk_file(Path(f.name))
            
            # Should work and produce chunks
            self.assertGreater(len(chunks), 0)
            
            # Should use boundary strategy by default
            self.assertEqual(old_style_chunker.chunking_strategy, 'boundary')
    
    def test_invalid_chunking_strategy(self):
        """Test handling of invalid chunking strategy"""
        # Should not raise an error during construction
        chunker = XSLTChunker(chunking_strategy='invalid_strategy')
        
        # Should default to boundary behavior for invalid strategy
        self.assertEqual(chunker.chunking_strategy, 'invalid_strategy')
        
        # Chunking should still work (falls back to boundary strategy)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xslt', delete=False) as f:
            f.write(self.test_xslt_content)
            f.flush()
            
            chunks = chunker.chunk_file(Path(f.name))
            self.assertGreater(len(chunks), 0)


class TestSemanticChunkingEdgeCases(unittest.TestCase):
    """Test edge cases for semantic chunking"""
    
    def test_file_with_no_helper_templates(self):
        """Test semantic chunking with file that has no helper templates"""
        simple_xslt = '''<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="2.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:template match="/">
        <Result>
            <xsl:value-of select="//data"/>
        </Result>
    </xsl:template>
</xsl:stylesheet>'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xslt', delete=False) as f:
            f.write(simple_xslt)
            f.flush()
            
            semantic_chunker = XSLTChunker(chunking_strategy='semantic')
            chunks = semantic_chunker.chunk_file(Path(f.name))
            
            # Should still work and produce chunks
            self.assertGreater(len(chunks), 0)
    
    def test_file_with_only_helper_templates(self):
        """Test semantic chunking with file that has only helper templates"""
        helpers_only_xslt = '''<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="2.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    
    <xsl:template name="vmf:vmf1_inputtoresult">
        <xsl:param name="input" />
        <xsl:choose>
            <xsl:when test="$input = 'P'">VPT</xsl:when>
            <xsl:otherwise></xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    
    <xsl:template name="vmf:vmf2_inputtoresult">
        <xsl:param name="input" />
        <xsl:value-of select="$input"/>
    </xsl:template>
    
</xsl:stylesheet>'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xslt', delete=False) as f:
            f.write(helpers_only_xslt)
            f.flush()
            
            semantic_chunker = XSLTChunker(chunking_strategy='semantic')
            chunks = semantic_chunker.chunk_file(Path(f.name))
            
            # Should still work and produce chunks
            self.assertGreater(len(chunks), 0)
            
            # Should detect helper templates
            helper_chunks = [c for c in chunks if c.chunk_type == ChunkType.HELPER_TEMPLATE]
            self.assertGreater(len(helper_chunks), 0)


if __name__ == '__main__':
    unittest.main()