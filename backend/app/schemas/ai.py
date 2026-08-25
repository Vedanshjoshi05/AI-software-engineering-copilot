"""
Structured JSON schemas for AI feature outputs.

These replace the original free-form markdown strings with validated
Pydantic models so downstream consumers (the frontend, or any other
service) never need to parse unreliable text. Each *Result model is what
`LLMProvider.generate_structured()` is asked to produce, and each
*Response model is the full HTTP response envelope (matches the original
API contract: success/repositoryId/repository/summary/<field>/sources).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.rag import SourceReference

Severity = Literal["critical", "high", "medium", "low", "info"]
Priority = Literal["high", "medium", "low"]


# ----------------------------------------------------------------------
# Bug detection
# ----------------------------------------------------------------------
class BugFinding(BaseModel):
    severity: Severity
    category: str
    title: str
    affectedFile: str
    type: Literal["confirmed_bug", "probable_bug", "code_quality_concern"]
    evidence: str
    failureScenario: str
    impact: str
    recommendedFix: str


class BugAnalysisResult(BaseModel):
    summary: str
    findings: list[BugFinding] = Field(default_factory=list)
    goodPractices: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class BugDetectionResponse(BaseModel):
    success: bool = True
    repositoryId: str
    repository: str
    summary: str
    analysis: BugAnalysisResult | None
    sources: list[SourceReference]


# ----------------------------------------------------------------------
# Security analysis
# ----------------------------------------------------------------------
class SecurityFinding(BaseModel):
    severity: Severity
    category: str
    title: str
    affectedFile: str
    type: Literal["vulnerability", "security_concern"]
    evidence: str
    impact: str
    recommendation: str


class SecurityAnalysisResult(BaseModel):
    summary: str
    findings: list[SecurityFinding] = Field(default_factory=list)
    goodPractices: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class SecurityAnalysisResponse(BaseModel):
    success: bool = True
    repositoryId: str
    repository: str
    summary: str
    analysis: SecurityAnalysisResult | None
    sources: list[SourceReference]


# ----------------------------------------------------------------------
# Code optimization
# ----------------------------------------------------------------------
class OptimizationRecommendation(BaseModel):
    priority: Priority
    category: Literal["performance", "scalability", "reliability", "maintainability"]
    title: str
    affectedFile: str
    currentImplementation: str
    problem: str
    recommendedOptimization: str
    expectedBenefit: str
    example: str | None = None


class OptimizationResult(BaseModel):
    summary: str
    recommendations: list[OptimizationRecommendation] = Field(default_factory=list)
    existingGoodPractices: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class OptimizationResponse(BaseModel):
    success: bool = True
    repositoryId: str
    repository: str
    summary: str
    analysis: OptimizationResult | None
    sources: list[SourceReference]


# ----------------------------------------------------------------------
# Test generation
# ----------------------------------------------------------------------
class GeneratedTestFile(BaseModel):
    suggestedPath: str
    framework: str
    covers: list[str] = Field(default_factory=list)
    code: str


class TestGenerationResult(BaseModel):
    summary: str
    testingStrategy: str
    testFiles: list[GeneratedTestFile] = Field(default_factory=list)
    additionalTestCases: list[str] = Field(default_factory=list)
    runningInstructions: str | None = None
    limitations: list[str] = Field(default_factory=list)


class TestGenerationResponse(BaseModel):
    success: bool = True
    repositoryId: str
    repository: str
    summary: str
    tests: TestGenerationResult | None
    sources: list[SourceReference]


# ----------------------------------------------------------------------
# API documentation
# ----------------------------------------------------------------------
class ApiEndpointDoc(BaseModel):
    method: str
    path: str
    purpose: str
    authentication: str
    controller: str | None = None
    middleware: list[str] = Field(default_factory=list)
    pathParameters: list[str] = Field(default_factory=list)
    queryParameters: list[str] = Field(default_factory=list)
    requestBody: str | None = None
    successResponse: str
    errorResponses: list[str] = Field(default_factory=list)
    implementationNotes: str | None = None
    sourceFiles: list[str] = Field(default_factory=list)


class ApiDocumentationResult(BaseModel):
    summary: str
    overview: str
    endpoints: list[ApiEndpointDoc] = Field(default_factory=list)
    authentication: str | None = None
    validation: str | None = None
    errorHandling: str | None = None
    limitations: list[str] = Field(default_factory=list)


class ApiDocumentationResponse(BaseModel):
    success: bool = True
    repositoryId: str
    repository: str
    summary: str
    documentation: ApiDocumentationResult | None
    sources: list[SourceReference]


# ----------------------------------------------------------------------
# UML / architecture generation
# ----------------------------------------------------------------------
class UmlResult(BaseModel):
    summary: str
    architectureSummary: str
    mermaid: str
    componentRelationships: str
    limitations: list[str] = Field(default_factory=list)


class UmlResponse(BaseModel):
    success: bool = True
    repositoryId: str
    repository: str
    summary: str
    report: UmlResult | None
    mermaid: str | None
    sources: list[SourceReference]


# ----------------------------------------------------------------------
# Deployment generation
# ----------------------------------------------------------------------
class DeploymentResult(BaseModel):
    summary: str
    stackDetection: str
    existingConfiguration: str
    recommendedArchitecture: str
    environmentVariables: list[str] = Field(default_factory=list)
    dockerfile: str | None = None
    dockerignore: str | None = None
    githubActions: str | None = None
    awsDeployment: str | None = None
    deploymentSteps: list[str] = Field(default_factory=list)
    risksAndVerification: list[str] = Field(default_factory=list)


class DeploymentResponse(BaseModel):
    success: bool = True
    repositoryId: str
    repository: str
    summary: str
    report: DeploymentResult | None
    dockerfile: str | None
    dockerignore: str | None
    githubActions: str | None
    sources: list[SourceReference]
