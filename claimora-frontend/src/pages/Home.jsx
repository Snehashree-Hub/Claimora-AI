
import React from "react";
import {
  ShieldCheck,
  BrainCircuit,
  FileCheck2,
  Activity,
  Hospital,
  ArrowRight,
  Sparkles,
  LockKeyhole,
  Stethoscope,
} from "lucide-react";

const INSURANCE_IMAGE_URL =
  "https://images.unsplash.com/photo-1450101499163-c8848c66ca85?auto=format&fit=crop&w=2400&q=85";

export default function Home({ onNavigate, backendStatus = "checking" }) {
  const navigate = (page) => {
    if (typeof onNavigate === "function") {
      onNavigate(page);
    } else {
      console.warn(`Navigation callback is not configured for: ${page}`);
    }
  };

  const features = [
    {
      icon: BrainCircuit,
      title: "AI Claim Assistant",
      description:
        "Get guidance about claim procedures, policy documents and insurance-related questions.",
      page: "assistant",
    },
    {
      icon: FileCheck2,
      title: "Document Verification",
      description:
        "Submit claim documents for verification and identify missing information.",
      page: "documents",
    },
    {
      icon: ShieldCheck,
      title: "Fraud Risk Analysis",
      description:
        "Analyze claim information for potential risk indicators and inconsistencies.",
      page: "fraud",
    },
    {
      icon: Hospital,
      title: "Hospital Finder",
      description:
        "Explore hospitals according to your treatment, location and insurance preferences.",
      page: "hospitals",
    },
    {
      icon: Stethoscope,
      title: "Doctor Finder",
      description:
        "Find doctors and treatment-related recommendations based on available records.",
      page: "doctors",
    },
    {
      icon: Activity,
      title: "Claim Tracking",
      description:
        "Check claim progress and follow the available processing stages.",
      page: "tracking",
    },
  ];

  const isConnected =
    typeof backendStatus === "string" &&
    backendStatus.toLowerCase() === "connected";

  return (
    <main className="claimora-home">
      <style>{`
        .claimora-home {
          --home-bg: #070b18;
          --home-panel: rgba(17, 25, 49, 0.76);
          --home-border: rgba(148, 163, 184, 0.18);
          --home-text: #f7f8ff;
          --home-muted: #aab5d0;
          --home-cyan: #67e8f9;
          --home-purple: #a78bfa;
          position: relative;
          isolation: isolate;
          min-height: 100vh;
          overflow: hidden;
          color: var(--home-text);
          background:
            radial-gradient(ellipse at 15% 15%, rgba(79, 70, 229, .22), transparent 45%),
            radial-gradient(ellipse at 85% 55%, rgba(8, 145, 178, .12), transparent 40%),
            var(--home-bg);
          font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }

        .claimora-watermark {
          position: absolute;
          z-index: -2;
          inset: 0;
          width: 100%;
          height: 100%;
          min-height: 100%;
          object-fit: cover;
          object-position: center;
          opacity: .16;
          filter: saturate(.65) contrast(1.08);
          pointer-events: none;
        }

        .claimora-home::before {
          content: "";
          position: absolute;
          z-index: -1;
          inset: 0;
          pointer-events: none;
          background:
            linear-gradient(90deg, rgba(7, 11, 24, .96) 0%, rgba(7, 11, 24, .84) 48%, rgba(7, 11, 24, .74) 100%),
            linear-gradient(180deg, rgba(7, 11, 24, .2), #070b18 78%);
        }

        .claimora-home button {
          font: inherit;
        }

        .claimora-hero {
          width: min(1180px, 100%);
          margin: 0 auto;
          padding: 76px 28px 66px;
          display: grid;
          grid-template-columns: minmax(0, 1.25fr) minmax(260px, .75fr);
          gap: 48px;
          align-items: center;
        }

        .claimora-eyebrow {
          display: inline-flex;
          align-items: center;
          gap: 9px;
          padding: 9px 14px;
          margin-bottom: 24px;
          border: 1px solid rgba(103, 232, 249, .28);
          border-radius: 999px;
          background: rgba(15, 23, 42, .58);
          color: #b9f5ff;
          font-size: 12px;
          font-weight: 700;
          letter-spacing: .11em;
          text-transform: uppercase;
        }

        .claimora-hero h1 {
          max-width: 760px;
          margin: 0;
          font-size: clamp(36px, 5.2vw, 65px);
          line-height: 1.08;
          letter-spacing: -.045em;
          font-weight: 800;
        }

        .claimora-hero h1 span {
          display: block;
          margin-top: 10px;
          color: transparent;
          background: linear-gradient(100deg, #67e8f9 0%, #a5b4fc 48%, #c4b5fd 100%);
          background-clip: text;
          -webkit-background-clip: text;
        }

        .claimora-hero-copy {
          max-width: 640px;
          margin: 24px 0 0;
          color: #bdc7df;
          font-size: 16px;
          line-height: 1.85;
        }

        .claimora-hero-actions {
          display: flex;
          flex-wrap: wrap;
          gap: 13px;
          margin-top: 30px;
        }

        .claimora-btn {
          display: inline-flex;
          justify-content: center;
          align-items: center;
          gap: 10px;
          min-height: 48px;
          padding: 13px 19px;
          border-radius: 13px;
          border: 1px solid transparent;
          cursor: pointer;
          font-weight: 700 !important;
          transition: transform .2s ease, border-color .2s ease, background .2s ease;
        }

        .claimora-btn:hover {
          transform: translateY(-2px);
        }

        .claimora-btn-primary {
          color: #07111f;
          background: linear-gradient(110deg, #67e8f9, #a5b4fc);
          box-shadow: 0 12px 36px rgba(103, 232, 249, .14);
        }

        .claimora-btn-secondary {
          color: #eef2ff;
          border-color: rgba(165, 180, 252, .3);
          background: rgba(15, 23, 42, .68);
        }

        .claimora-status {
          display: flex;
          align-items: center;
          gap: 9px;
          margin-top: 25px;
          color: #bdc7df;
          font-size: 13px;
        }

        .claimora-status-dot {
          width: 8px;
          height: 8px;
          flex: 0 0 8px;
          border-radius: 50%;
          background: #fbbf24;
          box-shadow: 0 0 12px rgba(251, 191, 36, .4);
        }

        .claimora-status-dot.online {
          background: #67e8f9;
          box-shadow: 0 0 12px rgba(103, 232, 249, .55);
        }

        .claimora-hero-panel {
          position: relative;
          padding: 28px;
          border: 1px solid rgba(165, 180, 252, .23);
          border-radius: 25px;
          background: linear-gradient(145deg, rgba(21, 31, 59, .91), rgba(13, 18, 38, .77));
          box-shadow: 0 25px 80px rgba(0, 0, 0, .24);
          backdrop-filter: blur(18px);
        }

        .claimora-panel-icon {
          display: grid;
          place-items: center;
          width: 54px;
          height: 54px;
          margin-bottom: 21px;
          border: 1px solid rgba(103, 232, 249, .2);
          border-radius: 17px;
          color: var(--home-cyan);
          background: rgba(34, 211, 238, .09);
        }

        .claimora-hero-panel h2 {
          margin: 0;
          font-size: 21px;
          letter-spacing: -.02em;
        }

        .claimora-hero-panel > p {
          margin: 11px 0 24px;
          color: var(--home-muted);
          font-size: 14px;
          line-height: 1.75;
        }

        .claimora-panel-item {
          display: flex;
          gap: 12px;
          align-items: flex-start;
          padding: 15px 0;
          border-top: 1px solid rgba(148, 163, 184, .13);
        }

        .claimora-panel-item svg {
          flex: 0 0 auto;
          margin-top: 2px;
          color: var(--home-cyan);
        }

        .claimora-panel-item strong {
          display: block;
          font-size: 13px;
        }

        .claimora-panel-item span {
          display: block;
          margin-top: 5px;
          color: var(--home-muted);
          font-size: 12px;
          line-height: 1.6;
        }

        .claimora-features {
          width: min(1180px, 100%);
          margin: 0 auto;
          padding: 18px 28px 80px;
        }

        .claimora-section-heading {
          margin-bottom: 25px;
        }

        .claimora-section-heading p {
          margin: 0 0 10px;
          color: var(--home-cyan);
          font-size: 11px;
          font-weight: 800;
          letter-spacing: .15em;
          text-transform: uppercase;
        }

        .claimora-section-heading h2 {
          margin: 0;
          font-size: clamp(25px, 3vw, 35px);
          letter-spacing: -.035em;
        }

        .claimora-section-heading span {
          display: block;
          margin-top: 10px;
          color: var(--home-muted);
          font-size: 14px;
          line-height: 1.7;
        }

        .claimora-feature-grid {
          display: grid;
          grid-template-columns: repeat(3, minmax(0, 1fr));
          gap: 17px;
        }

        .claimora-feature-card {
          display: flex;
          flex-direction: column;
          align-items: flex-start;
          min-height: 205px;
          padding: 23px;
          border: 1px solid var(--home-border);
          border-radius: 19px;
          color: var(--home-text);
          text-align: left;
          background: rgba(13, 19, 39, .76);
          backdrop-filter: blur(12px);
          cursor: pointer;
          transition: transform .2s ease, border-color .2s ease, background .2s ease;
        }

        .claimora-feature-card:hover {
          transform: translateY(-4px);
          border-color: rgba(103, 232, 249, .4);
          background: rgba(22, 31, 59, .92);
        }

        .claimora-feature-icon {
          display: grid;
          place-items: center;
          width: 43px;
          height: 43px;
          margin-bottom: 19px;
          border-radius: 13px;
          color: #a5f3fc;
          background: rgba(34, 211, 238, .1);
        }

        .claimora-feature-card h3 {
          margin: 0;
          font-size: 16px;
        }

        .claimora-feature-card p {
          flex: 1;
          margin: 10px 0 17px;
          color: var(--home-muted);
          font-size: 13px;
          line-height: 1.75;
        }

        .claimora-feature-link {
          display: flex;
          align-items: center;
          gap: 7px;
          color: #a5f3fc;
          font-size: 12px;
          font-weight: 700;
        }

        .claimora-home-footer {
          width: min(1180px, 100%);
          margin: 0 auto;
          padding: 20px 28px 30px;
          border-top: 1px solid rgba(148, 163, 184, .14);
          color: #8591ae;
          font-size: 12px;
          line-height: 1.8;
        }

        @media (max-width: 850px) {
          .claimora-hero {
            grid-template-columns: 1fr;
            gap: 32px;
            padding-top: 54px;
          }

          .claimora-hero-panel {
            max-width: 580px;
          }

          .claimora-feature-grid {
            grid-template-columns: repeat(2, minmax(0, 1fr));
          }
        }

        @media (max-width: 540px) {
          .claimora-hero {
            padding: 42px 18px 42px;
          }

          .claimora-hero h1 {
            font-size: clamp(34px, 10vw, 47px);
          }

          .claimora-hero-copy {
            font-size: 14px;
          }

          .claimora-hero-actions {
            flex-direction: column;
          }

          .claimora-btn {
            width: 100%;
          }

          .claimora-hero-panel {
            padding: 21px;
          }

          .claimora-features {
            padding: 10px 18px 55px;
          }

          .claimora-feature-grid {
            grid-template-columns: 1fr;
          }

          .claimora-feature-card {
            min-height: 180px;
          }

          .claimora-home-footer {
            padding: 20px 18px 28px;
          }
        }

        @media (prefers-reduced-motion: reduce) {
          .claimora-home *,
          .claimora-home *::before,
          .claimora-home *::after {
            transition: none !important;
            scroll-behavior: auto !important;
          }
        }
      `}</style>

      <img
        className="claimora-watermark"
        src={INSURANCE_IMAGE_URL}
        alt=""
        aria-hidden="true"
        onError={(event) => {
          event.currentTarget.style.display = "none";
        }}
      />

      <section className="claimora-hero">
        <div>
          <div className="claimora-eyebrow">
            <Sparkles size={15} />
            Intelligent Insurance Assistance
          </div>

          <h1>
            AI Agent for Health Insurance
            <span>Claim Assistance</span>
          </h1>

          <p className="claimora-hero-copy">
            A smarter way to navigate health insurance claims. Get AI-powered
            guidance, submit documents for verification, explore hospital and
            doctor recommendations, and follow your claim processing journey
            through one unified workspace.
          </p>

          <div className="claimora-hero-actions">
            <button
              type="button"
              className="claimora-btn claimora-btn-primary"
              onClick={() => navigate("assistant")}
            >
              Start AI Assistance <ArrowRight size={17} />
            </button>

            <button
              type="button"
              className="claimora-btn claimora-btn-secondary"
              onClick={() => navigate("documents")}
            >
              <FileCheck2 size={17} />
              Verify Documents
            </button>
          </div>

          <div className="claimora-status">
            <span
              className={`claimora-status-dot ${isConnected ? "online" : ""}`}
            />
            Backend status:{" "}
            {isConnected
              ? "Connected"
              : backendStatus === "checking"
                ? "Checking connection"
                : "Not confirmed"}
          </div>
        </div>

        <aside className="claimora-hero-panel">
          <div className="claimora-panel-icon">
            <ShieldCheck size={29} />
          </div>

          <h2>Your claim journey, simplified</h2>
          <p>
            Bring key insurance assistance tools together in a single,
            easy-to-navigate workspace.
          </p>

          <div className="claimora-panel-item">
            <BrainCircuit size={19} />
            <div>
              <strong>AI-powered guidance</strong>
              <span>Ask questions and get assistance through the AI service.</span>
            </div>
          </div>

          <div className="claimora-panel-item">
            <FileCheck2 size={19} />
            <div>
              <strong>Document and claim support</strong>
              <span>Review submitted information using available backend services.</span>
            </div>
          </div>

          <div className="claimora-panel-item">
            <LockKeyhole size={19} />
            <div>
              <strong>Security-aware workflow</strong>
              <span>Access the configured claim security and analysis features.</span>
            </div>
          </div>
        </aside>
      </section>

      <section className="claimora-features">
        <div className="claimora-section-heading">
          <p>Explore Claimora</p>
          <h2>Everything starts in one workspace</h2>
          <span>
            Choose a feature to continue. Results depend on the connected
            backend services and available claim data.
          </span>
        </div>

        <div className="claimora-feature-grid">
          {features.map((feature) => {
            const Icon = feature.icon;

            return (
              <button
                type="button"
                className="claimora-feature-card"
                key={feature.title}
                onClick={() => navigate(feature.page)}
              >
                <div className="claimora-feature-icon">
                  <Icon size={22} />
                </div>

                <h3>{feature.title}</h3>
                <p>{feature.description}</p>

                <span className="claimora-feature-link">
                  Open feature <ArrowRight size={14} />
                </span>
              </button>
            );
          })}
        </div>
      </section>

      <footer className="claimora-home-footer">
        Claimora · AI Agent for Health Insurance Claim Assistance
        <br />
        AI-generated guidance supports your workflow and does not guarantee
        claim approval or replace confirmation from your insurer.
      </footer>
    </main>
  );
}
