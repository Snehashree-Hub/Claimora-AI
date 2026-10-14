import React, { useCallback, useEffect, useMemo, useState } from "react";
import {
  Activity, AlertTriangle, ArrowRight, Bot, Building2, CheckCircle2,
  ClipboardCheck, Clock3, Database, ExternalLink, FileCheck2, FileText,
  HeartPulse, Home, LoaderCircle, LockKeyhole, MapPin, MessageCircle,
  RefreshCw, Search, Send, ShieldAlert, ShieldCheck, Stethoscope, Upload,
  UserRound, Wifi, WifiOff, Plus, Copy, Workflow, XCircle
} from "lucide-react";

const API_BASE = (import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000").replace(/\/+$/, "");
const HERO_IMAGE = "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?auto=format&fit=crop&w=1800&q=85";
const SECURITY_IMAGE = "https://images.unsplash.com/photo-1563013544-824ae1b704d3?auto=format&fit=crop&w=1400&q=85";
const T = { bg: "#1F1410", surface: "#2B1D18", elevated: "#3A2620", text: "#FAF3E8", muted: "#B8A99A", coral: "#E06464", peach: "#FBC3B9", border: "rgba(250,243,232,.12)" };

async function apiRequest(path, options = {}) {
  const isForm = typeof FormData !== "undefined" && options.body instanceof FormData;
  let response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers: {
        ...(isForm || options.body == null ? {} : { "Content-Type": "application/json" }),
        ...options.headers
      }
    });
  } catch (error) {
    throw new Error(`Cannot connect to Claimora API at ${API_BASE}. Start FastAPI and confirm the port/CORS settings. ${error?.message || "Network error"}`);
  }
  const raw = await response.text();
  let data;
  try { data = raw ? JSON.parse(raw) : {}; } catch { data = { detail: raw }; }
  if (!response.ok) {
    const detail = data?.detail || data?.message || data?.error;
    const message = typeof detail === "string" ? detail : detail ? JSON.stringify(detail) : `Request failed (${response.status})`;
    throw new Error(`${message} [${options.method || "GET"} ${path} → HTTP ${response.status}]`);
  }
  return data;
}
function asArray(data) {
  if (Array.isArray(data)) return data;
  for (const key of ["events", "claims", "items", "data", "results", "hospitals", "doctors", "recommendations"]) {
    if (Array.isArray(data?.[key])) return data[key];
  }
  return [];
}
function displayData(data) {
  if (typeof data === "string") return data;
  return data?.answer || data?.response || data?.message || data?.detail || JSON.stringify(data, null, 2);
}
function resultEntries(data) {
  let value = data;
  if (value && typeof value === "object" && !Array.isArray(value)) {
    value = value.result ?? value.analysis ?? value.data ?? value.claim ?? value;
  }
  if (Array.isArray(value)) return value.map((item, index) => [String(index + 1), item]);
  if (value && typeof value === "object") return Object.entries(value);
  return [["Response", value ?? "No response returned"]];
}
function prettyValue(value) {
  if (value === null || value === undefined || value === "") return "—";
  if (typeof value === "object") return JSON.stringify(value, null, 2);
  return String(value);
}
function makeClaimId() {
  const d = new Date();
  const stamp = `${d.getFullYear()}${String(d.getMonth() + 1).padStart(2, "0")}${String(d.getDate()).padStart(2, "0")}${String(d.getHours()).padStart(2, "0")}${String(d.getMinutes()).padStart(2, "0")}${String(d.getSeconds()).padStart(2, "0")}`;
  const random = Math.random().toString(36).slice(2, 6).toUpperCase();
  return `CLM-${stamp}-${random}`;
}
const TREATMENTS = ["General Surgery", "Appendectomy", "Kidney Stone", "Hernia Repair", "Gallbladder Surgery", "Thyroid Surgery", "Sinus Surgery", "Emergency Care", "Cardiac Evaluation", "Cataract Surgery", "Orthopaedic Treatment", "Maternity Care"];
const CITIES = ["Chennai", "Bengaluru", "Hyderabad", "Mumbai", "Delhi"];
const WORKFLOW = ["Orchestrator Agent", "Eligibility Agent", "Document Verification Agent", "Fraud Detection Agent", "Claim Processing", "Claim Tracking Agent"];

export default function App() {
  const [page, setPage] = useState("home");
  const [backendStatus, setBackendStatus] = useState("checking");
  const [backendMessage, setBackendMessage] = useState("Checking backend connection...");

  const [question, setQuestion] = useState("");
  const [chatAnswer, setChatAnswer] = useState("");
  const [chatLoading, setChatLoading] = useState(false);
  const [chatError, setChatError] = useState("");

  const [treatment, setTreatment] = useState("General Surgery");
  const [city, setCity] = useState("Chennai");
  const [area, setArea] = useState("");
  const [insurance, setInsurance] = useState("");
  const [hospitalResults, setHospitalResults] = useState(null);
  const [hospitalError, setHospitalError] = useState("");
  const [hospitalLoading, setHospitalLoading] = useState(false);

  const [doctorTreatment, setDoctorTreatment] = useState("Appendectomy");
  const [doctorCity, setDoctorCity] = useState("Chennai");
  const [doctorArea, setDoctorArea] = useState("");
  const [doctorResults, setDoctorResults] = useState(null);
  const [doctorError, setDoctorError] = useState("");
  const [doctorLoading, setDoctorLoading] = useState(false);

  const [files, setFiles] = useState([]);
  const [readinessResult, setReadinessResult] = useState(null);
  const [readinessError, setReadinessError] = useState("");
  const [readinessLoading, setReadinessLoading] = useState(false);
  const [readinessTreatment, setReadinessTreatment] = useState("General Surgery");
  const [readinessHospital, setReadinessHospital] = useState("");
  const [readinessCity, setReadinessCity] = useState("Chennai");
  const [readinessExpense, setReadinessExpense] = useState("");

  const [secureDocumentClaimId, setSecureDocumentClaimId] = useState("");
  const [secureDocument, setSecureDocument] = useState(null);
  const [secureUploadResult, setSecureUploadResult] = useState(null);
  const [secureUploadError, setSecureUploadError] = useState("");
  const [secureUploadLoading, setSecureUploadLoading] = useState(false);

  const [claimId, setClaimId] = useState("");
  const [trackingResult, setTrackingResult] = useState(null);
  const [trackingError, setTrackingError] = useState("");
  const [trackingLoading, setTrackingLoading] = useState(false);

  const [fraudClaimId, setFraudClaimId] = useState("");
  const [fraudResult, setFraudResult] = useState(null);
  const [fraudError, setFraudError] = useState("");
  const [fraudLoading, setFraudLoading] = useState(false);

  const [securityLoading, setSecurityLoading] = useState(false);
  const [securityError, setSecurityError] = useState("");
  const [securityCheckedAt, setSecurityCheckedAt] = useState("");
  const [securityBackend, setSecurityBackend] = useState(null);
  const [securityAnalyzer, setSecurityAnalyzer] = useState(null);
  const [auditHealth, setAuditHealth] = useState(null);
  const [auditEvents, setAuditEvents] = useState([]);
  const [auditCount, setAuditCount] = useState(null);

  const [newClaimId, setNewClaimId] = useState(makeClaimId);
  const [claimForm, setClaimForm] = useState({ full_name: "", age: "", email: "", contact: "", policy_id: "", claim_amount: "", diagnosis: "", treatment_date: "", treatment: "General Surgery", hospital: "", doctor: "", insurer: "Star Health", claim_type: "Reimbursement", city: "Chennai", notes: "" });
  const [claimCreated, setClaimCreated] = useState(null);
  const [claimCreateError, setClaimCreateError] = useState("");
  const [claimCreateLoading, setClaimCreateLoading] = useState(false);

  const checkBackend = useCallback(async () => {
    try {
      const data = await apiRequest("/status");
      setBackendStatus("connected");
      setBackendMessage(data.status || data.message || "Backend is responding.");
    } catch (error) {
      setBackendStatus("offline");
      setBackendMessage(error.message || "Backend unavailable");
    }
  }, []);

  const refreshSecurity = useCallback(async () => {
    setSecurityLoading(true); setSecurityError("");
    const results = await Promise.allSettled([
      apiRequest("/status"), apiRequest("/api/security/health"),
      apiRequest("/api/security/audit/health"), apiRequest("/api/security/audit/")
    ]);
    const errors = [];
    if (results[0].status === "fulfilled") {
      setSecurityBackend(results[0].value); setBackendStatus("connected");
      setBackendMessage(results[0].value.status || results[0].value.message || "Connected");
    } else {
      setSecurityBackend(null); setBackendStatus("offline");
      setBackendMessage(results[0].reason?.message || "Backend unavailable");
      errors.push(`Backend status: ${results[0].reason?.message || "unavailable"}`);
    }
    if (results[1].status === "fulfilled") setSecurityAnalyzer(results[1].value);
    else { setSecurityAnalyzer(null); errors.push(`Security analyzer: ${results[1].reason?.message || "unavailable"}`); }
    if (results[2].status === "fulfilled") setAuditHealth(results[2].value);
    else { setAuditHealth(null); errors.push(`Audit service: ${results[2].reason?.message || "unavailable"}`); }
    if (results[3].status === "fulfilled") {
      const data = results[3].value; const events = asArray(data);
      setAuditEvents(events); setAuditCount(Number.isFinite(data?.count) ? data.count : events.length);
    } else { setAuditEvents([]); setAuditCount(null); errors.push(`Audit events: ${results[3].reason?.message || "unavailable"}`); }
    setSecurityCheckedAt(new Date().toLocaleString()); setSecurityError(errors.join("\n")); setSecurityLoading(false);
  }, []);

  useEffect(() => {
    checkBackend(); const timer = window.setInterval(checkBackend, 15000);
    return () => window.clearInterval(timer);
  }, [checkBackend]);
  useEffect(() => {
    if (page !== "security") return undefined;
    refreshSecurity(); const timer = window.setInterval(refreshSecurity, 30000);
    return () => window.clearInterval(timer);
  }, [page, refreshSecurity]);

  function navigate(nextPage) { setPage(nextPage); window.scrollTo({ top: 0, behavior: "smooth" }); }
  function updateClaimField(key, value) { setClaimForm(prev => ({ ...prev, [key]: value })); }

  async function askAssistant(event) {
    event.preventDefault(); if (!question.trim()) return;
    setChatLoading(true); setChatAnswer(""); setChatError("");
    try {
      const data = await apiRequest("/api/rag/chat", { method: "POST", body: JSON.stringify({ message: question.trim(), top_k: 5 }) });
      if (data.success === false) throw new Error(displayData(data));
      setChatAnswer(data.answer || data.response || displayData(data) || "The AI service returned no answer.");
    } catch (error) { setChatError(error.message); }
    finally { setChatLoading(false); }
  }

  async function searchHospitals(event) {
    event.preventDefault(); setHospitalLoading(true); setHospitalError(""); setHospitalResults(null);
    try {
      const data = await apiRequest("/api/recommendations/search", { method: "POST", body: JSON.stringify({ treatment, city, area: area.trim() || "Any Area", insurance_company: insurance.trim() || "All Insurance" }) });
      setHospitalResults(data);
    } catch (error) { setHospitalError(error.message); }
    finally { setHospitalLoading(false); }
  }

  async function searchDoctors(event) {
    event.preventDefault(); setDoctorLoading(true); setDoctorError(""); setDoctorResults(null);
    const payload = { treatment: doctorTreatment, city: doctorCity, area: doctorArea.trim() || "Any Area" };
    try {
      let data;
      try {
        data = await apiRequest("/api/recommendations/doctors/search", { method: "POST", body: JSON.stringify(payload) });
      } catch (firstError) {
        // Some backend builds expose the doctor endpoint without the plural prefix.
        try { data = await apiRequest("/api/recommendations/doctor/search", { method: "POST", body: JSON.stringify(payload) }); }
        catch { throw firstError; }
      }
      setDoctorResults(data);
    } catch (error) { setDoctorError(`${error.message}. Check the active doctor-search route in /docs; this page does not fabricate doctor records.`); }
    finally { setDoctorLoading(false); }
  }

  async function analyzeDocuments(event) {
    event.preventDefault(); setReadinessError(""); setReadinessResult(null);
    if (!files.length) { setReadinessError("Please select a policy PDF first."); return; }
    if (!readinessHospital.trim()) { setReadinessError("Enter the hospital name for the readiness analysis."); return; }
    if (!String(files[0].name || "").toLowerCase().endsWith(".pdf")) { setReadinessError("The claim-readiness endpoint accepts a PDF policy file only."); return; }
    setReadinessLoading(true);
    try {
      const formData = new FormData();
      formData.append("policy_pdf", files[0]);
      formData.append("planned_treatment", readinessTreatment);
      formData.append("hospital_name", readinessHospital.trim());
      formData.append("city", readinessCity);
      formData.append("estimated_expense", readinessExpense || "0");
      const data = await apiRequest("/api/claim-readiness/analyze", { method: "POST", body: formData });
      setReadinessResult(data);
    } catch (error) {
      setReadinessError(`${error.message}. The current FastAPI main.py must include a claim-readiness router for this feature; the uploaded policy has not been marked as approved.`);
    } finally { setReadinessLoading(false); }
  }

  async function uploadSecureDocument(event) {
    event.preventDefault(); setSecureUploadError(""); setSecureUploadResult(null);
    if (!secureDocumentClaimId.trim() || !secureDocument) { setSecureUploadError("Claim ID and document are required."); return; }
    setSecureUploadLoading(true);
    try {
      const formData = new FormData();
      formData.append("claim_id", secureDocumentClaimId.trim());
      formData.append("user", "system");
      formData.append("document", secureDocument);
      const data = await apiRequest("/api/security/documents/upload", { method: "POST", body: formData });
      setSecureUploadResult(data);
      setClaimId(secureDocumentClaimId.trim());
      setTrackingResult(null);
    } catch (error) { setSecureUploadError(error.message); }
    finally { setSecureUploadLoading(false); }
  }

  async function checkTracking(event) {
    event.preventDefault(); setTrackingError(""); setTrackingResult(null);
    if (!claimId.trim()) { setTrackingError("Enter a claim reference or policy ID."); return; }
    setTrackingLoading(true);
    try {
      const data = await apiRequest("/api/demo-claims/"); const records = asArray(data); const searched = claimId.trim().toLowerCase();
      const found = records.find(item => [item.claim_number, item.claim_id, item.id, item.policy_number, item.policy_id].filter(Boolean).some(value => String(value).toLowerCase() === searched));
      if (!found) setTrackingError("No matching record was found in the configured demo-claims endpoint. This is not live insurer tracking.");
      else setTrackingResult(found);
    } catch (error) { setTrackingError(error.message); }
    finally { setTrackingLoading(false); }
  }

  async function runFraudCheck(event) {
    event.preventDefault(); setFraudError(""); setFraudResult(null);
    if (!fraudClaimId.trim()) { setFraudError("Enter a Claim ID."); return; }
    setFraudLoading(true);
    const claimRef = fraudClaimId.trim();
    try {
      let data;
      try {
        data = await apiRequest("/api/security/analyze", { method: "POST", body: JSON.stringify({ claim_id: claimRef }) });
      } catch (securityError) {
        if (!/Not Found|404/.test(securityError.message)) throw securityError;
        data = await apiRequest("/api/fraud/check", { method: "POST", body: JSON.stringify({ claim_id: claimRef }) });
      }
      if (data?.success === false) throw new Error(displayData(data));
      setFraudResult(data);
    } catch (error) {
      setFraudError(`Claim-specific analysis could not be completed for ${claimRef}: ${error.message}. Confirm the endpoint schema in ${API_BASE}/docs.`);
    } finally { setFraudLoading(false); }
  }

  async function createClaim(event) {
    event.preventDefault(); setClaimCreateError(""); setClaimCreated(null);
    if (!claimForm.full_name.trim() || !claimForm.email.trim() || !claimForm.age || !claimForm.policy_id.trim() || !claimForm.claim_amount || !claimForm.diagnosis.trim() || !claimForm.treatment_date) {
      setClaimCreateError("Complete all required claimant, policy, treatment date, diagnosis and amount fields."); return;
    }
    setClaimCreateLoading(true);
    const payload = {
      patient_name: claimForm.full_name.trim(), age: Number(claimForm.age),
      email: claimForm.email.trim(), claim_amount: Number(claimForm.claim_amount),
      diagnosis: claimForm.diagnosis.trim(), hospital: claimForm.hospital.trim() || "Not specified",
      doctor: claimForm.doctor.trim() || "Not specified", treatment_date: claimForm.treatment_date,
      description: claimForm.notes.trim(), insurer: claimForm.insurer,
      claim_type: claimForm.claim_type, claim_id: newClaimId,
      policy_number: claimForm.policy_id.trim(), city: claimForm.city,
      treatment: claimForm.treatment
    };
    try {
      let response;
      try {
        response = await apiRequest("/api/claims/", { method: "POST", body: JSON.stringify(payload) });
      } catch (firstError) {
        if (!/HTTP 404|Not Found|404/.test(firstError.message)) throw firstError;
        response = await apiRequest("/api/v1/claims", { method: "POST", body: JSON.stringify(payload) });
      }
      if (response?.success === false) throw new Error(displayData(response));
      const saved = response?.claim || response?.data?.claim || response?.data || response;
      const created = {
        ...payload,
        claim_id: saved?.claim_id || saved?.claim_number || saved?.id || newClaimId,
        status: saved?.status || "Submitted to backend",
        created_at: saved?.created_at || new Date().toISOString(),
        backend_saved: true,
        backend_response: response
      };
      setClaimCreated(created);
      setClaimId(created.claim_id);
      setFraudClaimId(created.claim_id);
    } catch (error) {
      setClaimCreateError(`Claim was not saved. ${error.message}. Check ${API_BASE}/docs for the active claim-create route and required request fields. No fake approval or local-only claim is created.`);
    } finally { setClaimCreateLoading(false); }
  }

  const navItems = useMemo(() => [
    { id: "home", label: "Home", icon: Home }, { id: "assistant", label: "AI Assistant", icon: Bot },
    { id: "hospitals", label: "Find Hospital", icon: Building2 }, { id: "doctors", label: "Find Doctor", icon: Stethoscope },
    { id: "documents", label: "Documents", icon: FileText }, { id: "tracking", label: "Tracking", icon: Activity },
    { id: "security", label: "Security", icon: ShieldCheck }
  ], []);

  const css = `
    *{box-sizing:border-box} body{margin:0;background:${T.bg}} button,input,select,textarea{font:inherit} button{cursor:pointer}
    .app{min-height:100vh;background:${T.bg};color:${T.text};font-family:Inter,system-ui,-apple-system,"Segoe UI",sans-serif}
    .shell{width:min(1200px,calc(100% - 36px));margin:0 auto}.topbar{position:sticky;top:0;z-index:20;background:rgba(31,20,16,.96);backdrop-filter:blur(16px);border-bottom:1px solid ${T.border}}
    .nav{min-height:76px;display:flex;align-items:center;justify-content:space-between;gap:15px;flex-wrap:wrap;padding:12px 0}.brand{display:flex;align-items:center;gap:11px;padding:0;border:0;background:transparent;color:${T.text};text-align:left}
    .brand-icon{display:grid;place-items:center;width:44px;height:44px;border-radius:14px;background:${T.coral};color:white}.brand-name{display:block;font-size:22px;font-weight:850;letter-spacing:-.7px}.brand-sub{display:block;margin-top:3px;font-size:10px;color:${T.muted};letter-spacing:1px}
    .nav-links{display:flex;align-items:center;flex-wrap:wrap;gap:4px}.nav-link{display:flex;align-items:center;gap:6px;padding:10px;border-radius:10px;border:1px solid transparent;background:transparent;color:${T.muted};font-size:12px;white-space:nowrap}.nav-link:hover,.nav-link.active{color:${T.text};background:${T.surface};border-color:${T.border}}
    .status{display:inline-flex;align-items:center;gap:7px;border:1px solid ${T.border};border-radius:999px;padding:8px 10px;font-size:11px;color:${T.muted};white-space:nowrap}.dot{width:7px;height:7px;background:#E5AD58;border-radius:50%}.status.online .dot{background:#73C69B}.status.offline .dot{background:${T.coral}}
    .main{padding:32px 0 68px;min-height:70vh}.hero{position:relative;overflow:hidden;min-height:470px;display:flex;align-items:center;padding:clamp(28px,5vw,64px);border:1px solid ${T.border};border-radius:27px;background:linear-gradient(90deg,rgba(31,20,16,.97) 0%,rgba(31,20,16,.86) 52%,rgba(31,20,16,.24) 100%),url('${HERO_IMAGE}') center/cover no-repeat,linear-gradient(135deg,#34231D,#241712)}
    .hero:after{content:"CLAIMORA";position:absolute;right:24px;bottom:12px;font-size:clamp(28px,5vw,66px);font-weight:900;letter-spacing:5px;color:rgba(250,243,232,.12);pointer-events:none}.hero-content{position:relative;z-index:1;max-width:760px}.eyebrow{display:inline-flex;align-items:center;gap:8px;color:${T.peach};font-size:11px;font-weight:800;letter-spacing:1.3px;text-transform:uppercase}
    h1{margin:22px 0 18px;font-size:clamp(38px,6vw,68px);line-height:1.04;letter-spacing:-2px}.accent{color:${T.coral}}.lead{max-width:650px;color:#E0D0C4;font-size:15px;line-height:1.85}.actions{display:flex;flex-wrap:wrap;gap:10px;margin-top:24px}.btn{display:inline-flex;align-items:center;justify-content:center;gap:8px;padding:12px 15px;border:1px solid ${T.border};border-radius:11px;background:${T.surface};color:${T.text};font-size:12px;font-weight:750}.btn.primary{background:${T.coral};border-color:${T.coral};color:white}.btn:disabled{opacity:.65;cursor:wait}.btn.small{padding:8px 10px;font-size:11px}
    .section-head{display:flex;justify-content:space-between;align-items:end;gap:12px;margin:34px 0 18px}.section-head h2{margin:0;font-size:23px;letter-spacing:-.5px}.section-head p{margin:7px 0 0;color:${T.muted};font-size:12px;line-height:1.7}.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}.feature{min-height:170px;padding:20px;text-align:left;color:${T.text};border:1px solid ${T.border};border-radius:17px;background:${T.surface};transition:transform .2s,border-color .2s}.feature:hover{transform:translateY(-3px);border-color:rgba(224,100,100,.6)}.feature-icon{display:grid;place-items:center;width:42px;height:42px;margin-bottom:17px;border-radius:12px;color:${T.peach};background:rgba(224,100,100,.12)}.feature h3{margin:0 0 8px;font-size:15px}.feature p{margin:0;color:${T.muted};font-size:12px;line-height:1.7}
    .panel{padding:clamp(20px,4vw,30px);border:1px solid ${T.border};border-radius:19px;background:${T.surface}}.panel h2{display:flex;align-items:center;gap:9px;margin:0 0 10px;font-size:24px;letter-spacing:-.5px}.panel>p{margin:0 0 22px;color:${T.muted};font-size:12px;line-height:1.75}.form-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:15px}.field{display:flex;flex-direction:column;gap:8px;min-width:0}.field.full{grid-column:1/-1}.field label{color:${T.muted};font-size:12px;font-weight:650}.control{width:100%;min-height:45px;padding:11px 12px;outline:none;border:1px solid ${T.border};border-radius:10px;background:${T.bg};color:${T.text}}.control:focus{border-color:${T.coral}}textarea.control{min-height:110px;resize:vertical}.result{margin-top:18px;padding:15px;border:1px solid ${T.border};border-radius:12px;background:rgba(31,20,16,.65);color:${T.text};font-size:12px;line-height:1.8;white-space:pre-wrap;overflow-wrap:anywhere}.error{color:#FFB0A5}.muted{color:${T.muted}}.file-drop{padding:22px;text-align:center;border:1px dashed rgba(251,195,185,.35);border-radius:13px;background:rgba(31,20,16,.4)}.file-drop input{display:block;max-width:100%;margin:14px auto 0;color:${T.muted}}.spinner{animation:spin 1s linear infinite}@keyframes spin{to{transform:rotate(360deg)}}
    .workflow{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:9px}.workflow-step{position:relative;min-height:116px;padding:15px 12px;border:1px solid ${T.border};border-radius:14px;background:${T.surface}}.workflow-number{display:grid;place-items:center;width:27px;height:27px;margin-bottom:12px;border-radius:9px;background:rgba(224,100,100,.14);color:${T.peach};font-size:11px;font-weight:800}.workflow-step strong{display:block;font-size:12px;line-height:1.5}.workflow-step small{display:block;margin-top:6px;color:${T.muted};font-size:10px;line-height:1.5}
    .new-claim{display:grid;grid-template-columns:1fr auto;align-items:center;gap:16px;padding:22px;border:1px solid ${T.border};border-radius:18px;background:linear-gradient(120deg,#34231D,#211511)}.claim-id{display:flex;align-items:center;gap:8px;flex-wrap:wrap;font-weight:800;color:${T.peach};overflow-wrap:anywhere}.tag{display:inline-flex;align-items:center;gap:6px;padding:5px 8px;border:1px solid ${T.border};border-radius:999px;color:${T.muted};font-size:10px}.tag.good{color:#A8E0BD;border-color:rgba(115,198,155,.3)}.tag.bad{color:#FFB0A5;border-color:rgba(224,100,100,.35)}
    .security-hero{display:grid;grid-template-columns:1.1fr .9fr;align-items:center;gap:24px;padding:24px;border:1px solid ${T.border};border-radius:21px;background:linear-gradient(120deg,#34231D,#211511);overflow:hidden}.security-hero h2{margin:14px 0 10px;font-size:clamp(26px,4vw,37px);line-height:1.15}.security-hero p{color:${T.muted};font-size:12px;line-height:1.8}.security-image{display:block;width:100%;height:235px;object-fit:cover;border-radius:15px;border:1px solid ${T.border};background:${T.elevated}}
    .metric-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin:16px 0}.metric{min-width:0;padding:18px;border:1px solid ${T.border};border-radius:15px;background:${T.surface}}.metric-top{display:flex;align-items:center;justify-content:space-between;gap:8px;color:${T.muted};font-size:11px}.metric-value{margin-top:14px;font-size:24px;font-weight:850;overflow-wrap:anywhere}.metric-note{margin-top:6px;color:${T.muted};font-size:10px;line-height:1.6}.pill{display:inline-flex;align-items:center;gap:6px;padding:5px 8px;border:1px solid ${T.border};border-radius:999px;color:${T.muted};font-size:10px}.pill.good{color:#A8E0BD;border-color:rgba(115,198,155,.3)}.pill.bad{color:#FFB0A5;border-color:rgba(224,100,100,.35)}.security-columns{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:15px}.security-card{min-width:0;padding:20px;border:1px solid ${T.border};border-radius:16px;background:${T.surface}}.security-card h3{display:flex;align-items:center;gap:8px;margin:0 0 8px;font-size:15px}.security-card>p{color:${T.muted};font-size:11px;line-height:1.7}.event-list{display:grid;gap:9px;margin-top:14px}.event{padding:12px;border:1px solid ${T.border};border-radius:11px;background:rgba(31,20,16,.45);overflow-wrap:anywhere}.event-head{display:flex;align-items:flex-start;justify-content:space-between;gap:9px}.event-title{font-size:12px;font-weight:750}.event-meta{margin-top:7px;color:${T.muted};font-size:10px;line-height:1.7}.empty{padding:20px;text-align:center;color:${T.muted};border:1px dashed ${T.border};border-radius:12px;font-size:12px;line-height:1.7}.warning{margin-top:14px;padding:12px;border:1px solid rgba(229,173,88,.3);border-radius:11px;color:#EBCB9B;background:rgba(229,173,88,.06);font-size:11px;line-height:1.8}.footer{padding:22px 0;border-top:1px solid ${T.border};color:${T.muted};font-size:11px}.footer-inner{display:flex;justify-content:space-between;flex-wrap:wrap;gap:10px}.response-label{display:flex;align-items:center;gap:8px;margin-bottom:8px;color:${T.peach};font-weight:800}.record-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}.record{padding:12px;border:1px solid ${T.border};border-radius:10px;background:rgba(31,20,16,.4)}.record small{display:block;color:${T.muted};font-size:10px}.record strong{display:block;margin-top:4px;font-size:12px;overflow-wrap:anywhere}
    @media(max-width:1000px){.nav{align-items:flex-start}.nav-links{order:3;width:100%}.metric-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.workflow{grid-template-columns:repeat(3,minmax(0,1fr))}}
    @media(max-width:760px){.grid{grid-template-columns:repeat(2,minmax(0,1fr))}.security-hero,.security-columns{grid-template-columns:1fr}.security-image{height:190px}.new-claim{grid-template-columns:1fr}.workflow{grid-template-columns:repeat(2,minmax(0,1fr))}}
    @media(max-width:540px){.shell{width:calc(100% - 24px)}.main{padding-top:20px}.grid,.form-grid,.record-grid{grid-template-columns:1fr}.field.full{grid-column:auto}.nav-links{flex-wrap:nowrap;overflow-x:auto}.metric-grid{grid-template-columns:repeat(2,minmax(0,1fr))}h1{letter-spacing:-1.2px}.hero{padding:27px 21px;min-height:430px}.workflow{grid-template-columns:1fr 1fr}.status{margin-left:auto}}
  `;

  function featureCard(Icon, title, description, destination) {
    return <button type="button" className="feature" key={title} onClick={() => navigate(destination)}><span className="feature-icon"><Icon size={21} /></span><h3>{title}</h3><p>{description}</p></button>;
  }
  function renderHome() {
    return <>
      <section className="hero"><div className="hero-content"><div className="eyebrow"><HeartPulse size={16} /> Smarter Health Insurance Assistance</div><h1>Health claims,<br />made <span className="accent">simpler.</span></h1><p className="lead">Claimora brings AI assistance, hospital and doctor discovery, document readiness, claim workflow visibility and security monitoring into one calm, connected workspace.</p><div className="actions"><button className="btn primary" onClick={() => navigate("new-claim")}><Plus size={16} /> Start a New Claim <ArrowRight size={16} /></button><button className="btn" onClick={() => navigate("assistant")}><Bot size={16} /> Ask AI Assistant</button><button className="btn" onClick={() => navigate("documents")}><Upload size={16} /> Upload Documents</button></div></div></section>
      <div className="section-head"><div><h2>Start with what you need</h2><p>Helpful tools for your health insurance journey.</p></div><span className="tag"><Activity size={13} /> {backendStatus === "connected" ? "API connected" : backendStatus === "offline" ? "API offline" : "Checking API"}</span></div>
      <section className="grid">{featureCard(Plus,"Create a Claim","Enter basic details and generate a Claimora reference.","new-claim")}{featureCard(Bot,"AI Claim Assistant","Ask questions and receive a response from the connected RAG assistant.","assistant")}{featureCard(Building2,"Find Hospital","Search the hospital recommendation dataset.","hospitals")}{featureCard(Stethoscope,"Find Doctor","Search doctor records available through the backend.","doctors")}{featureCard(FileCheck2,"Document Readiness","Upload a policy or claim document for backend analysis.","documents")}{featureCard(ShieldAlert,"Fraud Analysis","Enter a claim reference to request claim-specific security analysis.","fraud")}</section>
      <div className="section-head"><div><h2>Your claim workflow</h2><p>The intended processing sequence across Claimora's agent workflow.</p></div></div>
      <section className="workflow">{WORKFLOW.map((step,i)=><div className="workflow-step" key={step}><span className="workflow-number">{String(i+1).padStart(2,"0")}</span><strong>{step}</strong><small>{["Coordinates the claim workflow","Checks policy eligibility","Checks submitted document integrity","Flags potential risk signals","Routes the claim decision process","Displays the available tracking status"][i]}</small></div>)}</section>
      <div className="section-head"><div><h2>Claimora workspace</h2><p>A simple starting point for your next claim.</p></div></div>
      <section className="new-claim"><div><div className="eyebrow"><ClipboardCheck size={15}/> Ready when you are</div><h3 style={{margin:"12px 0 7px"}}>Create your claim reference</h3><p className="muted" style={{margin:0,fontSize:12,lineHeight:1.7}}>Enter basic claim details, generate a unique Claim ID and submit the record to the connected claim API.</p></div><button className="btn primary" onClick={() => navigate("new-claim")}>Create Claim <ArrowRight size={15}/></button></section>
    </>;
  }
  function renderNewClaim() {
    return <section className="panel"><h2><ClipboardCheck color={T.coral} size={24}/> Start a New Claim</h2><p>Enter the claimant and treatment details. Claimora generates a Claim ID and submits the record to the connected claims API endpoint. If the API rejects the request, the generated reference is retained as a local draft.</p><div className="new-claim" style={{marginBottom:22}}><div><div className="muted" style={{fontSize:11,marginBottom:8}}>Automatically generated Claimora reference</div><div className="claim-id"><span>{newClaimId}</span><button className="btn small" type="button" onClick={() => GenCopy(newClaimId)}><Copy size={13}/> Copy ID</button></div></div><button className="btn" type="button" onClick={() => {setNewClaimId(makeClaimId());setClaimCreated(null);}}><RefreshCw size={14}/> Generate New ID</button></div>
      <form onSubmit={createClaim}><div className="form-grid"><div className="field"><label htmlFor="claimantName">Claimant full name *</label><input id="claimantName" className="control" value={claimForm.full_name} onChange={e=>updateClaimField("full_name",e.target.value)} required placeholder="Enter full name"/></div><div className="field"><label htmlFor="claimContact">Contact number or email *</label><input id="claimContact" className="control" value={claimForm.contact} onChange={e=>updateClaimField("contact",e.target.value)} required placeholder="Phone or email"/></div><div className="field"><label htmlFor="claimAge">Age *</label><input id="claimAge" type="number" min="1" max="120" className="control" value={claimForm.age} onChange={e=>updateClaimField("age",e.target.value)} required placeholder="Age"/></div><div className="field"><label htmlFor="claimEmail">Email *</label><input id="claimEmail" type="email" className="control" value={claimForm.email} onChange={e=>updateClaimField("email",e.target.value)} required placeholder="name@example.com"/></div><div className="field"><label htmlFor="claimAmount">Claim amount (₹) *</label><input id="claimAmount" type="number" min="0" step="0.01" className="control" value={claimForm.claim_amount} onChange={e=>updateClaimField("claim_amount",e.target.value)} required placeholder="Amount"/></div><div className="field"><label htmlFor="claimDiagnosis">Diagnosis / reason *</label><input id="claimDiagnosis" className="control" value={claimForm.diagnosis} onChange={e=>updateClaimField("diagnosis",e.target.value)} required placeholder="Diagnosis or treatment reason"/></div><div className="field"><label htmlFor="claimDate">Treatment date *</label><input id="claimDate" type="date" className="control" value={claimForm.treatment_date} onChange={e=>updateClaimField("treatment_date",e.target.value)} required/></div><div className="field"><label htmlFor="policyId">Existing policy ID *</label><input id="policyId" className="control" value={claimForm.policy_id} onChange={e=>updateClaimField("policy_id",e.target.value)} required placeholder="Enter policy ID"/></div><div className="field"><label htmlFor="claimTreatment">Treatment category</label><select id="claimTreatment" className="control" value={claimForm.treatment} onChange={e=>updateClaimField("treatment",e.target.value)}>{TREATMENTS.map(item=><option key={item}>{item}</option>)}</select></div><div className="field"><label htmlFor="claimHospital">Hospital (if known)</label><input id="claimHospital" className="control" value={claimForm.hospital} onChange={e=>updateClaimField("hospital",e.target.value)} placeholder="Hospital name"/></div><div className="field"><label htmlFor="claimDoctor">Doctor (optional)</label><input id="claimDoctor" className="control" value={claimForm.doctor} onChange={e=>updateClaimField("doctor",e.target.value)} placeholder="Doctor name"/></div><div className="field"><label htmlFor="claimInsurer">Insurance company</label><select id="claimInsurer" className="control" value={claimForm.insurer} onChange={e=>updateClaimField("insurer",e.target.value)}>{["Star Health","Care Health","Niva Bupa","ManipalCigna","Aditya Birla Health","HDFC ERGO","ICICI Lombard","Tata AIG","Bajaj Allianz","Other"].map(item=><option key={item}>{item}</option>)}</select></div><div className="field"><label htmlFor="claimType">Claim type</label><select id="claimType" className="control" value={claimForm.claim_type} onChange={e=>updateClaimField("claim_type",e.target.value)}><option>Reimbursement</option><option>Cashless</option></select></div><div className="field"><label htmlFor="claimCity">City</label><select id="claimCity" className="control" value={claimForm.city} onChange={e=>updateClaimField("city",e.target.value)}>{CITIES.map(item=><option key={item}>{item}</option>)}</select></div><div className="field full"><label htmlFor="claimNotes">Additional notes (optional)</label><textarea id="claimNotes" className="control" value={claimForm.notes} onChange={e=>updateClaimField("notes",e.target.value)} placeholder="Briefly describe what assistance you need"/></div></div><div className="actions"><button className="btn primary" type="submit" disabled={claimCreateLoading}>{claimCreateLoading?<LoaderCircle className="spinner" size={15}/>:<Plus size={15}/>} {claimCreateLoading?"Submitting...":"Create Claim & Generate ID"}</button></div></form>
      {claimCreateError&&<div className="result error">{claimCreateError}</div>}{claimCreated&&<div className="result"><div className="response-label">{claimCreated.backend_saved?<CheckCircle2 size={17}/>:<AlertTriangle size={17}/>} {claimCreated.backend_saved?"Claim record created":"Local claim draft created"}</div><div className="record-grid">{[["Claimora reference",claimCreated.claim_id],["Claimant",claimCreated.patient_name],["Policy ID",claimCreated.policy_number],["Treatment",claimCreated.treatment],["Claim amount",`₹${claimCreated.claim_amount}`],["Status",claimCreated.status],["Backend saved",claimCreated.backend_saved?"Yes":"No"],["Created",new Date(claimCreated.created_at).toLocaleString()]].map(([label,value])=><div className="record" key={label}><small>{label}</small><strong>{value||"Not supplied"}</strong></div>)}</div>{!claimCreated.backend_saved&&<div className="warning">Backend save failed: {claimCreated.backend_error||"Unknown API error"}. This ID is not yet available in backend tracking or claim analysis.</div>}<div className="actions"><button className="btn" onClick={()=>{setClaimId(claimCreated.claim_id);navigate("tracking");}}>Open Tracking</button><button className="btn" onClick={()=>{setFraudClaimId(claimCreated.claim_id);navigate("fraud");}}>Analyse Claim</button><button className="btn" onClick={()=>GenCopy(claimCreated.claim_id)}><Copy size={14}/> Copy Claim ID</button></div></div>}
    </section>;
  }
  function renderAssistant() {
    return <section className="panel"><h2><Bot color={T.coral} size={24}/> AI Claim Assistant</h2><p>Ask about claim steps, policy wording or commonly required documents. Your message is sent to the configured backend RAG assistant.</p><form onSubmit={askAssistant}><div className="field"><label htmlFor="question">Your message</label><textarea id="question" className="control" value={question} onChange={e=>setQuestion(e.target.value)} placeholder="Example: What documents should I prepare for a hospitalisation claim?" required/></div><div className="actions"><button className="btn primary" type="submit" disabled={chatLoading}>{chatLoading?<LoaderCircle className="spinner" size={16}/>:<Send size={16}/>} {chatLoading?"Sending...":"Send Message"}</button><button className="btn" type="button" onClick={()=>{setQuestion("");setChatAnswer("");setChatError("");}}><XCircle size={15}/> Clear</button></div></form>{chatError&&<div className="result error">{chatError}</div>}{chatAnswer&&<div className="result"><div className="response-label"><MessageCircle size={16}/> Assistant response</div>{chatAnswer}</div>}<p style={{marginTop:18}}>AI responses are informational. They do not guarantee claim approval or replace your insurer's policy terms.</p></section>;
  }
  function renderHospitals() {
    return <section className="panel"><h2><Building2 color={T.coral} size={24}/> Find Hospital</h2><p>Search the existing hospital recommendation service backed by your hospital Excel dataset.</p><form onSubmit={searchHospitals}><div className="form-grid"><div className="field"><label htmlFor="treatment">Treatment / procedure</label><select id="treatment" className="control" value={treatment} onChange={e=>setTreatment(e.target.value)}>{TREATMENTS.map(item=><option key={item}>{item}</option>)}</select></div><div className="field"><label htmlFor="city">City</label><select id="city" className="control" value={city} onChange={e=>setCity(e.target.value)}>{CITIES.map(item=><option key={item}>{item}</option>)}</select></div><div className="field"><label htmlFor="area">Area (optional)</label><input id="area" className="control" value={area} onChange={e=>setArea(e.target.value)} placeholder="e.g. Porur"/></div><div className="field"><label htmlFor="insurance">Insurance company (optional)</label><input id="insurance" className="control" value={insurance} onChange={e=>setInsurance(e.target.value)} placeholder="e.g. Star Health"/></div></div><div className="actions"><button className="btn primary" type="submit" disabled={hospitalLoading}>{hospitalLoading?<LoaderCircle className="spinner" size={16}/>:<Search size={16}/>} {hospitalLoading?"Searching...":"Search Hospitals"}</button></div></form>{hospitalError&&<div className="result error">{hospitalError}</div>}{hospitalResults&&<div className="result"><div className="response-label"><Building2 size={16}/> Hospital recommendations</div><div className="record-grid">{resultEntries(hospitalResults).map(([key,value])=><div className="record" key={String(key)}><small>{String(key).replaceAll("_"," ")}</small><strong style={{whiteSpace:"pre-wrap"}}>{prettyValue(value)}</strong></div>)}</div></div>}<p style={{marginTop:16}}>Confirm treatment suitability, network status and cashless eligibility with the hospital and insurer directly.</p></section>;
  }
  function renderDoctors() {
    return <section className="panel"><h2><Stethoscope color={T.coral} size={24}/> Find Doctor</h2><p>Search the doctor recommendation service backed by the existing doctors.pdf dataset and its extracted records.</p><form onSubmit={searchDoctors}><div className="form-grid"><div className="field"><label htmlFor="doctorTreatment">Treatment / specialty</label><select id="doctorTreatment" className="control" value={doctorTreatment} onChange={e=>setDoctorTreatment(e.target.value)}>{TREATMENTS.map(item=><option key={item}>{item}</option>)}</select></div><div className="field"><label htmlFor="doctorCity">City</label><select id="doctorCity" className="control" value={doctorCity} onChange={e=>setDoctorCity(e.target.value)}>{CITIES.map(item=><option key={item}>{item}</option>)}</select></div><div className="field"><label htmlFor="doctorArea">Area (optional)</label><input id="doctorArea" className="control" value={doctorArea} onChange={e=>setDoctorArea(e.target.value)} placeholder="e.g. Porur"/></div></div><div className="actions"><button className="btn primary" type="submit" disabled={doctorLoading}>{doctorLoading?<LoaderCircle className="spinner" size={16}/>:<Search size={16}/>} {doctorLoading?"Searching...":"Search Doctors"}</button></div></form>{doctorError&&<div className="result error">{doctorError}</div>}{doctorResults&&<div className="result"><div className="response-label"><UserRound size={16}/> Doctor search results</div><div className="record-grid">{resultEntries(doctorResults).map(([key,value])=><div className="record" key={String(key)}><small>{String(key).replaceAll("_"," ")}</small><strong style={{whiteSpace:"pre-wrap"}}>{prettyValue(value)}</strong></div>)}</div></div>}<div className="warning"><AlertTriangle size={14} style={{verticalAlign:"middle",marginRight:6}}/>Results depend on the current doctor-search endpoint and extracted records. Confirm qualifications, availability and treatment suitability directly with the provider.</div></section>;
  }
  function renderDocuments() {
    return <div style={{display:"grid",gap:16}}>
      <section className="panel"><h2><FileText color={T.coral} size={24}/> Document Readiness</h2><p>Analyse a readable policy PDF using the backend readiness endpoint. Treatment and hospital details are required by the API.</p>
        <form onSubmit={analyzeDocuments}><div className="form-grid">
          <div className="field"><label htmlFor="policyFile">Policy PDF *</label><div className="file-drop"><Upload size={29} color={T.peach}/><p>Select a readable policy PDF (maximum 10 MB)</p><input id="policyFile" type="file" accept=".pdf,application/pdf" onChange={e=>setFiles(Array.from(e.target.files||[]))} required/>{files.length>0&&<p className="muted">Selected: {files[0].name} · {(files[0].size/1024/1024).toFixed(2)} MB</p>}</div></div>
          <div className="field"><label htmlFor="readinessTreatment">Planned treatment *</label><select id="readinessTreatment" className="control" value={readinessTreatment} onChange={e=>setReadinessTreatment(e.target.value)}>{TREATMENTS.map(item=><option key={item}>{item}</option>)}</select></div>
          <div className="field"><label htmlFor="readinessHospital">Hospital name *</label><input id="readinessHospital" className="control" value={readinessHospital} onChange={e=>setReadinessHospital(e.target.value)} required placeholder="Enter planned hospital"/></div>
          <div className="field"><label htmlFor="readinessCity">City</label><select id="readinessCity" className="control" value={readinessCity} onChange={e=>setReadinessCity(e.target.value)}>{CITIES.map(item=><option key={item}>{item}</option>)}</select></div>
          <div className="field"><label htmlFor="readinessExpense">Estimated expense (₹)</label><input id="readinessExpense" type="number" min="0" step="0.01" className="control" value={readinessExpense} onChange={e=>setReadinessExpense(e.target.value)} placeholder="Optional estimate"/></div>
        </div><div className="actions"><button className="btn primary" type="submit" disabled={readinessLoading}>{readinessLoading?<LoaderCircle className="spinner" size={16}/>:<ClipboardCheck size={16}/>} {readinessLoading?"Analysing document...":"Analyse Policy Readiness"}</button><button className="btn" type="button" onClick={()=>{setFiles([]);setReadinessResult(null);setReadinessError("");const el=document.getElementById("policyFile");if(el)el.value="";}}><XCircle size={15}/> Clear PDF</button></div></form>
        {readinessError&&<div className="result error">{readinessError}</div>}{readinessResult&&<div className="result"><div className="response-label"><FileCheck2 size={16}/> Document analysis response</div><div className="record-grid">{resultEntries(readinessResult).map(([key,value])=><div className="record" key={String(key)}><small>{String(key).replaceAll("_"," ")}</small><strong style={{whiteSpace:"pre-wrap"}}>{prettyValue(value)}</strong></div>)}</div></div>}
        <div className="warning"><LockKeyhole size={14} style={{verticalAlign:"middle",marginRight:6}}/>This is preliminary keyword screening, not a coverage decision or guarantee of claim approval.</div>
      </section>
      <section className="panel"><h2><Upload color={T.coral} size={24}/> Secure Claim Document Upload</h2><p>Store a supporting document using the security document API. This upload sends all required multipart fields: claim_id, user and document.</p>
        <form onSubmit={uploadSecureDocument}><div className="form-grid">
          <div className="field"><label htmlFor="secureClaimId">Claim ID *</label><input id="secureClaimId" className="control" value={secureDocumentClaimId} onChange={e=>setSecureDocumentClaimId(e.target.value)} required placeholder="Enter an existing Claim ID"/></div>
          <div className="field"><label htmlFor="secureDocumentFile">Supporting document *</label><input id="secureDocumentFile" className="control" type="file" accept=".pdf,.png,.jpg,.jpeg,.doc,.docx" onChange={e=>setSecureDocument(e.target.files?.[0]||null)} required/></div>
        </div>{secureDocument&&<p className="muted">Selected: {secureDocument.name} · {(secureDocument.size/1024/1024).toFixed(2)} MB</p>}<div className="actions"><button className="btn primary" type="submit" disabled={secureUploadLoading}>{secureUploadLoading?<LoaderCircle className="spinner" size={16}/>:<Upload size={16}/>} {secureUploadLoading?"Uploading...":"Upload Secure Document"}</button></div></form>
        {secureUploadError&&<div className="result error">{secureUploadError}</div>}{secureUploadResult&&<div className="result"><div className="response-label"><CheckCircle2 size={16}/> Document upload response</div>{displayData(secureUploadResult)}</div>}
      </section>
    </div>;
  }

  function renderTracking() {
    return <section className="panel"><h2><Activity color={T.coral} size={24}/> Claim Tracking</h2><p>Look up a reference in the configured demo-claims records. Locally created drafts will not appear here until they are saved by a connected backend claim-creation endpoint.</p><form onSubmit={checkTracking}><div className="field"><label htmlFor="claimId">Claim reference / policy ID</label><input id="claimId" className="control" value={claimId} onChange={e=>setClaimId(e.target.value)} placeholder="e.g. CLM-20261013-AB12" required/></div><div className="actions"><button className="btn primary" type="submit" disabled={trackingLoading}>{trackingLoading?<LoaderCircle className="spinner" size={16}/>:<Search size={16}/>} {trackingLoading?"Checking...":"Check Status"}</button></div></form>{trackingError&&<div className="result error">{trackingError}</div>}{trackingResult&&<div className="result"><div className="response-label"><CheckCircle2 size={16}/> Matching claim record</div><div className="record-grid">{Object.entries(trackingResult).map(([key,value])=><div className="record" key={key}><small>{key.replaceAll("_"," ")}</small><strong>{typeof value==="object"?JSON.stringify(value):String(value??"—")}</strong></div>)}</div></div>}<div className="warning"><AlertTriangle size={14} style={{verticalAlign:"middle",marginRight:6}}/>This screen does not connect to a live insurer tracking system unless the backend is explicitly integrated with that insurer.</div></section>;
  }
  function renderFraud() {
    return <section className="panel"><h2><ShieldAlert color={T.coral} size={24}/> Fraud & Claim Security Analysis</h2><p>Enter a claim reference to request a claim-specific analysis from the security analyzer. The result depends on the backend request schema and the claim data available to it.</p><form onSubmit={runFraudCheck}><div className="field"><label htmlFor="fraudClaimId">Claim ID</label><input id="fraudClaimId" className="control" value={fraudClaimId} onChange={e=>setFraudClaimId(e.target.value)} placeholder="Enter Claimora or backend claim ID" required/></div><div className="actions"><button className="btn primary" type="submit" disabled={fraudLoading}>{fraudLoading?<LoaderCircle className="spinner" size={16}/>:<ShieldCheck size={16}/>} {fraudLoading?"Analysing claim...":"Analyse Claim"}</button></div></form>{fraudError&&<div className="result error">{fraudError}</div>}{fraudResult&&<div className="result"><div className="response-label"><ShieldCheck size={16}/> Claim analysis response</div>{displayData(fraudResult)}</div>}<div className="warning"><AlertTriangle size={14} style={{verticalAlign:"middle",marginRight:6}}/>The existing GET /api/fraud/test endpoint only verifies that the fraud service is running. It is intentionally not used as a substitute for analysing the claim ID.</div></section>;
  }
  function metric(Icon,label,value,note,state) { return <div className="metric"><div className="metric-top"><span>{label}</span><Icon size={18} color={T.peach}/></div><div className="metric-value">{value}</div><div className="metric-note">{note}</div>{state&&<span className={`pill ${state}`} style={{marginTop:9}}>{state==="good"?"Responding":"Needs checking"}</span>}</div>; }
  function renderSecurity() {
    const backendOk=Boolean(securityBackend); const analyzerOk=securityAnalyzer?.status==="healthy"; const auditOk=auditHealth?.status==="healthy";
    const features=Array.isArray(securityAnalyzer?.features)?securityAnalyzer.features:[]; const recentEvents=[...auditEvents].reverse().slice(0,10);
    return <><section className="security-hero"><div><div className="eyebrow"><LockKeyhole size={16}/> Claimora Security Centre</div><h2>Security status, backed by your API.</h2><p>Live checks for backend status, claim security analyzer health, audit service health and stored audit records. An available endpoint does not prove that every security control is enabled.</p><div className="actions"><button className="btn primary" onClick={refreshSecurity} disabled={securityLoading}>{securityLoading?<LoaderCircle className="spinner" size={16}/>:<RefreshCw size={16}/>} {securityLoading?"Refreshing...":"Refresh Security Data"}</button><button className="btn" onClick={()=>window.open(`${API_BASE}/docs`,"_blank","noopener,noreferrer")}><ExternalLink size={15}/> API Docs</button></div><p>Last checked: {securityCheckedAt||"Not checked yet"}</p></div><img className="security-image" src={SECURITY_IMAGE} alt="Cybersecurity and digital protection" loading="lazy" onError={e=>{e.currentTarget.style.display="none";}}/></section>
      {securityError&&<div className="result error">{securityError}</div>}
      <section className="metric-grid">{metric(Wifi,"Backend API",backendOk?"Responding":"Unavailable",backendOk?`Status: ${securityBackend.status||"response received"}`:"Unable to read /status",backendOk?"good":"bad")}{metric(ShieldCheck,"Claim Analyzer",analyzerOk?"Healthy":"Unknown","GET /api/security/health",analyzerOk?"good":"bad")}{metric(Database,"Audit Service",auditOk?"Healthy":"Unknown",auditHealth?.storage?`Storage: ${auditHealth.storage}`:"GET audit health endpoint",auditOk?"good":"bad")}{metric(Activity,"Audit Events",auditCount===null?"—":auditCount,"Count returned by the backend audit API",auditCount===null?"bad":"good")}</section>
      <section className="security-columns"><div className="security-card"><h3><ShieldCheck size={18} color={T.coral}/> Service checks</h3><p>Results returned by backend health endpoints.</p><div className="event-list">{[["Backend status",backendOk?"Responding":"Unavailable",backendMessage,backendOk],["Claim security analyzer",analyzerOk?"Healthy":"Unknown",securityAnalyzer?.module||"No module metadata returned.",analyzerOk],["Audit trail",auditOk?"Healthy":"Unknown",`${auditHealth?.module||"No audit metadata returned."}${auditHealth?.storage?` · Storage: ${auditHealth.storage}`:""}`,auditOk]].map(([title,status,meta,ok])=><div className="event" key={title}><div className="event-head"><span className="event-title">{title}</span><span className={`pill ${ok?"good":"bad"}`}>{status}</span></div><div className="event-meta">{meta}</div></div>)}</div></div>
      <div className="security-card"><h3><ClipboardCheck size={18} color={T.coral}/> Analyzer capabilities</h3><p>Capabilities advertised by the backend health endpoint, not individual test results.</p>{features.length?<div className="event-list">{features.map((feature,index)=><div className="event" key={`${feature}-${index}`}><CheckCircle2 size={15} color={T.peach} style={{verticalAlign:"middle",marginRight:8}}/>{feature}</div>)}</div>:<div className="empty">No feature list returned by /api/security/health.</div>}</div></section>
      <section className="panel" style={{marginTop:15}}><div className="section-head" style={{marginTop:0}}><div><h2><Activity size={21} color={T.coral}/> Recent audit events</h2><p>Records returned by GET /api/security/audit/. These are stored audit events, not automatically detected attacks.</p></div><span className="pill">{auditEvents.length} loaded</span></div>{recentEvents.length?<div className="event-list">{recentEvents.map((event,index)=>{const title=event.action||event.event||event.type||"Audit event";const status=event.status||event.decision||"Recorded";const risk=event.risk_level||event.risk||"Not specified";const time=event.timestamp||event.created_at||event.time||"Not supplied";const risky=String(risk).toLowerCase().includes("high")||String(status).toLowerCase().includes("block");return <div className="event" key={`${event.id||event.event_id||index}-${time}`}><div className="event-head"><span className="event-title">{title}</span><span className={`pill ${risky?"bad":""}`}>{String(status)}</span></div><div className="event-meta">{`Time: ${time} · Claim: ${event.claim_id||"Not linked"} · Risk: ${risk}`}{event.security_score!==undefined?` · Security score: ${event.security_score}`:""}{event.user?` · Actor: ${event.user}`:""}{event.decision?` · Decision: ${event.decision}`:""}</div></div>;})}</div>:<div className="empty"><Clock3 size={22}/><p>{auditCount===null?"Audit events could not be loaded. Check the backend response.":"The backend returned no audit events. No sample threat events have been invented."}</p></div>}<div className="warning"><AlertTriangle size={15} style={{verticalAlign:"middle",marginRight:7}}/>Security notice: protect audit event creation and sensitive claim data with authentication and authorization before deployment.</div></section></>;
  }
  function GenCopy(value) { try { navigator.clipboard?.writeText(value); } catch { /* clipboard permission may be unavailable */ } }

  let content;
  switch(page) {
    case "new-claim": content=renderNewClaim(); break;
    case "assistant": content=renderAssistant(); break;
    case "hospitals": content=renderHospitals(); break;
    case "doctors": content=renderDoctors(); break;
    case "documents": content=renderDocuments(); break;
    case "tracking": content=renderTracking(); break;
    case "fraud": content=renderFraud(); break;
    case "security": content=renderSecurity(); break;
    default: content=renderHome();
  }

  return <div className="app"><style>{css}</style><header className="topbar"><div className="shell nav"><button className="brand" onClick={()=>navigate("home")} aria-label="Claimora Home"><span className="brand-icon"><HeartPulse size={24}/></span><span><span className="brand-name">Claimora</span><span className="brand-sub">SMART CLAIM ASSISTANCE</span></span></button><nav className="nav-links" aria-label="Main navigation">{navItems.map(({id,label,icon:Icon})=><button key={id} className={`nav-link ${page===id?"active":""}`} onClick={()=>navigate(id)}><Icon size={15}/>{label}</button>)}<button className={`nav-link ${page==="new-claim"?"active":""}`} onClick={()=>navigate("new-claim")}><Plus size={15}/>New Claim</button><button className={`nav-link ${page==="fraud"?"active":""}`} onClick={()=>navigate("fraud")}><ShieldAlert size={15}/>Fraud</button></nav><div className={`status ${backendStatus==="connected"?"online":backendStatus==="offline"?"offline":""}`} title={backendMessage}><span className="dot"/>{backendStatus==="connected"?<Wifi size={14}/>:backendStatus==="offline"?<WifiOff size={14}/>:<LoaderCircle className="spinner" size={14}/>}{backendStatus==="connected"?"Backend Connected":backendStatus==="offline"?"Backend Offline":"Checking"}</div></div></header><main className="shell main">{content}</main><footer className="footer"><div className="shell footer-inner"><span>© {new Date().getFullYear()} Claimora · AI Agent for Health Insurance Claim Assistance</span><span><MapPin size={13} style={{verticalAlign:"middle"}}/> Secure, backend-connected claim workspace</span></div></footer></div>;
}
