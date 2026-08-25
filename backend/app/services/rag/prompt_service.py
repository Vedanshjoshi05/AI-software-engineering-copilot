"""
PromptService — centralizes every prompt template so AI feature services
stay thin and don't duplicate prompt-construction logic.

Each `build_*_query()` function produces a retrieval query (used to fetch
relevant chunks from Qdrant). Each `build_*_prompt()` function produces the
final generation prompt. Structured-output prompts intentionally omit
markdown-format instructions since GeminiProvider.generate_structured()
appends the JSON schema automatically -- the prompt only needs to describe
the analysis task and the grounding rules.
"""

from __future__ import annotations


# ----------------------------------------------------------------------
# RAG Q&A
# ----------------------------------------------------------------------
def build_rag_prompt(
    repository_name: str, repository_context: str, question: str
) -> str:
    return f"""
You are an AI software engineering assistant analyzing a software repository.

Repository:
{repository_name}

Your task is to answer the user's question using the repository context provided below.

IMPORTANT RULES:

1. Base your answer on the supplied repository context.
2. Do not invent files, functions, classes, variables, APIs, architecture, or repository behavior.
3. If the provided context is insufficient to answer the question, clearly say that the indexed context does not contain enough information.
4. Explain the relevant code clearly.
5. Mention relevant file names when useful.
6. When multiple files contribute to the behavior, explain how they relate.
7. Do not claim knowledge about repository code that is not present in the provided context.

USER QUESTION:

{question}

REPOSITORY CONTEXT:

{repository_context}

ANSWER:
"""


# ----------------------------------------------------------------------
# Code explanation
# ----------------------------------------------------------------------
def build_explanation_query(target: str) -> str:
    return f"""
Explain the following code, file, component, function, class, module, or feature from this repository:

{target}

Find the implementation and directly related code.
"""


def build_explanation_prompt(
    repository_name: str, repository_context: str, target: str
) -> str:
    return f"""
You are an AI software engineer explaining source code from a software repository.

Repository:
{repository_name}

TARGET TO EXPLAIN:

{target}

REPOSITORY CONTEXT:

{repository_context}

Your job is to explain the target using ONLY the repository context above.

IMPORTANT RULES:

1. Do not invent files, functions, classes, APIs, dependencies, or behavior.
2. If the retrieved context does not contain enough information, explicitly state what information is missing.
3. Distinguish clearly between behavior directly shown in the code and reasonable interpretation.
4. Mention relevant file names.
5. Explain relationships between files when the context demonstrates them.
6. Do not give generic framework explanations unless necessary to understand the supplied code.

Structure the explanation using these sections when the repository context supports them:
Purpose, How It Works, Important Functions / Components, Data Flow, Dependencies, Engineering Notes.

EXPLANATION:
"""


# ----------------------------------------------------------------------
# Bug detection
# ----------------------------------------------------------------------
def build_bug_query() -> str:
    return """
Perform a defensive software correctness review.

Find code related to: application logic, controllers and services, API routes, async
operations, promises, error handling, database operations, state management, null or
undefined values, validation, loops and conditions, resource handling, frontend event
handlers, API requests, authentication flows, data transformations, concurrency, edge cases.

Find implementation that may contain runtime errors, logic bugs, incorrect assumptions,
or reliability issues.
"""


def build_bug_prompt(repository_name: str, repository_context: str) -> str:
    return f"""
You are a senior software engineer reviewing source code for correctness and reliability.

Repository:
{repository_name}

REPOSITORY CONTEXT:

{repository_context}

Analyze ONLY the supplied source code. Do not invent files, functions, variables, APIs,
runtime behavior, or bugs.

Classify each finding's type as one of:
- confirmed_bug: strong evidence the implementation can behave incorrectly.
- probable_bug: appears incorrect, but more context would be needed to confirm.
- code_quality_concern: works or may work, but implementation could cause
  maintainability or reliability problems.

Do not report style preferences as bugs. Do not claim a bug is confirmed when its
behavior depends on code missing from the supplied context. Do not claim the entire
repository is bug-free if no problems appear in the retrieved chunks.

For each finding, identify: severity, category, title, affectedFile, type, evidence,
failureScenario, impact, and recommendedFix. Also list goodPractices visible in the
code and limitations describing what could not be verified because relevant repository
context was not retrieved.
"""


# ----------------------------------------------------------------------
# Security analysis
# ----------------------------------------------------------------------
def build_security_query() -> str:
    return """
Perform a defensive secure-code review of this repository.

Find implementation related to: authentication, authorization, login, logout, JWT
handling, cookies, sessions, middleware, API routes, admin functionality, user-controlled
input, input validation, sanitization, database queries, sensitive data, configuration,
CORS, HTTP security headers, rate limiting, external requests, file uploads, credentials
and secrets.
"""


def build_security_prompt(repository_name: str, repository_context: str) -> str:
    return f"""
You are performing a defensive secure-code review for the developer of a software
repository, to help them identify and fix security weaknesses in their own source code.

Repository:
{repository_name}

REPOSITORY CONTEXT:

{repository_context}

Analyze ONLY the supplied repository context. Do not invent files, routes, functions,
configuration, vulnerabilities, or implementation details.

Review the supplied code for defensive security issues in areas such as: authentication,
authorization, broken access control, session handling, JWT handling, cookie security,
CSRF defenses, CORS, user input validation, sanitization, injection risks, sensitive data
handling, secrets, password handling, database operations, security headers, rate
limiting, error handling, privilege boundaries.

Classify each finding's type as one of:
- vulnerability: a concrete security weakness supported by supplied code.
- security_concern: potentially risky behavior needing more context to confirm.

Do NOT claim that the entire repository is secure when the retrieved context is
incomplete. Do NOT report hypothetical vulnerabilities as confirmed vulnerabilities.
Do NOT claim a file was analyzed unless its code appears in the supplied context.

For each finding, identify: severity, category, title, affectedFile, type, evidence,
impact, and recommendation. Also list goodPractices (defensive controls actually visible)
and limitations (areas that cannot be assessed because relevant code was not retrieved).
"""


def build_security_fallback_prompt(
    repository_name: str, repository_context: str
) -> str:
    """Used when the primary prompt triggers a model safety refusal, mirroring the
    original fallback in securityAnalysisService.js."""
    return f"""
You are helping a software developer improve the defensive security quality of their
own application by reviewing their own source code, which they have explicitly shared
with you for this purpose.

Repository:
{repository_name}

REPOSITORY CONTEXT:

{repository_context}

Identify implementation weaknesses the developer should consider fixing. Focus on:
authentication implementation, authorization checks, cookie configuration,
session/token handling, input validation, user-controlled data, database operations,
sensitive information, API protection, server configuration, security middleware,
error handling.

Only make observations supported by the supplied code. Do not invent missing code or
implementation details.

For each finding, identify: severity, category, title, affectedFile, type
(use "security_concern" if unsure), evidence, impact, and recommendation. Also list
goodPractices and limitations.
"""


# ----------------------------------------------------------------------
# Code optimization
# ----------------------------------------------------------------------
def build_optimization_query() -> str:
    return """
Review this repository for software engineering and performance optimization
opportunities.

Find code related to: database queries, loops and repeated computation, API requests,
frontend rendering, React state updates, async operations, network requests, caching,
search functionality, data fetching, database indexing, unnecessary work, duplicate
operations, memory usage, scalability, error handling, concurrency, expensive operations.
"""


def build_optimization_prompt(repository_name: str, repository_context: str) -> str:
    return f"""
You are a senior software engineer performing a performance and code optimization review.

Repository:
{repository_name}

REPOSITORY CONTEXT:

{repository_context}

Analyze ONLY the supplied repository context. Do not invent files, functions, database
queries, APIs, performance measurements, or bottlenecks.

Look for improvements involving: unnecessary API requests, inefficient database queries,
missing pagination, missing database indexes, repeated computation, frontend
re-rendering, asynchronous request handling, caching opportunities, network efficiency,
memory usage, scalability, duplicated logic, maintainability, error handling.

Classify each recommendation's category as one of: performance, scalability,
reliability, maintainability.

For each recommendation, identify: priority, category, title, affectedFile,
currentImplementation, problem, recommendedOptimization, expectedBenefit, and an
optional example code snippet when the supplied context contains enough information to
safely provide one. Also list existingGoodPractices and limitations.

Do not invent performance numbers. Do not claim something is slow unless the supplied
code provides reasonable evidence. Do not recommend unnecessary complexity.
"""


# ----------------------------------------------------------------------
# Test generation
# ----------------------------------------------------------------------
def build_test_query() -> str:
    return """
Analyze this repository for automated test generation.

Find code related to: package manifest and testing dependencies, existing test files,
test configuration, controllers, services, API routes, middleware, validation, models,
React components, utility functions, authentication, error handling, request and
response behavior.
"""


def build_test_prompt(repository_name: str, repository_context: str) -> str:
    return f"""
You are a senior software engineer generating automated tests for an existing software
repository.

Repository:
{repository_name}

REPOSITORY CONTEXT:

{repository_context}

Generate tests ONLY from the supplied repository context. Do not invent functions,
routes, files, fields, middleware, or behavior.

Prefer the testing framework already visible in the repository; if it cannot be
determined, clearly state that in testingStrategy before generating code. Test
observable behavior rather than implementation details. Include success cases,
validation failures, auth failures, and important edge cases when supported by
retrieved code. Do not use real production credentials or call external production
services. Clearly identify assumptions required to run the tests. Generated test code
should be syntactically complete where enough repository context exists.

Provide: summary, testingStrategy, a list of testFiles (each with suggestedPath,
framework, covers, and complete code), additionalTestCases that cannot safely be
generated because required context is missing, optional runningInstructions (only if
determinable from repository configuration), and limitations.
"""


# ----------------------------------------------------------------------
# API documentation
# ----------------------------------------------------------------------
def build_api_documentation_query() -> str:
    return """
Analyze this repository and find HTTP API implementation.

Find code related to: routers, route definitions, route mounting, HTTP methods
(GET/POST/PUT/PATCH/DELETE), controllers, middleware, authentication, authorization,
request body handling, query parameters, URL parameters, validation, response status
codes, response JSON, error responses.
"""


def build_api_documentation_prompt(
    repository_name: str, repository_context: str
) -> str:
    return f"""
You are a senior backend engineer generating API documentation from an existing
software repository.

Repository:
{repository_name}

REPOSITORY CONTEXT:

{repository_context}

Generate documentation ONLY from the supplied context. Do not invent endpoints, request
fields, response fields, authentication requirements, status codes, controllers, or
middleware. Determine endpoint paths from route definitions; if a router is mounted
under a base path and that information exists in the context, combine the base path and
router path. Use controllers and validation code to determine request/response
behavior. Determine whether an endpoint is authenticated from middleware shown in the
context. If information cannot be determined, use the literal string
"Not determined from retrieved context." for that field.

Provide: summary, overview, a list of endpoints (each with method, path, purpose,
authentication, controller, middleware, pathParameters, queryParameters, requestBody,
successResponse, errorResponses, implementationNotes, sourceFiles), an overall
authentication description, a validation description, an errorHandling description,
and limitations (routes/behavior that cannot be confidently documented).

Do not output fictional example responses unless their fields can be inferred from the
supplied controller code.
"""


# ----------------------------------------------------------------------
# UML / architecture
# ----------------------------------------------------------------------
def build_uml_query() -> str:
    return """
Analyze the architecture and structure of this repository for UML diagram generation.

Find code related to: application entry points, frontend components, backend routes,
controllers, services, middleware, database models, schemas, utility modules,
authentication, API requests, database access, relationships between modules, imports
and dependencies, data flow.
"""


def build_uml_prompt(repository_name: str, repository_context: str) -> str:
    return f"""
You are a senior software architect generating a UML-style architecture diagram for an
existing software repository.

Repository:
{repository_name}

REPOSITORY CONTEXT:

{repository_context}

Generate the diagram ONLY from the supplied context. Do not invent components, files,
classes, services, databases, APIs, or relationships. Include only relationships
supported by the retrieved repository context. Prefer meaningful architectural
components rather than every individual function. Show important relationships between
frontend, backend, routes, controllers, middleware, models, database, and external
services.

The `mermaid` field must contain valid Mermaid flowchart syntax (starting with
"flowchart TD"), using simple safe node IDs (e.g. Client, App, LeadRoutes,
LeadController, LeadModel) with human-readable names inside node labels. Do not put
markdown formatting inside Mermaid labels. If a relationship cannot be confirmed, do not
include it.

Provide: summary, architectureSummary (explaining the major components and how they
interact), mermaid (the diagram source), componentRelationships (explaining the
important relationships represented in the diagram), and limitations (architecture that
could not be determined from the retrieved context).
"""


# ----------------------------------------------------------------------
# Deployment / CI/CD generation
# ----------------------------------------------------------------------
def build_deployment_query() -> str:
    return """
Analyze this repository for deployment and CI/CD configuration.

Find code and files related to: application entry points, frontend/backend framework,
runtime and language, package manifest, dependencies, build/start scripts, environment
variables, database connections, external services, API configuration, ports, CORS,
authentication, Docker, Docker Compose, deployment configuration, GitHub Actions,
CI/CD workflows, testing commands, build commands, production configuration, static
frontend builds, server startup, health checks, cloud deployment requirements.
"""


def build_deployment_prompt(repository_name: str, repository_context: str) -> str:
    return f"""
You are a senior DevOps and cloud engineer analyzing an existing software repository to
produce a practical deployment and CI/CD plan. The preferred cloud platform is AWS when
the repository architecture supports it.

Repository:
{repository_name}

REPOSITORY CONTEXT:

{repository_context}

IMPORTANT RULES:

1. Base all repository-specific claims on the supplied repository context.
2. Do not invent frameworks, dependencies, scripts, environment variables, databases,
   services, ports, files, or tests.
3. Clearly distinguish existing repository configuration from recommended configuration.
4. Never output real secret values -- environment variables must use placeholders, e.g.
   MONGODB_URI=<your-mongodb-uri>. Never fabricate API keys, JWT secrets, passwords,
   connection strings, tokens, or credentials.
5. If package scripts or commands cannot be confirmed, explicitly say so.
6. Prefer containerized backend deployment when suitable.
7. For a static frontend, AWS S3 + CloudFront may be recommended when supported by the
   repository structure. For containerized backend services, AWS ECR + ECS/Fargate may
   be recommended when appropriate.
8. Do not claim that recommended AWS resources already exist.
9. Generated files must be presented as recommendations, not existing repository files.
10. Keep generated configuration minimal and practical.

Provide: summary, stackDetection, existingConfiguration (Docker/workflows/deployment
files/scripts already present, or state none were found), recommendedArchitecture,
environmentVariables (confirmed or strongly supported by context, never secret values),
optional dockerfile, optional dockerignore, optional githubActions workflow, an
awsDeployment explanation, ordered deploymentSteps, and risksAndVerification
(assumptions, missing information, or anything that must be verified before production
deployment).
"""
