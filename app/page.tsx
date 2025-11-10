"use client";

import { useEffect, useState } from "react";

type ApiStatus = {
  status: string;
  integrations?: {
    notion?: boolean;
    openai?: boolean;
    github?: boolean;
  };
};

export default function HomePage() {
  const [apiStatus, setApiStatus] = useState<ApiStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchStatus() {
      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/status`);
        const data = await response.json();
        setApiStatus(data);
      } catch (error) {
        console.error("API Status Error:", error);
      } finally {
        setLoading(false);
      }
    }

    fetchStatus();
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center px-4">
      <div className="w-full max-w-xl bg-white rounded-lg shadow-lg p-8 border border-gray-100">
        <h1 className="text-3xl font-bold text-gray-900 mb-6 text-center">
          🛠️ Engineering Department
        </h1>

        <div className="space-y-4">
          <section className="text-center">
            <h2 className="text-lg font-semibold text-gray-700">System Status</h2>
            <p className="text-sm text-gray-500 mt-1">
              Quick health snapshot of your local environment
            </p>
          </section>

          {loading ? (
            <div className="text-center text-gray-500">Loading...</div>
          ) : apiStatus ? (
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-gray-600">API Status:</span>
                <span className="text-green-600 font-medium">{apiStatus.status}</span>
              </div>

              <div className="border-t border-gray-200 pt-4">
                <h3 className="font-medium text-gray-700 mb-3">Integrations</h3>
                <dl className="space-y-2">
                  <IntegrationRow label="Notion" value={apiStatus.integrations?.notion} />
                  <IntegrationRow label="OpenAI" value={apiStatus.integrations?.openai} />
                  <IntegrationRow label="GitHub" value={apiStatus.integrations?.github} />
                </dl>
              </div>
            </div>
          ) : (
            <div className="text-center text-red-600">❌ API not responding</div>
          )}

          <div className="border-t border-gray-200 pt-4 mt-6">
            <nav className="grid grid-cols-2 gap-3">
              <NavLink href="/chat" label="Chat" color="blue" />
              <NavLink href="/backlog" label="Backlog" color="green" />
            </nav>
          </div>
        </div>
      </div>
    </div>
  );
}

function IntegrationRow({ label, value }: { label: string; value?: boolean }) {
  const color = value ? "text-green-600" : "text-red-600";
  const text = value ? "✅ Connected" : "❌ Not configured";

  return (
    <div className="flex justify-between text-sm">
      <dt className="text-gray-600">{label}:</dt>
      <dd className={`font-medium ${color}`}>{text}</dd>
    </div>
  );
}

function NavLink({
  href,
  label,
  color,
}: {
  href: string;
  label: string;
  color: "blue" | "green";
}) {
  const styles =
    color === "blue"
      ? "bg-blue-500 hover:bg-blue-600"
      : "bg-green-500 hover:bg-green-600";

  return (
    <a
      href={href}
      className={`${styles} text-white px-4 py-2 rounded text-center font-medium transition-colors`}
    >
      {label}
    </a>
  );
}
