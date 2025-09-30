"""
File Management Service for XML Wizard.

This module handles file operations including temporary directory management,
XSD dependency resolution, and file copying operations.
"""

import os
import tempfile
import shutil
from typing import Optional
from config import get_config


class FileManager:
    """Handles file operations and temporary directory management."""
    
    def __init__(self, config_instance=None):
        """
        Initialize the file manager.
        
        Args:
            config_instance: Configuration instance (uses global config if None)
        """
        self.config = config_instance or get_config()
    
    def setup_temp_directory_with_dependencies(self, xsd_file_path: str, xsd_file_name: str, source_xsd_path: str = None) -> None:
        """
        Set up temporary directory with XSD dependencies from the same directory as the source XSD.
        
        Args:
            xsd_file_path: Path to the XSD file in temp directory
            xsd_file_name: Original name of the XSD file
            source_xsd_path: Optional path to the original XSD file location
        """
        try:
            temp_dir = os.path.dirname(xsd_file_path)
            if not os.path.exists(temp_dir):
                print(f"Warning: Temp directory not found: {temp_dir}")
                return
            
            # Find the source directory containing the original XSD file
            source_dir = self._find_source_directory(xsd_file_name, source_xsd_path)
            
            if source_dir and os.path.exists(source_dir):
                print(f"Looking for dependencies in: {source_dir}")
                print(f"Copying to temp directory: {temp_dir}")

                # Copy all XSD files from source directory except the main file
                for filename in os.listdir(source_dir):
                    if filename.endswith('.xsd') and filename != xsd_file_name:
                        try:
                            src_path = os.path.join(source_dir, filename)
                            dst_path = os.path.join(temp_dir, filename)

                            # Skip copying if source and destination are the same
                            if os.path.abspath(src_path) == os.path.abspath(dst_path):
                                print(f"Skipping {filename}: source and destination are the same")
                                continue

                            if os.path.exists(src_path) and os.path.isfile(src_path):
                                with open(src_path, 'rb') as src_file:
                                    with open(dst_path, 'wb') as dst_file:
                                        dst_file.write(src_file.read())
                                print(f"Copied dependency: {filename}")
                        except Exception as e:
                            print(f"Warning: Could not copy {filename}: {e}")
            else:
                print(f"Warning: Could not find source directory for {xsd_file_name}")
                        
        except Exception as e:
            print(f"Warning: Error setting up dependencies: {e}")
    
    def _find_source_directory(self, xsd_file_name: str, source_xsd_path: str = None) -> Optional[str]:
        """
        Find the source directory containing the XSD file and its dependencies.
        
        Args:
            xsd_file_name: Name of the XSD file
            source_xsd_path: Optional path to the original XSD file location
            
        Returns:
            Path to the source directory containing dependencies, or None if not found
        """
        # If we have the source path, use its directory
        if source_xsd_path and os.path.exists(source_xsd_path):
            return os.path.dirname(source_xsd_path)
        
        # Otherwise, search in current working directory and subdirectories
        current_dir = os.getcwd()
        for root, dirs, files in os.walk(current_dir):
            if xsd_file_name in files:
                return root
        
        return None
    
    def create_temp_file(self, content: str, suffix: str = '.xml', encoding: str = 'utf-8') -> str:
        """
        Create a temporary file with the given content.
        
        Args:
            content: Content to write to the file
            suffix: File suffix (default: .xml)
            encoding: File encoding (default: utf-8)
            
        Returns:
            Path to the created temporary file
        """
        temp_file = tempfile.NamedTemporaryFile(
            mode='w', 
            suffix=suffix, 
            delete=False, 
            encoding=encoding
        )
        temp_file.write(content)
        temp_file.close()
        return temp_file.name
    
    def create_temp_directory(self) -> str:
        """
        Create a temporary directory.
        
        Returns:
            Path to the created temporary directory
        """
        return tempfile.mkdtemp()
    
    def cleanup_temp_file(self, file_path: str) -> None:
        """
        Clean up a temporary file.
        
        Args:
            file_path: Path to the file to clean up
        """
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(f"Warning: Could not clean up temporary file {file_path}: {e}")
    
    def cleanup_temp_directory(self, dir_path: str) -> None:
        """
        Clean up a temporary directory and all its contents.
        
        Args:
            dir_path: Path to the directory to clean up
        """
        try:
            if os.path.exists(dir_path):
                shutil.rmtree(dir_path, ignore_errors=True)
        except Exception as e:
            print(f"Warning: Could not clean up temporary directory {dir_path}: {e}")
    
    def write_temp_xsd_with_dependencies(self, xsd_content: str, xsd_filename: str, source_xsd_path: str = None) -> tuple[str, str]:
        """
        Write XSD content to a temporary file and set up dependencies.
        
        Args:
            xsd_content: XSD file content
            xsd_filename: Original XSD filename
            source_xsd_path: Optional path to the original XSD file location
            
        Returns:
            Tuple of (temp_xsd_path, temp_dir_path)
        """
        temp_dir = self.create_temp_directory()
        temp_xsd_path = os.path.join(temp_dir, xsd_filename)
        
        # Write the XSD content
        with open(temp_xsd_path, 'w', encoding='utf-8') as f:
            f.write(xsd_content)
        
        # Set up dependencies
        self.setup_temp_directory_with_dependencies(temp_xsd_path, xsd_filename, source_xsd_path)
        
        return temp_xsd_path, temp_dir