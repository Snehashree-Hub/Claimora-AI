import React, { useState } from "react";

const API_BASE =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export default function FraudAnalysisPanel() {
  const [claimId, setClaimId] = useState("");
  const [amount, setAmount] = useState("");
  const [treatment, setTreatment] = useState("");
  const [documents, setDocuments] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function analyzeClaim(event) {
    event.preventDefault();
    setResult(null);
    setError("");

    if (!claimId.trim() || !amount || !treatment.trim()) {
      setError("Enter the Claim ID, submitted amount and treatment.");
      return;
    }

    setLoading(true);

    try {
      // Confirm this route and payload against your active FastAPI endpoint.
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
          data.detail || `Fraud analysis request failed (${response.status}).`
        );
      }

      setResult(data);
    } catch (err) {
      setError(
        err.message ||
          "Could not connect to the fraud analysis service."
      );
    } finally {
      setLoading(false);
    }
  }

  async function testService() {
    setError("");
    setResult(null);
    setLoading(true);

    try {
      const response = await fetch(`${API_BASE}/api/fraud/test`);
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Service health test failed.");
      }

      setResult({ service_health_test: true, ...data });
    } catch (err) {
      setError(err.message || "Could not test the fraud service.");
    } finally {
      setLoading(false);
    }
  }

  const riskScore =
    result?.risk_score ??
    result?.fraud_score ??
    result?.score ??
    result?.risk_probability;

  const indicators =
    result?.risk_indicators ??
    result?.indicators ??
    result?.reasons ??
    result?.flags;

  const recommendation =
    result?.review_recommendation ??
    result?.recommendation ??
    result?.message;

  return (
    <section className="fraud-panel">
      <div className="fraud-heading">
        <div>
          <p className="fraud-eyebrow">CLAIMORA SECURITY</p>
          <h2>Fraud Detection Center</h2>
          <p className="fraud-muted">
            Analyze claim-specific information using the connected backend.
          </p>
        </div>
        <div className="fraud-icon" aria-hidden="true">🛡️</div>
      </div>

      <div className="fraud-steps">
        <div><span>01</span><strong>Select Claim</strong></div>
        <div><span>02</span><strong>Run Analysis</strong></div>
        <div><span>03</span><strong>Review Results</strong></div>
      </div>

      <form className="fraud-form" onSubmit={analyzeClaim}>
        <div className="fraud-field">
          <label htmlFor="fraud-claim-id">Claim ID</label>
          <input
            id="fraud-claim-id"
            value={claimId}
            onChange={(e) => setClaimId(e.target.value)}
            placeholder="Enter an existing Claim ID"
            required
          />
        </div>

        <div className="fraud-field">
          <label htmlFor="fraud-amount">Submitted Amount (₹)</label>
          <input
            id="fraud-amount"
            type="number"
            min="0"
            step="0.01"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            placeholder="e.g. 25000"
            required
          />
        </div>

        <div className="fraud-field">
          <label htmlFor="fraud-treatment">Treatment / Procedure</label>
          <input
            id="fraud-treatment"
            value={treatment}
            onChange={(e) => setTreatment(e.target.value)}
            placeholder="Enter the actual treatment"
            required
          />
        </div>

        <div className="fraud-field fraud-field-full">
          <label htmlFor="fraud-documents">
            Available Document Names (optional)
          </label>
          <input
            id="fraud-documents"
            value={documents}
            onChange={(e) => setDocuments(e.target.value)}
            placeholder="bill.pdf, discharge_summary.pdf"
          />
          <small>Enter filenames separated by commas.</small>
        </div>

        <div className="fraud-actions">
          <button
            className="fraud-primary"
            type="submit"
            disabled={loading}
          >
            {loading ? "Analyzing..." : "Analyze Claim for Fraud Risk"}
          </button>

          <button
            className="fraud-secondary"
            type="button"
            onClick={testService}
            disabled={loading}
          >
            Test Fraud Detection Service
          </button>
        </div>
      </form>

      {error && (
        <div className="fraud-error" role="alert">
          <strong>Request failed</strong>
          <p>{error}</p>
        </div>
      )}

      {result && (
        <div className="fraud-results" aria-live="polite">
          <h3>
            {result.service_health_test
              ? "Service Health"
              : "Analysis Response"}
          </h3>

          {result.service_health_test ? (
            <p>
              The health endpoint responded. This does not analyze an
              individual claim.
            </p>
          ) : (
            <>
              {riskScore !== undefined && riskScore !== null && (
                <div className="fraud-result-metric">
                  <span>Backend Risk Score</span>
                  <strong>
                    {typeof riskScore === "number"
                      ? `${(riskScore <= 1 ? riskScore * 100 : riskScore).toFixed(1)}%`
                      : String(riskScore)}
                  </strong>
                </div>
              )}

              {indicators && (
                <div className="fraud-result-block">
                  <strong>Risk Indicators</strong>
                  {Array.isArray(indicators) ? (
                    <ul>
                      {indicators.map((item, index) => (
                        <li key={index}>
                          {typeof item === "string"
                            ? item
                            : JSON.stringify(item)}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p>{String(indicators)}</p>
                  )}
                </div>
              )}

              {recommendation && (
                <div className="fraud-result-block">
                  <strong>Review Recommendation</strong>
                  <p>
                    {typeof recommendation === "string"
                      ? recommendation
                      : JSON.stringify(recommendation)}
                  </p>
                </div>
              )}

              <p className="fraud-muted">
                Only fields returned by the backend are displayed. A risk
                prediction is not proof of fraud; human review is required.
              </p>
            </>
          )}

          <details>
            <summary>View raw backend response</summary>
            <pre>{JSON.stringify(result, null, 2)}</pre>
          </details>
        </div>
      )}
    </section>
  );
}

