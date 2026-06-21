"use client";

import { FormEvent, useMemo, useState } from "react";

import { submitIncidentReport } from "@/lib/api";
import type { ReportResponse } from "@/types/api";

const CATEGORY_COLORS: Record<string, string> = {
  Falls: "bg-orange-100 text-orange-800 ring-orange-200",
  Electrical: "bg-yellow-100 text-yellow-900 ring-yellow-200",
  Chemical: "bg-purple-100 text-purple-800 ring-purple-200",
  Machinery: "bg-slate-100 text-slate-800 ring-slate-200",
  Ergonomics: "bg-blue-100 text-blue-800 ring-blue-200",
  Fire: "bg-red-100 text-red-800 ring-red-200",
  "Slips/Trips": "bg-amber-100 text-amber-900 ring-amber-200",
};

function categoryBadgeClass(category: string): string {
  return (
    CATEGORY_COLORS[category] ??
    "bg-emerald-100 text-emerald-800 ring-emerald-200"
  );
}

function mtoBadgeClass(mto: string): string {
  switch (mto) {
    case "Human":
      return "bg-sky-100 text-sky-800";
    case "Technology":
      return "bg-violet-100 text-violet-800";
    case "Organisation":
      return "bg-rose-100 text-rose-800";
    default:
      return "bg-zinc-100 text-zinc-800";
  }
}

export default function Home() {
  const [text, setText] = useState("");
  const [image, setImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ReportResponse | null>(null);

  const rootCauseHypothesis = useMemo(() => {
    if (!result?.report.five_whys.length) {
      return null;
    }
    return result.report.five_whys[result.report.five_whys.length - 1];
  }, [result]);

  function handleImageChange(file: File | null) {
    setImage(file);
    if (imagePreview) {
      URL.revokeObjectURL(imagePreview);
    }
    setImagePreview(file ? URL.createObjectURL(file) : null);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setResult(null);

    if (!text.trim()) {
      setError("Please describe the incident before submitting.");
      return;
    }

    setLoading(true);
    try {
      const response = await submitIncidentReport(text.trim(), image);
      setResult(response);
    } catch (submitError) {
      const message =
        submitError instanceof Error
          ? submitError.message
          : "Something went wrong while submitting the report.";
      setError(message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-slate-100">
      <header className="border-b border-slate-200 bg-white/80 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-5">
          <div>
            <p className="text-sm font-medium uppercase tracking-[0.2em] text-slate-500">
              Tryggve.ai Prototype
            </p>
            <h1 className="text-2xl font-semibold text-slate-900">
              AI Safety Reporting Dashboard
            </h1>
          </div>
          <span className="rounded-full bg-emerald-50 px-3 py-1 text-sm font-medium text-emerald-700 ring-1 ring-emerald-200">
            Live backend
          </span>
        </div>
      </header>

      <main className="mx-auto grid max-w-7xl gap-6 px-6 py-8 lg:grid-cols-2">
        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="mb-6">
            <h2 className="text-lg font-semibold text-slate-900">
              Report an incident
            </h2>
            <p className="mt-1 text-sm text-slate-600">
              Upload a photo and describe what happened. The AI will structure
              the report and highlight hazards in the image.
            </p>
          </div>

          <form className="space-y-5" onSubmit={handleSubmit}>
            <div>
              <label
                htmlFor="photo"
                className="mb-2 block text-sm font-medium text-slate-700"
              >
                Photo (optional)
              </label>
              <input
                id="photo"
                type="file"
                accept="image/*"
                className="block w-full cursor-pointer rounded-xl border border-dashed border-slate-300 bg-slate-50 px-4 py-3 text-sm text-slate-600 file:mr-4 file:rounded-lg file:border-0 file:bg-slate-900 file:px-4 file:py-2 file:text-sm file:font-medium file:text-white hover:border-slate-400"
                onChange={(event) =>
                  handleImageChange(event.target.files?.[0] ?? null)
                }
              />
              {imagePreview ? (
                <img
                  src={imagePreview}
                  alt="Selected incident preview"
                  className="mt-4 max-h-56 w-full rounded-xl border border-slate-200 object-cover"
                />
              ) : null}
            </div>

            <div>
              <label
                htmlFor="description"
                className="mb-2 block text-sm font-medium text-slate-700"
              >
                Incident description
              </label>
              <textarea
                id="description"
                rows={8}
                value={text}
                onChange={(event) => setText(event.target.value)}
                placeholder="Example: Worker slipped on icy steps near the loading bay. No guardrails visible on temporary scaffolding."
                className="w-full rounded-xl border border-slate-300 px-4 py-3 text-sm text-slate-900 shadow-sm outline-none transition focus:border-slate-500 focus:ring-2 focus:ring-slate-200"
              />
            </div>

            {error ? (
              <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                {error}
              </div>
            ) : null}

            <button
              type="submit"
              disabled={loading}
              className="inline-flex w-full items-center justify-center rounded-xl bg-slate-900 px-4 py-3 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
            >
              {loading ? (
                <>
                  <span className="mr-2 inline-block h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                  Analyzing incident...
                </>
              ) : (
                "Submit safety report"
              )}
            </button>
          </form>
        </section>

        <section className="space-y-6">
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="text-lg font-semibold text-slate-900">
              Annotated image
            </h2>
            <p className="mt-1 text-sm text-slate-600">
              Hazard bounding boxes detected by the vision model.
            </p>

            <div className="mt-4 flex min-h-[280px] items-center justify-center rounded-xl border border-dashed border-slate-200 bg-slate-50 p-4">
              {result?.annotated_image_base64 ? (
                <img
                  src={`data:image/jpeg;base64,${result.annotated_image_base64}`}
                  alt="Annotated hazard visualization"
                  className="max-h-[420px] w-full rounded-lg object-contain"
                />
              ) : (
                <p className="text-sm text-slate-500">
                  {loading
                    ? "Generating annotated image..."
                    : "Submit a report with a photo to see hazard boxes here."}
                </p>
              )}
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="text-lg font-semibold text-slate-900">
              Structured report
            </h2>

            {result ? (
              <div className="mt-5 space-y-5">
                <div className="rounded-xl border border-slate-200 p-4">
                  <div className="flex flex-wrap items-center gap-2">
                    <span
                      className={`rounded-full px-3 py-1 text-xs font-semibold ring-1 ${categoryBadgeClass(result.report.hazard_category)}`}
                    >
                      {result.report.hazard_category}
                    </span>
                    <span
                      className={`rounded-full px-3 py-1 text-xs font-semibold ${mtoBadgeClass(result.report.mto_classification)}`}
                    >
                      MTO: {result.report.mto_classification}
                    </span>
                    {result.report.hazards_detected.length > 0 ? (
                      <span className="rounded-full bg-red-50 px-3 py-1 text-xs font-semibold text-red-700">
                        {result.report.hazards_detected.length} hazard
                        {result.report.hazards_detected.length === 1 ? "" : "s"}{" "}
                        detected
                      </span>
                    ) : null}
                  </div>
                  <h3 className="mt-3 text-xl font-semibold text-slate-900">
                    {result.report.title}
                  </h3>
                  <p className="mt-2 text-sm leading-6 text-slate-600">
                    {result.report.description}
                  </p>
                </div>

                <div className="rounded-xl border border-slate-200 p-4">
                  <h4 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
                    Root cause hypothesis
                  </h4>
                  <p className="mt-2 text-sm leading-6 text-slate-800">
                    {rootCauseHypothesis}
                  </p>
                  <ol className="mt-4 space-y-2">
                    {result.report.five_whys.map((why, index) => (
                      <li
                        key={`${index}-${why.slice(0, 12)}`}
                        className="rounded-lg bg-slate-50 px-3 py-2 text-sm text-slate-700"
                      >
                        <span className="font-semibold text-slate-900">
                          Why {index + 1}:
                        </span>{" "}
                        {why}
                      </li>
                    ))}
                  </ol>
                </div>

                <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4">
                  <h4 className="text-sm font-semibold uppercase tracking-wide text-emerald-800">
                    Hierarchy of controls recommendation
                  </h4>
                  <p className="mt-2 text-sm leading-6 text-emerald-900">
                    {result.report.hierarchy_of_controls_recommendation}
                  </p>
                </div>

                <div className="rounded-xl border border-slate-200 p-4">
                  <h4 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
                    Grounded regulations
                  </h4>
                  <ul className="mt-3 space-y-2">
                    {result.report.cited_regulation_snippets.map((snippet) => (
                      <li
                        key={snippet.slice(0, 40)}
                        className="rounded-lg bg-slate-50 px-3 py-2 text-xs leading-5 text-slate-700"
                      >
                        {snippet}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            ) : (
              <p className="mt-4 text-sm text-slate-500">
                {loading
                  ? "Waiting for AI analysis..."
                  : "Your structured incident report will appear here after submission."}
              </p>
            )}
          </div>
        </section>
      </main>
    </div>
  );
}
