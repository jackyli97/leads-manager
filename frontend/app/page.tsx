"use client";

import { FormEvent, useEffect, useState } from "react";
import { ArrowRight, BriefcaseBusiness, CheckCircle2, FileText, LogOut, RotateCcw, Scale } from "lucide-react";
import Link from "next/link";

import { getErrorMessage } from "@/lib/api";

type Mode = "login" | "signup";

type User = {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
  role: "attorney";
};

type Lead = {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
  resume_url: string;
  assigned_attorney_id: number | null;
  status: "pending" | "reached_out";
};

const TOKEN_KEY = "counsel_desk_access_token";

export default function Home() {
  const [mode, setMode] = useState<Mode>("login");
  const [user, setUser] = useState<User | null>(null);
  const [leads, setLeads] = useState<Lead[]>([]);
  const [portalError, setPortalError] = useState("");
  const [updatingLeadId, setUpdatingLeadId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  async function loadPortal(token: string) {
    const headers = { Authorization: `Bearer ${token}` };
    const profileResponse = await fetch("/api/auth/me", { headers });
    if (!profileResponse.ok) throw new Error("Session expired");
    setUser((await profileResponse.json()) as User);

    const leadsResponse = await fetch("/api/leads", { headers });
    if (!leadsResponse.ok) {
      setPortalError(await getErrorMessage(leadsResponse));
      return;
    }
    setLeads((await leadsResponse.json()) as Lead[]);
    setPortalError("");
  }

  useEffect(() => {
    async function restoreSession() {
      const token = window.localStorage.getItem(TOKEN_KEY);
      if (!token) {
        setLoading(false);
        return;
      }

      try {
        await loadPortal(token);
      } catch {
        window.localStorage.removeItem(TOKEN_KEY);
      } finally {
        setLoading(false);
      }
    }

    void restoreSession();
  }, []);

  function changeMode(nextMode: Mode) {
    setMode(nextMode);
    setError("");
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setSubmitting(true);

    const form = new FormData(event.currentTarget);
    const email = String(form.get("email"));
    const password = String(form.get("password"));

    try {
      if (mode === "signup") {
        const signupResponse = await fetch("/api/auth/signup", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            first_name: form.get("firstName"),
            last_name: form.get("lastName"),
            email,
            password,
          }),
        });
        if (!signupResponse.ok) throw new Error(await getErrorMessage(signupResponse));
      }

      const loginResponse = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      if (!loginResponse.ok) throw new Error(await getErrorMessage(loginResponse));

      const { access_token } = (await loginResponse.json()) as { access_token: string };
      window.localStorage.setItem(TOKEN_KEY, access_token);

      await loadPortal(access_token);
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "Something went wrong.");
    } finally {
      setSubmitting(false);
    }
  }

  function logout() {
    window.localStorage.removeItem(TOKEN_KEY);
    setUser(null);
    setLeads([]);
    setPortalError("");
    setMode("login");
  }

  async function updateLeadStatus(leadId: number, status: Lead["status"]) {
    const token = window.localStorage.getItem(TOKEN_KEY);
    if (!token) {
      logout();
      return;
    }

    setUpdatingLeadId(leadId);
    setPortalError("");
    try {
      const response = await fetch(`/api/leads/${leadId}/status`, {
        method: "PATCH",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ status }),
      });
      if (!response.ok) throw new Error(await getErrorMessage(response));

      const updatedLead = (await response.json()) as Lead;
      setLeads((currentLeads) =>
        currentLeads.map((lead) => lead.id === updatedLead.id ? updatedLead : lead),
      );
    } catch (caughtError) {
      setPortalError(
        caughtError instanceof Error ? caughtError.message : "Could not update the lead.",
      );
    } finally {
      setUpdatingLeadId(null);
    }
  }

  if (loading) {
    return <main className="loading-screen" aria-label="Loading" />;
  }

  if (user) {
    return (
      <main className="portal-shell">
        <header className="portal-header">
          <div className="brand brand-dark">
            <span className="brand-mark"><Scale size={20} strokeWidth={2} /></span>
            <span>Counsel Desk</span>
          </div>
          <button className="icon-button" type="button" onClick={logout} aria-label="Log out" title="Log out">
            <LogOut size={19} />
          </button>
        </header>

        <section className="portal-content">
          <div className="portal-kicker"><CheckCircle2 size={18} /> Signed in</div>
          <p className="eyebrow">Attorney portal</p>
          <h1>Lead pipeline</h1>
          <p className="portal-copy">
            Welcome, {user.first_name} {user.last_name}. Review prospective clients and their submitted materials.
          </p>

          <section className="leads-section" aria-labelledby="leads-heading">
            <div className="leads-heading">
              <div>
                <h2 id="leads-heading">Prospective clients</h2>
                <span>{leads.length} {leads.length === 1 ? "lead" : "leads"}</span>
              </div>
            </div>

            {portalError ? (
              <p className="portal-error" role="alert">{portalError}</p>
            ) : leads.length === 0 ? (
              <div className="empty-state">
                <BriefcaseBusiness size={24} />
                <div>
                  <strong>No active leads yet</strong>
                  <span>Submitted leads will be organized in this workspace.</span>
                </div>
              </div>
            ) : (
              <div className="leads-table-wrap">
                <table className="leads-table">
                  <thead>
                    <tr>
                      <th scope="col">Prospect</th>
                      <th scope="col">Status</th>
                      <th scope="col">Assignment</th>
                      <th scope="col"><span className="sr-only">Resume</span></th>
                    </tr>
                  </thead>
                  <tbody>
                    {leads.map((lead) => (
                      <tr key={lead.id}>
                        <td>
                          <strong>{lead.first_name} {lead.last_name}</strong>
                          <a href={`mailto:${lead.email}`}>{lead.email}</a>
                        </td>
                        <td>
                          <div className="status-cell">
                            <span className={`status-badge status-${lead.status}`}>{lead.status.replace("_", " ")}</span>
                            <button
                              className="status-action"
                              type="button"
                              disabled={updatingLeadId === lead.id}
                              onClick={() => updateLeadStatus(
                                lead.id,
                                lead.status === "pending" ? "reached_out" : "pending",
                              )}
                            >
                              {lead.status === "pending"
                                ? <CheckCircle2 size={15} />
                                : <RotateCcw size={15} />}
                              {updatingLeadId === lead.id
                                ? "Saving..."
                                : lead.status === "pending"
                                  ? "Mark reached out"
                                  : "Move to pending"}
                            </button>
                          </div>
                        </td>
                        <td>
                          {lead.assigned_attorney_id === user.id
                            ? "Assigned to you"
                            : lead.assigned_attorney_id
                              ? `Attorney #${lead.assigned_attorney_id}`
                              : "Unassigned"}
                        </td>
                        <td>
                          <a className="resume-link" href={lead.resume_url} target="_blank" rel="noreferrer">
                            <FileText size={17} /> Resume
                          </a>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </section>
      </main>
    );
  }

  return (
    <main className="auth-shell">
      <section className="intro-panel">
        <div className="brand">
          <span className="brand-mark"><Scale size={20} strokeWidth={2} /></span>
          <span>Counsel Desk</span>
        </div>
        <div className="intro-copy">
          <p className="eyebrow">Legal intake, made clear</p>
          <h1>Your client pipeline starts here.</h1>
          <p>A focused workspace for attorneys to review prospective clients and move each matter forward.</p>
        </div>
        <p className="intro-footer">Private access for your legal team</p>
      </section>

      <section className="form-panel">
        <div className="auth-card">
          <div className="mode-switch" role="tablist" aria-label="Authentication mode">
            <button
              type="button"
              role="tab"
              aria-selected={mode === "login"}
              className={mode === "login" ? "active" : ""}
              onClick={() => changeMode("login")}
            >
              Log in
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={mode === "signup"}
              className={mode === "signup" ? "active" : ""}
              onClick={() => changeMode("signup")}
            >
              Sign up
            </button>
          </div>

          <div className="form-heading">
            <p className="eyebrow">{mode === "login" ? "Welcome back" : "Create your account"}</p>
            <h2>{mode === "login" ? "Sign in to your portal" : "Join your attorney workspace"}</h2>
          </div>

          <form onSubmit={handleSubmit}>
            {mode === "signup" && (
              <div className="name-grid">
                <label>
                  First name
                  <input name="firstName" type="text" autoComplete="given-name" required maxLength={100} />
                </label>
                <label>
                  Last name
                  <input name="lastName" type="text" autoComplete="family-name" required maxLength={100} />
                </label>
              </div>
            )}
            <label>
              Email address
              <input name="email" type="email" autoComplete="email" required />
            </label>
            <label>
              Password
              <input
                name="password"
                type="password"
                autoComplete={mode === "login" ? "current-password" : "new-password"}
                minLength={8}
                required
              />
            </label>

            {error && <p className="form-error" role="alert">{error}</p>}

            <button className="primary-button" type="submit" disabled={submitting}>
              <span>{submitting ? "Please wait..." : mode === "login" ? "Log in" : "Create account"}</span>
              {!submitting && <ArrowRight size={18} />}
            </button>
          </form>

          <p className="form-note">Accounts are currently available to attorneys only.</p>
          <div className="client-entry">
            <span>Looking for legal assistance?</span>
            <Link href="/intake">Submit an inquiry <ArrowRight size={15} /></Link>
          </div>
        </div>
      </section>
    </main>
  );
}
