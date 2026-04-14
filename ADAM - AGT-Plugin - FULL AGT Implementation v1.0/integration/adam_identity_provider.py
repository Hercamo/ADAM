"""
ADAM Identity Provider Module

Bridges Microsoft's Agent Governance Toolkit (AGT) Agent Mesh with ADAM's 81-Agent
identity system. Manages Decentralized Identifiers (DIDs), cryptographic key pairs,
trust scoring, and Inter-Agent Trust Protocol (IATP) for agent authentication and
authorization across the ADAM autonomous mesh.

Key Components:
- DIDManager: Manages DIDs for ADAM's 81 agents across 5 layers
- Ed25519KeyPair: Key generation, signing, verification for agent authentication
- TrustScoreTranslator: Maps AGT trust scores (0-1000) to ADAM BOSS composite scores (0-100)
- IATProtocolHandler: Inter-Agent Trust Protocol message handling
- AdamAgentIdentityProvider: Full lifecycle management for agent identity

ADAM Concepts:
- 81-Agent Mesh: 5-layer topology (Intent, Governor Agent, Orchestration, Work Group, Digital Twin)
- CORE Engine: Identity policy and agent governance
- Exception Economy: Trust-based authorization budgets

AGT Concepts:
- DID (Decentralized Identifier): Cryptographically verifiable agent identity
- Ed25519: Signing algorithm for agent authentication
- IATP: Inter-Agent Trust Protocol for agent-to-agent communication
- Trust Score: 0-1000 scale with tiers (QUARANTINED, RESTRICTED, MONITORED, VERIFIED, TRUSTED)

Author: ADAM Framework
Version: 1.0.0
Python: 3.10+
"""

import asyncio
import base64
import hashlib
import json
import logging
import secrets
import uuid
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from abc import ABC, abstractmethod

# cryptography library for Ed25519 and X25519
try:
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import ed25519
    from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
    from cryptography.hazmat.backends import default_backend
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning(
        "cryptography library not available. "
        "Install with: pip install cryptography"
    )

__version__ = "1.0.0"
__author__ = "ADAM Framework"

# Configure logging
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)


# ============================================================================
# Enums and Constants
# ============================================================================

class AgentLayer(str, Enum):
    """ADAM 81-Agent Mesh layers."""
    INTENT = "intent-layer"
    GOVERNOR_AGENT = "governor_agent-layer"
    ORCHESTRATION = "orchestration-layer"
    WORK_GROUP = "workgroup-layer"
    DIGITAL_TWIN = "digital-twin-layer"


class AgentRole(str, Enum):
    """Agent roles within ADAM ecosystem."""
    INTENT_CAPTURE = "intent_capture"
    DOMAIN_POLICY = "domain_policy"
    ORCHESTRATION = "orchestration"
    TASK_EXECUTION = "task_execution"
    META_GOVERNANCE = "meta_governance"


class TrustTier(str, Enum):
    """AGT trust score tiers (0-1000 scale)."""
    QUARANTINED = "QUARANTINED"     # 0-100: Quarantined/untrusted
    RESTRICTED = "RESTRICTED"       # 101-300: Restricted access
    MONITORED = "MONITORED"         # 301-500: Monitored/under observation
    VERIFIED = "VERIFIED"           # 501-800: Verified and trusted
    TRUSTED = "TRUSTED"             # 801-1000: Fully trusted


class IATMessageType(str, Enum):
    """Inter-Agent Trust Protocol message types."""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    TRUST_UPDATE = "trust_update"
    KEY_EXCHANGE = "key_exchange"
    HEARTBEAT = "heartbeat"
    CHALLENGE = "challenge"
    RESPONSE = "response"


# Trust score tier boundaries
TRUST_TIER_BOUNDARIES = {
    TrustTier.QUARANTINED: (0, 100),
    TrustTier.RESTRICTED: (101, 300),
    TrustTier.MONITORED: (301, 500),
    TrustTier.VERIFIED: (501, 800),
    TrustTier.TRUSTED: (801, 1000),
}


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class DIDDocument:
    """W3C-compatible DID Document for agent identity."""

    did: str  # Format: did:adam:{agentId}
    agent_id: str
    agent_layer: AgentLayer
    agent_role: AgentRole
    public_key_ed25519: str  # Base64-encoded Ed25519 public key
    public_key_x25519: str  # Base64-encoded X25519 public key
    created: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    proof: str = ""  # Cryptographic proof of DID ownership

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dictionary."""
        return {
            "@context": [
                "https://www.w3.org/ns/did/v1",
                "https://adam-governance.io/contexts/adam-v0.4",
            ],
            "id": self.did,
            "agent": {
                "id": self.agent_id,
                "layer": self.agent_layer.value,
                "role": self.agent_role.value,
            },
            "verificationMethod": [
                {
                    "id": f"{self.did}#key-ed25519-signing",
                    "type": "Ed25519VerificationKey2020",
                    "controller": self.did,
                    "publicKeyMultibase": f"z{self.public_key_ed25519}",
                },
                {
                    "id": f"{self.did}#key-x25519-encryption",
                    "type": "X25519KeyAgreementKey2020",
                    "controller": self.did,
                    "publicKeyMultibase": f"z{self.public_key_x25519}",
                },
            ],
            "authentication": [f"{self.did}#key-ed25519-signing"],
            "service": [
                {
                    "id": f"{self.did}#mesh-endpoint",
                    "type": "MeshCommunicationService",
                    "serviceEndpoint": f"grpc://agent-{self.agent_id}.mesh.adam-governance.io:50051",
                }
            ],
            "created": self.created.isoformat(),
            "updated": self.updated.isoformat(),
            "proof": self.proof,
        }


@dataclass
class TrustScore:
    """AGT trust score for an agent."""

    agent_id: str
    score: float  # 0-1000 scale
    tier: TrustTier = field(init=False)
    factors: Dict[str, float] = field(default_factory=dict)
    # Factors: latency_score, compliance_score, error_rate, anomaly_score, security_incidents
    history: List[Tuple[datetime, float]] = field(default_factory=list)
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc) + timedelta(hours=24))

    def __post_init__(self):
        """Validate and set tier."""
        if not 0 <= self.score <= 1000:
            raise ValueError(f"Trust score must be 0-1000, got {self.score}")

        # Determine tier
        for tier, (min_val, max_val) in TRUST_TIER_BOUNDARIES.items():
            if min_val <= self.score <= max_val:
                self.tier = tier
                break

    def is_expired(self) -> bool:
        """Check if trust score has expired."""
        return datetime.now(timezone.utc) > self.expires_at

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "agent_id": self.agent_id,
            "score": round(self.score, 2),
            "tier": self.tier.value,
            "factors": {k: round(v, 2) for k, v in self.factors.items()},
            "history": [
                {"timestamp": ts.isoformat(), "score": round(s, 2)}
                for ts, s in self.history[-10:]  # Last 10 entries
            ],
            "last_updated": self.last_updated.isoformat(),
            "expires_at": self.expires_at.isoformat(),
        }


@dataclass
class IATMessage:
    """Inter-Agent Trust Protocol message."""

    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    message_type: IATMessageType = IATMessageType.AUTHENTICATION
    from_agent_id: str = ""
    to_agent_id: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    payload: Dict[str, Any] = field(default_factory=dict)
    signature: str = ""  # Ed25519 signature of payload
    nonce: str = field(default_factory=lambda: secrets.token_hex(16))
    expiration: datetime = field(default_factory=lambda: datetime.now(timezone.utc) + timedelta(minutes=5))

    def is_expired(self) -> bool:
        """Check if message has expired."""
        return datetime.now(timezone.utc) > self.expiration

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (without signature for signing)."""
        return {
            "message_id": self.message_id,
            "message_type": self.message_type.value,
            "from_agent_id": self.from_agent_id,
            "to_agent_id": self.to_agent_id,
            "timestamp": self.timestamp.isoformat(),
            "payload": self.payload,
            "nonce": self.nonce,
            "expiration": self.expiration.isoformat(),
        }


@dataclass
class AgentIdentity:
    """Complete ADAM agent identity including DID and trust."""

    agent_id: str
    layer: AgentLayer
    role: AgentRole
    did_document: DIDDocument
    trust_score: TrustScore
    signing_key_private: Optional[str] = None  # Base64-encoded, store securely
    encryption_key_private: Optional[str] = None  # Base64-encoded, store securely
    authorization_capabilities: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_public_dict(self) -> Dict[str, Any]:
        """Convert to public-safe dictionary (no private keys)."""
        return {
            "agent_id": self.agent_id,
            "layer": self.layer.value,
            "role": self.role.value,
            "did_document": self.did_document.to_dict(),
            "trust_score": self.trust_score.to_dict(),
            "authorization_capabilities": self.authorization_capabilities,
        }


# ============================================================================
# Ed25519 Key Pair Manager
# ============================================================================

class Ed25519KeyPair:
    """
    Manages Ed25519 key pair generation, signing, and verification
    for agent cryptographic authentication.
    """

    def __init__(self):
        """Initialize key pair manager."""
        if not CRYPTO_AVAILABLE:
            raise RuntimeError(
                "cryptography library required. Install with: pip install cryptography"
            )
        self.logger = logging.getLogger(f"{__name__}.Ed25519KeyPair")

    @staticmethod
    def generate_keypair() -> Tuple[str, str]:
        """
        Generate a new Ed25519 key pair.

        Returns:
            Tuple of (private_key_base64, public_key_base64)
        """
        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()

        # Serialize to base64
        private_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption(),
        )
        public_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )

        private_b64 = base64.b64encode(private_bytes).decode('utf-8')
        public_b64 = base64.b64encode(public_bytes).decode('utf-8')

        return private_b64, public_b64

    @staticmethod
    def generate_encryption_keypair() -> Tuple[str, str]:
        """
        Generate a new X25519 key pair for encryption.

        Returns:
            Tuple of (private_key_base64, public_key_base64)
        """
        private_key = X25519PrivateKey.generate()
        public_key = private_key.public_key()

        # Serialize to base64
        private_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption(),
        )
        public_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )

        private_b64 = base64.b64encode(private_bytes).decode('utf-8')
        public_b64 = base64.b64encode(public_bytes).decode('utf-8')

        return private_b64, public_b64

    @staticmethod
    def sign_message(private_key_b64: str, message: str) -> str:
        """
        Sign a message with Ed25519 private key.

        Args:
            private_key_b64: Base64-encoded Ed25519 private key
            message: Message to sign

        Returns:
            Base64-encoded signature
        """
        private_bytes = base64.b64decode(private_key_b64)
        private_key = ed25519.Ed25519PrivateKey.from_private_bytes(private_bytes)
        signature = private_key.sign(message.encode('utf-8'))
        return base64.b64encode(signature).decode('utf-8')

    @staticmethod
    def verify_signature(public_key_b64: str, message: str, signature_b64: str) -> bool:
        """
        Verify message signature with Ed25519 public key.

        Args:
            public_key_b64: Base64-encoded Ed25519 public key
            message: Original message
            signature_b64: Base64-encoded signature

        Returns:
            True if signature is valid, False otherwise
        """
        try:
            public_bytes = base64.b64decode(public_key_b64)
            public_key = ed25519.Ed25519PublicKey.from_public_bytes(public_bytes)
            signature_bytes = base64.b64decode(signature_b64)
            public_key.verify(signature_bytes, message.encode('utf-8'))
            return True
        except Exception:
            return False


# ============================================================================
# DID Manager
# ============================================================================

class DIDManager:
    """
    Manages Decentralized Identifiers (DIDs) for ADAM's 81-agent mesh.
    Handles DID creation, resolution, and document management.
    """

    def __init__(self, registry_endpoint: str = "https://did-registry.adam-governance.io/api/v1"):
        """
        Initialize DID manager.

        Args:
            registry_endpoint: DID registry endpoint URL
        """
        self.logger = logging.getLogger(f"{__name__}.DIDManager")
        self.registry_endpoint = registry_endpoint
        self.did_cache: Dict[str, DIDDocument] = {}
        self.key_manager = Ed25519KeyPair()

    async def create_did(
        self,
        agent_id: str,
        agent_layer: AgentLayer,
        agent_role: AgentRole,
    ) -> DIDDocument:
        """
        Create a new DID for an agent.

        Args:
            agent_id: Unique agent identifier
            agent_layer: Layer in ADAM 5-layer topology
            agent_role: Role within agent layer

        Returns:
            DIDDocument with generated identity
        """
        self.logger.info(f"Creating DID for agent {agent_id} in {agent_layer.value}")

        # Generate cryptographic keys
        signing_priv, signing_pub = self.key_manager.generate_keypair()
        encryption_priv, encryption_pub = self.key_manager.generate_encryption_keypair()

        # Create DID
        did = f"did:adam:{agent_id}"

        # Create proof of DID ownership
        proof_input = f"{did}:{agent_layer.value}:{agent_role.value}:{signing_pub}"
        proof = hashlib.sha256(proof_input.encode()).hexdigest()

        # Create DID document
        did_doc = DIDDocument(
            did=did,
            agent_id=agent_id,
            agent_layer=agent_layer,
            agent_role=agent_role,
            public_key_ed25519=signing_pub,
            public_key_x25519=encryption_pub,
            proof=proof,
        )

        # Cache locally
        self.did_cache[did] = did_doc

        self.logger.debug(f"Created DID {did} with proof {proof[:16]}...")
        return did_doc

    async def resolve_did(self, did: str) -> Optional[DIDDocument]:
        """
        Resolve a DID to its document.

        Args:
            did: DID to resolve

        Returns:
            DIDDocument if found, None otherwise
        """
        # Check cache first
        if did in self.did_cache:
            return self.did_cache[did]

        # In production, would query registry endpoint
        # For now, simulate async lookup
        await asyncio.sleep(0.01)

        self.logger.debug(f"Resolved DID {did} from cache")
        return self.did_cache.get(did)

    def verify_did_proof(self, did_doc: DIDDocument) -> bool:
        """
        Verify that a DID document proof is valid.

        Args:
            did_doc: DID document to verify

        Returns:
            True if proof is valid
        """
        expected_proof_input = (
            f"{did_doc.did}:{did_doc.agent_layer.value}:"
            f"{did_doc.agent_role.value}:{did_doc.public_key_ed25519}"
        )
        expected_proof = hashlib.sha256(expected_proof_input.encode()).hexdigest()
        return did_doc.proof == expected_proof

    async def register_did(self, did_doc: DIDDocument) -> bool:
        """
        Register a DID document with the registry.

        Args:
            did_doc: DID document to register

        Returns:
            True if registration successful
        """
        self.logger.info(f"Registering DID {did_doc.did}")

        # Verify proof before registration
        if not self.verify_did_proof(did_doc):
            self.logger.error(f"Invalid proof for DID {did_doc.did}")
            return False

        # In production, would POST to registry endpoint
        # For now, cache locally
        self.did_cache[did_doc.did] = did_doc

        self.logger.debug(f"Registered DID {did_doc.did}")
        return True

    def get_agent_did(self, agent_id: str) -> Optional[DIDDocument]:
        """
        Get DID for a specific agent ID.

        Args:
            agent_id: Agent identifier

        Returns:
            DIDDocument if found, None otherwise
        """
        for did_doc in self.did_cache.values():
            if did_doc.agent_id == agent_id:
                return did_doc
        return None


# ============================================================================
# Trust Score Translator
# ============================================================================

class TrustScoreTranslator:
    """
    Translates between AGT trust scores (0-1000) and ADAM BOSS composite scores (0-100).
    Provides bidirectional mapping with tier alignment.
    """

    def __init__(self):
        """Initialize trust score translator."""
        self.logger = logging.getLogger(f"{__name__}.TrustScoreTranslator")

    def agt_trust_to_boss_score(self, trust_score: float) -> float:
        """
        Convert AGT trust score (0-1000) to ADAM BOSS composite score (0-100).

        Args:
            trust_score: AGT trust score (0-1000)

        Returns:
            ADAM BOSS composite score (0-100)
        """
        if not 0 <= trust_score <= 1000:
            raise ValueError(f"Trust score must be 0-1000, got {trust_score}")

        # Invert mapping: high trust = low risk (high BOSS)
        # TRUSTED (801-1000) -> SOAP (0-10)
        # VERIFIED (501-800) -> MODERATE (11-30)
        # MONITORED (301-500) -> ELEVATED (31-50)
        # RESTRICTED (101-300) -> HIGH (51-75)
        # QUARANTINED (0-100) -> OHSHAT (76-100)

        if trust_score >= 801:
            # TRUSTED -> SOAP
            return 20 * (1000 - trust_score) / 199
        elif trust_score >= 501:
            # VERIFIED -> MODERATE
            return 20 + 20 * (800 - trust_score) / 300
        elif trust_score >= 301:
            # MONITORED -> ELEVATED
            return 40 + 20 * (500 - trust_score) / 200
        elif trust_score >= 101:
            # RESTRICTED -> HIGH
            return 60 + 20 * (300 - trust_score) / 200
        else:
            # QUARANTINED -> OHSHAT
            return 80 + 20 * (100 - trust_score) / 101

    def boss_score_to_agt_trust(self, boss_score: float) -> float:
        """
        Convert ADAM BOSS composite score (0-100) to AGT trust score (0-1000).

        Args:
            boss_score: ADAM BOSS composite score (0-100)

        Returns:
            AGT trust score (0-1000)
        """
        if not 0 <= boss_score <= 100:
            raise ValueError(f"BOSS score must be 0-100, got {boss_score}")

        # Inverse of agt_trust_to_boss_score mapping
        if boss_score <= 20:
            # SOAP -> TRUSTED
            return 1000 - boss_score * 199 / 20
        elif boss_score <= 40:
            # MODERATE -> VERIFIED
            return 800 - (boss_score - 20) * 300 / 20
        elif boss_score <= 60:
            # ELEVATED -> MONITORED
            return 500 - (boss_score - 40) * 200 / 20
        elif boss_score <= 80:
            # HIGH -> RESTRICTED
            return 300 - (boss_score - 60) * 200 / 20
        else:
            # OHSHAT -> QUARANTINED
            return 100 - (boss_score - 80) * 101 / 20

    def get_tier_alignment(
        self,
        agt_trust_tier: TrustTier,
    ) -> Tuple[str, str, float]:
        """
        Get alignment between AGT trust tier and ADAM BOSS tier.

        Args:
            agt_trust_tier: AGT trust tier

        Returns:
            Tuple of (agt_tier, adam_tier, boss_score)
        """
        tier_map = {
            TrustTier.TRUSTED: ("TRUSTED", "SOAP", 10.0),
            TrustTier.VERIFIED: ("VERIFIED", "MODERATE", 30.0),
            TrustTier.MONITORED: ("MONITORED", "ELEVATED", 50.0),
            TrustTier.RESTRICTED: ("RESTRICTED", "HIGH", 70.0),
            TrustTier.QUARANTINED: ("QUARANTINED", "OHSHAT", 90.0),
        }
        return tier_map.get(agt_trust_tier, ("MONITORED", "ELEVATED", 50.0))

    def calculate_trust_factors(
        self,
        latency_p99_ms: float,
        compliance_rate: float,
        error_rate: float,
        anomaly_score: float,
        security_incidents: int,
    ) -> Dict[str, float]:
        """
        Calculate component trust factors for overall score.

        Args:
            latency_p99_ms: P99 latency in milliseconds
            compliance_rate: Compliance rate 0-1
            error_rate: Error rate 0-1
            anomaly_score: Anomaly score 0-100
            security_incidents: Number of recent security incidents

        Returns:
            Dictionary of factor scores (0-100 scale)
        """
        # Latency factor: lower latency = higher trust
        # Target <100ms, penalize above
        latency_factor = max(0, 100 - min(latency_p99_ms, 100))

        # Compliance factor: higher compliance = higher trust
        compliance_factor = compliance_rate * 100

        # Error rate factor: lower error rate = higher trust
        error_factor = max(0, 100 - error_rate * 100)

        # Anomaly factor: lower anomaly score = higher trust
        anomaly_factor = max(0, 100 - anomaly_score)

        # Security factor: penalize based on recent incidents
        security_factor = max(0, 100 - security_incidents * 20)

        return {
            "latency_score": round(latency_factor, 2),
            "compliance_score": round(compliance_factor, 2),
            "error_rate": round(error_factor, 2),
            "anomaly_score": round(anomaly_factor, 2),
            "security_score": round(security_factor, 2),
        }


# ============================================================================
# Inter-Agent Trust Protocol Handler
# ============================================================================

class IATProtocolHandler:
    """
    Handles Inter-Agent Trust Protocol (IATP) message exchange between agents.
    Manages authentication, authorization, and trust updates.
    """

    def __init__(self, did_manager: DIDManager):
        """
        Initialize IATP handler.

        Args:
            did_manager: DID manager for agent identity resolution
        """
        self.logger = logging.getLogger(f"{__name__}.IATProtocolHandler")
        self.did_manager = did_manager
        self.key_manager = Ed25519KeyPair()
        self.message_cache: Dict[str, IATMessage] = {}
        self.pending_challenges: Dict[str, str] = {}  # agent_id -> nonce

    async def create_authentication_message(
        self,
        from_agent_id: str,
        to_agent_id: str,
        private_key_b64: str,
    ) -> IATMessage:
        """
        Create an authentication message for agent-to-agent communication.

        Args:
            from_agent_id: Sending agent ID
            to_agent_id: Receiving agent ID
            private_key_b64: Sender's Ed25519 private key

        Returns:
            Signed IATMessage
        """
        self.logger.info(f"Creating authentication message from {from_agent_id} to {to_agent_id}")

        message = IATMessage(
            message_type=IATMessageType.AUTHENTICATION,
            from_agent_id=from_agent_id,
            to_agent_id=to_agent_id,
            payload={
                "agent_id": from_agent_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "protocol_version": "1.0",
            },
        )

        # Sign message
        message_json = json.dumps(message.to_dict(), sort_keys=True)
        message.signature = self.key_manager.sign_message(private_key_b64, message_json)

        self.message_cache[message.message_id] = message
        return message

    async def verify_authentication_message(
        self,
        message: IATMessage,
        sender_public_key_b64: str,
    ) -> bool:
        """
        Verify authentication message signature.

        Args:
            message: IATMessage to verify
            sender_public_key_b64: Sender's Ed25519 public key

        Returns:
            True if signature is valid
        """
        if message.is_expired():
            self.logger.warning(f"Authentication message {message.message_id} expired")
            return False

        # Verify signature
        message_dict = message.to_dict()
        message_json = json.dumps(message_dict, sort_keys=True)

        is_valid = self.key_manager.verify_signature(
            sender_public_key_b64,
            message_json,
            message.signature,
        )

        if is_valid:
            self.logger.debug(f"Verified authentication message {message.message_id}")
        else:
            self.logger.warning(f"Failed to verify authentication message {message.message_id}")

        return is_valid

    async def create_trust_update_message(
        self,
        from_agent_id: str,
        to_agent_id: str,
        trust_score: TrustScore,
        private_key_b64: str,
    ) -> IATMessage:
        """
        Create a trust score update message.

        Args:
            from_agent_id: Sending agent ID
            to_agent_id: Receiving agent ID
            trust_score: Updated trust score
            private_key_b64: Sender's private key

        Returns:
            Signed trust update message
        """
        self.logger.info(
            f"Creating trust update from {from_agent_id} to {to_agent_id}: "
            f"score={trust_score.score} tier={trust_score.tier}"
        )

        message = IATMessage(
            message_type=IATMessageType.TRUST_UPDATE,
            from_agent_id=from_agent_id,
            to_agent_id=to_agent_id,
            payload={
                "trust_score": trust_score.to_dict(),
                "reason": "Periodic trust reevaluation",
            },
        )

        # Sign message
        message_json = json.dumps(message.to_dict(), sort_keys=True)
        message.signature = self.key_manager.sign_message(private_key_b64, message_json)

        return message

    async def create_challenge_response(
        self,
        from_agent_id: str,
        to_agent_id: str,
        challenge_nonce: str,
        private_key_b64: str,
    ) -> IATMessage:
        """
        Create a response to an authentication challenge.

        Args:
            from_agent_id: Responding agent ID
            to_agent_id: Challenging agent ID
            challenge_nonce: Nonce from challenge message
            private_key_b64: Responder's private key

        Returns:
            Signed challenge response message
        """
        self.logger.debug(f"Creating challenge response from {from_agent_id}")

        message = IATMessage(
            message_type=IATMessageType.RESPONSE,
            from_agent_id=from_agent_id,
            to_agent_id=to_agent_id,
            payload={
                "challenge_nonce": challenge_nonce,
                "response_nonce": secrets.token_hex(16),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

        # Sign message
        message_json = json.dumps(message.to_dict(), sort_keys=True)
        message.signature = self.key_manager.sign_message(private_key_b64, message_json)

        return message


# ============================================================================
# Main ADAM Agent Identity Provider
# ============================================================================

class AdamAgentIdentityProvider:
    """
    Main orchestration class for ADAM-AGT identity integration.

    Manages complete agent identity lifecycle including DID creation, trust scoring,
    and Inter-Agent Trust Protocol (IATP) message exchange.
    """

    def __init__(self):
        """Initialize ADAM Agent Identity Provider."""
        self.logger = logging.getLogger(__name__)
        self.did_manager = DIDManager()
        self.trust_translator = TrustScoreTranslator()
        self.iatp_handler = IATProtocolHandler(self.did_manager)
        self.agent_identities: Dict[str, AgentIdentity] = {}
        self.trust_scores: Dict[str, TrustScore] = {}
        self.metrics = {
            "total_agents": 0,
            "agents_by_layer": {},
            "avg_trust_score": 0.0,
            "trust_refreshes": 0,
        }

    async def provision_agent_identity(
        self,
        agent_id: str,
        agent_layer: AgentLayer,
        agent_role: AgentRole,
        initial_trust_score: float = 500.0,  # MONITORED tier
    ) -> AgentIdentity:
        """
        Provision complete identity for a new agent.

        Args:
            agent_id: Unique agent identifier
            agent_layer: Layer in ADAM topology
            agent_role: Role within layer
            initial_trust_score: Initial AGT trust score (0-1000)

        Returns:
            Fully provisioned AgentIdentity
        """
        self.logger.info(
            f"Provisioning agent identity: {agent_id} "
            f"layer={agent_layer.value} role={agent_role.value}"
        )

        # Create DID
        did_doc = await self.did_manager.create_did(
            agent_id,
            agent_layer,
            agent_role,
        )

        # Register DID
        await self.did_manager.register_did(did_doc)

        # Create trust score
        trust_score = TrustScore(
            agent_id=agent_id,
            score=initial_trust_score,
            factors={
                "latency_score": 80.0,
                "compliance_score": 85.0,
                "error_rate": 95.0,
                "anomaly_score": 10.0,
                "security_score": 100.0,
            },
        )
        self.trust_scores[agent_id] = trust_score

        # Create full identity
        signing_priv, _ = Ed25519KeyPair.generate_keypair()
        encryption_priv, _ = Ed25519KeyPair.generate_encryption_keypair()

        identity = AgentIdentity(
            agent_id=agent_id,
            layer=agent_layer,
            role=agent_role,
            did_document=did_doc,
            trust_score=trust_score,
            signing_key_private=signing_priv,
            encryption_key_private=encryption_priv,
            authorization_capabilities=self._determine_capabilities(agent_layer, trust_score),
            metadata={
                "provisioned_at": datetime.now(timezone.utc).isoformat(),
                "mesh_address": f"grpc://agent-{agent_id}.mesh.adam-governance.io:50051",
            },
        )

        self.agent_identities[agent_id] = identity

        # Update metrics
        self._update_metrics(agent_layer)

        self.logger.debug(f"Provisioned identity for agent {agent_id}")
        return identity

    async def refresh_agent_trust(
        self,
        agent_id: str,
        latency_p99_ms: float,
        compliance_rate: float,
        error_rate: float,
        anomaly_score: float,
        security_incidents: int,
    ) -> TrustScore:
        """
        Refresh trust score for an agent based on recent metrics.

        Args:
            agent_id: Agent to update
            latency_p99_ms: P99 latency in milliseconds
            compliance_rate: Compliance rate 0-1
            error_rate: Error rate 0-1
            anomaly_score: Anomaly score 0-100
            security_incidents: Number of security incidents

        Returns:
            Updated TrustScore
        """
        self.logger.info(f"Refreshing trust score for agent {agent_id}")

        if agent_id not in self.trust_scores:
            raise ValueError(f"Agent {agent_id} not found")

        # Calculate trust factors
        factors = self.trust_translator.calculate_trust_factors(
            latency_p99_ms,
            compliance_rate,
            error_rate,
            anomaly_score,
            security_incidents,
        )

        # Weighted average of factors
        trust_percentile = (
            factors["latency_score"] * 0.15 +
            factors["compliance_score"] * 0.25 +
            factors["error_rate"] * 0.25 +
            factors["anomaly_score"] * 0.20 +
            factors["security_score"] * 0.15
        )

        # Convert 0-100 to 0-1000 trust score
        new_trust_score = (trust_percentile / 100) * 1000

        # Update trust score
        current_trust = self.trust_scores[agent_id]
        current_trust.history.append((current_trust.last_updated, current_trust.score))
        current_trust.score = new_trust_score
        current_trust.factors = factors
        current_trust.last_updated = datetime.now(timezone.utc)
        current_trust.expires_at = datetime.now(timezone.utc) + timedelta(hours=24)

        self.metrics["trust_refreshes"] += 1

        self.logger.debug(
            f"Updated trust score for {agent_id}: "
            f"{new_trust_score:.0f} ({current_trust.tier.value})"
        )

        return current_trust

    async def authenticate_agent_pair(
        self,
        agent1_id: str,
        agent2_id: str,
    ) -> bool:
        """
        Authenticate a pair of agents for inter-agent communication.

        Args:
            agent1_id: First agent
            agent2_id: Second agent

        Returns:
            True if authentication succeeds
        """
        self.logger.info(f"Authenticating agent pair: {agent1_id} <-> {agent2_id}")

        # Verify both agents exist
        if agent1_id not in self.agent_identities:
            self.logger.error(f"Agent {agent1_id} not found")
            return False

        if agent2_id not in self.agent_identities:
            self.logger.error(f"Agent {agent2_id} not found")
            return False

        identity1 = self.agent_identities[agent1_id]
        identity2 = self.agent_identities[agent2_id]

        # Check trust tiers
        tier1 = identity1.trust_score.tier
        tier2 = identity2.trust_score.tier

        # QUARANTINED agents cannot authenticate
        if tier1 == TrustTier.QUARANTINED or tier2 == TrustTier.QUARANTINED:
            self.logger.warning(
                f"Cannot authenticate: {agent1_id} tier={tier1}, {agent2_id} tier={tier2}"
            )
            return False

        # Create authentication message
        auth_msg = await self.iatp_handler.create_authentication_message(
            agent1_id,
            agent2_id,
            identity1.signing_key_private or "",
        )

        # Verify authentication message
        is_verified = await self.iatp_handler.verify_authentication_message(
            auth_msg,
            identity1.did_document.public_key_ed25519,
        )

        self.logger.debug(f"Agent pair authentication: {is_verified}")
        return is_verified

    def get_agent_identity(self, agent_id: str) -> Optional[AgentIdentity]:
        """Get agent identity by ID."""
        return self.agent_identities.get(agent_id)

    def get_agent_trust_score(self, agent_id: str) -> Optional[TrustScore]:
        """Get agent trust score."""
        return self.trust_scores.get(agent_id)

    def get_metrics(self) -> Dict[str, Any]:
        """Get identity provider metrics."""
        avg_trust = (
            sum(ts.score for ts in self.trust_scores.values()) / len(self.trust_scores)
            if self.trust_scores
            else 0
        )

        return {
            "total_agents": self.metrics["total_agents"],
            "agents_by_layer": self.metrics["agents_by_layer"],
            "avg_trust_score": round(avg_trust, 2),
            "trust_score_distribution": {
                tier.value: sum(
                    1 for ts in self.trust_scores.values()
                    if ts.tier == tier
                )
                for tier in TrustTier
            },
            "trust_refreshes": self.metrics["trust_refreshes"],
        }

    def _determine_capabilities(
        self,
        layer: AgentLayer,
        trust_score: TrustScore,
    ) -> List[str]:
        """Determine authorization capabilities based on layer and trust."""
        base_capabilities = ["self_authenticate"]

        # Layer-specific capabilities
        layer_capabilities = {
            AgentLayer.INTENT: ["receive_user_input", "create_intent"],
            AgentLayer.GOVERNOR_AGENT: ["enforce_domain_policy", "escalate"],
            AgentLayer.ORCHESTRATION: ["route_requests", "coordinate_sagas"],
            AgentLayer.WORK_GROUP: ["execute_tasks", "report_status"],
            AgentLayer.DIGITAL_TWIN: ["monitor_system", "update_policies"],
        }

        capabilities = base_capabilities + layer_capabilities.get(layer, [])

        # Trust tier restrictions
        if trust_score.tier == TrustTier.RESTRICTED:
            capabilities = [c for c in capabilities if c not in ["escalate", "update_policies"]]
        elif trust_score.tier == TrustTier.QUARANTINED:
            capabilities = ["self_authenticate"]

        return capabilities

    def _update_metrics(self, layer: AgentLayer):
        """Update metrics after agent provisioning."""
        self.metrics["total_agents"] += 1
        if layer not in self.metrics["agents_by_layer"]:
            self.metrics["agents_by_layer"][layer.value] = 0
        self.metrics["agents_by_layer"][layer.value] += 1


# ============================================================================
# Module initialization and exports
# ============================================================================

def create_identity_provider() -> AdamAgentIdentityProvider:
    """
    Factory function to create a configured ADAM Agent Identity Provider.

    Returns:
        Initialized AdamAgentIdentityProvider instance
    """
    return AdamAgentIdentityProvider()


if __name__ == "__main__":
    # Example usage
    logger.info(f"ADAM Agent Identity Provider v{__version__}")
