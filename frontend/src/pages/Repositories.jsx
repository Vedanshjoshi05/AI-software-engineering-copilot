import { useEffect, useState } from "react";
import { GitBranch, Plus, Trash2, X } from "lucide-react";
import { Link } from "react-router-dom";
import { api } from "../services/api";

export default function Repositories() {
  const [repos, setRepos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [connecting, setConnecting] = useState(false);
  const [deleting, setDeleting] = useState(null);

  const [showModal, setShowModal] = useState(false);
  const [githubUrl, setGithubUrl] = useState("");

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const loadRepositories = async () => {
    try {
      setLoading(true);
      setError("");

      const data = await api.repositories();

      setRepos(data.repositories || []);
    } catch (err) {
      setError(err.message || "Failed to load repositories");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRepositories();
  }, []);

  const connectRepository = async (event) => {
    event.preventDefault();

    const url = githubUrl.trim();

    if (!url) {
      setError("Please enter a GitHub repository URL.");
      return;
    }

    try {
      setConnecting(true);
      setError("");
      setSuccess("");

      await api.createRepository({
        githubUrl: url,
      });

      setGithubUrl("");
      setShowModal(false);
      setSuccess("Repository connected successfully.");

      await loadRepositories();
    } catch (err) {
      setError(err.message || "Failed to connect repository.");
    } finally {
      setConnecting(false);
    }
  };

  const remove = async (id) => {
    const confirmed = window.confirm(
      "Are you sure you want to delete this repository?"
    );

    if (!confirmed) {
      return;
    }

    try {
      setDeleting(id);
      setError("");
      setSuccess("");

      await api.deleteRepository(id);

      setRepos((currentRepos) =>
        currentRepos.filter((repo) => repo._id !== id)
      );

      setSuccess("Repository deleted successfully.");
    } catch (err) {
      setError(err.message || "Failed to delete repository.");
    } finally {
      setDeleting(null);
    }
  };

  return (
    <section className="section">
      <div className="section-header">
        <div>
          <h2>Connected repositories</h2>

          <p className="subtitle">
            {repos.length} repository{repos.length === 1 ? "" : "ies"} in your
            workspace.
          </p>
        </div>

        <button
          className="btn"
          type="button"
          onClick={() => {
            setShowModal(true);
            setError("");
            setSuccess("");
          }}
        >
          <Plus size={16} />
          Connect Repository
        </button>
      </div>

      {error && <div className="card error">{error}</div>}

      {success && <div className="card success">{success}</div>}

      {loading ? (
        <div className="card empty">Loading...</div>
      ) : repos.length === 0 ? (
        <div className="card empty">
          <p>Your connected repositories will appear here.</p>

          <button
            className="btn"
            type="button"
            onClick={() => {
              setShowModal(true);
              setError("");
            }}
          >
            <Plus size={16} />
            Connect your first repository
          </button>
        </div>
      ) : (
        <div className="grid">
          {repos.map((repo) => (
            <div className="card repo-card" key={repo._id}>
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

                <Link className="btn" to={`/repositories/${repo._id}`}>
                  Open
                </Link>

                <button
                  className="icon-btn btn-danger"
                  type="button"
                  disabled={deleting === repo._id}
                  onClick={() => remove(repo._id)}
                  aria-label="Delete repository"
                >
                  <Trash2 size={15} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {showModal && (
        <div className="modal-overlay">
          <div className="card modal">
            <div className="section-header">
              <div>
                <h2>Connect Repository</h2>

                <p className="subtitle">
                  Enter your GitHub repository URL.
                </p>
              </div>

              <button
                className="icon-btn"
                type="button"
                onClick={() => setShowModal(false)}
                aria-label="Close"
              >
                <X size={18} />
              </button>
            </div>

            <form onSubmit={connectRepository}>
              <label htmlFor="github-url">GitHub Repository URL</label>

              <input
                id="github-url"
                type="url"
                placeholder="https://github.com/username/repository"
                value={githubUrl}
                onChange={(event) => setGithubUrl(event.target.value)}
                disabled={connecting}
                required
              />

              <div className="row">
                <button
                  className="btn"
                  type="button"
                  onClick={() => setShowModal(false)}
                  disabled={connecting}
                >
                  Cancel
                </button>

                <button
                  className="btn"
                  type="submit"
                  disabled={connecting}
                >
                  {connecting ? "Connecting..." : "Connect Repository"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </section>
  );
}