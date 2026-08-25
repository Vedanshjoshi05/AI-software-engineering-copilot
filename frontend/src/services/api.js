const API_URL =
  import.meta.env.VITE_API_URL || "http://localhost:8000/api";

async function request(path, options = {}) {
  const token = localStorage.getItem("accessToken");

  const headers = {
    "Content-Type": "application/json",
    "Cache-Control": "no-cache",
    ...(options.headers || {}),
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_URL}${path}`, {
    cache: "no-store",
    ...options,
    headers,
  });

  let data = {};

  try {
    data = await response.json();
  } catch {
    // Response may not contain JSON.
  }

  if (!response.ok) {
    const error = new Error(data.message || "Request failed");
    error.status = response.status;
    error.data = data;
    throw error;
  }

  return data;
}

export const api = {
  // -----------------------------
  // Authentication
  // -----------------------------

  login: (body) =>
    request("/auth/login", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  register: (body) =>
    request("/auth/register", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  // -----------------------------
  // Repositories
  // -----------------------------

  repositories: () => request("/repositories"),

  repository: (id) => {
    if (!id) {
      throw new Error("Repository ID is required");
    }

    return request(`/repositories/${id}`);
  },

  createRepository: (body) =>
    request("/repositories", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  deleteRepository: (id) => {
    if (!id) {
      throw new Error("Repository ID is required");
    }

    return request(`/repositories/${id}`, {
      method: "DELETE",
    });
  },

  // -----------------------------
  // Repository indexing
  // -----------------------------

  indexRepository: (id) => {
    if (!id) {
      throw new Error("Repository ID is required");
    }

    return request(`/repositories/${id}/index`, {
      method: "POST",
    });
  },

  indexStatus: (id) => {
    if (!id) {
      throw new Error("Repository ID is required");
    }

    return request(`/repositories/${id}/index-status`);
  },

  // -----------------------------
  // AI features
  // -----------------------------

  explain: (id, body = {}) => {
    if (!id) {
      throw new Error("Repository ID is required");
    }

    return request(`/repositories/${id}/explain`, {
      method: "POST",
      body: JSON.stringify(body),
    });
  },

  bugs: (id, body = {}) => {
    if (!id) {
      throw new Error("Repository ID is required");
    }

    return request(`/repositories/${id}/bugs`, {
      method: "POST",
      body: JSON.stringify(body),
    });
  },

  optimize: (id, body = {}) => {
    if (!id) {
      throw new Error("Repository ID is required");
    }

    return request(`/repositories/${id}/optimize`, {
      method: "POST",
      body: JSON.stringify(body),
    });
  },

  security: (id, body = {}) => {
    if (!id) {
      throw new Error("Repository ID is required");
    }

    return request(`/repositories/${id}/security`, {
      method: "POST",
      body: JSON.stringify(body),
    });
  },

  uml: (id, body = {}) => {
    if (!id) {
      throw new Error("Repository ID is required");
    }

    return request(`/repositories/${id}/uml`, {
      method: "POST",
      body: JSON.stringify(body),
    });
  },

  tests: (id, body = {}) => {
    if (!id) {
      throw new Error("Repository ID is required");
    }

    return request(`/repositories/${id}/tests`, {
      method: "POST",
      body: JSON.stringify(body),
    });
  },

  documentation: (id, body = {}) => {
    if (!id) {
      throw new Error("Repository ID is required");
    }

    return request(`/repositories/${id}/documentation`, {
      method: "POST",
      body: JSON.stringify(body),
    });
  },

  deployment: (id, body = {}) => {
    if (!id) {
      throw new Error("Repository ID is required");
    }

    return request(`/repositories/${id}/deployment`, {
      method: "POST",
      body: JSON.stringify(body),
    });
  },

  ask: (id, body) => {
    if (!id) {
      throw new Error("Repository ID is required");
    }

    return request(`/repositories/${id}/ask`, {
      method: "POST",
      body: JSON.stringify(body),
    });
  },
};