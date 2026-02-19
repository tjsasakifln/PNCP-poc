import { ImageResponse } from "next/og";

export const runtime = "edge";

export async function GET() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "1200",
          height: "630",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          background: "linear-gradient(135deg, #0A1E3F 0%, #0D2B5E 50%, #116DFF 100%)",
          fontFamily: "sans-serif",
        }}
      >
        {/* Logo area */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "16px",
            marginBottom: "32px",
          }}
        >
          <div
            style={{
              display: "flex",
              gap: "4px",
              alignItems: "flex-end",
            }}
          >
            {[26, 22, 28, 24, 20].map((h, i) => (
              <div
                key={i}
                style={{
                  width: "8px",
                  height: `${h}px`,
                  backgroundColor: "#116DFF",
                  borderRadius: "2px",
                  opacity: 0.7 + i * 0.05,
                }}
              />
            ))}
          </div>
          <span
            style={{
              fontSize: "72px",
              fontWeight: 800,
              color: "#FFFFFF",
              letterSpacing: "-2px",
            }}
          >
            SmartLic
          </span>
        </div>

        {/* Tagline */}
        <p
          style={{
            fontSize: "32px",
            color: "#8BA3C7",
            margin: "0 0 48px 0",
          }}
        >
          Inteligência em Licitações Públicas
        </p>

        {/* Features bar */}
        <div
          style={{
            display: "flex",
            gap: "32px",
            padding: "16px 32px",
            backgroundColor: "rgba(255,255,255,0.08)",
            borderRadius: "12px",
          }}
        >
          {["15 Setores", "27 Estados", "Cobertura Nacional", "IA Avançada"].map(
            (feat) => (
              <span
                key={feat}
                style={{
                  fontSize: "20px",
                  color: "#FFD700",
                  fontWeight: 600,
                }}
              >
                {feat}
              </span>
            )
          )}
        </div>

        {/* URL */}
        <p
          style={{
            fontSize: "20px",
            color: "rgba(255,255,255,0.5)",
            marginTop: "32px",
          }}
        >
          smartlic.tech
        </p>
      </div>
    ),
    {
      width: 1200,
      height: 630,
    }
  );
}
