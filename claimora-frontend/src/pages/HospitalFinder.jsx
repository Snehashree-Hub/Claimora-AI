
import { useEffect, useState } from "react";

const API_BASE = (
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000"
).replace(/\/+$/, "");

const THEME = {
  bg: "#fff8f4",
  card: "#ffffff",
  text: "#39251f",
  muted: "#8b7770",
  primary: "#b95742",
  primaryDark: "#91412f",
  peach: "#f8e2d8",
  border: "#ead8cf",
  success: "#267653",
  error: "#b42318",
};

const DEFAULT_TREATMENTS = [
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

const DEFAULT_CITIES = [
  "Chennai",
  "Bengaluru",
  "Hyderabad",
  "Mumbai",
  "Delhi",
];

const DEFAULT_INSURERS = [
  "RK Health Insurance",
  "Star Health",
  "Care Health",
  "Niva Bupa",
  "ManipalCigna",
  "Aditya Birla Health Insurance",
  "HDFC ERGO",
  "ICICI Lombard",
  "Tata AIG",
  "Bajaj Allianz",
];

function getArray(payload, keys = []) {
  if (Array.isArray(payload)) return payload;

  for (const key of keys) {
    if (Array.isArray(payload?.[key])) return payload[key];
  }

  return [];
}

function getValue(item, keys, fallback = "") {
  for (const key of keys) {
    const value = item?.[key];

    if (value !== null && value !== undefined && value !== "") {
      return value;
    }
  }

  return fallback;
}

function formatDistance(value) {
  if (value === null || value === undefined || value === "") {
    return "";
  }

  return typeof value === "number"
    ? `${value.toFixed(1)} km`
    : String(value);
}

function HospitalCard({ hospital }) {
  const name = getValue(
    hospital,
    ["hospital_name", "hospital", "name", "Hospital"],
    "Hospital name unavailable"
  );

  const address = getValue(
    hospital,
    ["address", "full_address", "Address"],
    ""
  );

  const area = getValue(
    hospital,
    ["area", "branch_area", "location", "Area"],
    ""
  );

  const city = getValue(hospital, ["city", "City"], "");

  const specialty = getValue(
    hospital,
    ["specialty", "speciality", "Specialty"],
    ""
  );

  const treatments = getValue(
    hospital,
    ["treatments", "disease_treatment", "treatment", "Treatments"],
    ""
  );

  const insurance = getValue(
    hospital,
    [
      "insurance_companies",
      "insurance_company",
      "insurance",
      "Insurance Companies",
    ],
    ""
  );

  const cashless = getValue(
    hospital,
    ["cashless", "cashless_available", "Cashless"],
    ""
  );

  const emergency = getValue(
    hospital,
    ["emergency", "emergency_available", "Emergency"],
    ""
  );

  const recommendation = getValue(
    hospital,
    ["recommendation", "match_level", "match_status", "Recommendation"],
    ""
  );

  const distance = getValue(
    hospital,
    ["distance", "distance_km", "distance_zone", "Distance Zone"],
    ""
  );

  const phone = getValue(hospital, ["phone", "phone_number"], "");

  const mapsQuery = encodeURIComponent(
    address || [name, area, city].filter(Boolean).join(", ")
  );

  const displayText = (value) => {
    if (Array.isArray(value)) return value.join(", ");
    if (typeof value === "object" && value !== null) {
      return JSON.stringify(value);
    }
    return String(value);
  };

  return (
    <article style={styles.hospitalCard}>
      <div style={styles.cardTop}>
        <div style={styles.hospitalIcon} aria-hidden="true">
          +
        </div>

        <div style={{ flex: 1, minWidth: 0 }}>
          <h3 style={styles.hospitalName}>{displayText(name)}</h3>

          <p style={styles.hospitalLocation}>
            {[area, city].filter(Boolean).map(displayText).join(", ") ||
              "Location not provided"}
          </p>
        </div>

        {recommendation && (
          <span style={styles.matchBadge}>
            {displayText(recommendation)}
          </span>
        )}
      </div>

      <div style={styles.cardDivider} />

      <div style={styles.detailsGrid}>
        <Detail label="Specialty" value={specialty} />
        <Detail label="Treatment" value={treatments} />
        <Detail label="Insurance" value={insurance} />
        <Detail label="Cashless" value={cashless} />
        <Detail label="Emergency" value={emergency} />
        <Detail label="Distance" value={formatDistance(distance)} />
      </div>

      {address && (
        <p style={styles.address}>
          <strong>Address:</strong> {displayText(address)}
        </p>
      )}

      <div style={styles.cardActions}>
        <a
          href={`https://www.google.com/maps/search/?api=1&query=${mapsQuery}`}
          target="_blank"
          rel="noreferrer"
          style={styles.mapButton}
        >
          View on Google Maps ↗
        </a>

        {phone && (
          <a
            href={`tel:${String(phone).replace(/[^\d+]/g, "")}`}
            style={styles.phoneButton}
          >
            Call Hospital
          </a>
        )}
      </div>

      <p style={styles.disclaimer}>
        Confirm treatment availability, insurance network status and cashless
        eligibility directly with the hospital and insurer.
      </p>
    </article>
  );
}

function Detail({ label, value }) {
  if (value === null || value === undefined || value === "") return null;

  const formatted =
    Array.isArray(value) ? value.join(", ") : String(value);

  return (
    <div style={styles.detailItem}>
      <span style={styles.detailLabel}>{label}</span>
      <span style={styles.detailValue}>{formatted}</span>
    </div>
  );
}

export default function Hospital() {
  const [treatment, setTreatment] = useState("");
  const [city, setCity] = useState("Chennai");
  const [area, setArea] = useState("");
  const [insuranceCompany, setInsuranceCompany] = useState("");

  const [treatments, setTreatments] = useState(DEFAULT_TREATMENTS);
  const [cities, setCities] = useState(DEFAULT_CITIES);
  const [areas, setAreas] = useState([]);
  const [insurers, setInsurers] = useState(DEFAULT_INSURERS);

  const [hospitals, setHospitals] = useState([]);
  const [loading, setLoading] = useState(false);
  const [loadingOptions, setLoadingOptions] = useState(true);
  const [error, setError] = useState("");
  const [searched, setSearched] = useState(false);

  useEffect(() => {
    let active = true;

    async function loadOptions() {
      try {
        const response = await fetch(
          `${API_BASE}/api/recommendations/options`
        );

        if (!response.ok) {
          throw new Error(`Options endpoint returned ${response.status}`);
        }

        const data = await response.json();

        if (!active) return;

        const treatmentOptions = getArray(data, ["treatments"]);
        const cityOptions = getArray(data, ["cities"]);
        const areaOptions = getArray(data, ["areas"]);
        const insuranceOptions = getArray(data, [
          "insurance_companies",
          "insurers",
        ]);

        if (treatmentOptions.length) {
          setTreatments(treatmentOptions.map((v) =>
            typeof v === "object"
              ? getValue(v, ["value", "name", "label"], "")
              : String(v)
          ).filter(Boolean));
        }

        if (cityOptions.length) {
          setCities(cityOptions.map((v) =>
            typeof v === "object"
              ? getValue(v, ["value", "name", "label"], "")
              : String(v)
          ).filter(Boolean));
        }

        if (areaOptions.length) {
          setAreas(areaOptions.map((v) =>
            typeof v === "object"
              ? getValue(v, ["value", "name", "label"], "")
              : String(v)
          ).filter(Boolean));
        }

        if (insuranceOptions.length) {
          setInsurers(insuranceOptions.map((v) =>
            typeof v === "object"
              ? getValue(v, ["value", "name", "label"], "")
              : String(v)
          ).filter(Boolean));
        }
      } catch (err) {
        // The form remains usable with its default options.
        console.warn("Could not load recommendation options:", err.message);
      } finally {
        if (active) setLoadingOptions(false);
      }
    }

    loadOptions();

    return () => {
      active = false;
    };
  }, []);

  async function searchHospitals(event) {
    event.preventDefault();

    setError("");
    setHospitals([]);
    setSearched(false);
    setLoading(true);

    try {
      const response = await fetch(
        `${API_BASE}/api/recommendations/search`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Accept: "application/json",
          },
          body: JSON.stringify({
            treatment,
            city,
            area,
            insurance_company: insuranceCompany,
            limit: 10,
          }),
        }
      );

      const raw = await response.text();

      let data = {};

      try {
        data = raw ? JSON.parse(raw) : {};
      } catch {
        throw new Error("The backend returned an invalid response.");
      }

      if (!response.ok) {
        const detail =
          typeof data.detail === "string"
            ? data.detail
            : Array.isArray(data.detail)
              ? data.detail
                  .map((item) => item.msg || JSON.stringify(item))
                  .join("; ")
              : data.message || `HTTP ${response.status}`;

        throw new Error(detail);
      }

      const results = getArray(data, [
        "hospitals",
        "results",
        "recommendations",
        "items",
        "data",
      ]);

      setHospitals(results);
      setSearched(true);
    } catch (err) {
      setError(
        `${err.message}. Check that the Claimora backend is running at ${API_BASE}.`
      );
    } finally {
      setLoading(false);
    }
  }

  function resetSearch() {
    setTreatment("");
    setCity("Chennai");
    setArea("");
    setInsuranceCompany("");
    setHospitals([]);
    setError("");
    setSearched(false);
  }

  return (
    <main style={styles.page}>
      <section style={styles.hero}>
        <div style={styles.heroIcon} aria-hidden="true">
          ✚
        </div>

        <div style={{ flex: 1 }}>
          <span style={styles.eyebrow}>CLAIMORA · CARE DISCOVERY</span>
          <h1 style={styles.title}>Find the Right Hospital</h1>
          <p style={styles.subtitle}>
            Explore hospitals based on your treatment, location and insurance
            provider before planning your care.
          </p>
        </div>
      </section>

      <section style={styles.searchPanel}>
        <div style={styles.sectionHeading}>
          <div>
            <h2 style={styles.sectionTitle}>Hospital Finder</h2>
            <p style={styles.sectionSubtitle}>
              Enter your preferences to search available records.
            </p>
          </div>
          <span style={styles.liveBadge}>API CONNECTED</span>
        </div>

        <form onSubmit={searchHospitals}>
          <div style={styles.formGrid}>
            <label style={styles.field}>
              <span style={styles.label}>Treatment / Procedure</span>
              <select
                value={treatment}
                onChange={(event) => setTreatment(event.target.value)}
                style={styles.input}
              >
                <option value="">All treatments</option>
                {treatments.map((item) => (
                  <option key={item} value={item}>
                    {item}
                  </option>
                ))}
              </select>
            </label>

            <label style={styles.field}>
              <span style={styles.label}>City</span>
              <select
                value={city}
                onChange={(event) => {
                  setCity(event.target.value);
                  setArea("");
                }}
                style={styles.input}
              >
                {cities.map((item) => (
                  <option key={item} value={item}>
                    {item}
                  </option>
                ))}
              </select>
            </label>

            <label style={styles.field}>
              <span style={styles.label}>Area / Locality</span>
              <input
                value={area}
                onChange={(event) => setArea(event.target.value)}
                placeholder="e.g. Porur, Adyar"
                style={styles.input}
                maxLength={100}
              />
            </label>

            <label style={styles.field}>
              <span style={styles.label}>Insurance Provider</span>
              <select
                value={insuranceCompany}
                onChange={(event) =>
                  setInsuranceCompany(event.target.value)
                }
                style={styles.input}
              >
                <option value="">All providers</option>
                {insurers.map((item) => (
                  <option key={item} value={item}>
                    {item}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <div style={styles.formActions}>
            <button
              type="button"
              onClick={resetSearch}
              disabled={loading}
              style={styles.resetButton}
            >
              Reset
            </button>

            <button
              type="submit"
              disabled={loading || loadingOptions}
              style={{
                ...styles.searchButton,
                opacity: loading || loadingOptions ? 0.7 : 1,
              }}
            >
              {loading
                ? "Searching hospitals..."
                : loadingOptions
                  ? "Loading options..."
                  : "Search Hospitals →"}
            </button>
          </div>
        </form>
      </section>

      {error && (
        <div role="alert" style={styles.errorBox}>
          <strong>Unable to search hospitals</strong>
          <p style={{ margin: "6px 0 0" }}>{error}</p>
        </div>
      )}

      {loading && (
        <div style={styles.loadingPanel} role="status">
          <div style={styles.spinner} />
          <p style={{ margin: "12px 0 0" }}>
            Finding matching hospital records...
          </p>
        </div>
      )}

      {!loading && searched && hospitals.length > 0 && (
        <section style={styles.resultsSection}>
          <div style={styles.resultsHeading}>
            <div>
              <span style={styles.eyebrow}>SEARCH RESULTS</span>
              <h2 style={styles.sectionTitle}>
                Hospitals for your preferences
              </h2>
            </div>

            <span style={styles.countBadge}>
              {hospitals.length} result{hospitals.length !== 1 ? "s" : ""}
            </span>
          </div>

          <div style={styles.resultsGrid}>
            {hospitals.map((hospital, index) => (
              <HospitalCard
                key={
                  getValue(hospital, [
                    "hospital_id",
                    "id",
                    "hospital_name",
                    "hospital",
                    "name",
                  ]) || index
                }
                hospital={hospital}
              />
            ))}
          </div>
        </section>
      )}

      {!loading && searched && hospitals.length === 0 && !error && (
        <section style={styles.emptyState}>
          <div style={styles.emptyIcon}>⌕</div>
          <h2 style={styles.sectionTitle}>No matching hospitals found</h2>
          <p style={styles.sectionSubtitle}>
            Try another treatment, remove the area filter, or select a
            different insurance provider.
          </p>
          <button onClick={resetSearch} style={styles.searchButton}>
            Change Search
          </button>
        </section>
      )}

      {!searched && !loading && !error && (
        <section style={styles.infoPanel}>
          <div style={styles.infoIcon}>i</div>
          <div>
            <h3 style={styles.infoTitle}>Before choosing a hospital</h3>
            <p style={styles.infoText}>
              Search results depend on the records available in the Claimora
              recommendation dataset. Contact the hospital and insurer to
              confirm network status, treatment availability, estimated costs
              and pre-authorisation requirements.
            </p>
          </div>
        </section>
      )}

      <footer style={styles.footer}>
        Claimora · Smart Claim Assistance
      </footer>
    </main>
  );
}

const styles = {
  page: {
    minHeight: "100vh",
    padding: "clamp(18px, 4vw, 42px)",
    background: THEME.bg,
    color: THEME.text,
    fontFamily:
      'Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
    boxSizing: "border-box",
  },
  hero: {
    display: "flex",
    alignItems: "center",
    gap: 20,
    maxWidth: 1200,
    margin: "0 auto 28px",
    padding: "12px 0",
  },
  heroIcon: {
    width: 66,
    height: 66,
    minWidth: 66,
    borderRadius: 20,
    background: THEME.peach,
    color: THEME.primary,
    display: "grid",
    placeItems: "center",
    fontSize: 32,
    fontWeight: 800,
    boxShadow: "0 8px 24px rgba(145,65,47,0.08)",
  },
  eyebrow: {
    color: THEME.primary,
    fontSize: 11,
    letterSpacing: 2,
    fontWeight: 800,
  },
  title: {
    margin: "8px 0",
    fontSize: "clamp(27px, 4vw, 40px)",
    lineHeight: 1.15,
    letterSpacing: "-1.3px",
  },
  subtitle: {
    margin: 0,
    color: THEME.muted,
    fontSize: 15,
    lineHeight: 1.7,
    maxWidth: 720,
  },
  searchPanel: {
    maxWidth: 1200,
    margin: "0 auto 28px",
    padding: "clamp(20px, 3vw, 32px)",
    border: `1px solid ${THEME.border}`,
    borderRadius: 22,
    background: THEME.card,
    boxShadow: "0 12px 35px rgba(78,42,30,0.045)",
  },
  sectionHeading: {
    display: "flex",
    alignItems: "flex-start",
    justifyContent: "space-between",
    flexWrap: "wrap",
    gap: 12,
    marginBottom: 24,
  },
  sectionTitle: {
    margin: "7px 0",
    fontSize: 22,
    letterSpacing: "-0.5px",
  },
  sectionSubtitle: {
    margin: 0,
    color: THEME.muted,
    fontSize: 14,
    lineHeight: 1.7,
  },
  liveBadge: {
    padding: "7px 10px",
    borderRadius: 8,
    background: "#fff0e8",
    color: THEME.primaryDark,
    fontSize: 10,
    letterSpacing: 1,
    fontWeight: 800,
  },
  formGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 225px), 1fr))",
    gap: 18,
  },
  field: {
    display: "flex",
    flexDirection: "column",
    gap: 9,
    minWidth: 0,
  },
  label: {
    fontSize: 13,
    fontWeight: 700,
    color: THEME.text,
  },
  input: {
    width: "100%",
    minHeight: 48,
    boxSizing: "border-box",
    border: `1px solid ${THEME.border}`,
    borderRadius: 11,
    padding: "12px 13px",
    background: "#fffdfb",
    color: THEME.text,
    fontSize: 14,
    outlineColor: THEME.primary,
  },
  formActions: {
    display: "flex",
    justifyContent: "flex-end",
    flexWrap: "wrap",
    gap: 12,
    marginTop: 24,
  },
  resetButton: {
    minHeight: 46,
    padding: "0 22px",
    borderRadius: 11,
    border: `1px solid ${THEME.border}`,
    background: "#fff",
    color: THEME.text,
    fontSize: 14,
    fontWeight: 700,
    cursor: "pointer",
  },
  searchButton: {
    minHeight: 46,
    padding: "0 22px",
    borderRadius: 11,
    border: "none",
    background: THEME.primary,
    color: "#fff",
    fontSize: 14,
    fontWeight: 750,
    cursor: "pointer",
    boxShadow: "0 7px 16px rgba(185,87,66,0.18)",
  },
  errorBox: {
    maxWidth: 1200,
    margin: "0 auto 24px",
    padding: 18,
    borderRadius: 13,
    border: "1px solid #f2b8b5",
    background: "#fff0ef",
    color: THEME.error,
    fontSize: 14,
    lineHeight: 1.6,
    overflowWrap: "anywhere",
  },
  loadingPanel: {
    maxWidth: 1200,
    margin: "0 auto 24px",
    padding: 32,
    textAlign: "center",
    color: THEME.muted,
    background: THEME.card,
    borderRadius: 18,
    border: `1px solid ${THEME.border}`,
  },
  spinner: {
    width: 28,
    height: 28,
    borderRadius: "50%",
    border: `3px solid ${THEME.peach}`,
    borderTopColor: THEME.primary,
    margin: "0 auto",
    animation: "claimora-hospital-spin 0.8s linear infinite",
  },
  resultsSection: {
    maxWidth: 1200,
    margin: "0 auto 28px",
  },
  resultsHeading: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    flexWrap: "wrap",
    gap: 12,
    marginBottom: 18,
  },
  countBadge: {
    padding: "8px 13px",
    borderRadius: 20,
    background: THEME.peach,
    color: THEME.primaryDark,
    fontWeight: 800,
    fontSize: 13,
  },
  resultsGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 330px), 1fr))",
    gap: 18,
  },
  hospitalCard: {
    minWidth: 0,
    padding: 22,
    background: THEME.card,
    border: `1px solid ${THEME.border}`,
    borderRadius: 18,
    boxShadow: "0 8px 22px rgba(78,42,30,0.04)",
    overflowWrap: "anywhere",
  },
  cardTop: {
    display: "flex",
    alignItems: "flex-start",
    gap: 12,
  },
  hospitalIcon: {
    width: 44,
    height: 44,
    minWidth: 44,
    borderRadius: 13,
    display: "grid",
    placeItems: "center",
    background: THEME.peach,
    color: THEME.primary,
    fontSize: 27,
    fontWeight: 800,
  },
  hospitalName: {
    margin: "2px 0 7px",
    fontSize: 18,
    lineHeight: 1.4,
  },
  hospitalLocation: {
    margin: 0,
    color: THEME.muted,
    fontSize: 13,
    lineHeight: 1.5,
  },
  matchBadge: {
    flexShrink: 0,
    maxWidth: 130,
    padding: "6px 8px",
    borderRadius: 8,
    background: "#fff0e8",
    color: THEME.primaryDark,
    fontSize: 10,
    fontWeight: 800,
  },
  cardDivider: {
    height: 1,
    background: THEME.border,
    margin: "19px 0",
  },
  detailsGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(125px, 1fr))",
    gap: 16,
  },
  detailItem: {
    display: "flex",
    flexDirection: "column",
    gap: 6,
    minWidth: 0,
  },
  detailLabel: {
    fontSize: 11,
    color: THEME.muted,
    fontWeight: 700,
  },
  detailValue: {
    fontSize: 13,
    fontWeight: 650,
    lineHeight: 1.5,
    whiteSpace: "pre-wrap",
  },
  address: {
    margin: "18px 0 0",
    color: THEME.muted,
    fontSize: 13,
    lineHeight: 1.6,
  },
  cardActions: {
    display: "flex",
    flexWrap: "wrap",
    gap: 10,
    marginTop: 19,
  },
  mapButton: {
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    padding: "11px 13px",
    borderRadius: 10,
    background: THEME.primary,
    color: "#fff",
    textDecoration: "none",
    fontSize: 12,
    fontWeight: 750,
  },
  phoneButton: {
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    padding: "10px 13px",
    borderRadius: 10,
    border: `1px solid ${THEME.border}`,
    color: THEME.primaryDark,
    textDecoration: "none",
    fontSize: 12,
    fontWeight: 750,
  },
  disclaimer: {
    margin: "17px 0 0",
    color: THEME.muted,
    fontSize: 11,
    lineHeight: 1.6,
  },
  emptyState: {
    maxWidth: 1200,
    margin: "0 auto 28px",
    padding: "45px 20px",
    textAlign: "center",
    background: THEME.card,
    border: `1px solid ${THEME.border}`,
    borderRadius: 18,
  },
  emptyIcon: {
    color: THEME.primary,
    fontSize: 42,
    marginBottom: 12,
  },
  infoPanel: {
    maxWidth: 1200,
    margin: "0 auto 28px",
    padding: 22,
    display: "flex",
    alignItems: "flex-start",
    gap: 14,
    background: "#fff1e9",
    border: "1px solid #f1d3c5",
    borderRadius: 16,
  },
  infoIcon: {
    width: 27,
    height: 27,
    minWidth: 27,
    display: "grid",
    placeItems: "center",
    borderRadius: "50%",
    background: THEME.primary,
    color: "#fff",
    fontWeight: 800,
  },
  infoTitle: {
    margin: "2px 0 8px",
    fontSize: 15,
  },
  infoText: {
    margin: 0,
    color: THEME.muted,
    fontSize: 13,
    lineHeight: 1.8,
  },
  footer: {
    maxWidth: 1200,
    margin: "35px auto 0",
    paddingTop: 20,
    borderTop: `1px solid ${THEME.border}`,
    color: THEME.muted,
    textAlign: "center",
    fontSize: 12,
  },
};

// Inject the spinner animation without requiring an additional CSS file.
if (typeof document !== "undefined" &&
    !document.getElementById("claimora-hospital-animation")) {
  const styleElement = document.createElement("style");
  styleElement.id = "claimora-hospital-animation";
  styleElement.textContent =
    "@keyframes claimora-hospital-spin { to { transform: rotate(360deg); } }";
  document.head.appendChild(styleElement);
}

