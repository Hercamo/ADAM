"""
ADAM DNA Tool - Conversation Engine
Orchestrates the AI-powered conversational flow that walks users through
ADAM DNA configuration. Manages context, document analysis, and DNA updates.
"""

import json
import re
from typing import Dict, Any, List, Optional
from datetime import datetime
import structlog

from app.ai.providers import AIProvider, AIMessage, AIResponse, create_provider
from app.ai.adam_system_prompt import build_system_prompt, get_section_prompt, DNA_SECTIONS
from app.models.session import (
    Session, ChatMessage, MessageRole, MessageType,
    DNAPhase, IngestedDocument, PHASE_SECTION_MAP, PHASE_TITLES,
)
from app.dna.dna_builder import DNABuilder
from app.ingestion.document_processor import DocumentProcessor
from app.core.config import settings

logger = structlog.get_logger()


class ConversationEngine:
    """Manages the AI-powered conversation for DNA configuration."""

    def __init__(self, session: Session, ai_provider: Optional[AIProvider] = None):
        self.session = session
        self.dna_builder = DNABuilder(session)

        if ai_provider:
            self.ai = ai_provider
        else:
            self.ai = create_provider(
                provider_name=settings.AI_PROVIDER,
                openai_key=settings.OPENAI_API_KEY,
                openai_model=settings.OPENAI_MODEL,
                openai_base_url=settings.OPENAI_BASE_URL,
                anthropic_key=settings.ANTHROPIC_API_KEY,
                anthropic_model=settings.ANTHROPIC_MODEL,
                azure_key=settings.AZURE_OPENAI_API_KEY,
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
                azure_deployment=settings.AZURE_OPENAI_DEPLOYMENT,
                azure_api_version=settings.AZURE_OPENAI_API_VERSION,
            )

        self.doc_processor = DocumentProcessor(settings.UPLOAD_DIR)

    async def process_message(self, user_message: str) -> ChatMessage:
        """Process a user message and return AI response."""
        # Record user message
        user_msg = ChatMessage(
            role=MessageRole.USER,
            content=user_message,
            message_type=MessageType.TEXT,
        )
        self.session.messages.append(user_msg)

        # Build AI context
        messages = self._build_message_context()

        # Get AI response
        response = await self.ai.chat(messages, temperature=0.3, max_tokens=4096)

        # Parse AI response for DNA updates
        dna_updates = await self._extract_dna_updates(response.content)

        # Record AI response
        assistant_msg = ChatMessage(
            role=MessageRole.ASSISTANT,
            content=response.content,
            message_type=MessageType.TEXT,
            metadata={
                "model": response.model,
                "provider": response.provider,
                "usage": response.usage,
                "dna_updates": dna_updates,
            },
        )
        self.session.messages.append(assistant_msg)
        self.session.updated_at = datetime.utcnow()

        return assistant_msg

    async def process_document_upload(self, filename: str, content: bytes) -> ChatMessage:
        """Process an uploaded document and generate AI analysis."""
        # Process the document
        doc_info = await self.doc_processor.process_file(filename, content)

        # Create document record
        doc = IngestedDocument(
            filename=filename,
            source_type="upload",
            mime_type=doc_info["mime_type"],
            size_bytes=doc_info["size_bytes"],
            extracted_text=doc_info["extracted_text"],
            extracted_sections=doc_info.get("extracted_sections", {}),
            relevance_mapping=doc_info.get("relevance_mapping", {}),
        )
        self.session.documents.append(doc)

        # Record upload message
        upload_msg = ChatMessage(
            role=MessageRole.USER,
            content=f"[Uploaded document: {filename}]",
            message_type=MessageType.DOCUMENT_UPLOAD,
            metadata={"document_id": doc.id, "filename": filename},
        )
        self.session.messages.append(upload_msg)

        # Get relevant sections
        relevant = self.doc_processor.get_relevant_sections(doc.relevance_mapping)
        relevance_summary = ", ".join(
            f"Section {s} ({doc.relevance_mapping.get(s, 0):.0%})"
            for s in relevant[:5]
        )

        # Ask AI to analyze the document
        analysis_prompt = f"""The user just uploaded a document: "{filename}" ({doc.mime_type}, {doc.size_bytes} bytes).

Here is the extracted content (truncated if very long):
---
{doc.extracted_text[:8000]}
---

Relevance analysis shows this document is most relevant to: {relevance_summary or 'No strong section matches detected'}

Please:
1. Summarize what this document contains and what ADAM-relevant information you found
2. Identify which DNA sections this document can help fill
3. Extract any specific answers you can determine for DNA questions
4. Ask the user to confirm your interpretations and fill any gaps

Remember: You're looking for doctrine-grade information — mission, vision, principles, governance structure, financial parameters, compliance requirements, product information, etc."""

        messages = self._build_message_context()
        messages.append(AIMessage(role="user", content=analysis_prompt))

        response = await self.ai.chat(messages, temperature=0.3, max_tokens=4096)

        # Extract any DNA updates from the analysis
        dna_updates = await self._extract_dna_updates(response.content)

        assistant_msg = ChatMessage(
            role=MessageRole.ASSISTANT,
            content=response.content,
            message_type=MessageType.DNA_UPDATE,
            metadata={
                "document_id": doc.id,
                "relevant_sections": relevant,
                "dna_updates": dna_updates,
            },
        )
        self.session.messages.append(assistant_msg)
        self.session.updated_at = datetime.utcnow()

        return assistant_msg

    async def process_url_fetch(self, url: str) -> ChatMessage:
        """Fetch and process content from a URL."""
        try:
            doc_info = await self.doc_processor.fetch_url(url)

            doc = IngestedDocument(
                filename=doc_info.get("filename", "url_content"),
                source_type="url",
                source_url=url,
                mime_type=doc_info.get("mime_type", "text/html"),
                size_bytes=doc_info.get("size_bytes", 0),
                extracted_text=doc_info.get("extracted_text", ""),
                relevance_mapping=doc_info.get("relevance_mapping", {}),
            )
            self.session.documents.append(doc)

            # Analyze same as document upload
            analysis_prompt = f"""The user provided a URL to fetch: {url}

Here is the extracted content:
---
{doc.extracted_text[:8000]}
---

Please analyze this content for ADAM DNA-relevant information and report what you found."""

            messages = self._build_message_context()
            messages.append(AIMessage(role="user", content=analysis_prompt))

            response = await self.ai.chat(messages, temperature=0.3, max_tokens=4096)

            return ChatMessage(
                role=MessageRole.ASSISTANT,
                content=response.content,
                message_type=MessageType.URL_FETCH,
                metadata={"url": url, "document_id": doc.id},
            )

        except Exception as e:
            logger.error("URL fetch failed", url=url, error=str(e))
            return ChatMessage(
                role=MessageRole.ASSISTANT,
                content=f"I wasn't able to fetch content from that URL: {str(e)}. Could you try uploading the content as a file instead?",
                message_type=MessageType.ERROR,
                metadata={"url": url, "error": str(e)},
            )

    async def get_welcome_message(self) -> ChatMessage:
        """Generate the initial welcome message."""
        welcome = """Welcome to the **ADAM DNA Configuration Tool**.

I'm your AI guide for implementing the **Autonomous Doctrine & Architecture Model** for your organization. Instead of filling out a static questionnaire, we'll work together conversationally — I'll analyze your existing documents and ask targeted questions to build your complete ADAM DNA configuration.

**Here's how this works:**

**Step 1 — Feed me your documents.** Upload strategy decks, mission statements, org charts, compliance docs, financial summaries, product descriptions — anything that defines how your company operates. I'll extract what I can automatically.

**Step 2 — We'll walk through 13 sections** covering everything from your constitutional doctrine to cloud infrastructure sizing. I'll ask questions based on what I still need, not what I already know.

**Step 3 — Review and deploy.** Once your DNA is complete, I'll generate the configuration that feeds directly into the ADAM DNA Deployment Tool to provision your entire autonomous infrastructure.

**Ready to start?** You can:
- **Upload documents** (strategy decks, financial reports, org charts, compliance docs)
- **Paste a URL** to fetch remote data
- **Tell me about your company** and I'll start asking the right questions

What would you like to do first?"""

        msg = ChatMessage(
            role=MessageRole.ASSISTANT,
            content=welcome,
            message_type=MessageType.TEXT,
        )
        self.session.messages.append(msg)
        self.session.current_phase = DNAPhase.DOCUMENT_INGESTION
        return msg

    async def advance_phase(self, target_phase: Optional[DNAPhase] = None) -> ChatMessage:
        """Advance to the next phase or a specific phase."""
        if target_phase:
            self.session.current_phase = target_phase
        else:
            next_phase = self.session.get_next_incomplete_phase()
            if next_phase:
                self.session.current_phase = next_phase

        # Generate phase introduction
        section_num = PHASE_SECTION_MAP.get(self.session.current_phase)
        section_prompt = get_section_prompt(section_num) if section_num else ""

        intro_prompt = f"""We're now moving to: **{PHASE_TITLES.get(self.session.current_phase, 'Next Section')}**

{section_prompt}

Based on the documents already uploaded and our conversation so far, prepare an introduction
for this section. If you already have information from uploaded documents that fills some
questions, present what you've found and ask for confirmation. For missing information,
ask targeted questions.

Format your response conversationally but make it clear what information you need."""

        messages = self._build_message_context()
        messages.append(AIMessage(role="user", content=intro_prompt))

        response = await self.ai.chat(messages, temperature=0.3, max_tokens=4096)

        msg = ChatMessage(
            role=MessageRole.ASSISTANT,
            content=response.content,
            message_type=MessageType.PHASE_TRANSITION,
            metadata={"phase": self.session.current_phase.value},
        )
        self.session.messages.append(msg)
        return msg

    async def generate_dna_review(self) -> ChatMessage:
        """Generate a comprehensive review of the accumulated DNA configuration."""
        status = self.dna_builder.get_overall_status()
        dna_json = self.dna_builder.export_dna_json()

        review_prompt = f"""Please provide a comprehensive review of the DNA configuration we've built.

Overall completion: {status['overall_completion_pct']}%
Total questions answered: {status['total_answered']}/{status['total_questions']}

Section status:
{json.dumps({k: {'answered': v['answered'], 'total': v['total_questions'], 'pct': v['completion_pct']} for k, v in status['sections'].items()}, indent=2)}

Current DNA data:
{json.dumps(dna_json, indent=2, default=str)[:10000]}

Please:
1. Summarize the key configurations
2. Flag any sections with low completion that need attention
3. Identify any inconsistencies or gaps
4. Recommend next steps"""

        messages = self._build_message_context()
        messages.append(AIMessage(role="user", content=review_prompt))

        response = await self.ai.chat(messages, temperature=0.3, max_tokens=4096)

        return ChatMessage(
            role=MessageRole.ASSISTANT,
            content=response.content,
            message_type=MessageType.PROGRESS_UPDATE,
            metadata={"status": status},
        )

    def _build_message_context(self) -> List[AIMessage]:
        """Build the message context for the AI, including system prompt and history."""
        # Build document summaries
        doc_summaries = ""
        for doc in self.session.documents[-10:]:  # Last 10 documents
            relevant = [f"S{s}" for s, score in doc.relevance_mapping.items() if score > 0.2]
            doc_summaries += f"- {doc.filename} ({doc.source_type}): Relevant to {', '.join(relevant) if relevant else 'general context'}\n"

        # Build current DNA state summary
        status = self.dna_builder.get_overall_status()
        dna_state = f"Overall: {status['overall_completion_pct']}% complete ({status['total_answered']}/{status['total_questions']} questions)\n"
        for sec_num, sec_status in status["sections"].items():
            if sec_status["answered"] > 0:
                dna_state += f"  Section {sec_num}: {sec_status['completion_pct']}% ({sec_status['answered']}/{sec_status['total_questions']})\n"

        # Get current section context
        section_num = PHASE_SECTION_MAP.get(self.session.current_phase, "")
        section_context = get_section_prompt(section_num) if section_num else ""

        # Build system prompt
        system_prompt = build_system_prompt(
            session_phase=self.session.current_phase.value,
            company_name=self.session.company_name,
            ingested_docs_summary=doc_summaries,
            current_dna_state=dna_state,
            section_context=section_context,
        )

        messages = [AIMessage(role="system", content=system_prompt)]

        # Add conversation history (keep last 30 messages for context)
        for msg in self.session.messages[-30:]:
            if msg.message_type == MessageType.DOCUMENT_UPLOAD:
                # Include document content summary
                doc_id = msg.metadata.get("document_id")
                doc = next((d for d in self.session.documents if d.id == doc_id), None)
                if doc:
                    content = f"[Uploaded: {doc.filename}]\nExtracted content:\n{doc.extracted_text[:3000]}"
                    messages.append(AIMessage(role="user", content=content))
                    continue

            messages.append(AIMessage(role=msg.role.value, content=msg.content))

        return messages

    async def _extract_dna_updates(self, ai_response: str) -> List[Dict[str, Any]]:
        """Use AI to extract structured DNA updates from a response."""
        # Look for explicit DNA question answers in the response
        updates = []

        # Pattern: question numbers like 1.1.1, 6.2.3 followed by answers
        pattern = r'(\d+\.\d+(?:\.\d+)?)\s*[:—]\s*(.+?)(?=\d+\.\d+(?:\.\d+)?\s*[:—]|$)'
        matches = re.findall(pattern, ai_response, re.DOTALL)

        for q_num, answer in matches:
            answer = answer.strip()
            if len(answer) > 10:  # Skip very short/empty matches
                self.dna_builder.update_answer(q_num, answer, confidence=0.8)
                updates.append({"question": q_num, "answer": answer[:200]})

        return updates

    async def apply_dna_updates(self, updates: List[Dict[str, Any]]):
        """Manually apply DNA updates from the frontend."""
        for update in updates:
            q_num = update.get("question_number")
            answer = update.get("answer")
            confidence = update.get("confidence", 1.0)
            if q_num and answer:
                self.dna_builder.update_answer(q_num, answer, confidence)
