
import React, { useState } from "react";
import "./ClaimAssistance.css";

const API_BASE = "http://127.0.0.1:8000";

export default function ClaimAssistance() {
  const [form, setForm] = useState({
    name: "",
    email: "",
    insurer: "",
    claimType: "",
    claimAmount: "",
    treatment: "",
    description: "",
  });

  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const updateField = (event) => {
    const { name, value } = event.target;
    setForm((previous) => ({ ...previous, [name]: value }));
  };

  const handleFiles = (event) => {
    const selected = Array.from(event.target.files || []);
    const maxSize = 10 * 1024 * 1024;

    if (selected.some((file) => file.size > maxSize)) {
      setError("Each document must be 10 MB or smaller.");
      event.target.value = "";
      return;
    }

    setError("");
    setDocuments(selected);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setMessage("");
    setError("");

    if (!form.insurer || !form.claimType || !form.treatment) {
      setError("Please complete the insurer, claim type and treatment fields.");
      return;
    }

    if (documents.length === 0) {
      setError("Please select at least one supporting document.");
      return;
    }

    setLoading(true);

    try {
      // Verify the backend is reachable before connecting the
      // form to the actual claim-processing endpoint.
      const response = await fetch(`${API_BASE}/openapi.json`, {
        method: "GET",
      });

      if (!response.ok) {
        throw new Error(`Backend returned HTTP ${response.status}.`);
      }

      const schema = await response.json();
      const paths = Object.keys(schema.paths || {});

      setMessage(
        `Backend connected. Found ${paths.length} API routes. ` +
        "Your form is ready for the claim submission endpoint."
      );
    } catch (err) {
      setError(
        `Cannot connect to Claimora backend at ${API_BASE}. ` +
        "Start the FastAPI server and try again."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="claim-assistance">
      <section className="claim-hero">
        <div className="claim-hero-copy">
          <span className="claim-eyebrow">
            <span className="status-dot" />
            CLAIMORA AI WORKSPACE
          </span>

          <h1>
            Your health claim,
            <span> made simpler.</span>
          </h1>

          <p>
            Organize your claim details, prepare supporting documents
            and get ready for the next step in your insurance journey.
          </p>

          <div className="claim-benefits">
            <span>âœ“ Guided claim preparation</span>
            <span>âœ“ Document checklist workflow</span>
            <span>âœ“ Secure connection to your backend</span>
          </div>
        </div>

        <div className="claim-hero-visual" aria-hidden="true">
          <div className="orbit orbit-one" />
          <div className="orbit orbit-two" />

          <div className="shield-card">
            <div className="shield-icon">âœš</div>
            <span>CLAIM SUPPORT</span>
            <strong>One step at a time.</strong>
            <div className="shield-line" />
            <div className="shield-line short" />
            <div className="shield-footer">
              <span className="status-dot" />
              Claim preparation workspace
            </div>
          </div>

          <div className="floating-chip chip-top">AI ASSIST</div>
          <div className="floating-chip chip-bottom">DOCUMENT READY</div>
        </div>
      </section>

      <section className="claim-workspace">
        <div className="section-heading">
          <div>
            <span className="section-kicker">GET STARTED</span>
            <h2>Claim assistance</h2>
            <p>Enter your details to prepare your claim.</p>
          </div>
          <span className="step-indicator">STEP 01 / 03</span>
        </div>

        <form className="claim-form" onSubmit={handleSubmit}>
          <div className="form-section-title">
            <span className="form-number">01</span>
            <div>
              <h3>Personal information</h3>
              <p>How can we identify your request?</p>
            </div>
          </div>

          <div className="form-grid">
            <label className="field">
              Full name
              <input
                name="name"
                value={form.name}
                onChange={updateField}
                placeholder="Enter your full name"
                autoComplete="name"
                required
              />
            </label>

            <label className="field">
              Email address
              <input
                name="email"
                type="email"
                value={form.email}
                onChange={updateField}
                placeholder="you@example.com"
                autoComplete="email"
                required
              />
            </label>
          </div>

          <div className="form-section-title second-section">
            <span className="form-number">02</span>
            <div>
              <h3>Claim details</h3>
              <p>Tell us about your insurance claim.</p>
            </div>
          </div>

          <div className="form-grid">
            <label className="field">
              Insurance provider
              <select
                name="insurer"
                value={form.insurer}
                onChange={updateField}
                required
              >
                <option value="">Select insurer</option>
                <option>RK Health Insurance</option>
                <option>Star Health</option>
                <option>Care Health Insurance</option>
                <option>Niva Bupa</option>
                <option>ManipalCigna</option>
                <option>Aditya Birla Health Insurance</option>
                <option>HDFC ERGO</option>
                <option>ICICI Lombard</option>
                <option>Tata AIG</option>
                <option>Bajaj Allianz</option>
                <option>Other</option>
              </select>
            </label>

            <label className="field">
              Claim type
              <select
                name="claimType"
                value={form.claimType}
                onChange={updateField}
                required
              >
                <option value="">Select claim type</option>
                <option value="cashless">Cashless treatment</option>
                <option value="reimbursement">Reimbursement</option>
                <option value="pre_authorization">Pre-authorization</option>
              </select>
            </label>

            <label className="field">
              Treatment or procedure
              <input
                name="treatment"
                value={form.treatment}
                onChange={updateField}
                placeholder="e.g. Appendectomy"
                required
              />
            </label>

            <label className="field">
              Estimated claim amount (â‚¹)
              <input
                name="claimAmount"
                type="number"
                min="0"
                value={form.claimAmount}
                onChange={updateField}
                placeholder="e.g. 50000"
              />
            </label>

            <label className="field full-width">
              Additional details
              <textarea
                name="description"
                value={form.description}
                onChange={updateField}
                placeholder="Describe your treatment or the assistance you need..."
                rows={4}
              />
            </label>
          </div>

          <div className="form-section-title second-section">
            <span className="form-number">03</span>
            <div>
              <h3>Supporting documents</h3>
              <p>Select the documents relevant to your claim.</p>
            </div>
          </div>

          <label className="upload-zone">
            <input
              type="file"
              multiple
              accept=".pdf,.png,.jpg,.jpeg,.doc,.docx"
              onChange={handleFiles}
            />
            <span className="upload-icon">â†‘</span>
            <strong>Choose documents to upload</strong>
            <span>PDF, PNG, JPG or DOCX Â· Maximum 10 MB per file</span>
            <span className="upload-button">Browse files</span>
          </label>

          {documents.length > 0 && (
            <div className="selected-files">
              {documents.map((file, index) => (
                <div className="selected-file" key={`${file.name}-${index}`}>
                  <span className="file-icon">PDF</span>
                  <span className="file-name">{file.name}</span>
                  <span className="file-size">
                    {(file.size / (1024 * 1024)).toFixed(2)} MB
                  </span>
                </div>
              ))}
            </div>
          )}

          <div className="document-note">
            <span>â“˜</span>
            <p>
              Upload only documents you are authorized to share.
              This first step checks backend connectivity; it does not
              submit your claim or upload files to the server.
            </p>
          </div>

          {error && (
            <div className="form-alert error-alert" role="alert">
              <span>!</span>
              {error}
            </div>
          )}

          {message && (
            <div className="form-alert success-alert" role="status">
              <span>âœ“</span>
              {message}
            </div>
          )}

          <div className="form-actions">
            <span className="required-note">* Required fields</span>
            <button className="submit-claim" type="submit" disabled={loading}>
              {loading
                ? "Connecting..."
                : "Check backend connection â†’"}
            </button>
          </div>
        </form>
      </section>

      <footer className="claim-footer">
        <span className="footer-brand">CLAIMORA</span>
        <span>Smart Claim Assistance</span>
        <span>AI-assisted guidance Â· Final decisions remain with the insurer</span>
      </footer>
    </main>
  );
}

