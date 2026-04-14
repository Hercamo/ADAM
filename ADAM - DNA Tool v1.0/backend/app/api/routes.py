"""
ADAM DNA Tool - API Routes
REST and WebSocket endpoints for the DNA configuration tool.
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
import structlog

from app.models.session import Session, DNAPhase, ChatMessage, MessageRole
from app.services.conversation_engine import ConversationEngine
from app.services.deployment_bridge import DeploymentBridge
from app.dna.dna_builder import DNABuilder
from app.core.config import settings

logger = structlog.get_logger()
router = APIRouter()

# In-memory session store (use Redis/DB in production)
sessions: Dict[str, Session] = {}
engines: Dict[str, ConversationEngine] = {}


def get_session(session_id: str) -> Session:
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    return sessions[session_id]


def get_engine(session_id: str) -> ConversationEngine:
    session = get_session(session_id)
    if session_id not in engines:
        engines[session_id] = ConversationEngine(session)
    return engines[session_id]


# --- Request/Response Models ---

class CreateSessionRequest(BaseModel):
    ai_provider: str = "openai"
    company_name: Optional[str] = None


class CreateSessionResponse(BaseModel):
    session_id: str
    status: str
    welcome_message: str


class SendMessageRequest(BaseModel):
    message: str


class FetchURLRequest(BaseModel):
    url: str


class AdvancePhaseRequest(BaseModel):
    target_phase: Optional[str] = None


class DeployRequest(BaseModel):
    platforms: List[str]
    include_docx: bool = True
    include_iac: bool = True
    include_config: bool = True


class DNAUpdateRequest(BaseModel):
    updates: List[Dict[str, Any]]


# --- Session Endpoints ---

@router.post("/sessions", response_model=CreateSessionResponse)
async def create_session(req: CreateSessionRequest):
    """Create a new ADAM DNA configuration session."""
    session = Session(ai_provider=req.ai_provider)
    if req.company_name:
        session.company_name = req.company_name

    sessions[session.id] = session
    engine = ConversationEngine(session)
    engines[session.id] = engine

    # Generate welcome message
    welcome_msg = await engine.get_welcome_message()

    return CreateSessionResponse(
        session_id=session.id,
        status="active",
        welcome_message=welcome_msg.content,
    )


@router.get("/sessions/{session_id}")
async def get_session_info(session_id: str):
    """Get session state and progress."""
    session = get_session(session_id)
    dna_builder = DNABuilder(session)
    status = dna_builder.get_overall_status()

    return {
        "id": session.id,
        "company_name": session.company_name,
        "current_phase": session.current_phase.value,
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat(),
        "message_count": len(session.messages),
        "document_count": len(session.documents),
        "progress": status,
        "section_progress": {
            k: {
                "title": v.title,
                "status": v.status,
                "completion_pct": v.completion_pct,
                "questions_total": v.questions_total,
                "questions_answered": v.questions_answered,
            }
            for k, v in session.section_progress.items()
        },
    }


@router.get("/sessions/{session_id}/messages")
async def get_messages(session_id: str, limit: int = 50, offset: int = 0):
    """Get conversation messages."""
    session = get_session(session_id)
    messages = session.messages[offset:offset + limit]
    return {
        "messages": [
            {
                "id": m.id,
                "role": m.role.value,
                "content": m.content,
                "type": m.message_type.value,
                "timestamp": m.timestamp.isoformat(),
                "metadata": m.metadata,
            }
            for m in messages
        ],
        "total": len(session.messages),
    }


# --- Conversation Endpoints ---

@router.post("/sessions/{session_id}/messages")
async def send_message(session_id: str, req: SendMessageRequest):
    """Send a message to the AI assistant."""
    engine = get_engine(session_id)
    response = await engine.process_message(req.message)

    session = get_session(session_id)
    dna_builder = DNABuilder(session)

    return {
        "message": {
            "id": response.id,
            "role": response.role.value,
            "content": response.content,
            "type": response.message_type.value,
            "timestamp": response.timestamp.isoformat(),
            "metadata": response.metadata,
        },
        "progress": dna_builder.get_overall_status(),
        "current_phase": session.current_phase.value,
    }


@router.post("/sessions/{session_id}/upload")
async def upload_document(session_id: str, file: UploadFile = File(...)):
    """Upload a document for analysis."""
    engine = get_engine(session_id)

    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"File too large. Max: {settings.MAX_UPLOAD_SIZE_MB}MB")

    response = await engine.process_document_upload(file.filename, content)

    session = get_session(session_id)
    dna_builder = DNABuilder(session)

    return {
        "message": {
            "id": response.id,
            "role": response.role.value,
            "content": response.content,
            "type": response.message_type.value,
            "timestamp": response.timestamp.isoformat(),
            "metadata": response.metadata,
        },
        "documents": [
            {
                "id": d.id,
                "filename": d.filename,
                "source_type": d.source_type,
                "mime_type": d.mime_type,
                "size_bytes": d.size_bytes,
                "relevance": d.relevance_mapping,
                "ingested_at": d.ingested_at.isoformat(),
            }
            for d in session.documents
        ],
        "progress": dna_builder.get_overall_status(),
    }


@router.post("/sessions/{session_id}/fetch-url")
async def fetch_url(session_id: str, req: FetchURLRequest):
    """Fetch and analyze content from a URL."""
    engine = get_engine(session_id)
    response = await engine.process_url_fetch(req.url)

    return {
        "message": {
            "id": response.id,
            "role": response.role.value,
            "content": response.content,
            "type": response.message_type.value,
            "timestamp": response.timestamp.isoformat(),
            "metadata": response.metadata,
        },
    }


# --- Phase & Progress Endpoints ---

@router.post("/sessions/{session_id}/advance-phase")
async def advance_phase(session_id: str, req: AdvancePhaseRequest):
    """Advance to the next DNA configuration phase."""
    engine = get_engine(session_id)

    target = None
    if req.target_phase:
        try:
            target = DNAPhase(req.target_phase)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid phase: {req.target_phase}")

    response = await engine.advance_phase(target)

    session = get_session(session_id)
    return {
        "message": {
            "id": response.id,
            "content": response.content,
            "type": response.message_type.value,
        },
        "current_phase": session.current_phase.value,
    }


@router.get("/sessions/{session_id}/progress")
async def get_progress(session_id: str):
    """Get detailed DNA completion progress."""
    session = get_session(session_id)
    dna_builder = DNABuilder(session)
    return dna_builder.get_overall_status()


# --- DNA Data Endpoints ---

@router.get("/sessions/{session_id}/dna")
async def get_dna_data(session_id: str):
    """Get the current DNA configuration data."""
    session = get_session(session_id)
    dna_builder = DNABuilder(session)
    return dna_builder.export_dna_json()


@router.post("/sessions/{session_id}/dna/update")
async def update_dna(session_id: str, req: DNAUpdateRequest):
    """Manually update DNA question answers."""
    engine = get_engine(session_id)
    await engine.apply_dna_updates(req.updates)

    session = get_session(session_id)
    dna_builder = DNABuilder(session)
    return {
        "status": "updated",
        "progress": dna_builder.get_overall_status(),
    }


@router.get("/sessions/{session_id}/review")
async def get_review(session_id: str):
    """Generate a comprehensive DNA review."""
    engine = get_engine(session_id)
    response = await engine.generate_dna_review()
    return {
        "review": response.content,
        "metadata": response.metadata,
    }


# --- Deployment Endpoints ---

@router.post("/sessions/{session_id}/deploy")
async def trigger_deployment(session_id: str, req: DeployRequest):
    """Trigger deployment generation using the DNA Deployment Tool."""
    session = get_session(session_id)
    bridge = DeploymentBridge()

    result = await bridge.generate_deployment(
        session=session,
        platforms=req.platforms,
        include_docx=req.include_docx,
        include_iac=req.include_iac,
        include_config=req.include_config,
    )

    return result


@router.post("/sessions/{session_id}/deploy/validate")
async def validate_for_deployment(session_id: str):
    """Validate the current DNA data for deployment readiness."""
    session = get_session(session_id)
    dna_builder = DNABuilder(session)
    dna_data = dna_builder.export_dna_json()

    bridge = DeploymentBridge()
    return bridge.validate_dna_json(dna_data)


# --- Documents Endpoint ---

@router.get("/sessions/{session_id}/documents")
async def get_documents(session_id: str):
    """List all ingested documents."""
    session = get_session(session_id)
    return {
        "documents": [
            {
                "id": d.id,
                "filename": d.filename,
                "source_type": d.source_type,
                "source_url": d.source_url,
                "mime_type": d.mime_type,
                "size_bytes": d.size_bytes,
                "relevance_mapping": d.relevance_mapping,
                "ingested_at": d.ingested_at.isoformat(),
            }
            for d in session.documents
        ],
    }


# --- WebSocket for Real-Time Chat ---

@router.websocket("/ws/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time chat interaction."""
    await websocket.accept()

    # Get or create session
    if session_id not in sessions:
        session = Session(id=session_id)
        sessions[session_id] = session
        engine = ConversationEngine(session)
        engines[session_id] = engine
        welcome = await engine.get_welcome_message()
        await websocket.send_json({
            "type": "message",
            "message": {
                "id": welcome.id,
                "role": "assistant",
                "content": welcome.content,
                "type": welcome.message_type.value,
            },
        })
    else:
        engine = get_engine(session_id)

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type", "message")

            if msg_type == "message":
                response = await engine.process_message(data["content"])
                session = get_session(session_id)
                dna_builder = DNABuilder(session)

                await websocket.send_json({
                    "type": "message",
                    "message": {
                        "id": response.id,
                        "role": "assistant",
                        "content": response.content,
                        "type": response.message_type.value,
                    },
                    "progress": dna_builder.get_overall_status(),
                    "phase": session.current_phase.value,
                })

            elif msg_type == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected", session_id=session_id)


# --- Health & Info ---

@router.get("/health")
async def health_check():
    return {"status": "healthy", "version": settings.APP_VERSION}


@router.get("/info")
async def app_info():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "ai_provider": settings.AI_PROVIDER,
        "supported_platforms": DeploymentBridge.SUPPORTED_PLATFORMS,
        "supported_file_types": [".docx", ".pptx", ".pdf", ".csv", ".json", ".xlsx", ".txt", ".md", ".yaml"],
    }
