"""
ADAM-AGT Integration Bridge Modules
====================================

Python integration bridges connecting Microsoft's Agent Governance Toolkit (AGT)
with the ADAM (Autonomy Doctrine & Architecture Model) framework.

Each module maps one AGT package to the corresponding ADAM architectural planes:

    adam_policy_bridge       - AGT Agent OS      <-> ADAM Policy & Risk Plane
    adam_identity_provider   - AGT Agent Mesh     <-> ADAM 81-Agent Identity System
    adam_execution_rings     - AGT Agent Runtime  <-> ADAM Enforcement Hooks
    adam_sre_integration     - AGT Agent SRE      <-> ADAM Stability & Drift Plane
    adam_compliance_bridge   - AGT Agent Compliance <-> ADAM Evidence & Audit Plane
    adam_plugin_governance   - AGT Agent Marketplace <-> ADAM Cryptographic Authorization Vault
    adam_rl_governance       - AGT Agent Lightning <-> ADAM Doctrine Alignment + Digital Twins

Usage:
    from integration.adam_policy_bridge import AdamPolicyBridge
    from integration.adam_identity_provider import AdamAgentIdentityProvider
    from integration.adam_execution_rings import AdamRuntimeBridge
    from integration.adam_sre_integration import AdamSREIntegration
    from integration.adam_compliance_bridge import AdamComplianceBridge
    from integration.adam_plugin_governance import AdamPluginGovernance
    from integration.adam_rl_governance import AdamRLGovernance
"""

__version__ = "1.0.0"
__author__ = "ADAM Framework"

__all__ = [
    "adam_policy_bridge",
    "adam_identity_provider",
    "adam_execution_rings",
    "adam_sre_integration",
    "adam_compliance_bridge",
    "adam_plugin_governance",
    "adam_rl_governance",
]
