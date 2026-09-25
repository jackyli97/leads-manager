"use client";

import { FormEvent, useState } from "react";
import { ArrowLeft, ArrowRight, CheckCircle2, FileText, Scale } from "lucide-react";
import Link from "next/link";

import { getErrorMessage } from "@/lib/api";

export default function IntakePage() {
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setSubmitting(true);

    const form = new FormData(event.currentTarget);
    const requestBody = new FormData();
    requestBody.append("first_name", String(form.get("firstName")));
    requestBody.append("last_name", String(form.get("lastName")));
    requestBody.append("email", String(form.get("email")));
    requestBody.append("resume", form.get("resume") as File);

    try {
      const response = await fetch("/api/leads", {
        method: "POST",
        body: requestBody,
      });

      if (!response.ok) throw new Error(await getErrorMessage(response));
      setSubmitted(true);
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "Something went wrong.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="intake-shell">
      <header className="public-header">
        <Link className="brand brand-dark" href="/">
          <span className="brand-mark"><Scale size={20} strokeWidth={2} /></span>
          <span>Counsel Desk</span>
        </Link>
        <Link className="back-link" href="/"><ArrowLeft size={16} /> Attorney login</Link>
      </header>

      <section className="intake-layout">
        <div className="intake-intro">
          <p className="eyebrow">Prospective clients</p>
          <h1>Tell us who you are.</h1>
          <p>Share your contact details and resume with our legal team for review.</p>
          <div className="intake-detail">
            <FileText size={21} />
            <span>Your submission will be routed to an available attorney.</span>
          </div>
        </div>

        <div className="intake-card">
          {submitted ? (
            <div className="success-state" role="status">
              <span className="success-icon"><CheckCircle2 size={30} /></span>
              <p className="eyebrow">Submission received</p>
              <h2>Thank you for reaching out.</h2>
              <p>Your information has been sent to the attorney team for review.</p>
              <button className="secondary-button" type="button" onClick={() => setSubmitted(false)}>
                Submit another inquiry
              </button>
            </div>
          ) : (
            <>
              <div className="form-heading intake-heading">
                <p className="eyebrow">Client intake</p>
                <h2>Submit your information</h2>
              </div>

              <form onSubmit={handleSubmit}>
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
                <label>
                  Email address
                  <input name="email" type="email" autoComplete="email" required />
                </label>
                <label>
                  Resume or CV
                  <input
                    name="resume"
                    type="file"
                    accept="application/pdf,.pdf"
                    required
                  />
                </label>

                {error && <p className="form-error" role="alert">{error}</p>}

                <button className="primary-button" type="submit" disabled={submitting}>
                  <span>{submitting ? "Submitting..." : "Submit inquiry"}</span>
                  {!submitting && <ArrowRight size={18} />}
                </button>
              </form>
            </>
          )}
        </div>
      </section>
    </main>
  );
}
