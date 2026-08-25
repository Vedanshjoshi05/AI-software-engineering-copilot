import React, { useEffect, useState } from "react";
import { GitBranch, Trash2 } from "lucide-react";
import AppLayout from "../components/layout/AppLayout.jsx";
import { api } from "../services/api.js";

export default function Repositories() {
  const [repos, setRepos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    loadRepositories();
  }, []);

  const loadRepositories = async () => {
    try {
      setLoading(true);
      setError("");

      const data = await api.repositories();

      setRepos(data.repositories || []);
    } catch (err) {
      console.error("Failed to load repositories:", err);
      setError(err.message || "Failed to load repositories");
    } finally {
      setLoading(false);
    }
  };

  const getRepositoryId = (repo) => {
    return repo.id || repo._id;
  };

  const remove = async (id) => {
    if (!id) {
      setError("Repository ID is missing.");
      return;
    }

    const confirmed = window.confirm(
      "Are you sure you want to delete this repository?"
    );

    if (!confirmed) {
      return;
    }

    try {
      setError("");

      await api.deleteRepository(id);

      setRepos((currentRepos) =>
        currentRepos.filter((repo) => getRepositoryId(repo) !== id)
      );
    } catch (err) {
      console.error("Failed to delete repository:", err);
      setError(err.message || "Failed to delete repository");
    }
  };

  return (
    <AppLayout>
      <div className="content">
        <section className="section">
          <div className="section-header">
            <h2>Connected repositories</h2>

            <p className="subtitle">
              {repos.length} repository
              {repos.length === 1 ? "" : "ies"} in your workspace.
            </p>
          </div>

          {error && <div className="error">{error}</div>}

          {loading ? (
            <div className="card empty">Loading...</div>
          ) : repos.length === 0 ? (
            <div className="card empty">
              Your connected repositories will appear here.
            </div>
          ) : (
            <div className="grid">
              {repos.map((repo) => {
                const repositoryId = getRepositoryId(repo);

                return (
                  <div
                    className="card repo-card"
                    key={repositoryId || repo.githubUrl}
                  >
                    <div className="repo-left">
                      <div className="repo-icon">
                        <GitBranch size={19} />
                      </div>

                      <div style={{ minWidth: 0 }}>
                        <div className="repo-name">{repo.name}</div>

                        <div className="repo-url">{repo.githubUrl}</div>
                      </div>
                    </div>

                    <div className="row">
                      <span className="badge">
                        {repo.activeIndexVersion
                          ? "Indexed"
                          : "Not indexed"}
                      </span>

                      {repositoryId ? (
                        <a
                          className="btn"
                          href={`/repositories/${repositoryId}`}
                        >
                          Open
                        </a>
                      ) : (
                        <span className="error">Invalid repository ID</span>
                      )}

                      {repositoryId && (
                        <button
                          className="icon-btn btn-danger"
                          onClick={() => remove(repositoryId)}
                          aria-label="Delete repository"
                        >
                          <Trash2 size={15} />
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </section>
      </div>
    </AppLayout>
  );
}