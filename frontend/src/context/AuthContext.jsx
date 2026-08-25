import React, { createContext, useContext, useMemo, useState } from "react";
import { api } from "../services/api.js";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem("accessToken"));

  const login = async (credentials) => {
    const data = await api.login(credentials);
    localStorage.setItem("accessToken", data.token);
    if (data.user) localStorage.setItem("currentUser", JSON.stringify(data.user));
    setToken(data.token);
    return data;
  };

  const register = (details) => api.register(details);

  const logout = () => {
    localStorage.removeItem("accessToken");
    localStorage.removeItem("currentUser");
    setToken(null);
  };

  const user = (() => {
    try { return JSON.parse(localStorage.getItem("currentUser") || "null"); }
    catch { return null; }
  })();

  const value = useMemo(() => ({ token, isAuthenticated: Boolean(token), user, login, register, logout }), [token, user]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside AuthProvider");
  return context;
}