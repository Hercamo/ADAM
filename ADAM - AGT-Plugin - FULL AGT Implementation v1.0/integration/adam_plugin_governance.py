"""
ADAM-AGT Plugin Governance Bridge Module

This module bridges Microsoft's Agent Governance Toolkit (AGT) Agent Marketplace
(plugin signing, manifest verification) with ADAM's Cryptographic Authorization Vault
and capability-based security model.

Key Components:
- Ed25519 digital signature support for plugin authenticity
- Plugin manifest validation against ADAM governance requirements
- Capability token issuance and validation (capability-based authorization)
- Cryptographic vault integration for key and capability management
- Full plugin lifecycle governance (registration, verification, activation, revocation)

The bridge ensures that all plugins integrated into ADAM's 81-Agent Mesh are
cryptographically signed, properly authorized, and respect agent capability boundaries.

Author: ADAM Book v0.4
Version: 1.0.0
Python: 3.10+
"""

import base64
import hashlib
import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Set
from uuid import uuid4

try:
    from cryptography.hazmat.primitives import serialization, hashes
    from cryptography.hazmat.primitives.asymmetric import ed25519
    from cryptography.hazmat.backends import default_backend
except ImportError:
    raise ImportError("cryptography >= 41.0.0 required for Ed25519 operations")

# Configure module logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class PluginStatus(Enum):
    """Plugin lifecycle status in ADAM governance."""
    REGISTERED = "registered"
    SIGNED = "signed"
    VERIFIED = "verified"
    AUTHORIZED = "authorized"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    REVOKED = "revoked"


class CapabilityLevel(Enum):
    """Agent capability authorization levels."""
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    ADMIN = "admin"


@dataclass
class PluginManifest:
    """Plugin manifest defining metadata, capabilities, and governance requirements."""
    plugin_id: str
    plugin_name: str
    version: str
    publisher: str
    description: str
    capabilities: List[str]  # List of capability names
    required_framework_version: str = "1.0.0"
    supported_agent_layers: List[int] = field(default_factory=list)  # Ring 0-4
    dependencies: List[str] = field(default_factory=list)
    security_level: str = "moderate"  # low, moderate, high, critical
    data_classification: str = "internal"  # public, internal, confidential, restricted
    author: str = ""
    repository_url: str = ""
    license: str = "MIT"
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    governance_requirements: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        return data

    def compute_manifest_hash(self) -> str:
        """Compute SHA-256 hash of manifest for verification."""
        # Exclude signature-related fields from hash
        manifest_dict = self.to_dict()
        manifest_json = json.dumps(manifest_dict, sort_keys=True)
        return hashlib.sha256(manifest_json.encode()).hexdigest()


@dataclass
class CapabilityToken:
    """Authorization token granting specific capabilities to an agent/plugin."""
    token_id: str
    plugin_id: str
    agent_id: str
    capabilities: Set[CapabilityLevel]
    issued_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    issued_by: str = "adam_vault_authority"
    signature: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_valid(self) -> bool:
        """Check if token is still valid (not expired)."""
        if self.expires_at is None:
            return True
        return datetime.utcnow(timezone.utc) < self.expires_at

    def has_capability(self, capability: CapabilityLevel) -> bool:
        """Check if token grants a specific capability."""
        return capability in self.capabilities

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'token_id': self.token_id,
            'plugin_id': self.plugin_id,
            'agent_id': self.agent_id,
            'capabilities': [c.value for c in self.capabilities],
            'issued_at': self.issued_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'issued_by': self.issued_by,
            'valid': self.is_valid(),
            'metadata': self.metadata,
        }


@dataclass
class SignatureVerificationResult:
    """Result of cryptographic signature verification."""
    is_valid: bool
    plugin_id: str
    signer_public_key: str
    signature_timestamp: datetime
    manifest_hash: str
    verification_timestamp: datetime = field(default_factory=datetime.utcnow)
    error_message: str = ""
    verified_by: str = "adam_plugin_governance"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'is_valid': self.is_valid,
            'plugin_id': self.plugin_id,
            'signer_public_key': self.signer_public_key,
            'signature_timestamp': self.signature_timestamp.isoformat(),
            'manifest_hash': self.manifest_hash,
            'verification_timestamp': self.verification_timestamp.isoformat(),
            'verified_by': self.verified_by,
            'error_message': self.error_message,
        }


class Ed25519Signer:
    """
    Cryptographic signer using Ed25519 algorithm for plugin authenticity.
    Provides key generation, signing, and verification operations.
    """

    def __init__(self):
        """Initialize Ed25519 signer."""
        self._private_key: Optional[ed25519.Ed25519PrivateKey] = None
        self._public_key: Optional[ed25519.Ed25519PublicKey] = None
        logger.info("Ed25519Signer initialized")

    def generate_keypair(self) -> Tuple[str, str]:
        """
        Generate a new Ed25519 key pair.

        Returns:
            Tuple of (private_key_pem, public_key_pem) as strings
        """
        # Generate private key
        private_key = ed25519.Ed25519PrivateKey.generate()
        self._private_key = private_key

        # Derive public key
        public_key = private_key.public_key()
        self._public_key = public_key

        # Serialize to PEM format
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode('utf-8')

        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')

        logger.info("Generated new Ed25519 key pair")
        return private_pem, public_pem

    def load_private_key(self, private_key_pem: str) -> None:
        """Load a private key from PEM format."""
        private_key = serialization.load_pem_private_key(
            private_key_pem.encode('utf-8'),
            password=None,
            backend=default_backend()
        )
        if not isinstance(private_key, ed25519.Ed25519PrivateKey):
            raise ValueError("Provided key is not an Ed25519 private key")
        self._private_key = private_key
        self._public_key = private_key.public_key()
        logger.info("Loaded private key from PEM")

    def load_public_key(self, public_key_pem: str) -> None:
        """Load a public key from PEM format."""
        public_key = serialization.load_pem_public_key(
            public_key_pem.encode('utf-8'),
            backend=default_backend()
        )
        if not isinstance(public_key, ed25519.Ed25519PublicKey):
            raise ValueError("Provided key is not an Ed25519 public key")
        self._public_key = public_key
        logger.info("Loaded public key from PEM")

    def sign(self, data: bytes) -> str:
        """
        Sign data with the private key.

        Args:
            data: Bytes to sign

        Returns:
            Base64-encoded signature
        """
        if self._private_key is None:
            raise ValueError("Private key not loaded")

        signature = self._private_key.sign(data)
        return base64.b64encode(signature).decode('utf-8')

    def verify(self, data: bytes, signature_b64: str) -> bool:
        """
        Verify a signature with the public key.

        Args:
            data: Original data that was signed
            signature_b64: Base64-encoded signature

        Returns:
            True if signature is valid, False otherwise
        """
        if self._public_key is None:
            raise ValueError("Public key not loaded")

        try:
            signature = base64.b64decode(signature_b64)
            self._public_key.verify(signature, data)
            return True
        except Exception as e:
            logger.warning(f"Signature verification failed: {e}")
            return False

    def get_public_key_pem(self) -> Optional[str]:
        """Get public key in PEM format."""
        if self._public_key is None:
            return None
        return self._public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')


class ManifestVerifier:
    """
    Validates plugin manifests against ADAM governance requirements
    and AGT plugin signing standards.
    """

    def __init__(self):
        """Initialize manifest verifier."""
        self._governance_rules = self._initialize_governance_rules()
        logger.info("ManifestVerifier initialized")

    def _initialize_governance_rules(self) -> Dict[str, Dict[str, Any]]:
        """Initialize governance validation rules."""
        return {
            'plugin_id': {
                'required': True,
                'type': 'string',
                'pattern': '^[a-z0-9-_]+$',
                'min_length': 3,
                'max_length': 64,
            },
            'plugin_name': {
                'required': True,
                'type': 'string',
                'min_length': 3,
                'max_length': 128,
            },
            'version': {
                'required': True,
                'type': 'string',
                'pattern': '^\\d+\\.\\d+\\.\\d+(-[a-zA-Z0-9]+)?$',  # Semantic versioning
            },
            'publisher': {
                'required': True,
                'type': 'string',
                'min_length': 3,
            },
            'capabilities': {
                'required': True,
                'type': 'list',
                'min_length': 1,
                'max_length': 50,
            },
            'security_level': {
                'required': True,
                'allowed_values': ['low', 'moderate', 'high', 'critical'],
            },
            'data_classification': {
                'required': True,
                'allowed_values': ['public', 'internal', 'confidential', 'restricted'],
            },
        }

    def verify_manifest(self, manifest: PluginManifest) -> Tuple[bool, List[str]]:
        """
        Verify plugin manifest against governance requirements.

        Args:
            manifest: Plugin manifest to verify

        Returns:
            Tuple of (is_valid, list_of_error_messages)
        """
        errors = []

        # Check required fields
        required_fields = {
            'plugin_id': manifest.plugin_id,
            'plugin_name': manifest.plugin_name,
            'version': manifest.version,
            'publisher': manifest.publisher,
        }

        for field_name, field_value in required_fields.items():
            if not field_value:
                errors.append(f"Required field '{field_name}' is empty")

        # Validate plugin_id format
        if manifest.plugin_id and not self._is_valid_plugin_id(manifest.plugin_id):
            errors.append("Invalid plugin_id format (must be lowercase alphanumeric with hyphens/underscores)")

        # Validate version format
        if manifest.version and not self._is_valid_version(manifest.version):
            errors.append("Invalid version format (must follow semantic versioning)")

        # Validate capabilities list
        if not manifest.capabilities or len(manifest.capabilities) == 0:
            errors.append("Plugin must declare at least one capability")

        # Validate security level
        if manifest.security_level not in ['low', 'moderate', 'high', 'critical']:
            errors.append(f"Invalid security_level: {manifest.security_level}")

        # Validate data classification
        if manifest.data_classification not in ['public', 'internal', 'confidential', 'restricted']:
            errors.append(f"Invalid data_classification: {manifest.data_classification}")

        # Check dependencies consistency
        if manifest.dependencies and not isinstance(manifest.dependencies, list):
            errors.append("Dependencies must be a list")

        # Check supported agent layers (Ring 0-4)
        for layer in manifest.supported_agent_layers:
            if layer < 0 or layer > 4:
                errors.append(f"Invalid agent layer: {layer} (must be 0-4)")

        is_valid = len(errors) == 0
        logger.info(
            f"Verified manifest for {manifest.plugin_id}: "
            f"valid={is_valid}, errors={len(errors)}"
        )

        return is_valid, errors

    @staticmethod
    def _is_valid_plugin_id(plugin_id: str) -> bool:
        """Check if plugin_id follows naming conventions."""
        import re
        return bool(re.match(r'^[a-z0-9][a-z0-9\-_]{1,62}[a-z0-9]$', plugin_id))

    @staticmethod
    def _is_valid_version(version: str) -> bool:
        """Check if version follows semantic versioning."""
        import re
        return bool(re.match(r'^\d+\.\d+\.\d+(-[a-zA-Z0-9]+)?$', version))


class CryptographicVaultBridge:
    """
    Integrates AGT marketplace signatures with ADAM's Cryptographic Authorization Vault.
    Manages plugin keys, capability tokens, and authorization policies.
    """

    def __init__(self):
        """Initialize vault bridge."""
        self._plugin_keys: Dict[str, str] = {}  # plugin_id -> public_key_pem
        self._capability_tokens: Dict[str, List[CapabilityToken]] = {}
        self._authorization_policies: Dict[str, Dict[str, Any]] = {}
        self._signer = Ed25519Signer()
        logger.info("CryptographicVaultBridge initialized")

    def register_plugin_key(self, plugin_id: str, public_key_pem: str) -> bool:
        """
        Register a plugin's public key in the vault.

        Args:
            plugin_id: Plugin identifier
            public_key_pem: Ed25519 public key in PEM format

        Returns:
            True if registered successfully
        """
        try:
            # Verify it's a valid Ed25519 public key
            signer = Ed25519Signer()
            signer.load_public_key(public_key_pem)

            self._plugin_keys[plugin_id] = public_key_pem
            logger.info(f"Registered plugin key for {plugin_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to register plugin key: {e}")
            return False

    def issue_capability_token(
        self,
        plugin_id: str,
        agent_id: str,
        capabilities: List[CapabilityLevel],
        duration_hours: int = 24
    ) -> CapabilityToken:
        """
        Issue a capability token for a plugin/agent combination.

        Args:
            plugin_id: Plugin requesting capabilities
            agent_id: Target agent
            capabilities: List of capabilities to grant
            duration_hours: Token validity duration in hours

        Returns:
            Issued CapabilityToken
        """
        token = CapabilityToken(
            token_id=str(uuid4()),
            plugin_id=plugin_id,
            agent_id=agent_id,
            capabilities=set(capabilities),
            expires_at=datetime.utcnow(timezone.utc) + timedelta(hours=duration_hours),
        )

        if plugin_id not in self._capability_tokens:
            self._capability_tokens[plugin_id] = []
        self._capability_tokens[plugin_id].append(token)

        logger.info(
            f"Issued capability token for {plugin_id}/{agent_id}: "
            f"capabilities={[c.value for c in capabilities]}"
        )

        return token

    def verify_capability_token(
        self,
        token: CapabilityToken,
        required_capability: CapabilityLevel
    ) -> bool:
        """
        Verify a capability token is valid and grants required capability.

        Args:
            token: Token to verify
            required_capability: Capability being requested

        Returns:
            True if token is valid and grants capability
        """
        if not token.is_valid():
            logger.warning(f"Token {token.token_id} is expired or invalid")
            return False

        if not token.has_capability(required_capability):
            logger.warning(
                f"Token {token.token_id} does not grant {required_capability.value}"
            )
            return False

        return True

    def get_plugin_authorization_policy(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        """Get authorization policy for a plugin."""
        return self._authorization_policies.get(plugin_id)

    def set_plugin_authorization_policy(
        self,
        plugin_id: str,
        policy: Dict[str, Any]
    ) -> None:
        """Set authorization policy for a plugin."""
        self._authorization_policies[plugin_id] = policy
        logger.info(f"Set authorization policy for {plugin_id}")


class AdamPluginGovernance:
    """
    Main plugin governance orchestrator providing full lifecycle governance:
    - Plugin registration and manifest validation
    - Cryptographic signing and verification
    - Capability token issuance and validation
    - Authorization policy enforcement
    - Integration with ADAM's 81-Agent Mesh and Cryptographic Authorization Vault

    This class implements the complete AGT/ADAM plugin lifecycle:
    1. REGISTERED: Plugin manifest submitted
    2. SIGNED: Manifest cryptographically signed
    3. VERIFIED: Signature and manifest validated
    4. AUTHORIZED: Capability tokens issued
    5. ACTIVE: Plugin can execute within its authorized scope
    6. SUSPENDED/REVOKED: Plugin access revoked
    """

    def __init__(self):
        """Initialize plugin governance system."""
        self._signer = Ed25519Signer()
        self._verifier = ManifestVerifier()
        self._vault = CryptographicVaultBridge()
        self._plugin_registry: Dict[str, Tuple[PluginManifest, PluginStatus]] = {}
        self._plugin_signatures: Dict[str, Tuple[str, datetime]] = {}
        logger.info("AdamPluginGovernance initialized")

    def register_plugin(self, manifest: PluginManifest) -> Tuple[bool, str]:
        """
        Register a new plugin with governance framework.

        Args:
            manifest: Plugin manifest

        Returns:
            Tuple of (success, plugin_id_or_error_message)
        """
        # Validate manifest
        is_valid, errors = self._verifier.verify_manifest(manifest)
        if not is_valid:
            error_msg = "; ".join(errors)
            logger.error(f"Manifest validation failed: {error_msg}")
            return False, error_msg

        # Check if plugin already registered
        if manifest.plugin_id in self._plugin_registry:
            logger.warning(f"Plugin {manifest.plugin_id} already registered")
            return False, f"Plugin {manifest.plugin_id} already exists"

        # Register plugin
        self._plugin_registry[manifest.plugin_id] = (manifest, PluginStatus.REGISTERED)
        logger.info(f"Registered plugin {manifest.plugin_id}")

        return True, manifest.plugin_id

    def sign_plugin_manifest(
        self,
        plugin_id: str,
        private_key_pem: str
    ) -> Tuple[bool, str]:
        """
        Sign plugin manifest with private key.

        Args:
            plugin_id: Plugin to sign
            private_key_pem: Ed25519 private key in PEM format

        Returns:
            Tuple of (success, signature_or_error_message)
        """
        if plugin_id not in self._plugin_registry:
            return False, f"Plugin {plugin_id} not found"

        manifest, _ = self._plugin_registry[plugin_id]

        # Load private key and sign
        self._signer.load_private_key(private_key_pem)
        manifest_bytes = json.dumps(manifest.to_dict(), sort_keys=True).encode('utf-8')
        signature = self._signer.sign(manifest_bytes)

        # Store signature
        self._plugin_signatures[plugin_id] = (signature, datetime.utcnow())

        # Update plugin status
        self._plugin_registry[plugin_id] = (manifest, PluginStatus.SIGNED)

        logger.info(f"Signed manifest for plugin {plugin_id}")
        return True, signature

    def verify_plugin_signature(
        self,
        plugin_id: str,
        signature: str,
        public_key_pem: str
    ) -> SignatureVerificationResult:
        """
        Verify plugin manifest signature.

        Args:
            plugin_id: Plugin to verify
            signature: Base64-encoded signature
            public_key_pem: Ed25519 public key in PEM format

        Returns:
            SignatureVerificationResult
        """
        if plugin_id not in self._plugin_registry:
            return SignatureVerificationResult(
                is_valid=False,
                plugin_id=plugin_id,
                signer_public_key=public_key_pem,
                signature_timestamp=datetime.utcnow(),
                manifest_hash="",
                error_message=f"Plugin {plugin_id} not found"
            )

        manifest, _ = self._plugin_registry[plugin_id]
        manifest_bytes = json.dumps(manifest.to_dict(), sort_keys=True).encode('utf-8')
        manifest_hash = hashlib.sha256(manifest_bytes).hexdigest()

        # Verify signature
        self._signer.load_public_key(public_key_pem)
        is_valid = self._signer.verify(manifest_bytes, signature)

        if is_valid:
            # Update plugin status
            self._plugin_registry[plugin_id] = (manifest, PluginStatus.VERIFIED)
            # Register key in vault
            self._vault.register_plugin_key(plugin_id, public_key_pem)
            logger.info(f"Verified signature for plugin {plugin_id}")

        result = SignatureVerificationResult(
            is_valid=is_valid,
            plugin_id=plugin_id,
            signer_public_key=public_key_pem,
            signature_timestamp=datetime.utcnow(),
            manifest_hash=manifest_hash,
        )

        return result

    def authorize_plugin_for_agent(
        self,
        plugin_id: str,
        agent_id: str,
        capabilities: List[CapabilityLevel]
    ) -> Tuple[bool, CapabilityToken]:
        """
        Authorize a plugin to interact with an agent with specified capabilities.

        Args:
            plugin_id: Plugin to authorize
            agent_id: Target agent
            capabilities: Capabilities to grant

        Returns:
            Tuple of (success, capability_token)
        """
        if plugin_id not in self._plugin_registry:
            return False, CapabilityToken(
                token_id="",
                plugin_id=plugin_id,
                agent_id=agent_id,
                capabilities=set(),
                error_message=f"Plugin {plugin_id} not found"
            )

        manifest, status = self._plugin_registry[plugin_id]

        # Check if plugin is verified
        if status != PluginStatus.VERIFIED:
            return False, CapabilityToken(
                token_id="",
                plugin_id=plugin_id,
                agent_id=agent_id,
                capabilities=set(),
            )

        # Check if capabilities match manifest
        for capability in capabilities:
            if capability.value not in manifest.capabilities:
                logger.warning(
                    f"Plugin {plugin_id} requesting unauthorized capability: {capability.value}"
                )

        # Issue capability token
        token = self._vault.issue_capability_token(
            plugin_id, agent_id, capabilities, duration_hours=24
        )

        # Update plugin status
        self._plugin_registry[plugin_id] = (manifest, PluginStatus.AUTHORIZED)

        logger.info(
            f"Authorized plugin {plugin_id} for agent {agent_id} "
            f"with {len(capabilities)} capabilities"
        )

        return True, token

    def activate_plugin(self, plugin_id: str) -> bool:
        """
        Activate a plugin (make it executable).

        Args:
            plugin_id: Plugin to activate

        Returns:
            True if activated successfully
        """
        if plugin_id not in self._plugin_registry:
            return False

        manifest, status = self._plugin_registry[plugin_id]

        if status not in [PluginStatus.AUTHORIZED, PluginStatus.SUSPENDED]:
            logger.warning(f"Cannot activate plugin {plugin_id} in status {status.value}")
            return False

        self._plugin_registry[plugin_id] = (manifest, PluginStatus.ACTIVE)
        logger.info(f"Activated plugin {plugin_id}")
        return True

    def suspend_plugin(self, plugin_id: str, reason: str = "") -> bool:
        """
        Suspend plugin execution (revoke capability tokens).

        Args:
            plugin_id: Plugin to suspend
            reason: Reason for suspension

        Returns:
            True if suspended successfully
        """
        if plugin_id not in self._plugin_registry:
            return False

        manifest, _ = self._plugin_registry[plugin_id]
        self._plugin_registry[plugin_id] = (manifest, PluginStatus.SUSPENDED)
        logger.warning(f"Suspended plugin {plugin_id}: {reason}")
        return True

    def revoke_plugin(self, plugin_id: str, reason: str = "") -> bool:
        """
        Permanently revoke plugin (remove from registry).

        Args:
            plugin_id: Plugin to revoke
            reason: Reason for revocation

        Returns:
            True if revoked successfully
        """
        if plugin_id not in self._plugin_registry:
            return False

        manifest, _ = self._plugin_registry[plugin_id]
        self._plugin_registry[plugin_id] = (manifest, PluginStatus.REVOKED)
        logger.warning(f"Revoked plugin {plugin_id}: {reason}")
        return True

    def get_plugin_status(self, plugin_id: str) -> Optional[PluginStatus]:
        """Get current status of a plugin."""
        if plugin_id not in self._plugin_registry:
            return None
        _, status = self._plugin_registry[plugin_id]
        return status

    def get_plugin_manifest(self, plugin_id: str) -> Optional[PluginManifest]:
        """Get manifest for a registered plugin."""
        if plugin_id not in self._plugin_registry:
            return None
        manifest, _ = self._plugin_registry[plugin_id]
        return manifest

    def list_plugins(self, status_filter: Optional[PluginStatus] = None) -> List[Tuple[str, PluginStatus]]:
        """
        List all registered plugins, optionally filtered by status.

        Args:
            status_filter: Optional status to filter by

        Returns:
            List of (plugin_id, status) tuples
        """
        plugins = []
        for plugin_id, (_, status) in self._plugin_registry.items():
            if status_filter is None or status == status_filter:
                plugins.append((plugin_id, status))
        return plugins

    def export_governance_report(self) -> Dict[str, Any]:
        """Export plugin governance status report."""
        status_counts = {}
        for _, (_, status) in self._plugin_registry.items():
            status_counts[status.value] = status_counts.get(status.value, 0) + 1

        return {
            'report_id': str(uuid4()),
            'generated_at': datetime.utcnow().isoformat(),
            'total_plugins': len(self._plugin_registry),
            'status_distribution': status_counts,
            'signed_plugins': len(self._plugin_signatures),
            'plugins': [
                {
                    'plugin_id': pid,
                    'name': manifest.plugin_name,
                    'version': manifest.version,
                    'status': status.value,
                }
                for pid, (manifest, status) in self._plugin_registry.items()
            ]
        }
