"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

const apiBaseUrl = process.env.NEXT_PUBLIC_VINAYA_API_URL ?? "http://127.0.0.1:4010";

export function ReviewForm({ requestId }: { requestId: string }) {
  const router = useRouter();
  const [reviewer, setReviewer] = useState("");
  const [result, setResult] = useState("maintain");
  const [comment, setComment] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      const response = await fetch(`${apiBaseUrl}/api/requests/${requestId}/review`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reviewer, result, comment }),
      });

      if (!response.ok) {
        throw new Error("人工复核提交失败，请确认 Python API 已启动。");
      }

      router.refresh();
      setReviewer("");
      setResult("maintain");
      setComment("");
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "提交失败");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="card form" onSubmit={handleSubmit}>
      <h2 className="section-title">人工复核</h2>
      <label className="field">
        <span>复核人</span>
        <input value={reviewer} onChange={(event) => setReviewer(event.target.value)} required />
      </label>
      <label className="field">
        <span>复核结论</span>
        <select value={result} onChange={(event) => setResult(event.target.value)}>
          <option value="maintain">维持</option>
          <option value="revise">修改</option>
          <option value="override">推翻</option>
        </select>
      </label>
      <label className="field">
        <span>复核意见</span>
        <textarea value={comment} onChange={(event) => setComment(event.target.value)} rows={4} required />
      </label>
      {error ? <p className="error-text">{error}</p> : null}
      <button className="button" type="submit" disabled={submitting}>
        {submitting ? "提交中..." : "提交复核"}
      </button>
    </form>
  );
}
