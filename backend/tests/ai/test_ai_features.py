import asyncio

import pytest

from app.schemas.ai import (
    ApiDocumentationResult,
    BugAnalysisResult,
    BugFinding,
    DeploymentResult,
    OptimizationRecommendation,
    OptimizationResult,
    SecurityAnalysisResult,
    SecurityFinding,
    TestGenerationResult,
    UmlResult,
)
from tests.conftest import GITHUB_URL, auth_headers, register_and_login


async def _create_and_index_repo(client, headers, github_mock, fake_embeddings) -> str:
    created = await client.post(
        "/api/repositories", json={"githubUrl": GITHUB_URL}, headers=headers
    )
    repo_id = created.json()["repository"]["id"]
    await client.post(f"/api/repositories/{repo_id}/index", headers=headers)
    await asyncio.sleep(0.5)
    return repo_id


@pytest.mark.asyncio
async def test_explain_requires_indexed_repository(client, github_mock):
    session = await register_and_login(client)
    headers = auth_headers(session["token"])
    created = await client.post(
        "/api/repositories", json={"githubUrl": GITHUB_URL}, headers=headers
    )
    repo_id = created.json()["repository"]["id"]

    response = await client.post(
        f"/api/repositories/{repo_id}/explain",
        json={"target": "login function"},
        headers=headers,
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_explain_success(client, github_mock, fake_embeddings, fake_llm):
    session = await register_and_login(client)
    headers = auth_headers(session["token"])
    repo_id = await _create_and_index_repo(
        client, headers, github_mock, fake_embeddings
    )

    fake_llm.generate_response = (
        "The login function checks credentials and responds with JSON."
    )
    response = await client.post(
        f"/api/repositories/{repo_id}/explain",
        json={"target": "login function"},
        headers=headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["explanation"] == fake_llm.generate_response
    assert body["target"] == "login function"


@pytest.mark.asyncio
async def test_bug_detection_success(client, github_mock, fake_embeddings, fake_llm):
    session = await register_and_login(client)
    headers = auth_headers(session["token"])
    repo_id = await _create_and_index_repo(
        client, headers, github_mock, fake_embeddings
    )

    fake_llm.structured_responses["BugAnalysisResult"] = BugAnalysisResult(
        summary="Found one probable bug",
        findings=[
            BugFinding(
                severity="medium",
                category="error-handling",
                title="Missing error handling",
                affectedFile="src/authController.js",
                type="probable_bug",
                evidence="No try/catch around JSON parsing",
                failureScenario="Malformed input crashes the handler",
                impact="Requests could fail with a 500 error",
                recommendedFix="Wrap parsing in a try/catch block",
            )
        ],
        goodPractices=["Consistent response shape"],
        limitations=["Only a subset of files were retrieved"],
    )

    response = await client.post(f"/api/repositories/{repo_id}/bugs", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["repositoryId"] == repo_id
    assert body["analysis"]["summary"] == "Found one probable bug"
    assert body["analysis"]["findings"][0]["severity"] == "medium"


@pytest.mark.asyncio
async def test_bug_detection_requires_indexed_repository(client, github_mock):
    session = await register_and_login(client)
    headers = auth_headers(session["token"])
    created = await client.post(
        "/api/repositories", json={"githubUrl": GITHUB_URL}, headers=headers
    )
    repo_id = created.json()["repository"]["id"]

    response = await client.post(f"/api/repositories/{repo_id}/bugs", headers=headers)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_security_analysis_success(
    client, github_mock, fake_embeddings, fake_llm
):
    session = await register_and_login(client)
    headers = auth_headers(session["token"])
    repo_id = await _create_and_index_repo(
        client, headers, github_mock, fake_embeddings
    )

    fake_llm.structured_responses["SecurityAnalysisResult"] = SecurityAnalysisResult(
        summary="One concern found",
        findings=[
            SecurityFinding(
                severity="high",
                category="authentication",
                title="No rate limiting on login",
                affectedFile="src/authController.js",
                type="security_concern",
                evidence="Login handler has no throttling",
                impact="Susceptible to brute-force attempts",
                recommendation="Add rate limiting middleware",
            )
        ],
        goodPractices=[],
        limitations=[],
    )

    response = await client.post(
        f"/api/repositories/{repo_id}/security", headers=headers
    )
    assert response.status_code == 200
    body = response.json()
    assert body["analysis"]["findings"][0]["type"] == "security_concern"


@pytest.mark.asyncio
async def test_security_analysis_falls_back_on_refusal(
    client, github_mock, fake_embeddings, fake_llm
):
    session = await register_and_login(client)
    headers = auth_headers(session["token"])
    repo_id = await _create_and_index_repo(
        client, headers, github_mock, fake_embeddings
    )

    call_count = {"n": 0}
    fallback_result = SecurityAnalysisResult(
        summary="Fallback analysis", findings=[], goodPractices=[], limitations=[]
    )

    async def flaky_generate_structured(prompt, schema):
        call_count["n"] += 1
        if call_count["n"] == 1:
            from app.services.ai.gemini_provider import LLMGenerationError

            raise LLMGenerationError("I cannot fulfill this request")
        return fallback_result

    fake_llm.generate_structured = flaky_generate_structured

    response = await client.post(
        f"/api/repositories/{repo_id}/security", headers=headers
    )
    assert response.status_code == 200
    assert response.json()["analysis"]["summary"] == "Fallback analysis"
    assert call_count["n"] == 2


@pytest.mark.asyncio
async def test_optimization_success(client, github_mock, fake_embeddings, fake_llm):
    session = await register_and_login(client)
    headers = auth_headers(session["token"])
    repo_id = await _create_and_index_repo(
        client, headers, github_mock, fake_embeddings
    )

    fake_llm.structured_responses["OptimizationResult"] = OptimizationResult(
        summary="One optimization found",
        recommendations=[
            OptimizationRecommendation(
                priority="medium",
                category="performance",
                title="Avoid re-fetching user on every request",
                affectedFile="src/authController.js",
                currentImplementation="User is fetched from DB on every call",
                problem="Adds latency to every request",
                recommendedOptimization="Cache user lookups",
                expectedBenefit="Reduced DB load",
            )
        ],
        existingGoodPractices=[],
        limitations=[],
    )

    response = await client.post(
        f"/api/repositories/{repo_id}/optimize", headers=headers
    )
    assert response.status_code == 200
    assert (
        response.json()["analysis"]["recommendations"][0]["category"] == "performance"
    )


@pytest.mark.asyncio
async def test_uml_generation_success(client, github_mock, fake_embeddings, fake_llm):
    session = await register_and_login(client)
    headers = auth_headers(session["token"])
    repo_id = await _create_and_index_repo(
        client, headers, github_mock, fake_embeddings
    )

    fake_llm.structured_responses["UmlResult"] = UmlResult(
        summary="Simple architecture",
        architectureSummary="Client talks to an Express-style API",
        mermaid="flowchart TD\nClient --> API\nAPI --> DB",
        componentRelationships="API depends on DB",
        limitations=[],
    )

    response = await client.post(f"/api/repositories/{repo_id}/uml", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["mermaid"].startswith("flowchart TD")


@pytest.mark.asyncio
async def test_test_generation_success(client, github_mock, fake_embeddings, fake_llm):
    session = await register_and_login(client)
    headers = auth_headers(session["token"])
    repo_id = await _create_and_index_repo(
        client, headers, github_mock, fake_embeddings
    )

    fake_llm.structured_responses["TestGenerationResult"] = TestGenerationResult(
        summary="Generated one test file",
        testingStrategy="pytest with mocked dependencies",
        testFiles=[],
        additionalTestCases=["Login with missing password"],
        limitations=[],
    )

    response = await client.post(f"/api/repositories/{repo_id}/tests", headers=headers)
    assert response.status_code == 200
    assert (
        response.json()["tests"]["testingStrategy"] == "pytest with mocked dependencies"
    )


@pytest.mark.asyncio
async def test_documentation_generation_success(
    client, github_mock, fake_embeddings, fake_llm
):
    session = await register_and_login(client)
    headers = auth_headers(session["token"])
    repo_id = await _create_and_index_repo(
        client, headers, github_mock, fake_embeddings
    )

    fake_llm.structured_responses["ApiDocumentationResult"] = ApiDocumentationResult(
        summary="One endpoint documented",
        overview="A small authentication API",
        endpoints=[],
        limitations=[],
    )

    response = await client.post(
        f"/api/repositories/{repo_id}/documentation", headers=headers
    )
    assert response.status_code == 200
    assert response.json()["documentation"]["overview"] == "A small authentication API"


@pytest.mark.asyncio
async def test_deployment_generation_success(
    client, github_mock, fake_embeddings, fake_llm
):
    session = await register_and_login(client)
    headers = auth_headers(session["token"])
    repo_id = await _create_and_index_repo(
        client, headers, github_mock, fake_embeddings
    )

    fake_llm.structured_responses["DeploymentResult"] = DeploymentResult(
        summary="Node/Express API detected",
        stackDetection="Node.js + Express",
        existingConfiguration="No Docker or CI/CD found",
        recommendedArchitecture="Containerize and deploy to ECS Fargate",
        environmentVariables=["JWT_SECRET=<your-jwt-secret>"],
        deploymentSteps=["Build image", "Push to ECR", "Deploy to Fargate"],
        risksAndVerification=["Confirm health check path before deploying"],
    )

    response = await client.post(
        f"/api/repositories/{repo_id}/deployment", headers=headers
    )
    assert response.status_code == 200
    body = response.json()
    assert body["report"]["stackDetection"] == "Node.js + Express"
    assert "<your-jwt-secret>" in body["report"]["environmentVariables"][0]


@pytest.mark.asyncio
async def test_ai_feature_ownership_enforced(
    client, github_mock, fake_embeddings, fake_llm
):
    owner_session = await register_and_login(client, "owner3@example.com")
    other_session = await register_and_login(client, "other3@example.com")
    repo_id = await _create_and_index_repo(
        client, auth_headers(owner_session["token"]), github_mock, fake_embeddings
    )

    response = await client.post(
        f"/api/repositories/{repo_id}/bugs",
        headers=auth_headers(other_session["token"]),
    )
    assert response.status_code == 404
