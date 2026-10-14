
import { useState } from "react";
import "./ClaimTracking.css";

const API_BASE = "http://127.0.0.1:8000";

const STATUS_FIELDS = [
  ["Eligibility", "eligibility_status"],
  ["Documents", "document_status"],
  ["Fraud screening", "fraud_risk"],
  ["Assessment", "assessment_status"],
  ["Email notification", "email_status"],
];

function formatAmount(value) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(Number(value || 0));
}

export default function ClaimTracking() {
  const [claimId, setClaimId] = useState("");
  const [claim, setClaim] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function searchClaim(event) {
    event.preventDefault();

    const id = claimId.trim();
    if (!id) {
      setError("Enter a claim number to continue.");
      return;
    }

    setLoading(true);
    setError("");
    setClaim(null);

    try {
      const response = await fetch(`${API_BASE}/api/demo-claims/`);

      if (!response.ok) {
        throw new Error(`Backend returned HTTP ${response.status}`);
      }

      const payload = await response.json();

      // Supports either a direct list or a wrapped list response.
      const records = Array.isArray(payload)
        ? payload
        : payload.claims || payload.items || payload.data || [];

      const found = records.find((item) =>
        [item.claim_number, item.id]
          .filter(Boolean)
          .some((value) => String(value).toLowerCase() === id.toLowerCase())
      );

      if (!found) {
        setError(
          "No matching demo claim was found. Check the claim number and try again."
        );
        return;
      }

      setClaim(found);
    } catch (err) {
      setError(
        `${err.message}. Check that the Claimora backend is running on port 8001.`
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="tracking-page">
      <section className="tracking-hero">
        <span className="tracking-eyebrow">CLAIMORA Â· CLAIM SERVICES</span>
        <h1>Claim Tracking</h1>
        <p>
          Check the available claim details and review the latest recorded
          processing statuses.
        </p>
      </section>

      <section className="tracking-search-card">
        <form onSubmit={searchClaim}>
          <label htmlFor="claim-number">Claim number or demo ID</label>
          <div className="tracking-search-row">
            <input
              id="claim-number"
              value={claimId}
              onChange={(event) => setClaimId(event.target.value)}
              placeholder="e.g. DEMO-CLM-025"
              autoComplete="off"
            />
            <button type="submit" disabled={loading}>
              {loading ? "Searching..." : "Track Claim"}
            </button>
          </div>
          <small>Demo example: DEMO-CLM-025</small>
        </form>

        {error && <div className="tracking-error">{error}</div>}
      </section>

      {claim && (
        <section className="tracking-results">
          {claim.demo === true && (
            <div className="tracking-demo-warning">
              <strong>DEMO RECORD</strong>
              <span>
                Illustrative sample data only. This is not a real insurance
                claim or an insurer-confirmed decision.
              </span>
            </div>
          )}

          <div className="tracking-claim-heading">
            <div>
              <span className="tracking-muted">CLAIM NUMBER</span>
              <h2>{claim.claim_number || claim.id}</h2>
              <p>{claim.patient_name || "Patient name unavailable"}</p>
            </div>
            <span className="tracking-status-pill">
              {claim.overall_status || "Status unavailable"}
            </span>
          </div>

          <div className="tracking-info-grid">
            <article className="tracking-info-card">
              <span>Insurance provider</span>
              <strong>{claim.insurance_company || "Not available"}</strong>
            </article>
            <article className="tracking-info-card">
              <span>Claim amount</span>
              <strong>{formatAmount(claim.claim_amount)}</strong>
            </article>
            <article className="tracking-info-card">
              <span>Treatment</span>
              <strong>{claim.treatment || "Not available"}</strong>
            </article>
            <article className="tracking-info-card">
              <span>Policy number</span>
              <strong>{claim.policy_number || "Not available"}</strong>
            </article>
            <article className="tracking-info-card">
              <span>Hospital</span>
              <strong>{claim.hospital_name || "Not available"}</strong>
            </article>
            <article className="tracking-info-card">
              <span>Eligibility</span>
              <strong>{claim.eligibility_status || "Not available"}</strong>
            </article>
          </div>

          <div className="tracking-workflow">
            <div className="tracking-section-heading">
              <div>
                <span className="tracking-muted">PROCESS OVERVIEW</span>
                <h2>Recorded status details</h2>
              </div>
            </div>

            {STATUS_FIELDS.map(([label, key]) => (
              <div className="tracking-stage" key={key}>
                <span className="tracking-stage-dot" />
                <div className="tracking-stage-content">
                  <strong>{label}</strong>
                  <span>{claim[key] || "Not reported"}</span>
                </div>
              </div>
            ))}

            {claim.remarks && (
              <p className="tracking-remarks">{claim.remarks}</p>
            )}
          </div>

          <p className="tracking-disclaimer">
            The information above reflects the returned API record. A pending
            status is not an approval or rejection, and this page does not
            confirm payment or insurer decisions.
          </p>
        </section>
      )}
    </main>
  );
}


