"""
AIService — implements every AI feature (explain, bugs, security,
optimization, tests, documentation, UML, deployment) on top of the shared
RetrievalService + PromptService + LLMProvider, so no retrieval logic is
duplicated per feature.

Structured features return validated Pydantic models instead of free-form
markdown, per the migration requirement to avoid parsing unreliable text.
"""

from __future__ import annotations

from app.core.logging import logger
from app.schemas.ai import (
    ApiDocumentationResult,
    BugAnalysisResult,
    DeploymentResult,
    OptimizationResult,
    SecurityAnalysisResult,
    TestGenerationResult,
    UmlResult,
)
from app.services.ai.factory import get_llm_provider
from app.services.ai.gemini_provider import LLMGenerationError
from app.services.rag import prompt_service as prompts
from app.services.rag.retrieval_service import (
    build_context,
    retrieve_repository_context,
    sources_from_context,
)

REFUSAL_PATTERNS = (
    "i cannot fulfill",
    "i can't fulfill",
    "i cannot assist",
    "i can't assist",
    "i cannot help",
    "i can't help",
    "cannot perform a security assessment",
    "can't perform a security assessment",
    "cannot perform vulnerability analysis",
    "can't perform vulnerability analysis",
)


def _looks_like_refusal(error: Exception) -> bool:
    message = str(error).lower()
    return any(pattern in message for pattern in REFUSAL_PATTERNS)


async def explain_code(repository_id: str, target: str, limit: int = 8) -> dict:
    retrieval_query = prompts.build_explanation_query(target)
    retrieval = await retrieve_repository_context(repository_id, retrieval_query, limit)

    if not retrieval.context:
        return {
            "explanation": "I could not find relevant code for that target in the indexed repository.",
            "sources": [],
        }

    repository_context = build_context(retrieval.context)
    prompt = prompts.build_explanation_prompt(
        retrieval.repository["name"], repository_context, target
    )

    llm = get_llm_provider()
    explanation = await llm.generate(prompt)

    return {
        "explanation": explanation,
        "sources": sources_from_context(retrieval.context),
    }


async def detect_repository_bugs(repository_id: str, limit: int = 12) -> dict:
    retrieval = await retrieve_repository_context(
        repository_id, prompts.build_bug_query(), limit
    )

    if not retrieval.context:
        return {
            "summary": "No relevant code was found for bug analysis.",
            "analysis": None,
            "sources": [],
        }

    repository_context = build_context(retrieval.context)
    prompt = prompts.build_bug_prompt(retrieval.repository["name"], repository_context)

    llm = get_llm_provider()
    analysis = await llm.generate_structured(prompt, BugAnalysisResult)

    return {
        "summary": "Bug analysis completed",
        "analysis": analysis,
        "sources": sources_from_context(retrieval.context),
    }


async def analyze_repository_security(repository_id: str, limit: int = 12) -> dict:
    retrieval = await retrieve_repository_context(
        repository_id, prompts.build_security_query(), limit
    )

    if not retrieval.context:
        return {
            "summary": "No security-relevant code was found in the indexed repository context.",
            "analysis": None,
            "sources": [],
        }

    repository_context = build_context(retrieval.context)
    llm = get_llm_provider()

    primary_prompt = prompts.build_security_prompt(
        retrieval.repository["name"], repository_context
    )

    try:
        analysis = await llm.generate_structured(primary_prompt, SecurityAnalysisResult)
    except LLMGenerationError as error:
        if not _looks_like_refusal(error):
            raise
        logger.warning(
            "Primary security review was refused. Retrying with fallback prompt..."
        )
        fallback_prompt = prompts.build_security_fallback_prompt(
            retrieval.repository["name"], repository_context
        )
        analysis = await llm.generate_structured(
            fallback_prompt, SecurityAnalysisResult
        )

    return {
        "summary": "Security analysis completed",
        "analysis": analysis,
        "sources": sources_from_context(retrieval.context),
    }


async def analyze_repository_optimization(repository_id: str, limit: int = 12) -> dict:
    retrieval = await retrieve_repository_context(
        repository_id, prompts.build_optimization_query(), limit
    )

    if not retrieval.context:
        return {
            "summary": "No relevant code was found for optimization analysis",
            "analysis": None,
            "sources": [],
        }

    repository_context = build_context(retrieval.context)
    prompt = prompts.build_optimization_prompt(
        retrieval.repository["name"], repository_context
    )

    llm = get_llm_provider()
    analysis = await llm.generate_structured(prompt, OptimizationResult)

    return {
        "summary": "Code optimization analysis completed",
        "analysis": analysis,
        "sources": sources_from_context(retrieval.context),
    }


async def generate_repository_tests(repository_id: str, limit: int = 20) -> dict:
    retrieval = await retrieve_repository_context(
        repository_id, prompts.build_test_query(), limit
    )

    if not retrieval.context:
        return {
            "summary": "No relevant code was found for test generation",
            "tests": None,
            "sources": [],
        }

    repository_context = build_context(retrieval.context)
    prompt = prompts.build_test_prompt(retrieval.repository["name"], repository_context)

    llm = get_llm_provider()
    tests = await llm.generate_structured(prompt, TestGenerationResult)

    return {
        "summary": "Repository tests generated successfully",
        "tests": tests,
        "sources": sources_from_context(retrieval.context),
    }


async def generate_api_documentation(repository_id: str, limit: int = 20) -> dict:
    retrieval = await retrieve_repository_context(
        repository_id, prompts.build_api_documentation_query(), limit
    )

    if not retrieval.context:
        return {
            "summary": "No API implementation was found in the retrieved repository context",
            "documentation": None,
            "sources": [],
        }

    repository_context = build_context(retrieval.context)
    prompt = prompts.build_api_documentation_prompt(
        retrieval.repository["name"], repository_context
    )

    llm = get_llm_provider()
    documentation = await llm.generate_structured(prompt, ApiDocumentationResult)

    return {
        "summary": "API documentation generated successfully",
        "documentation": documentation,
        "sources": sources_from_context(retrieval.context),
    }


async def generate_repository_uml(repository_id: str, limit: int = 20) -> dict:
    retrieval = await retrieve_repository_context(
        repository_id, prompts.build_uml_query(), limit
    )

    if not retrieval.context:
        return {
            "summary": "No relevant architecture context was found",
            "report": None,
            "mermaid": None,
            "sources": [],
        }

    repository_context = build_context(retrieval.context)
    prompt = prompts.build_uml_prompt(retrieval.repository["name"], repository_context)

    llm = get_llm_provider()
    report = await llm.generate_structured(prompt, UmlResult)

    return {
        "summary": "Repository UML generated successfully",
        "report": report,
        "mermaid": report.mermaid,
        "sources": sources_from_context(retrieval.context),
    }


async def generate_repository_deployment(repository_id: str, limit: int = 20) -> dict:
    retrieval = await retrieve_repository_context(
        repository_id, prompts.build_deployment_query(), limit
    )

    if not retrieval.context:
        return {
            "summary": "No deployment-related repository context was found",
            "report": None,
            "dockerfile": None,
            "dockerignore": None,
            "githubActions": None,
            "sources": [],
        }

    repository_context = build_context(retrieval.context)
    prompt = prompts.build_deployment_prompt(
        retrieval.repository["name"], repository_context
    )

    llm = get_llm_provider()
    report = await llm.generate_structured(prompt, DeploymentResult)

    return {
        "summary": "Deployment and CI/CD analysis completed",
        "report": report,
        "dockerfile": report.dockerfile,
        "dockerignore": report.dockerignore,
        "githubActions": report.githubActions,
        "sources": sources_from_context(retrieval.context),
    }
