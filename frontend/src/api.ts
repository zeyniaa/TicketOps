import snapshot from "./snapshot.json";
import {
  CATEGORIES,
  type Ticket,
  type Policy,
  type Evaluation,
  type Overview,
  type Readiness,
} from "./types";
export const SHOWCASE = import.meta.env.VITE_MODE !== "api";
const BASE = import.meta.env.VITE_API_URL || "/api/v1";
let csrf = "";
let session: Promise<void> | null = null;
let examples: Ticket[] = structuredClone(snapshot.tickets) as Ticket[];
try {
  const saved = sessionStorage.getItem("ticketops.examples.v1");
  if (saved) examples = JSON.parse(saved);
} catch {
  /* Storage may be disabled. */
}
const save = () => {
  try {
    sessionStorage.setItem("ticketops.examples.v1", JSON.stringify(examples));
  } catch {}
};
export async function request<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  if (!session)
    session = fetch(BASE + "/demo-sessions", {
      method: "POST",
      credentials: "include",
    })
      .then(async (r) => {
        if (!r.ok)
          throw new Error("Sesi demo tidak dapat dimulai. Periksa backend.");
        csrf = (await r.json()).csrf_token;
      })
      .catch((e) => {
        session = null;
        throw e;
      });
  await session;
  const r = await fetch(BASE + path, {
    ...init,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      "X-CSRF-Token": csrf,
      ...init.headers,
    },
  });
  if (!r.ok) {
    const body = await r.json().catch(() => ({}));
    throw new Error(body.message || "Permintaan gagal. Coba kembali.");
  }
  return r.json();
}
function example(id: string) {
  const t = examples.find((t) => t.id === id);
  if (!t) throw new Error("Tiket tidak ditemukan.");
  return t;
}
export const api = {
  async tickets(params: URLSearchParams) {
    if (!SHOWCASE)
      return request<{
        items: Ticket[];
        total: number;
        page: number;
        limit: number;
      }>("/tickets?" + params);
    let rows = examples.filter(
      (t) =>
        !params.get("q") ||
        (t.subject + " " + t.message + " " + t.customer + " " + t.order_code)
          .toLowerCase()
          .includes(params.get("q")!.toLowerCase()),
    );
    for (const field of ["status", "category", "priority", "team"] as const) {
      if (params.get(field))
        rows = rows.filter((t) => t[field] === params.get(field));
    }
    rows = [...rows].sort(
      (a, b) =>
        a.priority.localeCompare(b.priority) ||
        a.created_at.localeCompare(b.created_at),
    );
    const page = Number(params.get("page") || 1);
    return {
      items: structuredClone(rows.slice((page - 1) * 20, page * 20)),
      total: rows.length,
      page,
      limit: 20,
    };
  },
  async ticket(id: string) {
    return SHOWCASE
      ? structuredClone(example(id))
      : request<Ticket>("/tickets/" + id);
  },
  async create(data: unknown) {
    if (SHOWCASE)
      throw new Error("Pembuatan tiket tersedia pada aplikasi lokal.");
    return request<{ ticket: Ticket; job: unknown }>("/tickets", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },
  async update(id: string, data: Record<string, unknown>) {
    if (!SHOWCASE)
      return request<Ticket>("/tickets/" + id, {
        method: "PATCH",
        body: JSON.stringify(data),
      });
    const t = example(id);
    if (data.revision !== t.revision)
      throw new Error("Tiket berubah. Muat ulang.");
    if (data.status === "selesai" && t.drafts?.[0]?.status !== "approved")
      throw new Error("Setujui draf terlebih dahulu.");
    const content = ["category", "team", "priority"].some(
      (k) => data[k] !== undefined && data[k] !== t[k as keyof Ticket],
    );
    Object.assign(
      t,
      Object.fromEntries(
        Object.entries(data).filter(
          ([k]) => !["revision", "reason"].includes(k),
        ),
      ),
    );
    if (content) {
      t.revision++;
      t.status = "ditinjau";
      t.drafts?.forEach((d) => (d.status = "stale"));
    }
    t.events?.unshift({
      id: crypto.randomUUID(),
      action: content
        ? "Koreksi operator (simulasi)"
        : "Status diperbarui (simulasi)",
      created_at: new Date().toISOString(),
      detail: {},
    });
    save();
    return structuredClone(t);
  },
  async generate(id: string, kind: "analyses" | "drafts") {
    if (!SHOWCASE)
      return request("/tickets/" + id + "/" + kind, { method: "POST" });
    throw new Error(
      "Analisis ulang tersedia pada aplikasi lokal dengan backend aktif.",
    );
  },
  async saveDraft(draftId: string, data: { version: number; body: string }) {
    if (!SHOWCASE)
      return request("/drafts/" + draftId, {
        method: "PATCH",
        body: JSON.stringify(data),
      });
    const t = examples.find((t) => t.drafts?.some((d) => d.id === draftId))!;
    const d = t.drafts!.find((d) => d.id === draftId)!;
    if (d.revision !== t.revision || d.version !== data.version)
      throw new Error("Draf sudah berubah atau memerlukan pembaruan.");
    d.body = data.body;
    d.version++;
    d.status = "draft";
    t.status = "ditinjau";
    save();
    return structuredClone(d);
  },
  async approve(draftId: string, version: number) {
    if (!SHOWCASE)
      return request("/drafts/" + draftId + "/approve", {
        method: "POST",
        body: JSON.stringify({ version }),
      });
    const t = examples.find((t) => t.drafts?.some((d) => d.id === draftId))!;
    const d = t.drafts![0];
    if (
      d.id !== draftId ||
      d.revision !== t.revision ||
      d.status === "stale" ||
      d.version !== version
    )
      throw new Error("Draf memerlukan pembaruan.");
    d.status = "approved";
    d.version++;
    t.status = "disetujui";
    save();
    return structuredClone(d);
  },
  async policies() {
    return SHOWCASE
      ? (snapshot.policies as Policy[])
      : request<Policy[]>("/policies");
  },
  async evaluations() {
    return SHOWCASE
      ? (snapshot.evaluations as unknown as Evaluation[])
      : request<Evaluation[]>("/evaluations");
  },
  async overview(): Promise<Overview> {
    if (!SHOWCASE) return request("/overview");
    return {
      total: examples.length,
      new: examples.filter((t) => t.status === "baru").length,
      review: examples.filter((t) => t.status === "ditinjau").length,
      resolved: examples.filter((t) => t.status === "selesai").length,
      approved: examples.filter((t) => t.status === "disetujui").length,
      corrections: examples.filter((t) => t.revision > 1).length,
      categories: Object.fromEntries(
        Object.keys(CATEGORIES).map((k) => [
          k,
          examples.filter((t) => t.category === k).length,
        ]),
      ),
      daily: [...new Set(examples.map((t) => t.created_at.slice(0, 10)))]
        .sort()
        .map((date) => ({
          date,
          count: examples.filter((t) => t.created_at.startsWith(date)).length,
        })),
    };
  },
  async readiness(): Promise<Readiness> {
    return SHOWCASE
      ? {
          api: "showcase",
          database: "Browser session · simulasi",
          classifier: {
            version: "Contoh tersimpan",
            type: "stored_examples",
            review_required: true,
          },
          ollama: false,
          llm_model: "Tersedia di versi lokal",
          queue: 0,
          mode: "showcase",
          version: "0.1.0",
        }
      : request("/readiness");
  },
  reset() {
    sessionStorage.removeItem("ticketops.examples.v1");
    examples = structuredClone(snapshot.tickets) as Ticket[];
  },
};
