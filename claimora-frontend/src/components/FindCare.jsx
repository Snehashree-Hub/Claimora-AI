import React, { useEffect, useMemo, useState } from "react";

const API_BASE = (
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000"
).replace(/\/+$/, "");

const FALLBACK_HOSPITAL_TREATMENTS = [
  "Appendectomy",
  "Emergency Care",
  "Gallbladder Surgery",
  "General Surgery",
  "Hernia Repair",
];

const FALLBACK_AREAS = [
  "Adyar", "Ambattur", "Anna Nagar", "Guindy", "Kilpauk",
  "Mylapore", "OMR", "Porur", "T Nagar", "Tambaram", "Velachery",
];

const FALLBACK_INSURANCE = [
  "All Insurance", "Star Health", "Care", "Niva Bupa",
  "ManipalCigna", "Aditya Birla", "HDFC ERGO",
  "ICICI Lombard", "Tata AIG", "Bajaj Allianz",
];

function listFrom(source, keys, fallback = []) {
  if (Array.isArray(source)) return source.filter(Boolean);

  if (source && typeof source === "object") {
    for (const key of keys) {
      if (Array.isArray(source[key])) return source[key].filter(Boolean);
    }
  }

  return fallback;
}

function recordsFrom(data, mode) {
  if (Array.isArray(data)) return data;

  const keys = mode === "hospital"
    ? ["hospitals", "results", "items", "records", "matches"]
    : ["doctors", "results", "items", "records", "matches"];

  for (const key of keys) {
    if (Array.isArray(data?.[key])) return data[key];
  }

  if (data?.data && data.data !== data) {
    return recordsFrom(data.data, mode);
  }

  return [];
}

function valueOf(record, keys, fallback = "Not provided") {
  for (const key of keys) {
    const value = record?.[key];
    if (value !== undefined && value !== null && value !== "") {
      return Array.isArray(value) ? value.join(", ") : String(value);
    }
  }
  return fallback;
}

async function request(path, body) {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(
      data.detail || data.message || `Request failed (${response.status})`
    );
  }

  return data;
}

export default function FindCare() {
  const [mode, setMode] = useState("hospital");
  const [options, setOptions] = useState({});
  const [treatment, setTreatment] = useState("Appendectomy");
  const [city, setCity] = useState("Chennai");
  const [area, setArea] = useState("Any Area");
  const [insurance, setInsurance] = useState("All Insurance");
  const [results, setResults] = useState(null);
  const [guidance, setGuidance] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let active = true;

    fetch(`${API_BASE}/api/recommendations/options`)
      .then(async (response) => {
        const data = await response.json();
        if (!response.ok) throw new Error("Could not load recommendation options");
        return data;
      })
      .then((data) => {
        if (active) setOptions(data);
      })
      .catch((err) => {
        if (active) setError(`Options could not be loaded: ${err.message}`);
      });

    return () => {
      active = false;
    };
  }, []);

  const activeOptions = mode === "hospital"
    ? options.hospital_options
    : options.doctor_options;

  const treatments = useMemo(() => listFrom(
    activeOptions,
    ["treatments", "procedures", "treatment_options"],
    FALLBACK_HOSPITAL_TREATMENTS
  ), [activeOptions]);

  const areas = useMemo(() => {
    const values = listFrom(
      activeOptions,
      ["areas", "area_options", "locations"],
      FALLBACK_AREAS
    );
    return ["Any Area", ...values.filter(
      (value) => value !== "Any Area"
    )];
  }, [activeOptions]);

  const cities = useMemo(() => listFrom(
    options,
    ["city_options", "cities"],
    ["Chennai"]
  ), [options]);

  const insurers = useMemo(() => listFrom(
    options,
    ["insurance_options", "insurers"],
    FALLBACK_INSURANCE
  ), [options]);

  useEffect(() => {
    if (treatments.length && !treatments.includes(treatment)) {
      setTreatment(treatments[0]);
    }
  }, [treatments, treatment]);

  async function search(event) {
    event.preventDefault();
    setLoading(true);
    setError("");
    setResults(null);
    setGuidance("");

    try {
      const path = mode === "hospital"
        ? "/api/recommendations/search"
        : "/api/recommendations/doctors/search";

      const body = {
        treatment,
        city,
        area: area === "Any Area" ? "" : area,
        insurance_company: insurance === "All Insurance" ? "" : insurance,
        hospital: "",
        limit: 10,
      };

      const data = await request(path, body);
      setResults(data);
      setGuidance(data.ai_guidance || "");

      if (!data.success && data.message) {
        setGuidance(data.message);
      }
    } catch (err) {
      setError(err.message || "Unable to search the recommendation dataset.");
    } finally {
      setLoading(false);
    }
  }

  const records = recordsFrom(results, mode);

  const styles = {
    page: {
      color: "#f9e9df",
      background: "linear-gradient(135deg,#241713,#39231e 60%,#4b2925)",
      border: "1px solid #70443b",
      borderRadius: 20,
      padding: 24,
    },
    muted: { color: "#d3b9ac", lineHeight: 1.6 },
    label: {
      display: "block",
      marginBottom: 7,
      color: "#f5c9b7",
      fontSize: 13,
      fontWeight: 600,
    },
    control: {
      boxSizing: "border-box",
      width: "100%",
      padding: "12px 13px",
      border: "1px solid #775148",
      borderRadius: 10,
      background: "#2b1b18",
      color: "#fff2eb",
      outlineColor: "#ff9b7c",
    },
    button: {
      padding: "11px 16px",
      borderRadius: 10,
      border: "1px solid #8d5c4d",
      background: "#3b2822",
      color: "#ffe5d9",
      cursor: "pointer",
      fontWeight: 700,
    },
    primary: {
      background: "linear-gradient(135deg,#ff9978,#e97861)",
      color: "#281713",
      border: "none",
    },
    card: {
      background: "rgba(30,18,15,.75)",
      border: "1px solid #694239",
      borderRadius: 14,
      padding: 17,
      minWidth: 0,
    },
  };

  return (
    <section style={styles.page}>
      <div style={{ display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
        <div style={{
          width: 46, height: 46, borderRadius: 13,
          display: "grid", placeItems: "center",
          background: "#5a3027", color: "#ffb397", fontSize: 23,
        }}>✚</div>
        <div>
          <h2 style={{ margin: 0, fontSize: 25 }}>Find Care</h2>
          <p style={{ ...styles.muted, margin: "5px 0 0" }}>
            Search your connected hospital and doctor datasets.
          </p>
        </div>
      </div>

      <div style={{ display: "flex", gap: 10, margin: "22px 0", flexWrap: "wrap" }}>
        <button
          type="button"
          onClick={() => { setMode("hospital"); setResults(null); setError(""); setGuidance(""); }}
          style={{ ...styles.button, ...(mode === "hospital" ? styles.primary : {}) }}
        >Find Hospital</button>
        <button
          type="button"
          onClick={() => { setMode("doctor"); setResults(null); setError(""); setGuidance(""); }}
          style={{ ...styles.button, ...(mode === "doctor" ? styles.primary : {}) }}
        >Find Doctor</button>
      </div>

      <form onSubmit={search}>
        <div style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit,minmax(200px,1fr))",
          gap: 16,
        }}>
          <div>
            <label style={styles.label} htmlFor="fc-treatment">Treatment / Procedure</label>
            <select id="fc-treatment" style={styles.control} value={treatment}
              onChange={(event) => setTreatment(event.target.value)}>
              {treatments.map((item) => <option key={item} value={item}>{item}</option>)}
            </select>
          </div>
          <div>
            <label style={styles.label} htmlFor="fc-city">City</label>
            <select id="fc-city" style={styles.control} value={city}
              onChange={(event) => setCity(event.target.value)}>
              {cities.map((item) => <option key={item} value={item}>{item}</option>)}
            </select>
          </div>
          <div>
            <label style={styles.label} htmlFor="fc-area">Area</label>
            <select id="fc-area" style={styles.control} value={area}
              onChange={(event) => setArea(event.target.value)}>
              {areas.map((item) => <option key={item} value={item}>{item}</option>)}
            </select>
          </div>
          {mode === "hospital" && (
            <div>
              <label style={styles.label} htmlFor="fc-insurance">Insurance Company</label>
              <select id="fc-insurance" style={styles.control} value={insurance}
                onChange={(event) => setInsurance(event.target.value)}>
                {insurers.map((item) => <option key={item} value={item}>{item}</option>)}
              </select>
            </div>
          )}
        </div>
        <button type="submit" disabled={loading} style={{
          ...styles.button, ...styles.primary, marginTop: 20,
          opacity: loading ? 0.7 : 1,
        }}>
          {loading ? "Searching dataset..." : `Search ${mode === "hospital" ? "Hospitals" : "Doctors"}`}
        </button>
      </form>

      {error && <p role="alert" style={{
        marginTop: 18, padding: 13, borderRadius: 10,
        background: "#512824", color: "#ffd4c6",
      }}>{error}</p>}

      {results && (
        <div style={{ marginTop: 24 }}>
          <h3 style={{ marginBottom: 8 }}>
            {mode === "hospital" ? "Hospital matches" : "Verified doctor matches"}
            {" "}({records.length})
          </h3>
          {records.length > 0 ? (
            <div style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit,minmax(250px,1fr))",
              gap: 14,
            }}>
              {records.map((record, index) => {
                const name = valueOf(record,
                  mode === "hospital"
                    ? ["hospital", "hospital_name", "name"]
                    : ["doctor_name", "doctor", "name"]);
                const address = valueOf(record, ["address", "hospital_address", "branch_area", "area", "city"], "");
                const mapQuery = encodeURIComponent(`${name} ${address} Chennai`);
                return (
                  <article key={`${name}-${index}`} style={styles.card}>
                    <h4 style={{ color: "#ffb397", fontSize: 18, margin: "0 0 12px" }}>{name}</h4>
                    {mode === "hospital" ? (
                      <>
                        <p style={styles.muted}><b>Area:</b> {valueOf(record, ["area"])}</p>
                        <p style={styles.muted}><b>Specialty:</b> {valueOf(record, ["specialty"])}</p>
                        <p style={styles.muted}><b>Treatments:</b> {valueOf(record, ["treatments"])}</p>
                        <p style={styles.muted}><b>Insurance:</b> {valueOf(record, ["insurance_companies", "insurance_company"])}</p>
                        <p style={styles.muted}><b>Cashless:</b> {valueOf(record, ["cashless"])}</p>
                        <p style={styles.muted}><b>Recommendation:</b> {valueOf(record, ["recommendation"])}</p>
                        <p style={styles.muted}><b>Dataset score:</b> {valueOf(record, ["score"])}</p>
                      </>
                    ) : (
                      <>
                        <p style={styles.muted}><b>Specialty:</b> {valueOf(record, ["specialty", "specialisation"])}</p>
                        <p style={styles.muted}><b>Hospital:</b> {valueOf(record, ["hospital", "hospital_name"])}</p>
                        <p style={styles.muted}><b>Area:</b> {valueOf(record, ["branch_area", "area"])}</p>
                        <p style={styles.muted}><b>Treatment:</b> {valueOf(record, ["disease_treatment", "treatment"])}</p>
                        <p style={styles.muted}><b>Match details:</b> {valueOf(record, ["match_reasons", "score"])}</p>
                      </>
                    )}
                    <a
                      href={`https://www.google.com/maps/search/?api=1&query=${mapQuery}`}
                      target="_blank"
                      rel="noreferrer"
                      style={{ color: "#ffb397", fontWeight: 700 }}
                    >View on Google Maps ↗</a>
                  </article>
                );
              })}
            </div>
          ) : (
            <p style={styles.muted}>
              No matching verified records were returned by the dataset.
            </p>
          )}

          {guidance && (
            <div style={{
              ...styles.card, marginTop: 16, whiteSpace: "pre-wrap",
              lineHeight: 1.7,
            }}>
              <h4 style={{ marginTop: 0, color: "#ffb397" }}>
                {mode === "doctor" ? "General guidance (not a verified doctor match)" : "Search information"}
              </h4>
              {guidance}
            </div>
          )}
          {results.disclaimer && (
            <p style={{ ...styles.muted, marginTop: 18, fontSize: 12 }}>
              {results.disclaimer}
            </p>
          )}
        </div>
      )}

      <p style={{ ...styles.muted, marginTop: 22, fontSize: 12 }}>
        Results reflect the configured project datasets. Confirm doctor availability,
        hospital network status, cashless eligibility and treatment coverage directly
        with the provider and insurer. Recommendations do not guarantee claim approval.
      </p>
    </section>
  );
}

