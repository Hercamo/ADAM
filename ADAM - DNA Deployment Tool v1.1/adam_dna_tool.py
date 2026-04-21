#!/usr/bin/env python3
"""
ADAM DNA Deployment Tool
========================
Command-line application that reads a completed ADAM DNA Questionnaire (.docx)
and generates DNA Deployment Specifications for supported platforms:

  - Azure (Primary)
  - AWS (Warm Standby / Primary)
  - Google Cloud Platform
  - Open Source Kubernetes (Generic K8s)
  - Azure Local (On-Premises Failover)

Outputs include:
  - Professional Word documents (.docx)
  - Infrastructure-as-Code (Terraform, Bicep, CloudFormation, Helm)
  - JSON/YAML configuration bundles

Usage:
  python adam_dna_tool.py --input questionnaire.docx --platforms azure,aws
  python adam_dna_tool.py --input questionnaire.docx --platforms all
  python adam_dna_tool.py --input questionnaire.docx --platforms azure,k8s --output ./my-output

ADAM - Autonomy Doctrine & Architecture Model
Version 1.1 | DNA Questionnaire Version 1.0
"""

import os
import sys
import json
import argparse
from datetime import datetime
from typing import List

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from questionnaire_parser import DNAQuestionnaireParser
from generators.azure_generator import AzureGenerator
from generators.aws_generator import AWSGenerator
from generators.gcp_generator import GCPGenerator
from generators.k8s_generator import K8sGenerator
from generators.azure_local_generator import AzureLocalGenerator
from generators.docx_generator import DocxSpecGenerator
from generators.config_generator import ConfigBundleGenerator

BANNER = r"""
    _    ____    _    __  __
   / \  |  _ \  / \  |  \/  |
  / _ \ | | | |/ _ \ | |\/| |
 / ___ \| |_| / ___ \| |  | |
/_/   \_\____/_/   \_\_|  |_|

  Autonomy Doctrine & Architecture Model
  DNA Deployment Specification Generator
  Version 1.1 | March 2026
"""

PLATFORM_MAP = {
    "azure": ("Azure (Primary)", AzureGenerator),
    "aws": ("AWS (Warm Standby/Primary)", AWSGenerator),
    "gcp": ("Google Cloud Platform", GCPGenerator),
    "k8s": ("Open Source Kubernetes", K8sGenerator),
    "kubernetes": ("Open Source Kubernetes", K8sGenerator),
    "azure-local": ("Azure Local (On-Premises)", AzureLocalGenerator),
    "azurelocal": ("Azure Local (On-Premises)", AzureLocalGenerator),
}

ALL_PLATFORMS = ["azure", "aws", "gcp", "k8s", "azure-local"]

def parse_platforms(platform_str: str) -> List[str]:
    """Parse platform selection string into list of platform keys."""
    if platform_str.lower() == "all":
        return ALL_PLATFORMS

    platforms = []
    for p in platform_str.split(","):
        p = p.strip().lower()
        if p in PLATFORM_MAP:
            # Normalize aliases
            if p == "kubernetes":
                p = "k8s"
            elif p == "azurelocal":
                p = "azure-local"
            if p not in platforms:
                platforms.append(p)
        else:
            print(f"  WARNING: Unknown platform '{p}'. Skipping.")
            print(f"  Valid platforms: {', '.join(PLATFORM_MAP.keys())}")

    return platforms

def main():
    parser = argparse.ArgumentParser(
        description="ADAM DNA Deployment Specification Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --input questionnaire.docx --platforms azure,aws
  %(prog)s --input questionnaire.docx --platforms all
  %(prog)s --input questionnaire.docx --platforms k8s,azure-local --output ./output

Supported Platforms:
  azure       - Microsoft Azure (Primary deployment)
  aws         - Amazon Web Services (Warm Standby or Primary)
  gcp         - Google Cloud Platform
  k8s         - Open Source Kubernetes (Generic)
  azure-local - Azure Local / Azure Stack HCI (On-Premises Failover)
  all         - Generate for all platforms
        """
    )
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Path to the filled-out ADAM DNA Questionnaire (.docx file)"
    )
    parser.add_argument(
        "--platforms", "-p",
        required=True,
        help="Comma-separated list of target platforms (azure,aws,gcp,k8s,azure-local) or 'all'"
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Output directory (default: ./adam-deployment-<company>-<timestamp>)"
    )
    parser.add_argument(
        "--no-docx",
        action="store_true",
        help="Skip Word document generation (IaC and configs only)"
    )
    parser.add_argument(
        "--no-iac",
        action="store_true",
        help="Skip Infrastructure-as-Code generation (docs and configs only)"
    )
    parser.add_argument(
        "--no-config",
        action="store_true",
        help="Skip configuration bundle generation"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )

    args = parser.parse_args()

    # Banner
    print(BANNER)

    # Validate input file
    if not os.path.exists(args.input):
        print(f"  ERROR: Input file not found: {args.input}")
        sys.exit(1)

    if not args.input.endswith(".docx"):
        print(f"  ERROR: Input file must be a .docx file: {args.input}")
        sys.exit(1)

    # Parse platforms
    platforms = parse_platforms(args.platforms)
    if not platforms:
        print("  ERROR: No valid platforms selected.")
        sys.exit(1)

    # ================================================================
    # Phase 1: Parse DNA Questionnaire
    # ================================================================
    print("=" * 60)
    print("  Phase 1: Parsing DNA Questionnaire")
    print("=" * 60)
    print(f"  Input: {args.input}")

    try:
        parser_obj = DNAQuestionnaireParser(args.input)
        dna_data = parser_obj.parse()
    except Exception as e:
        print(f"  ERROR: Failed to parse questionnaire: {e}")
        sys.exit(1)

    company_name = dna_data["meta"]["company_name"]
    print(f"  Company: {company_name}")
    print(f"  Questions parsed: {len(parser_obj.raw_data)}")
    print(f"  Sections found: {len(dna_data['sections'])}")

    # Setup output directory
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    company_slug = company_name.lower().replace(" ", "-").replace(",", "").replace(".", "")[:30]
    if args.output:
        output_dir = args.output
    else:
        output_dir = f"./adam-deployment-{company_slug}-{timestamp}"

    os.makedirs(output_dir, exist_ok=True)
    print(f"  Output: {os.path.abspath(output_dir)}")

    # Save parsed DNA data
    dna_json_path = os.path.join(output_dir, "adam-dna-parsed.json")
    # Clean the data for JSON serialization
    serializable_dna = json.loads(json.dumps(dna_data, default=str))
    with open(dna_json_path, "w") as f:
        json.dump(serializable_dna, f, indent=2)
    print(f"  Parsed DNA data saved: adam-dna-parsed.json")

    # ================================================================
    # Phase 2: Generate Platform-Specific Deployments
    # ================================================================
    print()
    print("=" * 60)
    print("  Phase 2: Generating Deployment Specifications")
    print("=" * 60)
    print(f"  Target Platforms: {', '.join(platforms)}")

    all_files = {}
    total_files = 0

    for platform in platforms:
        platform_display, generator_class = PLATFORM_MAP.get(platform, (platform, None))
        if generator_class is None:
            continue

        print(f"\n  --- {platform_display} ---")

        # Generate IaC
        if not args.no_iac:
            try:
                gen = generator_class(dna_data, output_dir)
                files = gen.generate()
                all_files.update(files)
                total_files += len(files)
                print(f"    IaC templates: {len(files)} files")
                if args.verbose:
                    for fp, desc in files.items():
                        print(f"      - {os.path.relpath(fp, output_dir)}: {desc}")
            except Exception as e:
                print(f"    ERROR generating IaC: {e}")

    # ================================================================
    # Phase 3: Generate Configuration Bundle
    # ================================================================
    if not args.no_config:
        print(f"\n  --- Configuration Bundle ---")
        try:
            config_gen = ConfigBundleGenerator(dna_data, output_dir)
            config_files = config_gen.generate()
            all_files.update(config_files)
            total_files += len(config_files)
            print(f"    Config files: {len(config_files)} files")
            if args.verbose:
                for fp, desc in config_files.items():
                    print(f"      - {os.path.relpath(fp, output_dir)}: {desc}")
        except Exception as e:
            print(f"    ERROR generating configs: {e}")

    # ================================================================
    # Phase 4: Generate Word Documents
    # ================================================================
    if not args.no_docx:
        print(f"\n  --- Word Document Specifications ---")
        try:
            docx_gen = DocxSpecGenerator(dna_data, output_dir)
            docx_files = docx_gen.generate(platforms)
            all_files.update(docx_files)
            total_files += len(docx_files)
            print(f"    Word documents: {len(docx_files)} files")
            for fp, desc in docx_files.items():
                print(f"      - {os.path.basename(fp)}")
        except Exception as e:
            print(f"    ERROR generating Word docs: {e}")

    # ================================================================
    # Summary
    # ================================================================
    print()
    print("=" * 60)
    print("  ADAM DNA Deployment Specification — COMPLETE")
    print("=" * 60)
    print(f"  Company:         {company_name}")
    print(f"  Platforms:       {', '.join(platforms)}")
    print(f"  Total files:     {total_files}")
    print(f"  Output directory: {os.path.abspath(output_dir)}")
    print()
    print("  Generated artifacts:")
    print(f"    - Infrastructure-as-Code templates (Terraform/Bicep/CloudFormation/Helm)")
    print(f"    - JSON/YAML configuration bundles")
    print(f"    - CORE Graph seed data")
    print(f"    - BOSS scoring policies (OPA/Rego)")
    print(f"    - Agent registry ({sum(len(c['agents']) for c in generators.base_generator.AGENT_CLASSES.values())} agents)")
    print(f"    - Word document deployment specifications")
    print()
    print("  Next steps:")
    print("    1. Review generated deployment specifications")
    print("    2. Customize Terraform/Bicep variables for your environment")
    print("    3. Run 'terraform init && terraform plan' for your target platform")
    print("    4. Execute the 7-phase bootstrap deployment procedure")
    print()

    return 0

if __name__ == "__main__":
    try:
        import generators.base_generator
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n  Interrupted.")
        sys.exit(1)
