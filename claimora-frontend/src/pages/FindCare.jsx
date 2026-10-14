import React, { useState } from "react";
import {
  Building2, Stethoscope, Search, MapPin, ShieldCheck,
  LoaderCircle, UserRound, ArrowUpRight
} from "lucide-react";
import "./FindCare.css";

const API = "http://127.0.0.1:8000";

const treatments = [
  "Appendectomy", "Kidney Stone", "Hernia Repair",
  "Gallbladder Surgery", "Thyroid Surgery", "Sinus Surgery",
  "Emergency Care", "General Surgery", "Cardiac Evaluation",
  "Cataract Surgery", "Orthopaedic Treatment", "Maternity Care"
];

const cities = ["Chennai", "Bengaluru", "Hyderabad", "Mumbai", "Delhi"];

const insurers = [
  "Any / not specified", "RK Health Insurance", "Star Health",
  "Care Health", "Niva Bupa", "ManipalCigna", "Aditya Birla Health",
  "HDFC ERGO", "ICICI Lombard", "Tata AIG", "Bajaj Allianz"
];

export default function FindCare() {
  const [tab, setTab] = useState("hospital");
  const [treatment, setTreatment] = useState("Kidney Stone");
  const [city, setCity] = useState("Chennai");
  const [area, setArea] = useState("");
  const [insurance, setInsurance] = useState("Any / not specified");
  const [results, setResults] = useState([]);
  const [status, setStatus] = useState("");
  const [source, setSource] = useState("");
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  async function searchCare(event) {
    event.preventDefault();
    setLoading(true);
    setSearched(true);
    setResults([]);
    setStatus("");
    setSource("");

    const endpoint = tab === "doctor"
      ? "/api/recommendations/doctors/search"
      : "/api/recommendations/search";

    const payload = {
      treatment,
      city,
      area: area.trim(),
      insurance_provider: insurance === "Any / not specified" ? "" : insurance,
      insurance: insurance === "Any / not specified" ? "" : insurance
    };

    try {
      const response = await fetch(API + endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || data.message || `Request failed (${response.status})`);
      }

      const items = tab === "doctor"
        ? (Array.isArray(data.doctors) ? data.doctors : [])
        : (Array.isArray(data.hospitals)
            ? data.hospitals
            : Array.isArray(data.results)
              ? data.results
              : Array.isArray(data.recommendations)
                ? data.recommendations
                : []);

      setResults(items);
      setSource(data.source || "");

      if (items.length) {
        setStatus(`${items.length} ${tab === "doctor" ? "doctor" : "hospital"} record(s) returned by the recommendation service.`);
      } else {
        setStatus(data.ai_fallback_used && data.ai_guidance
          ? "No verified matching records were found. General AI guidance is available, but it is not a verified provider result."
          : `No matching ${tab === "doctor" ? "doctors" : "hospitals"} were returned. Try another treatment or area.`);
      }
    } catch (error) {
      setStatus(`Search failed: ${error.message}. Confirm that the Claimora backend is running on port 8000.`);
    } finally {
      setLoading(false);
    }
  }

  function changeTab(nextTab) {
    setTab(nextTab);
    setResults([]);
    setStatus("");
    setSource("");
    setSearched(false);
  }

  return (
    <main className="claimora-care">
      <header className="care-heading">
        <span className="care-eyebrow">CLAIMORA · HEALTHCARE DIRECTORY</span>
        <h1>Find hospitals and care</h1>
        <p>Discover provider records using treatment, location and insurance preferences.</p>
      </header>

      <nav className="care-tabs" aria-label="Care search type">
        <button type="button" className={tab === "hospital" ? "care-tab active" : "care-tab"} onClick={() => changeTab("hospital")}>
          <Building2 size={19} /> Find Hospital
        </button>
        <button type="button" className={tab === "doctor" ? "care-tab active" : "care-tab"} onClick={() => changeTab("doctor")}>
          <Stethoscope size={19} /> Find Doctor
        </button>
      </nav>

      <section className="care-panel">
        <div className="care-panel-heading">
          <span className="care-icon">
            {tab === "hospital" ? <Building2 size={23} /> : <Stethoscope size={23} />}
          </span>
          <div>
            <h2>{tab === "hospital" ? "Find Hospital" : "Find Doctor"}</h2>
            <p>{tab === "hospital"
              ? "Search hospitals using your care requirements."
              : "Search the existing doctor directory and procedure records."}</p>
          </div>
        </div>

        <form className="care-form" onSubmit={searchCare}>
          <label>
            Treatment or procedure
            <select value={treatment} onChange={e => setTreatment(e.target.value)}>
              {treatments.map(item => <option key={item} value={item}>{item}</option>)}
            </select>
          </label>

          <label>
            City
            <select value={city} onChange={e => setCity(e.target.value)}>
              {cities.map(item => <option key={item} value={item}>{item}</option>)}
            </select>
          </label>

          <label>
            Area or neighbourhood
            <input value={area} onChange={e => setArea(e.target.value)} placeholder="e.g. Porur, Adyar, OMR" />
          </label>

          <label>
            Insurance provider
            <select value={insurance} onChange={e => setInsurance(e.target.value)}>
              {insurers.map(item => <option key={item} value={item}>{item}</option>)}
            </select>
          </label>

          <button className="care-submit" type="submit" disabled={loading}>
            {loading ? <LoaderCircle className="care-spin" size={18} /> : <Search size={18} />}
            {loading ? "Searching..." : tab === "hospital" ? "Find Hospitals" : "Find Doctors"}
          </button>
        </form>

        <div className="care-notice">
          <ShieldCheck size={18} />
          Verify doctor credentials, hospital availability, insurance network status and cashless eligibility directly with the provider.
        </div>
      </section>

      <section className="care-results" aria-live="polite">
        <div className="care-results-heading">
          <div>
            <span className="care-eyebrow">RECOMMENDATION SERVICE</span>
            <h2>{tab === "hospital" ? "Hospital results" : "Doctor results"}</h2>
          </div>
          {source && <span className="care-source">Source: {source}</span>}
        </div>

        {loading && <p className="care-status">Searching the recommendation service…</p>}
        {!loading && status && <p className="care-status">{status}</p>}

        {!loading && searched && results.length > 0 && (
          <div className="care-result-grid">
            {results.map((item, index) => {
              const name = tab === "doctor"
                ? (item.doctor_name || item.name || "Doctor record")
                : (item.hospital || item.hospital_name || item.name || "Hospital record");

              const specialty = item.specialty || item.speciality || item.department || "";
              const hospital = item.hospital || item.hospital_name || "";
              const location = [
                item.branch_area || item.area || item.search_location,
                item.city || city
              ].filter(Boolean).join(", ");

              const key = item.record || item.id || item.doctor_id || item.hospital_id || `${name}-${index}`;

              return (
                <article className="care-result-card" key={key}>
                  <div className="care-result-top">
                    <span className="care-result-icon">
                      {tab === "hospital" ? <Building2 size={22} /> : <UserRound size={22} />}
                    </span>
                    {item.score != null && <span className="care-score">{item.score} match score</span>}
                  </div>

                  <h3>{name}</h3>
                  {specialty && <p className="care-specialty">{specialty}</p>}
                  {tab === "doctor" && hospital && <p><strong>Hospital:</strong> {hospital}</p>}
                  {location && <p className="care-result-location"><MapPin size={15} /> {location}</p>}
                  {item.disease_treatment && <p><strong>Treatment:</strong> {item.disease_treatment}</p>}
                  {item.relevant_procedure && <p><strong>Procedure:</strong> {item.relevant_procedure}</p>}
                  {item.procedure_clinical_history && <p><strong>Clinical context:</strong> {item.procedure_clinical_history}</p>}
                  {item.insurance_companies && <p><strong>Insurance:</strong> {Array.isArray(item.insurance_companies) ? item.insurance_companies.join(", ") : item.insurance_companies}</p>}
                  {item.cashless && <p><strong>Cashless:</strong> {String(item.cashless)}</p>}
                  {Array.isArray(item.match_reasons) && item.match_reasons.length > 0 && (
                    <div className="care-reasons">{item.match_reasons.map(reason => <span key={reason}>{reason}</span>)}</div>
                  )}
                  {item.verification_source && <p className="care-verification">Dataset source: {item.verification_source}</p>}
                  {item.hospital_address && <p className="care-address">{item.hospital_address}</p>}
                  <div className="care-card-footer">
                    <span>Record {item.record || index + 1}</span>
                    <ArrowUpRight size={16} />
                  </div>
                </article>
              );
            })}
          </div>
        )}

        {!loading && searched && results.length === 0 && (
          <div className="care-empty">
            {tab === "doctor" ? <Stethoscope size={28} /> : <Building2 size={28} />}
            <h3>No verified matches to display</h3>
            <p>Change the treatment or location and search again. General AI guidance is not shown as a verified provider record.</p>
          </div>
        )}

        {!searched && (
          <div className="care-empty">
            <Search size={28} />
            <h3>Ready to find care?</h3>
            <p>Choose your preferences above, then select {tab === "hospital" ? "Find Hospitals" : "Find Doctors"} to view matching records.</p>
          </div>
        )}
      </section>

      <p className="care-disclaimer">
        Recommendations are informational. Confirm availability, credentials, treatment suitability and insurance coverage directly with the provider.
      </p>
    </main>
  );
}
