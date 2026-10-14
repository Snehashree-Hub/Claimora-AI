import React, { useCallback, useEffect, useState } from "react";
import FindCareDirectory from "./components/FindCare.jsx";
import "./styles/ClaimReadinessReport.css";

/* =========================================================
   CLAIMORA — AI AGENT FOR HEALTH INSURANCE CLAIM ASSISTANCE
   Theme: Midnight Espresso · Warm Cream · Coral · Peach
   Backend: FastAPI on http://127.0.0.1:8000
   ========================================================= */

const API_BASE = (
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000"
).replace(/\/+$/, "");

const T = {
  bg: "#1F1410",
  surface: "#2B1D18",
  elevated: "#3A2620",
  text: "#FAF3E8",
  muted: "#B8A99A",
  coral: "#E06464",
  peach: "#FBC3B9",
  border: "rgba(250,243,232,.12)",
};

const NAV_ITEMS = [
  { id: "home", icon: "⌂", label: "Home" },
  { id: "claim", icon: "＋", label: "New Claim" },
  { id: "assistant", icon: "✧", label: "AI Assistant" },
  { id: "care", icon: "✚", label: "Find Care" },
  { id: "documents", icon: "▤", label: "Documents" },
  { id: "tracking", icon: "◎", label: "Claim Status" },
  { id: "security", icon: "⬡", label: "Security" },
];

const INSURERS = [
  "RK Health Insurance",
  "Star Health",
  "Care Health",
  "Niva Bupa",
  "ManipalCigna",
  "Aditya Birla Health",
  "HDFC ERGO",
  "ICICI Lombard",
  "Tata AIG",
  "Bajaj Allianz",
];

const TREATMENTS = [
  "Appendectomy",
  "Kidney Stone",
  "Hernia Repair",
  "Gallbladder Surgery",
  "Thyroid Surgery",
  "Sinus Surgery",
  "Emergency Care",
  "General Surgery",
  "Cardiac Evaluation",
  "Cataract Surgery",
  "Orthopaedic Treatment",
  "Maternity Care",
];

const CITIES = ["Chennai", "Bengaluru", "Hyderabad", "Mumbai", "Delhi"];

/* ---------- API HELPER ---------- */
async function apiRequest(path, options = {}) {
  const isForm =
    typeof FormData !== "undefined" && options.body instanceof FormData;

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      ...(isForm ? {} : { "Content-Type": "application/json" }),
      ...options.headers,
    },
  });

  const raw = await response.text();
  let data = {};

  try {
    data = raw ? JSON.parse(raw) : {};
  } catch {
    data = { detail: raw };
  }

  if (!response.ok) {
    const detail = data?.detail || data?.message;
    throw new Error(
      typeof detail === "string"
        ? detail
        : detail
          ? JSON.stringify(detail)
          : `Request failed (${response.status})`
    );
  }

  return data;
}

/* ---------- SMALL COMPONENTS ---------- */
function Button({ children, onClick, variant = "primary", disabled = false, type = "button" }) {
  return (
    <button
      type={type}
      className={`button button-${variant}`}
      onClick={onClick}
      disabled={disabled}
    >
      {children}
    </button>
  );
}

function Field({ label, children, hint }) {
  return (
    <label className="field">
      <span className="field-label">{label}</span>
      {children}
      {hint && <span className="field-hint">{hint}</span>}
    </label>
  );
}

function Input(props) {
  return <input className="input" {...props} />;
}

function Select({ children, ...props }) {
  return (
    <select className="input" {...props}>
      {children}
    </select>
  );
}

function Panel({ title, subtitle, action, children }) {
  return (
    <section className="panel">
      {(title || subtitle || action) && (
        <div className="panel-heading">
          <div>
            {title && <h2>{title}</h2>}
            {subtitle && <p>{subtitle}</p>}
          </div>
          {action}
        </div>
      )}
      {children}
    </section>
  );
}

function Message({ message, type = "info" }) {
  if (!message) return null;
  return <div className={`message message-${type}`}>{message}</div>;
}

function ClaimRecordView({ data }) {
  const value = (item) => {
    if (item === null || item === undefined || item === "") {
      return "Not provided";
    }

    if (typeof item === "object") {
      return JSON.stringify(item);
    }

    return String(item);
  };

  const amount = Number(data?.claim_amount);
  const hasAmount =
    data?.claim_amount !== null &&
    data?.claim_amount !== undefined &&
    data?.claim_amount !== "" &&
    Number.isFinite(amount);

  const money = hasAmount
    ? new Intl.NumberFormat("en-IN", {
        style: "currency",
        currency: "INR",
        maximumFractionDigits: 2,
      }).format(amount)
    : "Not provided";

  const fields = [
    ["Patient name", data?.patient_name],
    ["Patient age", data?.patient_age],
    ["Insurance company", data?.insurance_company],
    ["Claim amount", money],
    ["Diagnosis / treatment", data?.diagnosis],
    ["Hospital", data?.hospital_name],
    ["Doctor", data?.doctor_name],
    ["Treatment date", data?.treatment_date],
    ["Submitted on", data?.created_at],
    ["Eligibility status", data?.eligibility_status],
    ["Document status", data?.document_status],
    ["Fraud risk", data?.fraud_risk],
    ["Email status", data?.email_status],
  ];

  const status = value(data?.status || data?.overall_status);
  const claimId = data?.claim_id || data?.id || data?.claim_number;
  const policyId = data?.policy_id || data?.policy_number;
  const documents = data?.documents;

  return (
    <section
      className="claim-record-view"
      style={{
        display: "grid",
        gap: 20,
        color: "#FAF3E8",
      }}
    >
      <header
        style={{
          padding: 24,
          borderRadius: 20,
          background: "linear-gradient(135deg, #2B1D18, #3A2620)",
          border: "1px solid rgba(250,243,232,0.12)",
        }}
      >
        <p
          style={{
            margin: "0 0 8px",
            color: "#FBC3B9",
            fontSize: 12,
            fontWeight: 800,
            letterSpacing: "0.13em",
          }}
        >
          CLAIMORA · CLAIM TRACKING
        </p>

        <h2 style={{ margin: "0 0 14px", fontSize: 24 }}>
          Saved Claim Record
        </h2>

        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            gap: 12,
            alignItems: "center",
          }}
        >
          <span
            style={{
              padding: "8px 12px",
              borderRadius: 999,
              background: "rgba(224,100,100,0.15)",
              border: "1px solid rgba(224,100,100,0.45)",
              color: "#FBC3B9",
              fontWeight: 700,
            }}
          >
            {status}
          </span>

          <span style={{ color: "#B8A99A", fontSize: 13 }}>
            Status shown as returned by the backend
          </span>
        </div>
      </header>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
          gap: 14,
        }}
      >
        {[
          ["Claim ID", claimId],
          ["Policy ID", policyId],
        ].map(([label, item]) => (
          <article
            key={label}
            style={{
              padding: 18,
              borderRadius: 14,
              background: "#2B1D18",
              border: "1px solid rgba(250,243,232,0.12)",
              minWidth: 0,
            }}
          >
            <p style={{ margin: "0 0 8px", color: "#B8A99A", fontSize: 13 }}>
              {label}
            </p>
            <strong style={{ overflowWrap: "anywhere" }}>
              {value(item)}
            </strong>
          </article>
        ))}
      </div>

      <section
        style={{
          padding: 20,
          borderRadius: 16,
          background: "#2B1D18",
          border: "1px solid rgba(250,243,232,0.12)",
        }}
      >
        <h3 style={{ margin: "0 0 18px", fontSize: 17 }}>
          Claim details
        </h3>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
            gap: 18,
          }}
        >
          {fields.map(([label, item]) => (
            <div key={label} style={{ minWidth: 0 }}>
              <div style={{ color: "#B8A99A", fontSize: 12, marginBottom: 6 }}>
                {label}
              </div>
              <div
                style={{
                  color: "#FAF3E8",
                  fontSize: 14,
                  overflowWrap: "anywhere",
                }}
              >
                {value(item)}
              </div>
            </div>
          ))}
        </div>

        {data?.description && (
          <div
            style={{
              marginTop: 22,
              paddingTop: 18,
              borderTop: "1px solid rgba(250,243,232,0.12)",
            }}
          >
            <p style={{ color: "#B8A99A", fontSize: 12, margin: "0 0 8px" }}>
              Description
            </p>
            <p style={{ margin: 0, lineHeight: 1.7 }}>
              {value(data.description)}
            </p>
          </div>
        )}

        {documents !== undefined && documents !== null && (
          <div
            style={{
              marginTop: 22,
              paddingTop: 18,
              borderTop: "1px solid rgba(250,243,232,0.12)",
            }}
          >
            <p style={{ color: "#B8A99A", fontSize: 12, margin: "0 0 8px" }}>
              Documents recorded by backend
            </p>
            <div style={{ overflowWrap: "anywhere", lineHeight: 1.7 }}>
              {Array.isArray(documents)
                ? documents.length
                  ? documents.map((document, index) => (
                      <div key={index}>{value(document)}</div>
                    ))
                  : "No documents recorded"
                : value(documents)}
            </div>
          </div>
        )}
      </section>

      <p
        style={{
          margin: 0,
          padding: "14px 16px",
          borderRadius: 12,
          background: "rgba(251,195,185,0.07)",
          color: "#B8A99A",
          fontSize: 13,
          lineHeight: 1.7,
        }}
      >
        This page displays the saved claim record returned by the backend.
        A displayed status is not a guarantee of insurer approval or settlement.
      </p>
    </section>
  );
}
function ResultView({ data }) {
  const [sha256, setSha256] = useState("");
  const [hashStatus, setHashStatus] = useState(
    "Select the PDF to calculate its SHA-256 fingerprint."
  );
  const [copyStatus, setCopyStatus] = useState("");

  useEffect(() => {
    let cancelled = false;

    const calculateHash = async () => {
      try {
        const fileInputs = Array.from(
          document.querySelectorAll('input[type="file"]')
        );

        const pdfFiles = fileInputs.flatMap((input) =>
          Array.from(input.files || []).filter(
            (file) =>
              file.type === "application/pdf" ||
              file.name.toLowerCase().endsWith(".pdf")
          )
        );

        const expectedName = data?.inputs?.policy_filename;
        const file =
          pdfFiles.find((item) => item.name === expectedName) ||
          pdfFiles[0];

        if (!file) {
          if (!cancelled) {
            setSha256("");
            setHashStatus(
              "PDF file is not available in the file selector. Select it again to calculate the hash."
            );
          }
          return;
        }

        if (!window.crypto?.subtle) {
          if (!cancelled) {
            setHashStatus(
              "SHA-256 is unavailable in this browser context. Open the app on localhost or HTTPS."
            );
          }
          return;
        }

        if (!cancelled) {
          setHashStatus("Calculating SHA-256...");
        }

        const buffer = await file.arrayBuffer();
        const digest = await window.crypto.subtle.digest(
          "SHA-256",
          buffer
        );

        const hash = Array.from(new Uint8Array(digest))
          .map((byte) => byte.toString(16).padStart(2, "0"))
          .join("");

        if (!cancelled) {
          setSha256(hash);
          setHashStatus(
            "Calculated from the selected PDF in this browser."
          );
        }
      } catch (error) {
        if (!cancelled) {
          setSha256("");
          setHashStatus("Could not calculate the document hash.");
        }
      }
    };

    calculateHash();

    const handleFileChange = () => {
      calculateHash();
    };

    document.addEventListener("change", handleFileChange);

    return () => {
      cancelled = true;
      document.removeEventListener("change", handleFileChange);
    };
  }, [data]);

  const inputs = data?.inputs || {};
  const analysis = data?.document_analysis || {};
  const findings = Array.isArray(data?.findings) ? data.findings : [];
  const actions = Array.isArray(data?.next_actions)
    ? data.next_actions
    : [];

  const agents = [
    {
      name: "Eligibility Agent",
      status: String(data?.readiness_status || "NEEDS REVIEW")
        .replace(/_/g, " "),
      detail:
        data?.decision_notice ||
        "Preliminary screening result. Confirm coverage with the insurer."
    },
    {
      name: "Document Verification Agent",
      status: String(analysis.status || "NOT RETURNED")
        .replace(/_/g, " "),
      detail: analysis.pages_read != null
        ? `${analysis.pages_read} page(s) read · ${
            analysis.characters_extracted ?? 0
          } characters extracted`
        : "Document verification details were not returned by the backend."
    },
    {
      name: "Fraud Detection Agent",
      status: String(
        data?.fraud_detection_status ||
        data?.fraud_status ||
        data?.fraud_detection?.status ||
        "NOT RETURNED BY BACKEND"
      ).replace(/_/g, " "),
      detail: "Fraud result is shown only when supplied by the backend."
    },
    {
      name: "Claim Processing Agent",
      status: String(
        data?.claim_processing_status ||
        data?.claim_status ||
        data?.claim_processing?.status ||
        "NOT RETURNED BY BACKEND"
      ).replace(/_/g, " "),
      detail: "Processing status requires an actual backend result."
    },
    {
      name: "Claim Tracking Agent",
      status: String(
        data?.tracking_status ||
        data?.claim_tracking_status ||
        data?.tracking?.status ||
        "NOT RETURNED BY BACKEND"
      ).replace(/_/g, " "),
      detail: "Tracking details require a registered claim record."
    }
  ];

  const copyHash = async () => {
    try {
      await navigator.clipboard.writeText(sha256);
      setCopyStatus("Copied");
    } catch {
      setCopyStatus("Copy unavailable");
    }
  };

  return (
    <section className="cr-report">
      <header className="cr-heading">
        <div>
          <p className="cr-eyebrow">CLAIMORA AI · DOCUMENT REVIEW</p>
          <h2>Claim Readiness Report</h2>
          <p className="cr-subtitle">
            Actual response returned by the configured backend
          </p>
        </div>
        <span className="cr-badge cr-review">
          {String(data?.readiness_status || "NEEDS REVIEW").replace(/_/g, " ")}
        </span>
      </header>

      <div className="cr-reference">
        <div>
          <span>Analysis reference</span>
          <strong>{data?.analysis_id || "Not provided"}</strong>
        </div>
        <span className="cr-badge cr-review">ACTUAL RESULT</span>
      </div>

      <div className="cr-agent-grid">
        {agents.map((agent) => (
          <article className="cr-agent" key={agent.name}>
            <div className="cr-agent-top">
              <span className="cr-agent-dot" />
              <span className="cr-agent-status">{agent.status}</span>
            </div>
            <h3>{agent.name}</h3>
            <p>{agent.detail}</p>
          </article>
        ))}
      </div>

      <section className="cr-hash-card">
        <div>
          <p className="cr-eyebrow">DOCUMENT INTEGRITY</p>
          <h3>SHA-256 Fingerprint</h3>
          <p className="cr-subtitle">{hashStatus}</p>
        </div>

        <div className="cr-hash-meta">
          <span>Algorithm</span>
          <strong>SHA-256</strong>
          <span>Document</span>
          <strong>{inputs.policy_filename || "Selected PDF"}</strong>
        </div>

        {sha256 ? (
          <>
            <code className="cr-hash-value">{sha256}</code>
            <button
              type="button"
              className="cr-copy-button"
              onClick={copyHash}
            >
              Copy SHA-256
            </button>
            {copyStatus && (
              <span className="cr-copy-status">{copyStatus}</span>
            )}
          </>
        ) : (
          <p className="cr-subtitle">
            Select the same PDF used for analysis to calculate its fingerprint.
          </p>
        )}

        <p className="cr-hash-note">
          The fingerprint identifies the selected file's contents. It does
          not independently verify document authenticity, insurer approval,
          or whether the backend stored the same hash.
        </p>
      </section>

      <section className="cr-details">
        <h3>Submitted details</h3>
        <div className="cr-detail-grid">
          <div>
            <span>Policy / document</span>
            <strong>{inputs.policy_filename || "Not provided"}</strong>
          </div>
          <div>
            <span>Treatment</span>
            <strong>{inputs.planned_treatment || "Not provided"}</strong>
          </div>
          <div>
            <span>Hospital</span>
            <strong>{inputs.hospital_name || "Not provided"}</strong>
          </div>
          <div>
            <span>Pages read</span>
            <strong>{analysis.pages_read ?? "—"}</strong>
          </div>
          <div>
            <span>Extracted characters</span>
            <strong>{analysis.characters_extracted ?? "—"}</strong>
          </div>
          <div>
            <span>Analysis method</span>
            <strong>{analysis.analysis_method || "Not specified"}</strong>
          </div>
        </div>
      </section>

      {findings.length > 0 && (
        <section className="cr-details">
          <h3>Policy screening checks</h3>
          <div className="cr-check-list">
            {findings.map((item, index) => (
              <article className="cr-check" key={item.check_id || index}>
                <div className="cr-check-heading">
                  <strong>{item.label || "Policy check"}</strong>
                  <span className="cr-badge cr-review">
                    {String(item.status || "NOT RETURNED").replace(/_/g, " ")}
                  </span>
                </div>
                <p>{item.message || "No explanation returned."}</p>
                {item.next_action && (
                  <p className="cr-next">
                    <strong>Next action:</strong> {item.next_action}
                  </p>
                )}
              </article>
            ))}
          </div>
        </section>
      )}

      {actions.length > 0 && (
        <section className="cr-details">
          <h3>Recommended next actions</h3>
          {actions.map((item, index) => (
            <article className="cr-action" key={`${index}-${item.action}`}>
              <span className="cr-action-number">{index + 1}</span>
              <div>
                <strong>{item.action}</strong>
                <p>
                  {item.responsible_party || "User / Insurer"} ·{" "}
                  {item.status || "PENDING"}
                </p>
              </div>
              <span className="cr-priority">
                {item.priority || "NORMAL"}
              </span>
            </article>
          ))}
        </section>
      )}

      <footer className="cr-disclaimer">
        {data?.decision_notice ||
          "Preliminary document screening only. This is not a coverage decision, pre-authorisation, or guarantee of claim approval."}
      </footer>
    </section>
  );
}

function ClaimWorkflowPipeline() {
  const steps = [
    {
      title: "Upload Document",
      description: "Submit the policy and supporting documents.",
      icon: "01",
      tone: "cyan",
    },
    {
      title: "Orchestrator Agent",
      description: "Coordinates the claim-processing workflow.",
      icon: "02",
      tone: "violet",
    },
    {
      title: "Eligibility Agent",
      description: "Reviews eligibility-related information.",
      icon: "03",
      tone: "blue",
    },
    {
      title: "Document Verification Agent",
      description: "Checks document completeness and consistency.",
      icon: "04",
      tone: "indigo",
    },
    {
      title: "Fraud Detection Agent",
      description: "Screens for potential inconsistencies or risk indicators.",
      icon: "05",
      tone: "amber",
    },
    {
      title: "Claim Processing",
      description: "Supports the claim-processing stage.",
      icon: "06",
      tone: "pink",
    },
    {
      title: "Claim Tracking Agent",
      description: "Displays claim progress when tracking data is available.",
      icon: "07",
      tone: "cyan",
    },
  ];

  return (
    <section className="claim-workflow">
      <div className="claim-workflow-header">
        <div>
          <span className="claim-workflow-eyebrow">CLAIMORA AUTOMATION</span>
          <h2>AI Claim Processing Workflow</h2>
          <p>
            Follow the stages used to coordinate document review and claim handling.
          </p>
        </div>
        <span className="claim-workflow-badge">7 WORKFLOW STAGES</span>
      </div>

      <div className="claim-workflow-list">
        {steps.map((step, index) => (
          <React.Fragment key={step.icon}>
            <article className={`claim-workflow-step workflow-${step.tone}`}>
              <div className="claim-workflow-step-number">{step.icon}</div>
              <div className="claim-workflow-step-content">
                <h3>{step.title}</h3>
                <p>{step.description}</p>
              </div>
              <span className="claim-workflow-stage-label">WORKFLOW STAGE</span>
            </article>

            {index < steps.length - 1 && (
              <div className="claim-workflow-connector" aria-hidden="true">
                <span />
                <span className="claim-workflow-arrow">↓</span>
                <span />
              </div>
            )}
          </React.Fragment>
        ))}
      </div>

      <div className="claim-workflow-note">
        <span className="claim-workflow-note-icon">i</span>
        <p>
          This diagram shows the workflow stages, not live execution status.
          A stage is confirmed as completed only when the backend reports its
          actual status. Document screening alone does not mean a claim has
          been approved or processed.
        </p>
      </div>
    </section>
  );
}
function PageHeader({ eyebrow, title, subtitle }) {
  return (
    <div className="page-header">
      <div className="eyebrow">{eyebrow}</div>
      <h1>{title}</h1>
      <p>{subtitle}</p>
    </div>
  );
}

/* ---------- MAIN APP ---------- */
export default function App() {
  const [page, setPage] = useState("home");
  const [mobileMenu, setMobileMenu] = useState(false);

  const [backend, setBackend] = useState({
    checking: true,
    connected: false,
    message: "Checking backend connection...",
  });

  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState({ text: "", type: "info" });

  const [claimForm, setClaimForm] = useState({
    patient_name: "",
    policy_id: "",
    insurer: "",
    treatment: "",
    hospital: "",
    city: "Chennai",
    claim_amount: "",
    description: "",
  });

  const [claimResult, setClaimResult] = useState(null);
  const [trackingId, setTrackingId] = useState("");
  const [trackingResult, setTrackingResult] = useState(null);

  const [selectedFile, setSelectedFile] = useState(null);
  const [documentTreatment, setDocumentTreatment] = useState("");
  const [documentHospital, setDocumentHospital] = useState("");
  const [documentResult, setDocumentResult] = useState(null);

  const [careForm, setCareForm] = useState({
    treatment: "Appendectomy",
    city: "Chennai",
    area: "",
    insurer: "",
  });
  const [careResults, setCareResults] = useState(null);

  const [securityResult, setSecurityResult] = useState(null);
  const [auditResult, setAuditResult] = useState(null);
  const [fraudClaimId, setFraudClaimId] = useState("");
  const [fraudResult, setFraudResult] = useState(null);

  const [chatInput, setChatInput] = useState("");
  const [chatMessages, setChatMessages] = useState([
    {
      role: "assistant",
      text: "Hello! I'm Claimora AI. I can help you understand health insurance claim requirements, documents, and the claim process. Ask me a question to get started.",
    },
  ]);

  /* ---------- FORCE DARK BODY ---------- */
  useEffect(() => {
    document.body.style.background = T.bg;
    document.body.style.color = T.text;
    document.documentElement.style.background = T.bg;

    return () => {
      document.body.style.background = "";
      document.body.style.color = "";
      document.documentElement.style.background = "";
    };
  }, []);

  /* ---------- BACKEND CHECK ---------- */
  const checkBackend = useCallback(async () => {
    setBackend({
      checking: true,
      connected: false,
      message: "Checking backend connection...",
    });

    try {
      const data = await apiRequest("/health");
      setBackend({
        checking: false,
        connected: true,
        message: data?.message || data?.status || "Backend is online",
      });
    } catch {
      try {
        const data = await apiRequest("/status");
        setBackend({
          checking: false,
          connected: true,
          message: data?.message || data?.status || "Backend is online",
        });
      } catch {
        setBackend({
          checking: false,
          connected: false,
          message: "Cannot connect to FastAPI on port 8000",
        });
      }
    }
  }, []);

  useEffect(() => {
    checkBackend();
  }, [checkBackend]);

  function showNotice(text, type = "info") {
    setNotice({ text, type });
  }

  function updateClaim(key, value) {
    setClaimForm((previous) => ({ ...previous, [key]: value }));
  }

  function updateCare(key, value) {
    setCareForm((previous) => ({ ...previous, [key]: value }));
  }

  function navigate(id) {
    setPage(id);
    setMobileMenu(false);
    setNotice({ text: "", type: "info" });
  }

  /* ---------- SUBMIT CLAIM ---------- */
  async function submitClaim(event) {
    event.preventDefault();
    setBusy(true);
    setClaimResult(null);
    setNotice({ text: "", type: "info" });

    try {
      const data = await apiRequest("/api/claims", {
        method: "POST",
        body: JSON.stringify({
          ...claimForm,
          claim_amount: Number(claimForm.claim_amount),
        }),
      });

      setClaimResult(data);
      const id =
        data?.claim_id ||
        data?.claimId ||
        data?.reference_id ||
        data?.application_id;

      if (id) setTrackingId(String(id));

      showNotice("Claim submitted. Review the backend response below.", "success");
    } catch (error) {
      showNotice(`Claim submission failed: ${error.message}`, "error");
    } finally {
      setBusy(false);
    }
  }

  /* ---------- AI CHAT ---------- */
  async function sendChat(event) {
    event?.preventDefault();
    const question = chatInput.trim();
    if (!question || busy) return;

    setChatMessages((previous) => [
      ...previous,
      { role: "user", text: question },
    ]);
    setChatInput("");
    setBusy(true);

    try {
      const data = await apiRequest("/api/rag/chat", {
        method: "POST",
        body: JSON.stringify({ message: question, top_k: 5 }),
      });

      const answer =
        data?.answer ||
        data?.response ||
        data?.message ||
        "The server responded but no answer field was returned.";

      setChatMessages((previous) => [
        ...previous,
        { role: "assistant", text: String(answer) },
      ]);
    } catch (error) {
      setChatMessages((previous) => [
        ...previous,
        {
          role: "assistant",
          text: `I couldn't reach the AI backend. ${error.message}`,
        },
      ]);
    } finally {
      setBusy(false);
    }
  }

  /* ---------- UPLOAD ---------- */
  async function uploadDocument(event) {
    event.preventDefault();

    if (!selectedFile) {
      showNotice("Please select a document first.", "error");
      return;
    }

    const formData = new FormData();
    formData.append("policy_pdf", selectedFile);
    formData.append("planned_treatment", "Not specified");
    formData.append("hospital_name", "Not specified");

    setBusy(true);
    setDocumentResult(null);
    setNotice({ text: "", type: "info" });

    try {
      const data = await apiRequest("/api/claim-readiness/analyze", {
        method: "POST",
        body: formData,
      });

      setDocumentResult(data);
      showNotice("Document processed successfully.", "success");
    } catch (error) {
      showNotice(`Document upload failed: ${error.message}`, "error");
    } finally {
      setBusy(false);
    }
  }
  /* ---------- FIND CARE ---------- */
  async function findCare(event) {
    event.preventDefault();
    setBusy(true);
    setCareResults(null);
    setNotice({ text: "", type: "info" });

    try {
      const data = await apiRequest("/api/recommendations/search", {
        method: "POST",
        body: JSON.stringify(careForm),
      });

      setCareResults(data);
      showNotice("Care recommendation results received.", "success");
    } catch (error) {
      showNotice(`Could not load recommendations: ${error.message}`, "error");
    } finally {
      setBusy(false);
    }
  }

  /* ---------- TRACK CLAIM ---------- */
  async function trackClaim(event) {
    event.preventDefault();
    const id = trackingId.trim();

    if (!id) {
      showNotice("Enter your claim or policy reference.", "error");
      return;
    }

    setBusy(true);
    setTrackingResult(null);
    setNotice({ text: "", type: "info" });

    try {
      // Use the real backend endpoint that returns saved claim records.
      const payload = await apiRequest("/api/excel/claims");
      const records = Array.isArray(payload?.records)
        ? payload.records
        : [];

      const searchValue = id.toLowerCase();

      const record = records.find((item) => {
        const references = [
          item?.claim_id,
          item?.policy_id,
          item?.claim_number,
          item?.policy_number,
          item?.id,
        ];

        return references.some(
          (value) =>
            value != null &&
            String(value).trim().toLowerCase() === searchValue
        );
      });

      if (!record) {
        showNotice(
          "No saved claim matched that reference. Check the claim ID or policy ID and try again.",
          "error"
        );
        return;
      }

      // Preserve the backend fields and provide aliases for the existing UI.
      const result = {
        ...record,
        id: record.claim_id || record.id,
        claim_number: record.claim_id || record.claim_number,
        policy_number: record.policy_id || record.policy_number,
        overall_status: record.status || record.overall_status,
        document_status:
          record.document_status || record.documents || "Not provided",
      };

      setTrackingResult(result);
      showNotice("Claim record retrieved from the backend.", "success");
    } catch (error) {
      showNotice(
        `Unable to retrieve claim records: ${error.message}`,
        "error"
      );
    } finally {
      setBusy(false);
    }
  }

  /* ---------- SECURITY ---------- */
  async function refreshSecurity() {
    setBusy(true);
    setSecurityResult(null);
    setAuditResult(null);

    try {
      const results = await Promise.allSettled([
        apiRequest("/api/security/health"),
        apiRequest("/api/security/audit/health"),
        apiRequest("/api/security/audit/"),
      ]);

      if (results[0].status === "fulfilled") setSecurityResult(results[0].value);
      if (results[1].status === "fulfilled") setAuditResult(results[1].value);
      else if (results[2].status === "fulfilled") setAuditResult(results[2].value);

      if (results.every((result) => result.status === "rejected")) {
        showNotice("Security endpoints could not be reached.", "error");
      } else {
        showNotice("Security information refreshed.", "success");
      }
    } finally {
      setBusy(false);
    }
  }

  /* ---------- FRAUD ---------- */
  async function runFraudCheck(event) {
    event.preventDefault();

    const reference = fraudClaimId.trim();
    if (!reference) {
      showNotice("Enter a claim ID or policy ID.", "error");
      return;
    }

    setBusy(true);
    setFraudResult(null);

    try {
      const payload = await apiRequest("/api/excel/claims");
      const records = Array.isArray(payload)
        ? payload
        : Array.isArray(payload?.records)
          ? payload.records
          : Array.isArray(payload?.claims)
            ? payload.claims
            : [];

      const record = records.find((item) => {
        const values = [
          item?.claim_id,
          item?.policy_id,
          item?.claim_number,
          item?.policy_number,
          item?.id,
        ];
        return values.some(
          (value) =>
            value != null &&
            String(value).trim().toLowerCase() === reference.toLowerCase()
        );
      });

      if (!record) {
        throw new Error(
          "No saved claim matched that Claim ID or Policy ID. Check the reference and try again."
        );
      }

      const ageValue = Number(record.patient_age ?? record.age);
      const amountValue = Number(record.claim_amount);

      if (!record.patient_name || !record.policy_id ||
          !record.insurance_company || !record.hospital_name ||
          !(record.diagnosis || record.treatment) ||
          !Number.isFinite(ageValue) || ageValue <= 0 ||
          !Number.isFinite(amountValue) || amountValue < 0) {
        throw new Error(
          "This saved claim is missing required fraud-check fields. Complete the claim details before running the model."
        );
      }

      const result = await apiRequest("/api/fraud/check", {
        method: "POST",
        body: JSON.stringify({
          patient_name: String(record.patient_name),
          age: Math.round(ageValue),
          policy_number: String(record.policy_id),
          insurance_company: String(record.insurance_company),
          hospital_name: String(record.hospital_name),
          treatment: String(record.diagnosis || record.treatment),
          claim_amount: amountValue,
        }),
      });

      setFraudResult({
        ...result,
        claim_reference: record.claim_id || record.policy_id || reference,
        claim_patient_name: record.patient_name,
        claim_amount_checked: amountValue,
        claim_hospital_checked: record.hospital_name,
      });
      showNotice("Fraud assessment completed using the backend response.", "success");
    } catch (error) {
      showNotice(`Fraud check failed: ${error.message}`, "error");
    } finally {
      setBusy(false);
    }
  }/* ===================================================
     HOME
     =================================================== */
  function renderHome() {
    return (
      <>
        <section className="hero">
          <div className="hero-copy">
            <div className="eyebrow">
              <span className="eyebrow-dot" />
              INTELLIGENT CLAIM ASSISTANCE
            </div>
            <h1>
              AI Agent for Health Insurance
              <br />
              <span>Claim Assistance</span>
            </h1>
            <p>
              Understand your health insurance journey with AI-assisted
              guidance, document tools, claim tracking, and healthcare
              recommendations in one workspace.
            </p>
            <div className="hero-actions">
              <Button onClick={() => navigate("claim")}>
                Start a Claim <span>↗</span>
              </Button>
              <Button variant="secondary" onClick={() => navigate("tracking")}>
                Track a Claim
              </Button>
            </div>
            <div className="hero-footnote">
              <span>✦</span> AI-assisted guidance · You stay in control
            </div>
          </div>

          <div className="hero-art">
            <div className="orbit orbit-one" />
            <div className="orbit orbit-two" />
            <div className="hero-glow" />
            <div className="hero-emblem">
              <div className="emblem-cross">✚</div>
              <div className="emblem-ring" />
              <div className="emblem-caption">CLAIMORA AI</div>
            </div>
            <div className="floating-card floating-top">
              <span className="mini-icon peach">✧</span>
              <div>
                <strong>Smart assistance</strong>
                <small>Guidance for your next step</small>
              </div>
            </div>
            <div className="floating-card floating-bottom">
              <span className="mini-icon coral">✓</span>
              <div>
                <strong>Claim visibility</strong>
                <small>Review information in one place</small>
              </div>
            </div>
          </div>
        </section>

        <div className="section-intro">
          <div>
            <div className="eyebrow">YOUR WORKSPACE</div>
            <h2>Everything for your claim journey</h2>
            <p>Choose a tool to get started.</p>
          </div>
        </div>

        <div className="feature-grid">
          {[
            { icon: "＋", title: "New Claim", text: "Enter your policy and treatment details.", page: "claim" },
            { icon: "✧", title: "AI Assistant", text: "Ask questions about claim procedures.", page: "assistant" },
            { icon: "✚", title: "Find Care", text: "Search treatment and hospital recommendations.", page: "care" },
            { icon: "▤", title: "Documents", text: "Send supporting documents to the backend.", page: "documents" },
          ].map((item) => (
            <button
              className="feature-card"
              key={item.page}
              onClick={() => navigate(item.page)}
            >
              <span className="feature-icon">{item.icon}</span>
              <h3>{item.title}</h3>
              <p>{item.text}</p>
              <span className="feature-arrow">↗</span>
            </button>
          ))}
        </div>

        <Panel
          title="System status"
          subtitle="Connection to your local FastAPI service"
          action={
            <Button variant="secondary" onClick={checkBackend} disabled={backend.checking}>
              {backend.checking ? "Checking..." : "Refresh"}
            </Button>
          }
        >
          <div className="connection-row">
            <span
              className={`connection-indicator ${
                backend.connected ? "online" : "offline"
              }`}
            />
            <div className="connection-copy">
              <strong>
                {backend.connected ? "Backend connected" : "Backend unavailable"}
              </strong>
              <span>{backend.message}</span>
              <small>{API_BASE}</small>
            </div>
            <span
              className={`status-pill ${
                backend.connected ? "status-good" : "status-bad"
              }`}
            >
              {backend.connected ? "ONLINE" : "OFFLINE"}
            </span>
          </div>
        </Panel>
      </>
    );
  }

  /* ===================================================
     NEW CLAIM
     =================================================== */
  function renderClaim() {
    return (
      <>
        <PageHeader
          eyebrow="CLAIM WORKSPACE"
          title="Start a new claim"
          subtitle="Enter the information requested by your backend. Submission does not guarantee claim approval."
        />

        <Panel title="Claim application" subtitle="Fields marked * are required">
          <form className="form-grid" onSubmit={submitClaim}>
            <Field label="Patient name *">
              <Input
                required
                value={claimForm.patient_name}
                onChange={(e) => updateClaim("patient_name", e.target.value)}
                placeholder="Enter full name"
              />
            </Field>

            <Field label="Policy ID *">
              <Input
                required
                value={claimForm.policy_id}
                onChange={(e) => updateClaim("policy_id", e.target.value)}
                placeholder="Enter policy ID"
              />
            </Field>

            <Field label="Insurance provider *">
              <Select
                required
                value={claimForm.insurer}
                onChange={(e) => updateClaim("insurer", e.target.value)}
              >
                <option value="">Select insurer</option>
                {INSURERS.map((name) => (
                  <option key={name}>{name}</option>
                ))}
              </Select>
            </Field>

            <Field label="Treatment *">
              <Select
                required
                value={claimForm.treatment}
                onChange={(e) => updateClaim("treatment", e.target.value)}
              >
                <option value="">Select treatment</option>
                {TREATMENTS.map((name) => (
                  <option key={name}>{name}</option>
                ))}
              </Select>
            </Field>

            <Field label="Hospital name *">
              <Input
                required
                value={claimForm.hospital}
                onChange={(e) => updateClaim("hospital", e.target.value)}
                placeholder="Hospital or medical centre"
              />
            </Field>

            <Field label="City *">
              <Select
                required
                value={claimForm.city}
                onChange={(e) => updateClaim("city", e.target.value)}
              >
                {CITIES.map((city) => (
                  <option key={city}>{city}</option>
                ))}
              </Select>
            </Field>

            <Field label="Claim amount (₹) *">
              <Input
                required
                type="number"
                min="1"
                step="0.01"
                value={claimForm.claim_amount}
                onChange={(e) => updateClaim("claim_amount", e.target.value)}
                placeholder="Enter amount"
              />
            </Field>

            <Field label="Additional details">
              <Input
                value={claimForm.description}
                onChange={(e) => updateClaim("description", e.target.value)}
                placeholder="Brief details of the treatment"
              />
            </Field>

            <div className="form-footer">
              <p>
                Your application will be sent to the configured API. No
                approval is assumed by this interface.
              </p>
              <Button type="submit" disabled={busy}>
                {busy ? "Submitting..." : "Submit Claim Request →"}
              </Button>
            </div>
          </form>
        </Panel>

        {claimResult && (
          <Panel title="Backend response">
            <ResultView data={claimResult} />
            <div style={{ marginTop: 14 }}>
              <Button variant="secondary" onClick={() => navigate("tracking")}>
                Open Claim Status →
              </Button>
            </div>
          </Panel>
        )}
      </>
    );
  }

  /* ===================================================
     AI ASSISTANT
     =================================================== */
  function renderAssistant() {
    return (
      <>
        <PageHeader
          eyebrow="CLAIMORA INTELLIGENCE"
          title="AI claim assistant"
          subtitle="Ask about insurance claims, supporting documents, and common process steps."
        />

        <Panel title="Conversation" subtitle="Responses depend on your connected AI service">
          <div className="assistant-layout">
            <aside className="assistant-side">
              <div className="assistant-avatar">
                <div className="avatar-glow" />
                <div className="avatar-symbol">✧</div>
              </div>
              <div className="assistant-badge">
                <span className="pulse" /> Online
              </div>
              <div className="assistant-info">
                <strong>Claimora AI</strong>
                Trained on claim procedures, document requirements and insurance terminology.
              </div>
            </aside>

            <div className="assistant-chat">
              <div className="chat-window">
                {chatMessages.map((message, index) => (
                  <div
                    key={`${index}-${message.role}`}
                    className={`chat-message ${
                      message.role === "user" ? "chat-user" : "chat-assistant"
                    }`}
                  >
                    <div className="chat-avatar">
                      {message.role === "user" ? "Y" : "✧"}
                    </div>
                    <div className="chat-bubble">
                      <strong>
                        {message.role === "user" ? "You" : "Claimora AI"}
                      </strong>
                      <p>{message.text}</p>
                    </div>
                  </div>
                ))}
                {busy && <div className="typing">Claimora is working...</div>}
              </div>

              <form className="chat-form" onSubmit={sendChat}>
                <Input
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      sendChat(e);
                    }
                  }}
                  placeholder="Ask a question about your claim..."
                  aria-label="Your question"
                />
                <Button type="submit" disabled={busy || !chatInput.trim()}>
                  Send ↗
                </Button>
              </form>
              <p className="disclaimer">
                AI responses are informational and should be checked against
                your insurer's policy documents and official guidance.
              </p>
            </div>
          </div>
        </Panel>
      </>
    );
  }

  /* ===================================================
     FIND CARE
     =================================================== */
  function renderCare() {
    return <FindCareDirectory />;
  }

  /* ===================================================
     DOCUMENTS
     =================================================== */
  function renderDocuments() {
    return (
      <>
        <PageHeader
          eyebrow="DOCUMENT CENTRE"
          title="Supporting documents"
          subtitle="Upload a document to your backend's security document service."
        />

        <Panel title="Upload a document" subtitle="Follow the file requirements configured by your backend">
          <form onSubmit={uploadDocument}>

            <label className="upload-zone">
              <span className="upload-symbol">⇧</span>
              <strong>
                {selectedFile ? selectedFile.name : "Choose a document"}
              </strong>
              <span>
                {selectedFile
                  ? `${(selectedFile.size / 1024 / 1024).toFixed(2)} MB`
                  : "Select a file from your device"}
              </span>
              <input
                type="file"
                accept=".pdf,.png,.jpg,.jpeg,.doc,.docx"
                onChange={(e) => {
                  setSelectedFile(e.target.files?.[0] || null);
                  setDocumentResult(null);
                }}
              />
            </label>

            <div className="form-footer">
              <p>
                Only upload documents you are authorised to share. Confirm the
                permitted formats and file-size limits in the API.
              </p>
              <Button type="submit" disabled={busy || !selectedFile}>
                {busy ? "Uploading..." : "Upload Document →"}
              </Button>
            </div>
          </form>
        </Panel>

        {documentResult && (
          <Panel title="Claim readiness analysis">
            <ResultView data={documentResult} />
          </Panel>
        )}
</>
    );
  }

  /* ===================================================
     CLAIM STATUS
     =================================================== */
  function renderTracking() {
    return (
      <>
        <PageHeader
          eyebrow="CLAIM VISIBILITY"
          title="Track a claim"
          subtitle="Look up a claim or application using its reference number."
        />

        <Panel title="Find your claim">
          <form className="tracking-form" onSubmit={trackClaim}>
            <Field label="Claim or application reference">
              <Input
                value={trackingId}
                onChange={(e) => setTrackingId(e.target.value)}
                placeholder="Enter your reference ID"
                required
              />
            </Field>
            <Button type="submit" disabled={busy}>
              {busy ? "Searching..." : "Search Claim →"}
            </Button>
          </form>
          <p className="disclaimer">
            A reference number is not necessarily an insurer-issued claim
            number. Check the response returned by your backend.
          </p>
        </Panel>

        {trackingResult && (
          <Panel title="Claim information">
            <ClaimRecordView data={trackingResult} />
          </Panel>
        )}
      </>
    );
  }

  /* ===================================================
     SECURITY
     =================================================== */
  function renderSecurity() {
    return (
      <>
        <PageHeader
          eyebrow="TRUST AND VERIFICATION"
          title="Security centre"
          subtitle="Check the status of the security and audit services configured in your backend."
        />

        <Panel
          title="Security services"
          subtitle="Live information retrieved from FastAPI"
          action={
            <Button onClick={refreshSecurity} disabled={busy}>
              {busy ? "Refreshing..." : "Refresh"}
            </Button>
          }
        >
          <div className="security-grid">
            <div className="security-card">
              <span className="security-symbol">⬡</span>
              <h3>Security health</h3>
              <p>Service availability and status response.</p>
              {securityResult ? (
                <ResultView data={securityResult} />
              ) : (
                <span className="muted">Refresh to retrieve status.</span>
              )}
            </div>

            <div className="security-card">
              <span className="security-symbol">▤</span>
              <h3>Audit service</h3>
              <p>Audit health or audit records returned by the API.</p>
              {auditResult ? (
                <ResultView data={auditResult} />
              ) : (
                <span className="muted">Refresh to retrieve status.</span>
              )}
            </div>
          </div>
        </Panel>

        <Panel
          title="Fraud-check service"
          subtitle="Submit a claim reference to the configured fraud endpoint"
        >
          <form className="tracking-form" onSubmit={runFraudCheck}>
            <Field label="Claim ID">
              <Input
                value={fraudClaimId}
                onChange={(e) => setFraudClaimId(e.target.value)}
                placeholder="Enter claim ID"
                required
              />
            </Field>
            <Button type="submit" disabled={busy}>
              {busy ? "Checking..." : "Run Fraud Check →"}
            </Button>
          </form>

          {fraudResult && (
            <div className="result-spacing security-fraud-result">
              <div className="security-card">
                <span className="security-symbol">⬡</span>
                <h3>Fraud assessment result</h3>
                <p>Claim reference: {fraudResult.claim_reference || fraudClaimId}</p>
                {fraudResult.claim_patient_name && (
                  <p>Patient: {fraudResult.claim_patient_name}</p>
                )}
                {fraudResult.claim_hospital_checked && (
                  <p>Hospital: {fraudResult.claim_hospital_checked}</p>
                )}
                {fraudResult.claim_amount_checked != null && (
                  <p>
                    Claim amount checked:{" "}
                    {new Intl.NumberFormat("en-IN", {
                      style: "currency",
                      currency: "INR",
                      maximumFractionDigits: 0,
                    }).format(fraudResult.claim_amount_checked)}
                  </p>
                )}
                <p>
                  Prediction: <strong>{fraudResult.prediction || "Not returned"}</strong>
                </p>
                <p>
                  Risk level: <strong>{fraudResult.risk_level || "Not returned"}</strong>
                </p>
                <p>
                  Fraud probability:{" "}
                  <strong>
                    {Number.isFinite(Number(fraudResult.fraud_probability))
                      ? `${Number(fraudResult.fraud_probability).toFixed(2)}%`
                      : "Not returned"}
                  </strong>
                </p>
                <p>
                  Recommendation:{" "}
                  {fraudResult.recommendation || "No recommendation returned by the model."}
                </p>
                <p className="disclaimer">
                  This is an ML risk assessment, not proof of fraud and not an
                  insurer approval or rejection. Follow the authorised review process.
                </p>
              </div>
            </div>
          )}

          <p className="disclaimer">
            A risk assessment is not proof of fraud. Review any result using
            your authorised claims-review process.
          </p>
        </Panel>
      </>
    );
  }

  /* ===================================================
     ROUTER
     =================================================== */
  let pageContent;

  switch (page) {
    case "claim":
      pageContent = renderClaim();
      break;
    case "assistant":
      pageContent = renderAssistant();
      break;
    case "care":
      pageContent = renderCare();
      break;
    case "documents":
      pageContent = renderDocuments();
      break;
    case "tracking":
      pageContent = renderTracking();
      break;
    case "security":
      pageContent = renderSecurity();
      break;
    default:
      pageContent = renderHome();
  }

  return (
    <div className="app-shell">
      <style>{styles}</style>

      <aside className={`sidebar ${mobileMenu ? "sidebar-open" : ""}`}>
        <button className="brand" onClick={() => navigate("home")}>
          <span className="brand-mark">
            <span>✚</span>
          </span>
          <span className="brand-copy">
            <strong>claimora</strong>
            <small>SMART CLAIM ASSISTANCE</small>
          </span>
        </button>

        <div className="sidebar-section-label">WORKSPACE</div>

        <nav className="navigation">
          {NAV_ITEMS.map((item) => (
            <button
              key={item.id}
              className={`nav-item ${page === item.id ? "nav-active" : ""}`}
              onClick={() => navigate(item.id)}
            >
              <span className="nav-icon">{item.icon}</span>
              <span>{item.label}</span>
              {page === item.id && <span className="nav-indicator" />}
            </button>
          ))}
        </nav>

        <div className="sidebar-bottom">
          <div className="sidebar-help-icon">?</div>
          <div>
            <strong>Need assistance?</strong>
            <p>Use Claimora AI for general guidance.</p>
            <button onClick={() => navigate("assistant")}>
              Ask the assistant ↗
            </button>
          </div>
        </div>

        <div className="sidebar-footer">
          <span className="footer-dot" />
          <span>Claimora workspace</span>
          <span className="footer-version">v1.0</span>
        </div>
      </aside>

      {mobileMenu && (
        <button
          className="mobile-overlay"
          onClick={() => setMobileMenu(false)}
          aria-label="Close navigation"
        />
      )}

      <main className="main-area">
        <header className="topbar">
          <div className="topbar-left">
            <button
              className="menu-toggle"
              onClick={() => setMobileMenu((value) => !value)}
              aria-label="Toggle navigation"
            >
              ☰
            </button>
            <div>
              <div className="breadcrumb">
                Claimora / {NAV_ITEMS.find((x) => x.id === page)?.label}
              </div>
              <div className="topbar-title">
                {NAV_ITEMS.find((x) => x.id === page)?.label || "Home"}
              </div>
            </div>
          </div>

          <div className="topbar-right">
            <div className="api-status">
              <span
                className={`api-dot ${backend.connected ? "online" : "offline"}`}
              />
              <span>
                {backend.checking
                  ? "Connecting..."
                  : backend.connected
                    ? "API connected"
                    : "API offline"}
              </span>
            </div>
            <button
              className="topbar-refresh"
              onClick={checkBackend}
              title="Check backend connection"
            >
              ↻
            </button>
            <div className="user-avatar">C</div>
          </div>
        </header>

        <div className="page-container">
          <Message message={notice.text} type={notice.type} />
          {pageContent}

          <footer className="page-footer">
            <span>© {new Date().getFullYear()} Claimora</span>
            <span>AI-assisted health insurance claim workspace</span>
          </footer>
        </div>
      </main>
    </div>
  );
}

/* ===================================================
   STYLES — DARK ESPRESSO THEME
   =================================================== */
const styles = `
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');

:root {
  font-family: 'DM Sans', sans-serif;
  color: #FAF3E8;
  background: #1F1410;
  font-synthesis: none;
  text-rendering: optimizeLegibility;
  -webkit-font-smoothing: antialiased;
  --bg: #1F1410;
  --surface: #2B1D18;
  --elevated: #3A2620;
  --text: #FAF3E8;
  --muted: #B8A99A;
  --coral: #E06464;
  --peach: #FBC3B9;
  --border: rgba(250,243,232,.12);
  --border-strong: rgba(250,243,232,.2);
  --success: #8BC9A4;
}

* { box-sizing: border-box; }

html, body {
  margin: 0;
  min-width: 320px;
  min-height: 100vh;
  background: #1F1410 !important;
  color: #FAF3E8 !important;
  font-family: 'DM Sans', sans-serif;
}

body {
  background:
    radial-gradient(ellipse at 8% 0%, rgba(224,100,100,.09), transparent 35%),
    radial-gradient(ellipse at 95% 30%, rgba(251,195,185,.035), transparent 32%),
    #1F1410 !important;
  background-attachment: fixed !important;
}

#root { min-height: 100vh; background: transparent; }

button, input, select, textarea { font: inherit; font-family: 'DM Sans', sans-serif; }
button { cursor: pointer; }
button:disabled { opacity: .55; cursor: not-allowed; }

.app-shell {
  min-height: 100vh;
  background: transparent;
  color: var(--text);
}

/* ---------- SCROLLBAR ---------- */
::-webkit-scrollbar { width: 9px; height: 9px; }
::-webkit-scrollbar-track { background: #1F1410; }
::-webkit-scrollbar-thumb {
  border: 2px solid #1F1410;
  border-radius: 20px;
  background: #65463A;
}
::-webkit-scrollbar-thumb:hover { background: #87604F; }

/* ---------- SIDEBAR ---------- */
.sidebar {
  position: fixed; z-index: 30; left: 0; top: 0; bottom: 0;
  display: flex; flex-direction: column; width: 250px;
  padding: 27px 17px 15px;
  background: #1A100C;
  border-right: 1px solid var(--border);
  color: var(--text);
  overflow-y: auto;
}
.brand {
  display: flex; align-items: center; gap: 12px;
  border: 0; color: var(--text); background: transparent;
  text-align: left; padding: 0 8px 35px; cursor: pointer;
}
.brand-mark {
  width: 43px; height: 43px; border-radius: 14px;
  display: grid; place-items: center;
  color: #1F1410; font-size: 24px; font-weight: 900;
  background: linear-gradient(145deg, #FBC3B9, #E06464);
  box-shadow: 0 7px 22px rgba(224,100,100,.35);
  flex-shrink: 0;
}
.brand-copy { display: flex; flex-direction: column; gap: 3px; }
.brand-copy strong {
  font: 800 24px 'Manrope', sans-serif;
  letter-spacing: -.9px;
  color: var(--text);
}
.brand-copy small {
  color: var(--muted);
  font-size: 8px;
  letter-spacing: 1.5px;
}
.sidebar-section-label {
  padding: 0 12px 12px;
  font-size: 10px;
  letter-spacing: 1.5px;
  color: var(--muted);
  font-weight: 700;
  opacity: .7;
}
.navigation { display: grid; gap: 5px; }
.nav-item {
  position: relative; width: 100%;
  display: flex; align-items: center; gap: 13px;
  padding: 12px 13px; border: 0; border-radius: 10px;
  background: transparent; color: var(--muted);
  text-align: left; font-size: 13px;
  font-weight: 500;
  transition: all .18s;
}
.nav-item:hover {
  background: rgba(250,243,232,.055);
  color: var(--text);
}
.nav-active {
  color: var(--text);
  background: rgba(224,100,100,.14);
  font-weight: 600;
}
.nav-active::before {
  content: '';
  position: absolute; left: -17px; top: 9px; bottom: 9px;
  width: 3px;
  background: var(--coral);
  border-radius: 0 3px 3px 0;
}
.nav-icon {
  width: 20px; font-size: 19px;
  text-align: center; color: inherit;
}
.nav-indicator {
  margin-left: auto;
  width: 5px; height: 5px;
  border-radius: 50%;
  background: var(--coral);
  box-shadow: 0 0 8px var(--coral);
}
.sidebar-bottom {
  display: flex; gap: 11px;
  margin-top: auto;
  padding: 15px 12px;
  border: 1px solid var(--border);
  border-radius: 13px;
  background: rgba(250,243,232,.025);
}
.sidebar-help-icon {
  display: grid; place-items: center;
  flex: 0 0 27px; height: 27px;
  border-radius: 9px;
  background: rgba(224,100,100,.15);
  color: var(--peach);
  font-weight: 800;
}
.sidebar-bottom strong {
  color: var(--text);
  font-size: 11px;
  display: block;
}
.sidebar-bottom p {
  color: var(--muted);
  font-size: 10px;
  line-height: 1.6;
  margin: 6px 0;
}
.sidebar-bottom button {
  padding: 0;
  color: var(--peach);
  border: 0;
  background: transparent;
  font-size: 10px;
  font-weight: 700;
  cursor: pointer;
}
.sidebar-bottom button:hover { color: #FFE1DA; }
.sidebar-footer {
  display: flex; align-items: center; gap: 8px;
  color: var(--muted);
  font-size: 10px;
  padding: 19px 8px 0;
  opacity: .7;
}
.footer-dot {
  width: 6px; height: 6px;
  background: var(--success);
  border-radius: 50%;
  box-shadow: 0 0 8px var(--success);
}
.footer-version { margin-left: auto; }

/* ---------- MAIN AREA ---------- */
.main-area {
  margin-left: 250px;
  min-height: 100vh;
  background: transparent;
}
.topbar {
  height: 78px; padding: 0 39px;
  display: flex; align-items: center; justify-content: space-between;
  background: rgba(31,20,16,.85);
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  border-bottom: 1px solid var(--border);
  position: sticky; top: 0; z-index: 10;
}
.topbar-left, .topbar-right {
  display: flex; align-items: center; gap: 15px;
}
.breadcrumb {
  font-size: 10px; color: var(--muted);
  margin-bottom: 5px;
  opacity: .8;
}
.topbar-title {
  color: var(--text);
  font: 700 14px 'Manrope', sans-serif;
}
.api-status {
  display: flex; align-items: center; gap: 7px;
  font-size: 11px; color: var(--muted);
}
.api-dot, .connection-indicator {
  width: 7px; height: 7px; border-radius: 50%;
}
.online {
  background: var(--success);
  box-shadow: 0 0 8px var(--success);
}
.offline {
  background: var(--coral);
  box-shadow: 0 0 8px var(--coral);
}
.topbar-refresh {
  border: 1px solid var(--border);
  background: var(--surface);
  color: var(--muted);
  border-radius: 9px;
  width: 33px; height: 33px;
  font-size: 19px;
  display: grid; place-items: center;
  transition: all .18s;
}
.topbar-refresh:hover {
  border-color: var(--coral);
  color: var(--peach);
}
.user-avatar {
  display: grid; place-items: center;
  width: 34px; height: 34px;
  border-radius: 11px;
  background: rgba(224,100,100,.2);
  color: var(--peach);
  font-weight: 800;
  font-size: 12px;
}
.menu-toggle {
  display: none;
  border: 0; background: transparent;
  color: var(--text); font-size: 22px;
}
.page-container {
  max-width: 1450px;
  padding: 31px 39px 18px;
  margin: auto;
}

/* ---------- HERO ---------- */
.hero {
  display: grid;
  grid-template-columns: 1.1fr .9fr;
  min-height: 365px;
  background: linear-gradient(135deg, #2B1D18, #1F1410);
  border: 1px solid var(--border);
  border-radius: 19px;
  overflow: hidden;
  position: relative;
}
.hero-copy {
  padding: 47px 0 38px 42px;
  position: relative; z-index: 2;
}
.eyebrow {
  color: var(--peach);
  font-size: 9px; font-weight: 800;
  letter-spacing: 1.7px;
  text-transform: uppercase;
  display: inline-flex; align-items: center; gap: 8px;
}
.eyebrow-dot {
  display: inline-block;
  width: 6px; height: 6px;
  border-radius: 50%;
  background: var(--coral);
  box-shadow: 0 0 8px var(--coral);
}
.hero h1, .page-header h1 {
  font: 800 36px/1.22 'Manrope', sans-serif;
  letter-spacing: -1.4px;
  color: var(--text);
  margin: 20px 0 14px;
}
.hero h1 span { color: var(--coral); }
.hero-copy > p {
  max-width: 460px;
  color: var(--muted);
  font-size: 13px;
  line-height: 1.9;
}
.hero-actions {
  display: flex; gap: 10px;
  margin-top: 25px; flex-wrap: wrap;
}

/* ---------- BUTTONS ---------- */
.button {
  min-height: 42px;
  display: inline-flex; align-items: center; justify-content: center;
  gap: 9px; padding: 0 20px;
  border-radius: 10px;
  border: 1px solid transparent;
  font-size: 12px; font-weight: 700;
  transition: all .18s;
  font-family: 'DM Sans', sans-serif;
}
.button:hover:not(:disabled) { transform: translateY(-1px); }
.button-primary {
  background: linear-gradient(120deg, var(--coral), #D24E4E);
  color: #FFF8F3;
  box-shadow: 0 6px 18px rgba(224,100,100,.28);
}
.button-primary:hover:not(:disabled) {
  background: linear-gradient(120deg, #EC7777, #E06464);
  box-shadow: 0 10px 26px rgba(224,100,100,.4);
}
.button-secondary {
  background: var(--elevated);
  color: var(--text);
  border-color: var(--border-strong);
}
.button-secondary:hover:not(:disabled) {
  border-color: rgba(251,195,185,.4);
  color: var(--peach);
  background: #493027;
}
.hero-footnote {
  margin-top: 26px;
  color: var(--muted);
  font-size: 11px;
  opacity: .85;
}
.hero-footnote span { color: var(--coral); margin-right: 5px; }

/* ---------- HERO ART ---------- */
.hero-art {
  min-height: 350px;
  position: relative;
  overflow: hidden;
  background:
    radial-gradient(ellipse at 55% 45%, rgba(224,100,100,.15), transparent 55%),
    radial-gradient(ellipse at 50% 50%, rgba(251,195,185,.06), transparent 70%);
}
.hero-glow {
  position: absolute;
  width: 235px; height: 235px;
  border-radius: 50%;
  left: 50%; top: 49%;
  transform: translate(-50%,-50%);
  background: radial-gradient(circle, rgba(224,100,100,.35) 0, rgba(224,100,100,.08) 48%, transparent 72%);
}
.orbit {
  position: absolute;
  border: 1px solid rgba(224,100,100,.25);
  border-radius: 50%;
  left: 50%; top: 49%;
  transform: translate(-50%,-50%) rotate(-25deg);
}
.orbit-one { width: 275px; height: 190px; }
.orbit-two {
  width: 320px; height: 245px;
  transform: translate(-50%,-50%) rotate(34deg);
  border-color: rgba(251,195,185,.15);
  border-style: dashed;
}
.hero-emblem {
  position: absolute; z-index: 1;
  left: 50%; top: 49%;
  transform: translate(-50%,-50%);
  width: 133px; height: 133px;
  display: grid; place-items: center;
  border-radius: 38px;
  color: #FFF8F3;
  background: linear-gradient(145deg, var(--coral), #B94040);
  box-shadow:
    0 24px 55px rgba(224,100,100,.35),
    inset 0 1px 0 rgba(255,255,255,.3);
}
.emblem-cross {
  font-size: 60px;
  text-shadow: 0 3px 15px rgba(0,0,0,.4);
}
.emblem-ring {
  position: absolute; inset: 10px;
  border: 1px solid rgba(255,255,255,.28);
  border-radius: 30px;
}
.emblem-caption {
  position: absolute; bottom: 19px;
  font-size: 7px; letter-spacing: 2px; font-weight: 800;
}
.floating-card {
  position: absolute; z-index: 2;
  display: flex; align-items: center; gap: 9px;
  padding: 11px 13px;
  border: 1px solid var(--border-strong);
  border-radius: 12px;
  background: rgba(58,38,32,.92);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  box-shadow: 0 9px 30px rgba(0,0,0,.35);
}
.floating-top { top: 54px; right: 20px; }
.floating-bottom { bottom: 43px; left: 15px; }
.mini-icon {
  display: grid; place-items: center;
  width: 28px; height: 28px;
  border-radius: 8px;
  font-size: 15px;
}
.mini-icon.peach {
  color: var(--peach);
  background: rgba(251,195,185,.15);
}
.mini-icon.coral {
  color: var(--coral);
  background: rgba(224,100,100,.15);
}
.floating-card strong, .floating-card small { display: block; }
.floating-card strong { font-size: 10px; color: var(--text); }
.floating-card small { font-size: 9px; color: var(--muted); margin-top: 4px; }

/* ---------- SECTION ---------- */
.section-intro {
  display: flex; justify-content: space-between;
  align-items: end;
  margin: 30px 0 17px;
}
.section-intro h2, .panel-heading h2 {
  margin: 7px 0 5px;
  color: var(--text);
  font: 700 17px 'Manrope', sans-serif;
  letter-spacing: -.4px;
}
.section-intro p, .panel-heading p {
  margin: 0; color: var(--muted);
  font-size: 11px; line-height: 1.7;
}

/* ---------- FEATURE GRID ---------- */
.feature-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0,1fr));
  gap: 13px;
  margin-bottom: 21px;
}
.feature-card {
  position: relative;
  min-height: 166px;
  text-align: left;
  padding: 19px;
  background: linear-gradient(145deg, #2B1D18, #241812);
  border: 1px solid var(--border);
  border-radius: 14px;
  transition: all .18s;
  cursor: pointer;
}
.feature-card:hover {
  transform: translateY(-3px);
  border-color: rgba(224,100,100,.5);
  box-shadow: 0 12px 28px rgba(0,0,0,.35), 0 0 30px rgba(224,100,100,.08);
}
.feature-icon {
  display: grid; place-items: center;
  width: 40px; height: 40px;
  border-radius: 11px;
  background: rgba(224,100,100,.15);
  color: var(--peach);
  font-size: 20px;
}
.feature-card:nth-child(2) .feature-icon {
  background: rgba(251,195,185,.15);
  color: var(--peach);
}
.feature-card:nth-child(3) .feature-icon {
  background: rgba(139,201,164,.14);
  color: var(--success);
}
.feature-card:nth-child(4) .feature-icon {
  background: rgba(240,193,122,.14);
  color: #F0C17A;
}
.feature-card h3 {
  margin: 15px 0 6px;
  font-size: 13px;
  color: var(--text);
}
.feature-card p {
  margin: 0; font-size: 10px;
  line-height: 1.7; color: var(--muted);
  max-width: 200px;
}
.feature-arrow {
  position: absolute;
  right: 17px; top: 20px;
  color: var(--muted);
  opacity: .6;
}

/* ---------- PANEL ---------- */
.panel {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 15px;
  padding: 23px;
  margin-bottom: 20px;
  min-width: 0;
  box-shadow: 0 4px 14px rgba(0,0,0,.2);
}
.panel-heading {
  display: flex; justify-content: space-between;
  align-items: center; gap: 15px;
  margin-bottom: 20px;
}
.panel-heading h2 { margin-top: 0; }

/* ---------- CONNECTION ---------- */
.connection-row {
  display: flex; align-items: center; gap: 13px;
  padding: 14px;
  background: rgba(31,20,16,.6);
  border: 1px solid var(--border);
  border-radius: 11px;
}
.connection-indicator { flex: 0 0 9px; height: 9px; }
.connection-copy {
  display: flex; flex-direction: column;
  gap: 4px; min-width: 0;
}
.connection-copy strong { font-size: 12px; color: var(--text); }
.connection-copy span { font-size: 10px; color: var(--muted); }
.connection-copy small {
  font-size: 10px;
  color: var(--peach);
  overflow-wrap: anywhere;
  opacity: .7;
}
.status-pill {
  margin-left: auto;
  border-radius: 20px;
  padding: 6px 9px;
  font-size: 8px;
  font-weight: 800;
  letter-spacing: .7px;
}
.status-good {
  background: rgba(139,201,164,.15);
  color: var(--success);
  border: 1px solid rgba(139,201,164,.3);
}
.status-bad {
  background: rgba(224,100,100,.15);
  color: #FF8C8C;
  border: 1px solid rgba(224,100,100,.3);
}

/* ---------- PAGE HEADER ---------- */
.page-header { margin: 4px 0 25px; }
.page-header h1 {
  font-size: 29px;
  margin: 10px 0 8px;
  letter-spacing: -.9px;
}
.page-header p {
  margin: 0; max-width: 760px;
  color: var(--muted);
  font-size: 12px;
  line-height: 1.8;
}

/* ---------- FORM ---------- */
.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0,1fr));
  gap: 18px;
}
.field { display: flex; flex-direction: column; gap: 8px; min-width: 0; }
.field-label {
  color: var(--text);
  font-size: 11px;
  font-weight: 700;
}
.input {
  width: 100%; min-width: 0;
  min-height: 44px;
  padding: 11px 13px;
  border: 1px solid var(--border-strong);
  border-radius: 10px;
  outline: none;
  color: var(--text);
  background: #241812;
  font-size: 12px;
  transition: border-color .15s, box-shadow .15s;
}
.input:focus {
  border-color: var(--coral);
  box-shadow: 0 0 0 3px rgba(224,100,100,.15);
  background: #281B15;
}
.input::placeholder { color: #98877A; }
select.input { cursor: pointer; }
select.input option { background: var(--surface); color: var(--text); }
.field-hint { color: var(--muted); font-size: 10px; }
.form-footer {
  grid-column: 1 / -1;
  display: flex; justify-content: space-between;
  align-items: center; gap: 16px;
  border-top: 1px solid var(--border);
  padding-top: 18px;
  margin-top: 4px;
}
.form-footer p {
  max-width: 520px; margin: 0;
  color: var(--muted);
  font-size: 10px;
  line-height: 1.8;
  opacity: .85;
}

/* ---------- MESSAGES ---------- */
.message {
  padding: 12px 15px;
  border-radius: 10px;
  margin-bottom: 18px;
  font-size: 11px;
  line-height: 1.7;
  overflow-wrap: anywhere;
  border: 1px solid;
}
.message-info {
  color: #9CC9E8;
  background: rgba(156,201,232,.08);
  border-color: rgba(156,201,232,.25);
}
.message-success {
  color: var(--success);
  background: rgba(139,201,164,.08);
  border-color: rgba(139,201,164,.28);
}
.message-error {
  color: #FF8C8C;
  background: rgba(255,140,140,.08);
  border-color: rgba(255,140,140,.28);
}

/* ---------- JSON OUTPUT ---------- */
.json-output {
  margin: 0; padding: 16px;
  max-width: 100%;
  overflow: auto;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: rgba(31,20,16,.6);
  color: var(--text);
  font: 11px/1.8 ui-monospace, SFMono-Regular, Consolas, monospace;
}

/* ---------- AI ASSISTANT (with side avatar) ---------- */
.assistant-layout {
  display: grid;
  grid-template-columns: 220px 1fr;
  gap: 24px;
  align-items: start;
}
.assistant-side {
  position: sticky;
  top: 100px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.assistant-avatar {
  position: relative;
  width: 100%;
  aspect-ratio: 1;
  border-radius: 20px;
  overflow: hidden;
  border: 2px solid var(--coral);
  background:
    radial-gradient(circle at 50% 50%, rgba(224,100,100,.35), rgba(224,100,100,.08) 60%, transparent 80%),
    linear-gradient(145deg, #2B1D18, #1F1410);
  display: grid;
  place-items: center;
  box-shadow: 0 12px 30px rgba(224,100,100,.25);
}
.avatar-glow {
  position: absolute;
  inset: 20%;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(224,100,100,.4), transparent 70%);
  filter: blur(20px);
  animation: pulseGlow 3s ease-in-out infinite;
}
.avatar-symbol {
  position: relative;
  z-index: 2;
  font-size: 56px;
  color: var(--peach);
  text-shadow: 0 0 25px rgba(224,100,100,.6);
}
@keyframes pulseGlow {
  0%, 100% { opacity: .7; transform: scale(.9); }
  50% { opacity: 1; transform: scale(1.1); }
}
.assistant-badge {
  display: flex; align-items: center; gap: 8px;
  padding: 10px 14px;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: var(--surface);
  font-size: 11px;
  color: var(--peach);
  font-weight: 700;
}
.assistant-badge .pulse {
  width: 8px; height: 8px;
  border-radius: 50%;
  background: var(--success);
  box-shadow: 0 0 10px var(--success);
  animation: pulseDot 2s ease-in-out infinite;
}
@keyframes pulseDot {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: .5; transform: scale(1.3); }
}
.assistant-info {
  padding: 14px;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: rgba(31,20,16,.5);
  font-size: 11px;
  color: var(--muted);
  line-height: 1.7;
}
.assistant-info strong {
  color: var(--peach);
  display: block;
  margin-bottom: 6px;
  font-size: 12px;
}
.assistant-chat { min-width: 0; }

/* ---------- CHAT ---------- */
.chat-window {
  display: flex;
  flex-direction: column;
  gap: 19px;
  max-height: 470px;
  overflow-y: auto;
  padding: 4px 1px 18px;
}
.chat-message {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  max-width: 90%;
}
.chat-user {
  align-self: flex-end;
  flex-direction: row-reverse;
}
.chat-avatar {
  flex: 0 0 32px;
  width: 32px; height: 32px;
  display: grid; place-items: center;
  border-radius: 10px;
  background: rgba(224,100,100,.15);
  color: var(--peach);
  font-size: 13px;
  font-weight: 800;
}
.chat-user .chat-avatar {
  background: rgba(251,195,185,.15);
  color: var(--peach);
}
.chat-bubble {
  padding: 12px 14px;
  border-radius: 0 12px 12px 12px;
  background: var(--elevated);
  border: 1px solid var(--border);
  min-width: 0;
}
.chat-user .chat-bubble {
  border-radius: 12px 0 12px 12px;
  background: rgba(224,100,100,.14);
  border-color: rgba(224,100,100,.28);
}
.chat-bubble strong {
  font-size: 10px;
  color: var(--peach);
  text-transform: uppercase;
  letter-spacing: .5px;
}
.chat-bubble p {
  margin: 6px 0 0;
  color: var(--text);
  font-size: 12px;
  line-height: 1.8;
  overflow-wrap: anywhere;
}
.chat-form {
  display: flex;
  gap: 9px;
  border-top: 1px solid var(--border);
  padding-top: 18px;
}
.chat-form .input { flex: 1; }
.typing { font-size: 10px; color: var(--muted); font-style: italic; }
.disclaimer {
  color: var(--muted);
  font-size: 10px;
  line-height: 1.8;
  margin: 15px 0 0;
  opacity: .85;
}

/* ---------- UPLOAD ---------- */
.upload-zone {
  min-height: 180px;
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  gap: 9px;
  border: 1.5px dashed rgba(251,195,185,.3);
  border-radius: 13px;
  background: rgba(31,20,16,.5);
  color: var(--text);
  cursor: pointer;
  text-align: center;
  transition: all .2s;
}
.upload-zone:hover {
  border-color: var(--coral);
  background: rgba(224,100,100,.06);
}
.upload-symbol {
  display: grid; place-items: center;
  width: 43px; height: 43px;
  border-radius: 13px;
  background: rgba(224,100,100,.15);
  color: var(--peach);
  font-size: 25px;
}
.upload-zone strong {
  font-size: 13px;
  overflow-wrap: anywhere;
  max-width: 90%;
  color: var(--text);
}
.upload-zone span:last-of-type { font-size: 11px; color: var(--muted); }
.upload-zone input {
  max-width: 240px;
  font-size: 10px;
  margin-top: 8px;
  color: var(--muted);
}

/* ---------- TRACKING FORM ---------- */
.tracking-form {
  display: flex;
  align-items: end;
  gap: 13px;
}
.tracking-form .field { flex: 1; }

/* ---------- SECURITY ---------- */
.security-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0,1fr));
  gap: 14px;
}
.security-card {
  min-width: 0;
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 17px;
  background: rgba(31,20,16,.4);
}
.security-symbol {
  color: var(--coral);
  font-size: 22px;
}
.security-card h3 {
  margin: 12px 0 6px;
  font-size: 13px;
  color: var(--text);
}
.security-card > p {
  margin: 0 0 13px;
  color: var(--muted);
  font-size: 11px;
  line-height: 1.7;
}
.muted { color: var(--muted); font-size: 10px; }
.result-spacing { margin-top: 16px; }

/* ---------- FOOTER ---------- */
.page-footer {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  color: var(--muted);
  font-size: 9px;
  padding: 15px 2px 0;
  opacity: .7;
}

/* ---------- OVERLAY ---------- */
.mobile-overlay { display: none; }

/* ---------- RESPONSIVE ---------- */
@media (min-width: 1500px) {
  .page-container { padding-top: 38px; }
  .hero { min-height: 390px; }
  .hero-copy { padding-top: 57px; }
}

@media (max-width: 1180px) {
  .page-container { padding-left: 25px; padding-right: 25px; }
  .topbar { padding-left: 25px; padding-right: 25px; }
  .hero-copy { padding-left: 30px; }
  .hero h1 { font-size: 31px; }
  .feature-grid { grid-template-columns: repeat(2, minmax(0,1fr)); }
}

@media (max-width: 1000px) {
  .assistant-layout { grid-template-columns: 1fr; }
  .assistant-side {
    position: static;
    flex-direction: row;
    align-items: center;
  }
  .assistant-avatar { width: 100px; height: 100px; aspect-ratio: auto; }
  .avatar-symbol { font-size: 38px; }
  .assistant-info { flex: 1; }
}

@media (max-width: 820px) {
  .sidebar {
    transform: translateX(-100%);
    transition: transform .22s;
    box-shadow: 15px 0 35px rgba(0,0,0,.4);
  }
  .sidebar-open { transform: translateX(0); }
  .mobile-overlay {
    display: block;
    position: fixed;
    z-index: 20;
    inset: 0;
    border: 0;
    background: rgba(10,6,4,.65);
    backdrop-filter: blur(4px);
  }
  .main-area { margin-left: 0; }
  .menu-toggle { display: block; }
  .topbar { height: 69px; padding: 0 18px; }
  .page-container { padding: 22px 18px 16px; }
  .hero { grid-template-columns: 1fr; }
  .hero-copy { padding: 33px 25px 26px; }
  .hero-art { min-height: 270px; }
  .hero-emblem { width: 110px; height: 110px; }
  .emblem-cross { font-size: 48px; }
  .floating-top { top: 28px; right: 12px; }
  .floating-bottom { bottom: 25px; left: 12px; }
  .api-status { font-size: 0; gap: 0; }
  .api-dot { width: 9px; height: 9px; }
}

@media (max-width: 560px) {
  .topbar-title { font-size: 12px; }
  .breadcrumb { font-size: 9px; }
  .topbar-right { gap: 9px; }
  .hero h1 { font-size: 29px; }
  .hero-copy { padding: 27px 20px 22px; }
  .hero-art { min-height: 235px; }
  .hero-actions { align-items: stretch; }
  .hero-actions .button { flex: 1; }
  .feature-grid { grid-template-columns: 1fr; }
  .feature-card { min-height: 132px; }
  .panel { padding: 17px; }
  .panel-heading { align-items: flex-start; }
  .form-grid, .security-grid { grid-template-columns: 1fr; }
  .form-footer { align-items: stretch; flex-direction: column; }
  .form-footer .button { width: 100%; }
  .tracking-form { align-items: stretch; flex-direction: column; }
  .tracking-form .button { width: 100%; }
  .page-header h1 { font-size: 26px; }
  .page-footer { flex-direction: column; }
  .connection-row { align-items: flex-start; }
  .status-pill { font-size: 7px; }
  .chat-message { max-width: 100%; }
  .assistant-side { flex-direction: column; }
  .assistant-avatar { width: 100%; height: auto; aspect-ratio: 1; max-width: 160px; }
}
`;













