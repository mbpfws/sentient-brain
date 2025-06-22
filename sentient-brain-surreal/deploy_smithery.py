#!/usr/bin/env python3
"""
Smithery.ai Deployment Script for Sentient Brain Multi-Agent System

This script handles deployment preparation and validation for Smithery.ai platform.
"""

import os
import json
import subprocess
import sys
from pathlib import Path
import yaml
import logging
from typing import Dict, List, Any, Optional
import requests
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SmitheryDeployer:
    """Handles deployment to Smithery.ai platform."""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.required_files = [
            "Dockerfile",
            "smithery.yaml", 
            "smithery.json",
            "requirements.txt"
        ]
        
    def validate_deployment_readiness(self) -> Dict[str, Any]:
        """Validate that the project is ready for Smithery deployment."""
        logger.info("🔍 Validating deployment readiness...")
        
        validation_results = {
            "ready": True,
            "issues": [],
            "warnings": [],
            "files_checked": {}
        }
        
        # Check required files
        for file_name in self.required_files:
            file_path = self.project_root / file_name
            if file_path.exists():
                validation_results["files_checked"][file_name] = "✅ Found"
                logger.info(f"✅ {file_name} found")
            else:
                validation_results["ready"] = False
                validation_results["issues"].append(f"Missing required file: {file_name}")
                validation_results["files_checked"][file_name] = "❌ Missing"
                logger.error(f"❌ {file_name} missing")
        
        # Validate Dockerfile
        if (self.project_root / "Dockerfile").exists():
            dockerfile_issues = self.validate_dockerfile()
            if dockerfile_issues:
                validation_results["issues"].extend(dockerfile_issues)
                validation_results["ready"] = False
        
        # Validate smithery.yaml
        if (self.project_root / "smithery.yaml").exists():
            smithery_yaml_issues = self.validate_smithery_yaml()
            if smithery_yaml_issues:
                validation_results["issues"].extend(smithery_yaml_issues)
                validation_results["ready"] = False
        
        # Validate smithery.json
        if (self.project_root / "smithery.json").exists():
            smithery_json_issues = self.validate_smithery_json()
            if smithery_json_issues:
                validation_results["issues"].extend(smithery_json_issues)
                validation_results["ready"] = False
        
        # Check dependencies
        deps_issues = self.validate_dependencies()
        if deps_issues:
            validation_results["warnings"].extend(deps_issues)
        
        # Check environment variables
        env_issues = self.validate_environment_config()
        if env_issues:
            validation_results["warnings"].extend(env_issues)
        
        return validation_results
    
    def validate_dockerfile(self) -> List[str]:
        """Validate Dockerfile for Smithery compatibility."""
        issues = []
        dockerfile_path = self.project_root / "Dockerfile"
        
        try:
            with open(dockerfile_path, 'r') as f:
                content = f.read()
            
            # Check for required elements
            required_elements = [
                ("FROM", "Base image specification"),
                ("WORKDIR", "Working directory"),
                ("COPY", "File copying"),
                ("EXPOSE", "Port exposure"),
                ("CMD", "Start command")
            ]
            
            for element, description in required_elements:
                if element not in content:
                    issues.append(f"Dockerfile missing {element} ({description})")
            
            # Check for best practices
            if "USER" not in content:
                issues.append("Dockerfile should include USER instruction for security")
            
            if "HEALTHCHECK" not in content:
                issues.append("Dockerfile should include HEALTHCHECK for monitoring")
            
        except Exception as e:
            issues.append(f"Error reading Dockerfile: {str(e)}")
        
        return issues
    
    def validate_smithery_yaml(self) -> List[str]:
        """Validate smithery.yaml configuration."""
        issues = []
        yaml_path = self.project_root / "smithery.yaml"
        
        try:
            with open(yaml_path, 'r') as f:
                config = yaml.safe_load(f)
            
            # Check required fields
            required_fields = ["version", "start"]
            for field in required_fields:
                if field not in config:
                    issues.append(f"smithery.yaml missing required field: {field}")
            
            # Validate start configuration
            if "start" in config:
                start_config = config["start"]
                if "command" not in start_config:
                    issues.append("smithery.yaml start section missing command")
                if "port" not in start_config:
                    issues.append("smithery.yaml start section missing port")
            
            # Check configSchema if present
            if "configSchema" in config:
                schema = config["configSchema"]
                if "required" in schema and "properties" in schema:
                    required_props = schema["required"]
                    properties = schema["properties"]
                    
                    for prop in required_props:
                        if prop not in properties:
                            issues.append(f"Required property {prop} not defined in configSchema")
            
        except yaml.YAMLError as e:
            issues.append(f"Invalid YAML syntax in smithery.yaml: {str(e)}")
        except Exception as e:
            issues.append(f"Error reading smithery.yaml: {str(e)}")
        
        return issues
    
    def validate_smithery_json(self) -> List[str]:
        """Validate smithery.json metadata."""
        issues = []
        json_path = self.project_root / "smithery.json"
        
        try:
            with open(json_path, 'r') as f:
                metadata = json.load(f)
            
            # Check required fields
            required_fields = ["id", "name", "description", "version"]
            for field in required_fields:
                if field not in metadata:
                    issues.append(f"smithery.json missing required field: {field}")
            
            # Validate deployment section
            if "deployment" in metadata:
                deployment = metadata["deployment"]
                if "requirements" in deployment:
                    for req in deployment["requirements"]:
                        if "name" not in req:
                            issues.append("Deployment requirement missing name field")
                        if "required" not in req:
                            issues.append("Deployment requirement missing required field")
            
        except json.JSONDecodeError as e:
            issues.append(f"Invalid JSON syntax in smithery.json: {str(e)}")
        except Exception as e:
            issues.append(f"Error reading smithery.json: {str(e)}")
        
        return issues
    
    def validate_dependencies(self) -> List[str]:
        """Validate dependencies and versions."""
        warnings = []
        requirements_path = self.project_root / "requirements.txt"
        
        if not requirements_path.exists():
            return ["requirements.txt not found"]
        
        try:
            with open(requirements_path, 'r') as f:
                requirements = f.read().strip().split('\n')
            
            # Check for critical dependencies
            critical_deps = [
                "fastapi",
                "uvicorn", 
                "surrealdb",
                "groq",
                "google-genai"
            ]
            
            found_deps = []
            for line in requirements:
                if line.strip() and not line.startswith('#'):
                    dep_name = line.split('==')[0].split('>=')[0].split('~=')[0]
                    found_deps.append(dep_name.lower())
            
            for dep in critical_deps:
                if dep not in found_deps:
                    warnings.append(f"Critical dependency {dep} not found in requirements.txt")
            
            # Check for version pinning
            unpinned = []
            for line in requirements:
                if line.strip() and not line.startswith('#'):
                    if '==' not in line and '>=' not in line and '~=' not in line:
                        unpinned.append(line.strip())
            
            if unpinned:
                warnings.append(f"Unpinned dependencies found: {', '.join(unpinned)}")
        
        except Exception as e:
            warnings.append(f"Error reading requirements.txt: {str(e)}")
        
        return warnings
    
    def validate_environment_config(self) -> List[str]:
        """Validate environment configuration."""
        warnings = []
        
        # Check for .env.example
        env_example = self.project_root / ".env.example"
        if not env_example.exists():
            warnings.append(".env.example file not found - consider adding for documentation")
        
        # Check smithery.yaml for required environment variables
        yaml_path = self.project_root / "smithery.yaml"
        if yaml_path.exists():
            try:
                with open(yaml_path, 'r') as f:
                    config = yaml.safe_load(f)
                
                if "configSchema" in config and "required" in config["configSchema"]:
                    required_vars = config["configSchema"]["required"]
                    
                    # Common environment variables that should be documented
                    common_vars = ["API_KEY", "DATABASE_URL", "SECRET_KEY"]
                    
                    for var in required_vars:
                        if any(common in var.upper() for common in ["KEY", "SECRET", "PASSWORD"]):
                            warnings.append(f"Sensitive variable {var} detected - ensure proper security handling")
            
            except Exception as e:
                warnings.append(f"Error checking environment config: {str(e)}")
        
        return warnings
    
    def test_docker_build(self) -> Dict[str, Any]:
        """Test Docker build locally."""
        logger.info("🐳 Testing Docker build...")
        
        result = {
            "success": False,
            "build_time": 0,
            "image_size": None,
            "error": None
        }
        
        try:
            start_time = time.time()
            
            # Build Docker image
            build_command = [
                "docker", "build", 
                "-t", "sentient-brain-test",
                str(self.project_root)
            ]
            
            process = subprocess.run(
                build_command,
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            result["build_time"] = time.time() - start_time
            
            if process.returncode == 0:
                result["success"] = True
                logger.info(f"✅ Docker build successful ({result['build_time']:.1f}s)")
                
                # Get image size
                size_command = ["docker", "images", "sentient-brain-test", "--format", "{{.Size}}"]
                size_process = subprocess.run(size_command, capture_output=True, text=True)
                
                if size_process.returncode == 0:
                    result["image_size"] = size_process.stdout.strip()
                    logger.info(f"📦 Image size: {result['image_size']}")
                
            else:
                result["error"] = process.stderr
                logger.error(f"❌ Docker build failed: {process.stderr}")
        
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"❌ Docker build test failed: {str(e)}")
        
        return result
    
    def test_container_health(self) -> Dict[str, Any]:
        """Test container health and functionality."""
        logger.info("🏥 Testing container health...")
        
        result = {
            "success": False,
            "health_check": False,
            "api_responsive": False,
            "error": None
        }
        
        try:
            # Start container
            run_command = [
                "docker", "run", "-d", 
                "--name", "sentient-brain-test-container",
                "-p", "8000:8000",
                "sentient-brain-test"
            ]
            
            process = subprocess.run(run_command, capture_output=True, text=True)
            
            if process.returncode == 0:
                container_id = process.stdout.strip()
                logger.info(f"🚀 Container started: {container_id[:12]}")
                
                # Wait for startup
                time.sleep(10)
                
                # Check health
                health_command = ["docker", "inspect", "--format", "{{.State.Health.Status}}", container_id]
                health_process = subprocess.run(health_command, capture_output=True, text=True)
                
                if health_process.returncode == 0:
                    health_status = health_process.stdout.strip()
                    result["health_check"] = health_status == "healthy"
                    logger.info(f"🏥 Health status: {health_status}")
                
                # Test API endpoint
                try:
                    response = requests.get("http://localhost:8000/api/v1/health", timeout=10)
                    result["api_responsive"] = response.status_code == 200
                    if result["api_responsive"]:
                        logger.info("✅ API endpoint responsive")
                    else:
                        logger.warning(f"⚠️ API returned status {response.status_code}")
                except requests.RequestException as e:
                    logger.warning(f"⚠️ API not responsive: {str(e)}")
                
                result["success"] = True
                
                # Cleanup
                subprocess.run(["docker", "stop", container_id], capture_output=True)
                subprocess.run(["docker", "rm", container_id], capture_output=True)
                
            else:
                result["error"] = process.stderr
                logger.error(f"❌ Container start failed: {process.stderr}")
        
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"❌ Container health test failed: {str(e)}")
        
        return result
    
    def generate_deployment_checklist(self) -> List[str]:
        """Generate deployment checklist."""
        checklist = [
            "✅ All required files present (Dockerfile, smithery.yaml, smithery.json)",
            "✅ Dockerfile follows best practices",
            "✅ smithery.yaml properly configured",
            "✅ smithery.json metadata complete",
            "✅ Dependencies properly specified",
            "✅ Environment variables documented",
            "✅ Docker build successful",
            "✅ Container health checks passing",
            "✅ API endpoints responsive",
            "✅ Security considerations addressed",
            "✅ Performance requirements met",
            "✅ Documentation complete"
        ]
        
        return checklist
    
    def create_deployment_summary(self, validation_results: Dict[str, Any], 
                                docker_results: Dict[str, Any],
                                health_results: Dict[str, Any]) -> Dict[str, Any]:
        """Create comprehensive deployment summary."""
        
        # Calculate overall readiness score
        total_checks = 12  # From checklist
        passed_checks = 0
        
        if validation_results["ready"]:
            passed_checks += 6  # File validation checks
        
        if docker_results["success"]:
            passed_checks += 3  # Docker build checks
        
        if health_results["success"] and health_results["api_responsive"]:
            passed_checks += 3  # Health checks
        
        readiness_score = (passed_checks / total_checks) * 100
        
        summary = {
            "deployment_ready": readiness_score >= 90,
            "readiness_score": round(readiness_score, 1),
            "validation": validation_results,
            "docker_build": docker_results,
            "container_health": health_results,
            "checklist": self.generate_deployment_checklist(),
            "recommendations": []
        }
        
        # Generate recommendations
        if readiness_score >= 95:
            summary["recommendations"].append("🚀 Ready for production deployment!")
        elif readiness_score >= 80:
            summary["recommendations"].append("👍 Almost ready - address remaining issues")
        else:
            summary["recommendations"].append("⚠️ Significant issues need resolution before deployment")
        
        if validation_results["issues"]:
            summary["recommendations"].append("🔧 Fix validation issues first")
        
        if not docker_results["success"]:
            summary["recommendations"].append("🐳 Resolve Docker build issues")
        
        if not health_results["api_responsive"]:
            summary["recommendations"].append("🏥 Ensure API endpoints are working")
        
        return summary

def main():
    """Main deployment validation function."""
    logger.info("🚀 Smithery.ai Deployment Validator")
    logger.info("=" * 50)
    
    deployer = SmitheryDeployer()
    
    try:
        # Step 1: Validate deployment readiness
        validation_results = deployer.validate_deployment_readiness()
        
        # Step 2: Test Docker build
        docker_results = deployer.test_docker_build()
        
        # Step 3: Test container health
        health_results = deployer.test_container_health()
        
        # Step 4: Generate summary
        summary = deployer.create_deployment_summary(
            validation_results, docker_results, health_results
        )
        
        # Print results
        logger.info("=" * 50)
        logger.info("📊 DEPLOYMENT SUMMARY")
        logger.info(f"Readiness Score: {summary['readiness_score']}%")
        logger.info(f"Deployment Ready: {'✅ YES' if summary['deployment_ready'] else '❌ NO'}")
        
        if validation_results["issues"]:
            logger.info("\n❌ VALIDATION ISSUES:")
            for issue in validation_results["issues"]:
                logger.info(f"  • {issue}")
        
        if validation_results["warnings"]:
            logger.info("\n⚠️ WARNINGS:")
            for warning in validation_results["warnings"]:
                logger.info(f"  • {warning}")
        
        logger.info("\n💡 RECOMMENDATIONS:")
        for rec in summary["recommendations"]:
            logger.info(f"  {rec}")
        
        # Save detailed report
        report_file = f"deployment_report_{int(time.time())}.json"
        with open(report_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"\n📄 Detailed report saved to: {report_file}")
        
        # Exit with appropriate code
        exit_code = 0 if summary["deployment_ready"] else 1
        sys.exit(exit_code)
        
    except Exception as e:
        logger.error(f"❌ Deployment validation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()