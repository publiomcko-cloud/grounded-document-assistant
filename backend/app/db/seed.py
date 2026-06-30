import hashlib
import re
import uuid
from pathlib import Path

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import (
    Document,
    DocumentVersion,
    EvaluationQuestion,
    EvaluationSet,
    User,
    Workspace,
    WorkspaceMembership,
)
from app.models.enums import (
    DocumentStatus,
    DocumentVisibility,
    ExtractionStatus,
    WorkspaceRole,
)
from app.services.auth import DEMO_PASSWORD, hash_password
from app.services.ingestion import process_document_version
from app.services.storage import write_private_file


def slugify(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.strip().lower())
    return normalized.strip("-") or "workspace"


def seed_demo_data() -> None:
    demo_workspace_name = "Grounded Demo Workspace"
    workspace_slug = slugify(demo_workspace_name)
    owner_email = "owner@example.com"
    viewer_email = "viewer@example.com"

    with SessionLocal() as session:
        owner = session.scalar(select(User).where(User.email == owner_email))
        if owner is None:
            owner = User(
                name="Demo Owner",
                email=owner_email,
                password_hash=hash_password(DEMO_PASSWORD),
            )
            session.add(owner)
            session.flush()
        elif not owner.password_hash.startswith("$pbkdf2-sha256$"):
            owner.password_hash = hash_password(DEMO_PASSWORD)

        viewer = session.scalar(select(User).where(User.email == viewer_email))
        if viewer is None:
            viewer = User(
                name="Demo Viewer",
                email=viewer_email,
                password_hash=hash_password(DEMO_PASSWORD),
            )
            session.add(viewer)
            session.flush()
        elif not viewer.password_hash.startswith("$pbkdf2-sha256$"):
            viewer.password_hash = hash_password(DEMO_PASSWORD)

        workspace = session.scalar(
            select(Workspace).where(Workspace.slug == workspace_slug)
        )
        if workspace is None:
            workspace = Workspace(
                name=demo_workspace_name,
                slug=workspace_slug,
                created_by_user_id=owner.id,
            )
            session.add(workspace)
            session.flush()

        memberships = {
            (membership.user_id, membership.role)
            for membership in session.scalars(
                select(WorkspaceMembership).where(
                    WorkspaceMembership.workspace_id == workspace.id
                )
            )
        }

        desired_memberships = [
            (owner.id, WorkspaceRole.OWNER),
            (viewer.id, WorkspaceRole.VIEWER),
        ]
        for user_id, role in desired_memberships:
            if (user_id, role) not in memberships:
                session.add(
                    WorkspaceMembership(
                        workspace_id=workspace.id,
                        user_id=user_id,
                        role=role,
                    )
                )

        session.commit()

        demo_documents = _ensure_demo_documents(
            session,
            workspace=workspace,
            owner=owner,
        )
        _ensure_demo_evaluation_set(
            session,
            workspace=workspace,
            documents_by_title=demo_documents,
        )
        session.commit()


def _ensure_demo_documents(
    session,
    *,
    workspace: Workspace,
    owner: User,
) -> dict[str, Document]:
    documents_by_title: dict[str, Document] = {}
    for document_seed in DEMO_DOCUMENTS:
        document = session.scalar(
            select(Document).where(
                Document.workspace_id == workspace.id,
                Document.title == document_seed["title"],
            )
        )
        if document is None:
            document = Document(
                workspace_id=workspace.id,
                title=document_seed["title"],
                description=document_seed["description"],
                status=DocumentStatus.PENDING,
                visibility=document_seed["visibility"],
                uploaded_by_user_id=owner.id,
            )
            session.add(document)
            session.flush()

            version_id = uuid.uuid4()
            relative_path = (
                Path(str(workspace.id))
                / "seeded"
                / str(document.id)
                / str(version_id)
                / document_seed["file_name"]
            )
            content_bytes = document_seed["content"].encode("utf-8")
            stored_path = write_private_file(relative_path, content_bytes)

            session.add(
                DocumentVersion(
                    id=version_id,
                    document_id=document.id,
                    version_number=1,
                    file_name=document_seed["file_name"],
                    file_path=str(stored_path),
                    mime_type="text/plain",
                    file_size_bytes=len(content_bytes),
                    checksum=hashlib.sha256(content_bytes).hexdigest(),
                    extraction_status=ExtractionStatus.PENDING,
                )
            )
            session.commit()
            process_document_version(version_id)
            session.expire_all()
            document = session.scalar(
                select(Document).where(Document.id == document.id)
            )

        if document is not None:
            documents_by_title[document.title] = document

    return documents_by_title


def _ensure_demo_evaluation_set(
    session,
    *,
    workspace: Workspace,
    documents_by_title: dict[str, Document],
) -> None:
    evaluation_set = session.scalar(
        select(EvaluationSet).where(
            EvaluationSet.workspace_id == workspace.id,
            EvaluationSet.name == DEMO_EVALUATION_SET["name"],
        )
    )
    if evaluation_set is None:
        evaluation_set = EvaluationSet(
            workspace_id=workspace.id,
            name=DEMO_EVALUATION_SET["name"],
            description=DEMO_EVALUATION_SET["description"],
        )
        session.add(evaluation_set)
        session.flush()

    existing_questions = {
        question.question: question
        for question in session.scalars(
            select(EvaluationQuestion).where(
                EvaluationQuestion.evaluation_set_id == evaluation_set.id
            )
        )
    }

    for question_seed in DEMO_EVALUATION_QUESTIONS:
        expected_documents = [
            documents_by_title[title].id
            for title in question_seed["expected_document_titles"]
            if title in documents_by_title
        ]
        question = existing_questions.get(question_seed["question"])
        if question is None:
            session.add(
                EvaluationQuestion(
                    evaluation_set_id=evaluation_set.id,
                    question=question_seed["question"],
                    expected_answer_notes=question_seed["expected_answer_notes"],
                    expected_document_ids=expected_documents or None,
                )
            )
            continue

        question.expected_answer_notes = question_seed["expected_answer_notes"]
        question.expected_document_ids = expected_documents or None


DEMO_DOCUMENTS = [
    {
        "title": "Refund Policy",
        "file_name": "refund-policy.txt",
        "description": "Customer refund rules and edge cases for the demo workspace.",
        "visibility": DocumentVisibility.WORKSPACE,
        "content": (
            "REFUND POLICY\n"
            "Customers can request a refund within 30 days of purchase. "
            "The item must be unused and the request must include proof of "
            "purchase.\n\n"
            "DIGITAL GOODS\n"
            "Downloaded digital goods are not refundable after access has been "
            "used.\n\n"
            "SHIPPING\n"
            "Original shipping charges are not refunded."
        ),
    },
    {
        "title": "Warranty Guide",
        "file_name": "warranty-guide.txt",
        "description": (
            "Coverage and warranty claim requirements for the demo workspace."
        ),
        "visibility": DocumentVisibility.WORKSPACE,
        "content": (
            "WARRANTY GUIDE\n"
            "Standard warranty coverage lasts one year from the purchase date.\n\n"
            "CLAIMS\n"
            "Warranty claims require proof of purchase and the product serial number. "
            "A replacement is shipped only after defect verification is complete."
        ),
    },
    {
        "title": "Support Escalation Playbook",
        "file_name": "support-escalation-playbook.txt",
        "description": "Restricted internal support escalation instructions.",
        "visibility": DocumentVisibility.RESTRICTED,
        "content": (
            "SUPPORT ESCALATION PLAYBOOK\n"
            "Severity 1 incidents must be escalated to the incident lead within "
            "15 minutes.\n\n"
            "BILLING EXCEPTIONS\n"
            "Manager approval is required before a billing exception can be granted."
        ),
    },
    {
        "title": "Finance Approval Matrix",
        "file_name": "finance-approval-matrix.txt",
        "description": "Private finance approval rules for portfolio demo purposes.",
        "visibility": DocumentVisibility.PRIVATE,
        "content": (
            "FINANCE APPROVAL MATRIX\n"
            "Expenses above $5000 require approval from the finance director.\n\n"
            "TRAVEL\n"
            "Travel bookings above $1200 require CFO approval before purchase."
        ),
    },
]

DEMO_EVALUATION_SET = {
    "name": "Grounded Demo Golden Set",
    "description": (
        "Portfolio demo questions covering refund, warranty, support, and "
        "finance content."
    ),
}

DEMO_EVALUATION_QUESTIONS = [
    {
        "question": "What is the refund deadline?",
        "expected_answer_notes": "Mention 30 days from purchase.",
        "expected_document_titles": ["Refund Policy"],
    },
    {
        "question": "What is required when asking for a refund?",
        "expected_answer_notes": "Mention unused item and proof of purchase.",
        "expected_document_titles": ["Refund Policy"],
    },
    {
        "question": "Are downloaded digital goods refundable?",
        "expected_answer_notes": (
            "Mention they are not refundable after access has been used."
        ),
        "expected_document_titles": ["Refund Policy"],
    },
    {
        "question": "How long does standard warranty coverage last?",
        "expected_answer_notes": "Mention one year from purchase date.",
        "expected_document_titles": ["Warranty Guide"],
    },
    {
        "question": "What information is required for a warranty claim?",
        "expected_answer_notes": "Mention proof of purchase and serial number.",
        "expected_document_titles": ["Warranty Guide"],
    },
    {
        "question": "When is a replacement shipped under the warranty process?",
        "expected_answer_notes": (
            "Mention replacement ships after defect verification is complete."
        ),
        "expected_document_titles": ["Warranty Guide"],
    },
    {
        "question": "How quickly must Severity 1 incidents be escalated?",
        "expected_answer_notes": "Mention escalation within 15 minutes.",
        "expected_document_titles": ["Support Escalation Playbook"],
    },
    {
        "question": "Who must approve a billing exception?",
        "expected_answer_notes": "Mention manager approval.",
        "expected_document_titles": ["Support Escalation Playbook"],
    },
    {
        "question": "Who approves expenses above $5000?",
        "expected_answer_notes": "Mention finance director approval.",
        "expected_document_titles": ["Finance Approval Matrix"],
    },
    {
        "question": "Who must approve travel bookings above $1200?",
        "expected_answer_notes": "Mention CFO approval.",
        "expected_document_titles": ["Finance Approval Matrix"],
    },
]


if __name__ == "__main__":
    seed_demo_data()
