import React, { useState } from "react";
import { NavLink, useLocation } from "react-router-dom";
import { Code2, LayoutDashboard, FolderGit2, LogOut, Menu, X } from "lucide-react";
import { useAuth } from "../../context/AuthContext.jsx";

export default function AppLayout({ children }) {
  const [open, setOpen] = useState(false);
  const { user, logout } = useAuth();
  const location = useLocation();

  return (
    <div className="app">
      <aside className={`sidebar ${open ? "open" : ""}`}>
        <div className="brand">
          <div className="brand-mark"><Code2 size={19} /></div>
          <div><div className="brand-name">CodePilot</div><span className="brand-sub">Engineering Copilot</span></div>
        </div>
        <div className="nav-label">Workspace</div>
        <nav className="nav">
          <NavLink to="/" end onClick={() => setOpen(false)}><LayoutDashboard size={17}/>Dashboard</NavLink>
          <NavLink to="/repositories" onClick={() => setOpen(false)}><FolderGit2 size={17}/>Repositories</NavLink>
        </nav>
        <div className="sidebar-bottom">
          <button onClick={logout} style={{width:"100%",background:"transparent",border:0,padding:0}}>
            <span style={{display:"flex",alignItems:"center",gap:11,color:"#9da7b6",padding:"10px 11px",fontSize:14}}><LogOut size={17}/>Sign out</span>
          </button>
          <div className="user-mini">
            <div className="avatar">{(user?.name || "U").slice(0,1).toUpperCase()}</div>
            <div style={{minWidth:0}}><div className="user-name">{user?.name || "Developer"}</div><div className="user-email">{user?.email || "Local workspace"}</div></div>
          </div>
        </div>
      </aside>
      <main className="main">
        <header className="topbar">
          <button className="icon-btn mobile-menu" onClick={() => setOpen(!open)} aria-label="Toggle navigation">{open ? <X size={18}/> : <Menu size={18}/>}</button>
          <div className="page-title">{location.pathname.startsWith("/repositories") ? "Repositories" : "Overview"}</div>
          <div className="top-actions"><div className="avatar">{(user?.name || "U").slice(0,1).toUpperCase()}</div></div>
        </header>
        {children}
      </main>
    </div>
  );
}