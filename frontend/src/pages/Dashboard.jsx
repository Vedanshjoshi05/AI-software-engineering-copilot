import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { GitBranch } from "lucide-react";
import AppLayout from "../components/layout/AppLayout.jsx";
import { api } from "../services/api.js";

export default function Dashboard() {
  const [repos, setRepos] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;

    const loadRepositories = async () => {
      try {
        const data = await api.repositories();

        if (mounted) {
          setRepos(data.repositories || []);
        }
      } catch (error) {
        console.error("Failed to load repositories:", error);

        if (mounted) {
          setRepos([]);
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    };

    loadRepositories();

    return () => {
      mounted = false;
    };
  }, []);

  const getRepositoryId = (repo) => {
    return repo.id || repo._id;
  };

  return (
    <AppLayout>
      <div className="content">
        <div className="section-header">
          <h1>Dashboard</h1>
          <p className="subtitle">
            Your AI Software Engineering Copilot workspace.
          </p>
        </div>

        {loading ? (
          <div className="card empty">Loading repositories...</div>
        ) : repos.length === 0 ? (
          <div className="card empty">
            No repositories yet. Connect your first GitHub repository to get
            started.
          </div>
        ) : (
          <div className="grid">
            {repos.slice(0, 3).map((repo) => {
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
                      {repo.activeIndexVersion ? "Indexed" : "Not indexed"}
                    </span>

                    {repositoryId ? (
                      <Link
                        className="btn"
                        to={`/repositories/${repositoryId}`}
                      >
                        Open
                      </Link>
                    ) : (
                      <span className="error">Invalid repository ID</span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </AppLayout>
  );
}