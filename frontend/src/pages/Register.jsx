import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Code2 } from "lucide-react";
import { useAuth } from "../context/AuthContext.jsx";

export default function Register() {
  const { register, login } = useAuth(), navigate = useNavigate();
  const [form,setForm]=useState({name:"",email:"",password:""}),[error,setError]=useState(""),[loading,setLoading]=useState(false);
  const submit=async(e)=>{e.preventDefault();setError("");setLoading(true);try{await register(form);await login({email:form.email,password:form.password});navigate("/",{replace:true})}catch(err){setError(err.message)}finally{setLoading(false)}};
  return <div className="login-page"><div className="card auth-card">
    <div className="brand auth-logo" style={{padding:0}}><div className="brand-mark"><Code2 size={19}/></div><div><div className="brand-name">CodePilot</div><span className="brand-sub">Engineering Copilot</span></div></div>
    <div className="eyebrow">Get started</div><h1>Create your workspace</h1><p className="subtitle">Connect repositories and start understanding your code with AI.</p>
    <form className="auth-form" onSubmit={submit}>
      <div className="form-group"><label className="label">Name</label><input className="input" required value={form.name} onChange={e=>setForm({...form,name:e.target.value})} placeholder="Your name"/></div>
      <div className="form-group"><label className="label">Email</label><input className="input" type="email" required value={form.email} onChange={e=>setForm({...form,email:e.target.value})} placeholder="you@example.com"/></div>
      <div className="form-group"><label className="label">Password</label><input className="input" type="password" minLength={6} required value={form.password} onChange={e=>setForm({...form,password:e.target.value})} placeholder="At least 6 characters"/></div>
      {error&&<div className="error">{error}</div>}<button className="btn btn-primary" disabled={loading} style={{width:"100%",marginTop:8}}>{loading?"Creating...":"Create account"}</button>
    </form><div className="auth-footer">Already have an account? <Link to="/login">Sign in</Link></div>
  </div></div>;
}