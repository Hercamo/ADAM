"""
ADAM DNA Tool - Deployment Bridge
Connects the AI-generated DNA JSON to the existing ADAM DNA Deployment Tool.
Triggers deployment generation for selected platforms.
"""

import os
import re
import sys
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import structlog


_SLUG_SAFE_RE = re.compile(r"[^a-z0-9-]+")


def _safe_company_slug(name: str) -> str:
    """Produce a filesystem-safe slug from a company name.

    Guards against path-traversal sequences (CWE-22) leaking through the
    slug -> directory pipeline.  Collapses any run of non [a-z0-9-]
    characters to a single hyphen and trims stray hyphens.  Falls back to
    the literal string ``deployment`` if the input is empty after
    sanitisation.
    """
    if not name:
        return "deployment"
    slug = _SLUG_SAFE_RE.sub("-", name.lower()).strip("-")
    return (slug or "deployment")[:30]

from app.core.config import settings
from app.dna.dna_builder import DNABuilder
from app.models.session import Session

logger = structlog.get_logger()

class DeploymentBridge:
    """Bridge between the ADAM DNA Tool and the ADAM DNA Deployment Tool."""

    SUPPORTED_PLATFORMS = ["azure", "aws", "gcp", "k8s", "azure-local"]

    def __init__(self, dna_tool_path: Optional[str] = None):
        self.dna_tool_path = dna_tool_path or settings.DNA_TOOL_PATH
        self.output_base = settings.OUTPUT_DIR

    def validate_dna_json(self, dna_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that the DNA JSON has sufficient data for deployment generation."""
        issues = []
        warnings = []

        # Check meta
        meta = dna_data.get("meta", {})
        if not meta.get("company_name"):
            issues.append("Company name is missing")

        # Check critical sections
        sections = dna_data.get("sections", {})

        # Section 1: Doctrine Identity is mandatory
        doctrine = sections.get("doctrine_identity", {})
        doctrine_q = doctrine.get("questions", {})
        if not doctrine_q.get("1.1.1", {}).get("answer"):
            issues.append("Section 1.1.1 (Legal name) is required")
        if not doctrine_q.get("1.1.2", {}).get("answer"):
            issues.append("Section 1.1.2 (Mission statement) is required")

        # Section 12: Infrastructure is needed for deployment
        infra = sections.get("cloud_infrastructure", {})
        infra_q = infra.get("questions", {})
        if not infra_q.get("12.1.1", {}).get("answer"):
            warnings.append("Section 12.1.1 (Cloud topology) not defined — defaults will be used")

        # BOSS configuration
        boss = dna_data.get("boss_config", {})
        if not boss.get("dimensions"):
            warnings.append("BOSS dimensions not customized — ADAM defaults will be used")

        # Count total answered questions
        total_answered = 0
        total_questions = 0
        for sec_key, sec_data in sections.items():
            questions = sec_data.get("questions", {})
            for q_num, q_data in questions.items():
                total_questions += 1
                if q_data.get("answer"):
                    total_answered += 1

        completion_pct = round((total_answered / max(total_questions, 1)) * 100, 1)

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "completion_pct": completion_pct,
            "total_answered": total_answered,
            "total_questions": total_questions,
        }

    async def generate_deployment(
        self,
        session: Session,
        platforms: List[str],
        include_docx: bool = True,
        include_iac: bool = True,
        include_config: bool = True,
    ) -> Dict[str, Any]:
        """Generate deployment artifacts using the DNA Deployment Tool."""
        dna_builder = DNABuilder(session)
        dna_data = dna_builder.export_dna_json()

        # Validate
        validation = self.validate_dna_json(dna_data)
        if not validation["valid"]:
            return {
                "success": False,
                "error": "DNA validation failed",
                "validation": validation,
            }

        # Ensure platforms are valid
        valid_platforms = [p for p in platforms if p in self.SUPPORTED_PLATFORMS]
        if not valid_platforms:
            return {"success": False, "error": f"No valid platforms. Supported: {self.SUPPORTED_PLATFORMS}"}

        # Create output directory with a strictly sanitised slug to prevent
        # any path traversal via a crafted company name (CWE-22).
        company_slug = _safe_company_slug(session.company_name)
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        output_base = os.path.realpath(self.output_base)
        output_dir = os.path.realpath(
            os.path.join(output_base, f"adam-deployment-{company_slug}-{timestamp}")
        )
        if not output_dir.startswith(output_base + os.sep):
            raise ValueError("Resolved output path escapes the output directory")
        os.makedirs(output_dir, exist_ok=True)

        # Save DNA JSON for the deployment tool
        dna_json_path = os.path.join(output_dir, "adam-dna-parsed.json")
        with open(dna_json_path, "w") as f:
            json.dump(dna_data, f, indent=2, default=str)

        # Attempt to run the DNA Deployment Tool generators directly (Python API)
        try:
            result = await self._run_generators(dna_data, output_dir, valid_platforms,
                                                 include_docx, include_iac, include_config)
            return {
                "success": True,
                "output_dir": output_dir,
                "platforms": valid_platforms,
                "dna_json_path": dna_json_path,
                "files_generated": result.get("files_generated", 0),
                "artifacts": result.get("artifacts", []),
                "validation": validation,
            }
        except Exception as e:
            logger.error("Deployment generation failed", error=str(e))
            # Even if generators fail, the DNA JSON is saved and can be used manually
            return {
                "success": False,
                "partial": True,
                "error": str(e),
                "output_dir": output_dir,
                "dna_json_path": dna_json_path,
                "validation": validation,
                "message": "DNA JSON was saved successfully. You can run the DNA Deployment Tool manually.",
            }

    async def _run_generators(
        self,
        dna_data: Dict[str, Any],
        output_dir: str,
        platforms: List[str],
        include_docx: bool,
        include_iac: bool,
        include_config: bool,
    ) -> Dict[str, Any]:
        """Run the DNA Deployment Tool generators programmatically."""
        # Dynamically import from the DNA Deployment Tool if available
        tool_path = self.dna_tool_path
        if not os.path.exists(tool_path):
            logger.warning("DNA Deployment Tool path not found, using DNA JSON only", path=tool_path)
            return {"files_generated": 1, "artifacts": ["adam-dna-parsed.json"]}

        # Add tool to Python path
        if tool_path not in sys.path:
            sys.path.insert(0, tool_path)

        artifacts = []
        files_generated = 0

        try:
            from generators.config_generator import ConfigBundleGenerator

            # Platform generators
            platform_generators = {}
            if "azure" in platforms:
                from generators.azure_generator import AzureGenerator
                platform_generators["azure"] = AzureGenerator
            if "aws" in platforms:
                from generators.aws_generator import AWSGenerator
                platform_generators["aws"] = AWSGenerator
            if "gcp" in platforms:
                from generators.gcp_generator import GCPGenerator
                platform_generators["gcp"] = GCPGenerator
            if "k8s" in platforms:
                from generators.k8s_generator import K8sGenerator
                platform_generators["k8s"] = K8sGenerator
            if "azure-local" in platforms:
                from generators.azure_local_generator import AzureLocalGenerator
                platform_generators["azure-local"] = AzureLocalGenerator

            # Generate IaC for each platform
            if include_iac:
                for platform, gen_class in platform_generators.items():
                    gen = gen_class(dna_data, output_dir)
                    files = gen.generate()
                    files_generated += len(files)
                    for fp, desc in files.items():
                        artifacts.append({"path": fp, "description": desc, "platform": platform})

            # Generate config bundle
            if include_config:
                config_gen = ConfigBundleGenerator(dna_data, output_dir)
                config_files = config_gen.generate()
                files_generated += len(config_files)
                for fp, desc in config_files.items():
                    artifacts.append({"path": fp, "description": desc, "platform": "config"})

            # Generate DOCX specs
            if include_docx:
                from generators.docx_generator import DocxSpecGenerator
                docx_gen = DocxSpecGenerator(dna_data, output_dir)
                docx_files = docx_gen.generate(platforms)
                files_generated += len(docx_files)
                for fp, desc in docx_files.items():
                    artifacts.append({"path": fp, "description": desc, "platform": "docs"})

        except ImportError as e:
            logger.warning("Could not import DNA Deployment Tool generators", error=str(e))
            raise RuntimeError(f"DNA Deployment Tool generators not available: {e}") from e

        return {"files_generated": files_generated, "artifacts": artifacts}

    def get_deployment_status(self, output_dir: str) -> Dict[str, Any]:
        """Check the status of a deployment generation."""
        if not os.path.exists(output_dir):
            return {"exists": False}

        files = []
        for root, dirs, filenames in os.walk(output_dir):
            for f in filenames:
                filepath = os.path.join(root, f)
                files.append({
                    "path": os.path.relpath(filepath, output_dir),
                    "size": os.path.getsize(filepath),
                })

        return {
            "exists": True,
            "output_dir": output_dir,
            "total_files": len(files),
            "files": files,
        }
