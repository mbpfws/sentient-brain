"""
Service for extracting metadata (domain, role, language) from file paths.
"""

import os
import yaml
import fnmatch
from typing import Dict, Any, List, Optional

class MetadataExtractorService:
    """Parses domains.yml and classifies file paths."""

    def __init__(self, config_path="src/config/domains.yml"):
        self.config_path = config_path
        self.config = self._load_config()
        print("[MetadataExtractor] Service initialized.", flush=True)

    def _load_config(self) -> Dict[str, Any]:
        """Loads and parses the YAML configuration file."""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)

    def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extracts all relevant metadata for a given file path."""
        file_path = file_path.replace('\\', '/') # Normalize for matching
        
        language = self._get_language(file_path)
        domain_info = self._match_rule(file_path, self.config.get('domains', []))
        role_info = self._match_rule(file_path, self.config.get('roles', []))

        return {
            "language": language,
            "domain": domain_info.get('name', 'Unknown') if domain_info else 'Unknown',
            "role": role_info.get('name', 'Unknown') if role_info else 'Unknown',
            "tags": domain_info.get('tags', []) if domain_info else []
        }

    def _get_language(self, file_path: str) -> str:
        """Determines the programming language from the file extension."""
        ext_map = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.java': 'Java',
            '.go': 'Go',
            '.rs': 'Rust',
            '.rb': 'Ruby',
            '.php': 'PHP',
            '.cs': 'C#',
            '.html': 'HTML',
            '.css': 'CSS',
            '.scss': 'SCSS',
            '.jsx': 'JSX',
            '.tsx': 'TSX',
            '.md': 'Markdown',
            '.json': 'JSON',
            '.yml': 'YAML',
            '.yaml': 'YAML',
            '.xml': 'XML',
            '.sh': 'Shell',
            '.tf': 'Terraform',
            'Dockerfile': 'Dockerfile'
        }
        _, filename = os.path.split(file_path)
        if '.' in filename:
            ext = '.' + filename.rsplit('.', 1)[1]
            return ext_map.get(ext.lower(), 'Text')
        elif filename == 'Dockerfile':
            return 'Dockerfile'
        return 'Text'

    def _match_rule(self, file_path: str, rules: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Finds the first rule in a list that matches the file path."""
        for rule in rules:
            for pattern in rule.get('patterns', []):
                if fnmatch.fnmatch(file_path, f"*{pattern}") or fnmatch.fnmatch(os.path.basename(file_path), pattern):
                    return rule
        return None

# Factory function for easy access
def get_metadata_extractor() -> MetadataExtractorService:
    """Get a configured MetadataExtractorService instance."""
    return MetadataExtractorService()
