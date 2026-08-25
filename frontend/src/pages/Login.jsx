import React, { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { Code2 } from "lucide-react";
import { useAuth } from "../context/AuthContext.jsx";

export default function Login() {
  const { login } = useAuth(), navigate = useNavigate(), location = useLocation();
  const [form,setForm]=useState({email:"",password:""}),[error,setError]=useState(""),[loading,setLoading]=useState(false);
  const submit=async(e)=>{e.preventDefault();setError("");setLoading(true);try{await login(form);navigate(location.state?.from||"/",{replace:true})}catch(err){setError(err.message)}finally{setLoading(false)}};
  return <div className="login-page"><div className="card auth-card">
    <div className="brand auth-logo" style={{padding:0}}><div className="brand-mark"><Code2 size={19}/></div><div><div className="brand-name">CodePilot</div><span className="brand-sub">Engineering Copilot</span></div></div>
    <div className="eyebrow">Welcome back</div><h1>Sign in to your workspace</h1><p className="subtitle">Review repositories, run AI analysis, and understand your codebase.</p>
    <form className="auth-form" onSubmit={submit}>
      <div className="form-group"><label className="label">Email</label><input className="input" type="email" required value={form.email} onChange={e=>setForm({...form,email:e.target.value})} placeholder="you@example.com"/></div>
      <div className="form-group"><label className="label">Password</label><input className="input" type="password" required value={form.password} onChange={e=>setForm({...form,password:e.target.value})} placeholder="••••••••"/></div>
      {error&&<div className="error">{error}</div>}<button className="btn btn-primary" disabled={loading} style={{width:"100%",marginTop:8}}>{loading?"Signing in...":"Sign in"}</button>
    </form><div className="auth-footer">Don't have an account? <Link to="/register">Create one</Link></div>
  </div></div>;
}