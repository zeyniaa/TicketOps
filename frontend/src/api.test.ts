import { beforeEach, describe, it, expect, vi } from "vitest";
vi.stubEnv("VITE_MODE", "showcase");
const { api } = await import("./api");

beforeEach(() => {
  const store = new Map<string, string>();
  vi.stubGlobal("sessionStorage", {
    getItem: (k: string) => store.get(k) || null,
    setItem: (k: string, v: string) => store.set(k, v),
    removeItem: (k: string) => store.delete(k),
  });
  api.reset();
});
describe("showcase workflow boundaries", () => {
  it("filters categories and returns the actual count", async () => {
    const r = await api.tickets(
      new URLSearchParams({ category: "pembayaran" }),
    );
    expect(r.total).toBe(2);
    expect(r.items.every((t) => t.category === "pembayaran")).toBe(true);
  });
  it("invalidates drafts after category corrections", async () => {
    const r = await api.tickets(new URLSearchParams());
    const t = await api.ticket(r.items[0].id);
    const d = t.drafts![0];
    await api.update(t.id, { revision: t.revision, category: "akun" });
    await expect(api.approve(d.id, d.version)).rejects.toThrow();
    expect((await api.ticket(t.id)).drafts![0].status).toBe("stale");
  });
  it("requires approval before resolving and rejects stale edits", async () => {
    const r = await api.tickets(new URLSearchParams({ status: "ditinjau" }));
    const t = await api.ticket(r.items[0].id);
    const d = t.drafts![0];
    await expect(
      api.update(t.id, { revision: t.revision, status: "selesai" }),
    ).rejects.toThrow("Setujui");
    await api.saveDraft(d.id, {
      version: d.version,
      body: d.body + " Mohon konfirmasi informasi tambahan.",
    });
    await expect(api.approve(d.id, d.version)).rejects.toThrow();
    const latest = (await api.ticket(t.id)).drafts![0];
    await api.approve(latest.id, latest.version);
    expect(
      (await api.update(t.id, { revision: t.revision, status: "selesai" }))
        .status,
    ).toBe("selesai");
  });
  it("blocks live input and generation in the hosted showcase", async () => {
    await expect(api.create({})).rejects.toThrow("lokal");
    const r = await api.tickets(new URLSearchParams());
    await expect(api.generate(r.items[0].id, "analyses")).rejects.toThrow(
      "lokal",
    );
  });
});
