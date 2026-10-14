import React, { useState } from "react";
import "./fraud-detection.css";

const API_BASE =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export default function FraudDetection() {
  const [claimId, setClaimId] = useState("");
  const [amount, setAmount] = useState("");
  const [treatment, setTreatment] = useState("");
  const [documents, setDocuments] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  async function analyzeClaim(event) {
    event.preventDefault();
    setError("");
    setResult(null);

    if (!claimId.trim() || !amount || !treatment.trim()) {
      setError("Enter the Claim ID, submitted amount and treatment.");
      return;
    }

    setLoading(true);

    try {
      const response = await fetch(`${API_BASE}/api/fraud/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          claim_id: claimId.trim(),
          claim_amount: Number(amount),
          treatment: treatment.trim(),
          documents: documents
            .split(",")
            .map((item) => item.trim())
            .filter(Boolean),
        }),
      });

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(
          data.detail || data.message || `Request failed (${response.status})`
        );
      }

      if (data.success === false) {
        throw new Error(data.message || data.detail || "Analysis failed.");
      }

      setResult(data);
    } catch (err) {
      setError(
        `${err.message}. Verify the backend URL and actual fraud-analysis endpoint.`
      );
    } finally {
      setLoading(false);
    }
  }

  const riskScore =
    result?.risk_score ??
    result?.fraud_score ??
    result?.risk_probability ??
    result?.probability;

  const indicators =
    result?.risk_indicators ??
    result?.indicators ??
    result?.reasons ??
    result?.flags ??
    [];

  const recommendation =
    result?.review_recommendation ??
    result?.recommendation ??
    result?.action ??
    result?.message;

  const scoreNumber =
    riskScore !== undefined && riskScore !== null && riskScore !== ""
      ? Number(riskScore)
      : null;

  const scoreIsValid =
    scoreNumber !== null && Number.isFinite(scoreNumber);

  const scorePercent =
    scoreIsValid
      ? Math.max(0, Math.min(100, scoreNumber <= 1 ? scoreNumber * 100 : scoreNumber))
      : null;

  return (
    <section className="fraud-page">
      <header className="fraud-heading">
        <div className="fraud-icon">⌁</div>
        <div>
          <p className="fraud-eyebrow">CLAIMORA · RISK REVIEW</p>
          <h2>Fraud Detection Center</h2>
          <p className="fraud-muted">
            Analyze a specific claim using the connected backend model.
          </p>
        </div>
      </header>

      <div className="fraud-steps">
        <div className="fraud-step">
          <span>01</span>
          <strong>Select claim details</strong>
          <small>Claim information and documents</small>
        </div>
        <div className="fraud-step">
          <span>02</span>
          <strong>Run analysis</strong>
          <small>Submit data to the backend</small>
        </div>
        <div className="fraud-step">
          <span>03</span>
          <strong>Review results</strong>
          <small>Risk indicators and recommendation</small>
        </div>
      </div>

      <div className="fraud-panel">
        <div className="fraud-panel-heading">
          <div>
            <h3>Claim Information</h3>
            <p className="fraud-muted">
              Enter details for the claim you want to assess.
            </p>
          </div>
          <span className="fraud-status">Claim-specific analysis</span>
        </div>

        <form className="fraud-form" onSubmit={analyzeClaim}>
          <label>
            Claim ID
            <input
              value={claimId}
              onChange={(e) => setClaimId(e.target.value)}
              placeholder="e.g. CLM-20261012-001"
              required
            />
          </label>

          <label>
            Submitted amount (₹)
            <input
              type="number"
              min="0.01"
              step="0.01"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              placeholder="Enter claim amount"
              required
            />
          </label>

          <label className="fraud-full">
            Treatment / Procedure
            <input
              value={treatment}
              onChange={(e) => setTreatment(e.target.value)}
              placeholder="e.g. Appendectomy"
              required
            />
          </label>

          <label className="fraud-full">
            Document references (optional)
            <input
              value={documents}
              onChange={(e) => setDocuments(e.target.value)}
              placeholder="Comma-separated uploaded filenames or document IDs"
            />
            <small>
              Enter references only. This field does not upload or verify files.
            </small>
          </label>

          {error && (
            <div className="fraud-error fraud-full" role="alert">
              {error}
            </div>
          )}

          <div className="fraud-actions fraud-full">
            <button
              className="fraud-submit"
              type="submit"
              disabled={loading}
            >
              {loading ? "Analyzing claim..." : "Analyze Claim for Fraud Risk"}
            </button>
          </div>
        </form>
      </div>

      {loading && (
        <div className="fraud-panel fraud-loading" role="status">
          Sending claim details to the fraud-analysis service...
        </div>
      )}

      {result && (
        <section className="fraud-results" aria-live="polite">
          <div className="fraud-panel">
            <div className="fraud-panel-heading">
              <div>
                <h3>Analysis Results</h3>
                <p className="fraud-muted">Claim ID: {claimId}</p>
              </div>
              <span className="fraud-status">Backend response received</span>
            </div>

            <div className="fraud-result-grid">
              <div className="fraud-metric">
                <span>Fraud risk score</span>
                <strong>
                  {scoreIsValid
                    ? `${scoreNumber <= 1 ? scorePercent.toFixed(1) : scoreNumber.toFixed(1)}%`
                    : "Not provided"}
                </strong>
                {scoreIsValid && (
                  <div
                    className="fraud-meter"
                    role="progressbar"
                    aria-label="Fraud risk score"
                    aria-valuemin={0}
                    aria-valuemax={100}
                    aria-valuenow={scorePercent}
                  >
                    <div style={{ width: `${scorePercent}%` }} />
                  </div>
                )}
                <small>
                  {scoreIsValid
                    ? "Score returned by the backend; confirm its scale."
                    : "The backend did not return a recognized score field."}
                </small>
              </div>

              <div className="fraud-metric">
                <span>Review recommendation</span>
                <strong className="fraud-recommendation">
                  {recommendation || "Not provided by backend"}
                </strong>
                <small>Use the returned recommendation for human review.</small>
              </div>
            </div>

            <div className="fraud-indicators">
              <h4>Risk Indicators</h4>
              {Array.isArray(indicators) && indicators.length > 0 ? (
                <ul>
                  {indicators.map((item, index) => (
                    <li key={index}>
                      {typeof item === "string"
                        ? item
                        : item?.message || item?.reason || JSON.stringify(item)}
                    </li>
                  ))}
                </ul>
              ) : typeof indicators === "string" && indicators ? (
                <p>{indicators}</p>
              ) : (
                <p className="fraud-muted">
                  No risk indicators were returned in the recognized response fields.
                </p>
              )}
            </div>

            <details className="fraud-raw">
              <summary>View raw backend response</summary>
              <pre>{JSON.stringify(result, null, 2)}</pre>
            </details>

            <p className="fraud-disclaimer">
              A model risk score is not proof of fraud. A qualified reviewer
              should verify supporting documents and claim facts before making
              a decision.
            </p>
          </div>
        </section>
      )}
    </section>
  );
}

