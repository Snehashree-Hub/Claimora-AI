const API_BASE = (
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000"
).replace(/\/+$/, "");

export { API_BASE };

export async function apiRequest(path, options = {}) {
  const url = `${API_BASE}${path.startsWith("/") ? path : `/${path}`}`;

  const headers = new Headers(options.headers || {});

  // Do not manually set Content-Type for FormData.
  if (
    options.body &&
    !(options.body instanceof FormData) &&
    !headers.has("Content-Type")
  ) {
    headers.set("Content-Type", "application/json");
  }

  let response;

  try {
    response = await fetch(url, {
      ...options,
      headers
    });
  } catch {
    throw new Error(
      `Cannot connect to the backend at ${API_BASE}. Check that FastAPI is running and CORS allows the frontend origin.`
    );
  }

  const text = await response.text();
  let data = null;

  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = { detail: text };
    }
  }

  if (!response.ok) {
    const detail =
      data?.detail ||
      data?.message ||
      `Backend returned HTTP ${response.status}`;

    throw new Error(
      typeof detail === "string" ? detail : JSON.stringify(detail)
    );
  }

  return data;
}

export async function checkBackend() {
  return apiRequest("/status");
}

export async function askClaimAssistant(question) {
  return apiRequest("/api/rag/chat", {
    method: "POST",
    body: JSON.stringify({ message: question })
  });
}

export async function getRecommendationOptions() {
  return apiRequest("/api/recommendations/options");
}

export async function searchHospitals(filters) {
  return apiRequest("/api/recommendations/search", {
    method: "POST",
    body: JSON.stringify(filters)
  });
}

export async function searchDoctors(filters) {
  return apiRequest("/api/recommendations/doctors/search", {
    method: "POST",
    body: JSON.stringify(filters)
  });
}

export async function analyzeClaimReadiness(formData) {
  return apiRequest("/api/claim-readiness/analyze", {
    method: "POST",
    body: formData
  });
}



