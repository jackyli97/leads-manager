"use client";

import { FormEvent, useEffect, useState } from "react";
import { ArrowRight, BriefcaseBusiness, CheckCircle2, LogOut, Scale } from "lucide-react";

type Mode = "login" | "signup";

type User = {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
  role: "attorney";
};

type ApiError = { detail?: string | Array<{ msg: string }> };

const TOKEN_KEY = "counsel_desk_access_token";

async function getErrorMessage(response: Response) {
  const data = (await response.json().catch(() => ({}))) as ApiError;
  if (typeof data.detail === "string") return data.detail;
  if (Array.isArray(data.detail)) return data.detail[0]?.msg ?? "Please check your details.";
  return "Something went wrong. Please try again.";
}

export default function Home() {
  const [mode, setMode] = useState<Mode>("login");
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    async function restoreSession() {
      const token = window.localStorage.getItem(TOKEN_KEY);
      if (!token) {
        setLoading(false);
        return;
      }

      try {
        const response = await fetch("/api/auth/me", {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!response.ok) throw new Error("Session expired");
        setUser((await response.json()) as User);
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

      const meResponse = await fetch("/api/auth/me", {
        headers: { Authorization: `Bearer ${access_token}` },
      });
      if (!meResponse.ok) throw new Error(await getErrorMessage(meResponse));
      setUser((await meResponse.json()) as User);
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "Something went wrong.");
    } finally {
      setSubmitting(false);
    }
  }

  function logout() {
    window.localStorage.removeItem(TOKEN_KEY);
    setUser(null);
    setMode("login");
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
          <h1>Welcome, {user.first_name} {user.last_name}</h1>
          <p className="portal-copy">
            Your workspace is ready. New prospective clients and case activity will appear here.
          </p>
          <div className="empty-state">
            <BriefcaseBusiness size={24} />
            <div>
              <strong>No active leads yet</strong>
              <span>Submitted leads will be organized in this workspace.</span>
            </div>
          </div>
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
        </div>
      </section>
    </main>
  );
}
