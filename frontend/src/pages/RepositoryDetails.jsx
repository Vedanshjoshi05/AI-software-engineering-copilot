import React, { useCallback, useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  ArrowLeft, BrainCircuit, Bug, CheckCircle2, FileCode2, FileText,
  LoaderCircle, Network, RefreshCw, ShieldCheck, TestTube2, Wrench, X,
  Rocket, MessageSquare
} from "lucide-react";
import AppLayout from "../components/layout/AppLayout.jsx";
import { api } from "../services/api.js";

const actions = [
  ["Explain", "Understand a file or code target", FileCode2, "explain"],
  ["Bugs", "Find likely defects", Bug, "bugs"],
  ["Optimize", "Improve code quality", Wrench, "optimize"],
  ["Security", "Assess security risks", ShieldCheck, "security"],
  ["UML", "Generate an architecture diagram", Network, "uml"],
  ["Tests", "Generate test cases", TestTube2, "tests"],
  ["Documentation", "Generate API documentation", FileText, "documentation"],
  ["Deployment", "Generate deployment configuration", Rocket, "deployment"],
  ["Ask", "Chat with the repository", BrainCircuit, "ask"],
];

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

// Structured findings (bugs, security) share this shape: severity, category,
// title, affectedFile, evidence/problem, impact/benefit, recommendation/fix.
function FindingCard({ finding, index }) {
  const severity = (finding.severity || finding.priority || "").toLowerCase();
  return (
    <div className="finding-card" key={index}>
      <div className="finding-header">
        <span className={`severity-pill severity-${severity || "info"}`}>{finding.severity || finding.priority || "info"}</span>
        <span className="finding-title">{finding.title}</span>
      </div>
      {finding.affectedFile && <div className="finding-file">{finding.affectedFile}</div>}
      {(finding.evidence || finding.currentImplementation) && (
        <div className="finding-row"><strong>Evidence: </strong>{finding.evidence || finding.currentImplementation}</div>
      )}
      {(finding.impact || finding.problem) && (
        <div className="finding-row"><strong>Impact: </strong>{finding.impact || finding.problem}</div>
      )}
      {(finding.recommendedFix || finding.recommendation || finding.recommendedOptimization) && (
        <div className="finding-row"><strong>Recommendation: </strong>{finding.recommendedFix || finding.recommendation || finding.recommendedOptimization}</div>
      )}
    </div>
  );
}

function StructuredAnalysis({ analysis }) {
  const findings = analysis.findings || analysis.recommendations;
  return (
    <div className="result-section">
      {analysis.summary && <div className="result-summary">{analysis.summary}</div>}
      {Array.isArray(findings) && findings.length > 0 && (
        <div className="finding-list">
          {findings.map((finding, index) => <FindingCard finding={finding} index={index} key={index} />)}
        </div>
      )}
      {Array.isArray(analysis.goodPractices) && analysis.goodPractices.length > 0 && (
        <div className="result-section"><div className="result-label">Good practices observed</div><ul>{analysis.goodPractices.map((item, i) => <li key={i}>{item}</li>)}</ul></div>
      )}
      {Array.isArray(analysis.limitations) && analysis.limitations.length > 0 && (
        <div className="result-section"><div className="result-label">Limitations</div><ul>{analysis.limitations.map((item, i) => <li key={i}>{item}</li>)}</ul></div>
      )}
    </div>
  );
}

function StructuredTests({ tests }) {
  return (
    <div className="result-section">
      {tests.summary && <div className="result-summary">{tests.summary}</div>}
      {tests.testingStrategy && <div className="result-row"><strong>Strategy: </strong>{tests.testingStrategy}</div>}
      {(tests.testFiles || []).map((file, index) => (
        <div className="result-section" key={index}>
          <div className="result-label">{file.suggestedPath} ({file.framework})</div>
          <pre className="result-pre">{file.code}</pre>
        </div>
      ))}
      {Array.isArray(tests.additionalTestCases) && tests.additionalTestCases.length > 0 && (
        <div className="result-section"><div className="result-label">Additional cases to consider</div><ul>{tests.additionalTestCases.map((item, i) => <li key={i}>{item}</li>)}</ul></div>
      )}
    </div>
  );
}

function StructuredDocumentation({ documentation }) {
  return (
    <div className="result-section">
      {documentation.summary && <div className="result-summary">{documentation.summary}</div>}
      {documentation.overview && <div className="result-row">{documentation.overview}</div>}
      {(documentation.endpoints || []).map((endpoint, index) => (
        <div className="finding-card" key={index}>
          <div className="finding-header"><span className="severity-pill severity-info">{endpoint.method}</span><span className="finding-title">{endpoint.path}</span></div>
          <div className="finding-row">{endpoint.purpose}</div>
          <div className="finding-row"><strong>Auth: </strong>{endpoint.authentication}</div>
          <div className="finding-row"><strong>Response: </strong>{endpoint.successResponse}</div>
        </div>
      ))}
    </div>
  );
}

function ResultBlock({ data }) {
  if (!data) return null;
  const structured = data.analysis || null;
  const mermaid = data.mermaid;

  return (
    <div className="result-area">
      {data.summary && <div className="result-summary">{String(data.summary)}</div>}
      {structured && <StructuredAnalysis analysis={structured} />}
      {data.tests && <StructuredTests tests={data.tests} />}
      {data.documentation && <StructuredDocumentation documentation={data.documentation} />}
      {data.report && !mermaid && !data.dockerfile && (
        <div className="result-section"><pre className="result-pre">{JSON.stringify(data.report, null, 2)}</pre></div>
      )}
      {(data.explanation || data.answer) && (
        <pre className="result-pre">{data.explanation || data.answer}</pre>
      )}
      {mermaid && (
        <div className="result-section">
          <div className="result-label">Mermaid</div>
          <pre className="result-pre">{mermaid}</pre>
        </div>
      )}
      {data.dockerfile && <div className="result-section"><div className="result-label">Dockerfile</div><pre className="result-pre">{data.dockerfile}</pre></div>}
      {data.dockerignore && <div className="result-section"><div className="result-label">.dockerignore</div><pre className="result-pre">{data.dockerignore}</pre></div>}
      {data.githubActions && <div className="result-section"><div className="result-label">GitHub Actions</div><pre className="result-pre">{typeof data.githubActions === "string" ? data.githubActions : JSON.stringify(data.githubActions, null, 2)}</pre></div>}
      {data.sources?.length > 0 && (
        <div className="result-section">
          <div className="result-label">Sources</div>
          <div className="source-list">
            {data.sources.map((source, index) => (
              <div className="source-item" key={index}>{typeof source === "string" ? source : JSON.stringify(source)}</div>
            ))}
          </div>
        </div>
      )}
      {!structured && !data.tests && !data.documentation && !data.report && !data.explanation && !data.answer && !mermaid && !data.dockerfile && !data.githubActions && !data.dockerignore && (
        <pre className="result-pre">{JSON.stringify(data, null, 2)}</pre>
      )}
    </div>
  );
}

export default function RepositoryDetails() {
  const { id } = useParams();
  const [repo, setRepo] = useState(null);
  const [status, setStatus] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [selected, setSelected] = useState(null);
  const [result, setResult] = useState(null);
  const [target, setTarget] = useState("");
  const [question, setQuestion] = useState("");
  const pollRef = useRef(false);

  const load = useCallback(async () => {
    try {
      const [repoData, statusData] = await Promise.all([
        api.repository(id),
        api.indexStatus(id),
      ]);
      setRepo(repoData.repository);
      setStatus(statusData);
      return statusData;
    } catch (err) {
      setError(err.message || "Failed to load repository");
      return null;
    }
  }, [id]);

  useEffect(() => {
    load();
    return () => { pollRef.current = false; };
  }, [load]);

  const pollIndexing = async () => {
    pollRef.current = true;
    while (pollRef.current) {
      const current = await load();
      const currentStatus = current?.status;
      if (currentStatus === "ready" || currentStatus === "failed" || currentStatus === "not_indexed") break;
      await sleep(1500);
    }
  };

  const index = async () => {
    setBusy(true);
    setError("");
    try {
      await api.indexRepository(id);
      await load();
      setBusy(false);
      await pollIndexing();
    } catch (err) {
      setError(err.message || "Failed to start indexing");
      setBusy(false);
    }
  };

  const runAi = async (type) => {
    setError("");
    setResult(null);
    setBusy(true);
    try {
      let data;
      if (type === "explain") data = await api.explain(id, { target: target.trim() });
      else if (type === "ask") data = await api.ask(id, { question: question.trim() });
      else data = await api[type](id);
      setResult(data);
    } catch (err) {
      setError(err.message || "AI analysis failed");
    } finally {
      setBusy(false);
    }
  };

  const openTool = (type) => {
    setSelected(type);
    setResult(null);
    setError("");
    setTarget("");
    setQuestion("");
  };

  if (error && !repo) {
    return <AppLayout><div className="content"><div className="card empty"><div className="error">{error}</div><Link className="btn" to="/repositories" style={{ display: "inline-block", marginTop: 15 }}>Back to repositories</Link></div></div></AppLayout>;
  }
  if (!repo) return <AppLayout><div className="content"><div className="card empty">Loading repository...</div></div></AppLayout>;

  const statusName = status?.status || repo.indexingStatus || "not_indexed";
  const progress = Number.isFinite(Number(status?.progress)) ? Number(status.progress) : (repo.indexingProgress || 0);
  const indexed = statusName === "ready" || Boolean(repo.activeIndexVersion);
  const indexing = statusName === "indexing";
  const selectedAction = actions.find((item) => item[3] === selected);

  return (
    <AppLayout>
      <div className="content">
        <Link to="/repositories" className="back-link"><ArrowLeft size={14} /> Repositories</Link>

        <div className="row repo-heading">
          <div>
            <div className="eyebrow">Repository</div>
            <h1>{repo.name}</h1>
            <p className="subtitle">{repo.description || repo.githubUrl}</p>
          </div>
          <span className={`badge ${indexed ? "badge-success" : "badge-muted"}`}>
            {indexed ? <><CheckCircle2 size={12} /> Indexed</> : indexing ? <><LoaderCircle size={12} className="spin" /> Indexing</> : "Not indexed"}
          </span>
        </div>

        <div className="card index-card">
          <div className="row">
            <div>
              <h2>Repository indexing</h2>
              <p className="subtitle">Build the code index before running repository-aware AI analysis.</p>
            </div>
            <button className="btn btn-primary" disabled={busy || indexing || indexed} onClick={index}>
              {indexing || busy ? <><RefreshCw size={14} className="spin" /> Indexing...</> : indexed ? "Indexed" : "Start indexing"}
            </button>
          </div>
          <div className="index-meta">
            <span>Status: <strong>{statusName.replace("_", " ")}</strong></span>
            <span>{progress}%</span>
          </div>
          <div className="progress"><div className="progress-fill" style={{ width: `${Math.min(100, Math.max(0, progress))}%` }} /></div>
          {status?.error && <div className="error">{status.error}</div>}
          {error && <div className="error">{error}</div>}
        </div>

        <section className="section">
          <div className="section-header"><h2>AI analysis</h2><p className="subtitle">Run an analysis against the indexed repository.</p></div>
          <div className="grid tool-grid">
            {actions.map(([title, desc, Icon, type]) => (
              <button className="card tool" key={type} disabled={!indexed} onClick={() => openTool(type)}>
                <div className="tool-icon"><Icon size={17} /></div>
                <div className="tool-title">{title}</div>
                <div className="tool-desc">{desc}</div>
              </button>
            ))}
          </div>
          {!indexed && <p className="subtitle tool-note">Index the repository to unlock AI analysis.</p>}
        </section>
      </div>

      {selectedAction && (
        <div className="modal-backdrop" onMouseDown={(e) => e.target === e.currentTarget && !busy && setSelected(null)}>
          <div className="modal card">
            <div className="modal-header">
              <div><div className="eyebrow">AI workflow</div><h2>{selectedAction[0]}</h2></div>
              <button className="icon-btn" disabled={busy} onClick={() => setSelected(null)} aria-label="Close"><X size={17} /></button>
            </div>
            <p className="subtitle">{selectedAction[1]} for <strong>{repo.name}</strong>.</p>

            {selected === "explain" && <div className="form-group modal-form"><label className="label">File, symbol, or code target</label><input className="input" value={target} onChange={(e) => setTarget(e.target.value)} placeholder="src/controller/authController.js" autoFocus /></div>}
            {selected === "ask" && <div className="form-group modal-form"><label className="label">Question</label><textarea className="input textarea" value={question} onChange={(e) => setQuestion(e.target.value)} placeholder="How does authentication work in this repository?" autoFocus /></div>}

            <div className="modal-actions">
              <button className="btn" disabled={busy} onClick={() => setSelected(null)}>Cancel</button>
              <button className="btn btn-primary" disabled={busy || (selected === "explain" && !target.trim()) || (selected === "ask" && !question.trim())} onClick={() => runAi(selected)}>
                {busy ? <><LoaderCircle size={14} className="spin" /> Running...</> : <><MessageSquare size={14} /> Run analysis</>}
              </button>
            </div>
            {error && <div className="error">{error}</div>}
            {result && <ResultBlock data={result} />}
          </div>
        </div>
      )}
    </AppLayout>
  );
}
