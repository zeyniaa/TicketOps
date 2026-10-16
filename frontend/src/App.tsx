import { useEffect, useState, type ReactNode } from "react";
import {
  NavLink,
  Link,
  Route,
  Routes,
  useNavigate,
  useParams,
  useSearchParams,
  useLocation,
} from "react-router-dom";
import { useQuery, useQueryClient, useMutation } from "@tanstack/react-query";
import * as Dialog from "@radix-ui/react-dialog";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import {
  Activity,
  ArrowDownLeft,
  ArrowLeft,
  ArrowRight,
  ArrowUpRight,
  BookOpen,
  Check,
  CheckCheck,
  CheckCircle2,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  Circle,
  CircleHelp,
  Clock3,
  Copy,
  Cpu,
  Download,
  ExternalLink,
  FileText,
  Inbox as InboxIcon,
  LayoutDashboard,
  LoaderCircle,
  Menu,
  MessageSquareText,
  MoreHorizontal,
  Plus,
  RefreshCw,
  Search,
  Settings2,
  ShieldCheck,
  SlidersHorizontal,
  Sparkles,
  Tag,
  TriangleAlert,
  TrendingUp,
  X,
} from "lucide-react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
} from "recharts";
import { api, SHOWCASE } from "./api";
import {
  CATEGORIES,
  STATUSES,
  TEAMS,
  type Category,
  type Ticket,
  type Status,
  type Evaluation,
} from "./types";

const activeJob = (t?: Ticket) =>
  !!t?.job && ["queued", "running"].includes(t.job.status);
const date = (v: string) =>
  new Intl.DateTimeFormat("id-ID", {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(v));
const initials = (name: string) =>
  name
    .split(" ")
    .map((x) => x[0])
    .slice(0, 2)
    .join("");
const pct = (n: number) =>
  new Intl.NumberFormat("id-ID", {
    style: "percent",
    maximumFractionDigits: 1,
  }).format(n);
const palette = [
  "#0f766e",
  "#2b9a8f",
  "#56b2a5",
  "#8bcbc0",
  "#b7dcd4",
  "#51777a",
  "#799a9a",
  "#d6e5e1",
];

function Badge({
  children,
  tone = "neutral",
}: {
  children: ReactNode;
  tone?: string;
}) {
  return <span className={"badge " + tone}>{children}</span>;
}
function StatusBadge({ status }: { status: Status }) {
  return (
    <Badge tone={status}>
      <span className="status-dot" />
      {STATUSES[status]}
    </Badge>
  );
}
function Priority({ value }: { value: string }) {
  return (
    <span className={"priority " + value.toLowerCase()}>
      <i />
      {value}{" "}
      <span>
        {value === "P1" ? "Tinggi" : value === "P2" ? "Sedang" : "Normal"}
      </span>
    </span>
  );
}
function Loading() {
  return (
    <div className="empty">
      <LoaderCircle className="spin" />
      <h3>Menyiapkan workspace</h3>
      <p>Mengambil data tiket dan status terbaru.</p>
    </div>
  );
}
function ErrorBox({ error, retry }: { error: unknown; retry?: () => void }) {
  return (
    <div className="notice danger">
      <TriangleAlert size={18} />
      <div>
        <strong>Belum dapat memuat data</strong>
        <p>{error instanceof Error ? error.message : "Terjadi kesalahan."}</p>
        {retry && (
          <button className="text-button" onClick={retry}>
            Coba kembali <RefreshCw size={13} />
          </button>
        )}
      </div>
    </div>
  );
}
function PageHeading({
  eyebrow,
  title,
  description,
  action,
}: {
  eyebrow: string;
  title: string;
  description: string;
  action?: ReactNode;
}) {
  return (
    <div className="page-heading">
      <div>
        <div className="eyebrow">{eyebrow}</div>
        <h1>{title}</h1>
        <p>{description}</p>
      </div>
      {action}
    </div>
  );
}

export default function App() {
  const [mobile, setMobile] = useState(false);
  const [create, setCreate] = useState(false);
  const location = useLocation();
  useEffect(() => {
    setMobile(false);
    window.scrollTo(0, 0);
  }, [location.pathname]);
  const { data: ready } = useQuery({
    queryKey: ["readiness"],
    queryFn: api.readiness,
    staleTime: 30000,
  });
  return (
    <div className="app-shell">
      <a className="skip" href="#main">
        Ke konten utama
      </a>
      <aside className={"sidebar " + (mobile ? "open" : "")}>
        <Link to="/tickets" className="brand">
          <div className="brand-icon">
            <MessageSquareText size={23} />
          </div>
          <span>
            ticket<span>ops</span>
            <small>AI SUPPORT WORKSPACE</small>
          </span>
        </Link>
        <div className="workspace-switch">
          <div className="workspace-icon">S</div>
          <div>
            <strong>Toko Senada</strong>
            <small>Workspace demo</small>
          </div>
          <ChevronDown size={15} />
        </div>
        <div className="nav-label">WORKSPACE</div>
        <nav aria-label="Navigasi utama">
          <NavLink to="/overview">
            <LayoutDashboard size={19} />
            Ringkasan
          </NavLink>
          <NavLink to="/tickets">
            <InboxIcon size={19} />
            Inbox tiket
            <span className="nav-dot" />
          </NavLink>
          <NavLink to="/policies">
            <BookOpen size={19} />
            Kebijakan toko
          </NavLink>
        </nav>
        <div className="nav-label secondary-label">INTELLIGENCE</div>
        <nav aria-label="Navigasi AI">
          <NavLink to="/evaluation">
            <Activity size={19} />
            Evaluasi model
          </NavLink>
          <NavLink to="/system">
            <Settings2 size={19} />
            Status sistem
          </NavLink>
        </nav>
        <div className="sidebar-bottom">
          <div className="assist-card">
            <div className="assist-icon">
              <ShieldCheck size={20} />
            </div>
            <strong>AI membantu. Kamu memutuskan.</strong>
            <p>Periksa bukti dan tinjau draf sebelum menyetujui.</p>
            <Link to="/policies">
              Lihat kebijakan <ArrowUpRight size={14} />
            </Link>
          </div>
          <div className="profile">
            <div className="avatar owner">Z</div>
            <div>
              <strong>Zeiniah</strong>
              <small>Demo operator</small>
            </div>
            <Badge tone="teal">v0.1</Badge>
          </div>
        </div>
      </aside>
      {mobile && (
        <button
          className="overlay"
          aria-label="Tutup navigasi"
          onClick={() => setMobile(false)}
        />
      )}
      <div className="main-shell">
        <header className="topbar">
          <div className="breadcrumbs">
            <button
              className="icon-button mobile-menu"
              aria-label="Buka navigasi"
              onClick={() => setMobile(!mobile)}
            >
              <Menu size={20} />
            </button>
            <span>Workspace</span>
            <ChevronRight size={13} />
            <strong>
              {location.pathname.includes("overview")
                ? "Ringkasan"
                : location.pathname.includes("policies")
                  ? "Kebijakan toko"
                  : location.pathname.includes("evaluation")
                    ? "Evaluasi model"
                    : location.pathname.includes("system")
                      ? "Status sistem"
                      : "Inbox tiket"}
            </strong>
          </div>
          <div className="topbar-right">
            <span className="top-status">
              <i />
              {SHOWCASE
                ? "Showcase interaktif"
                : ready?.api === "ready"
                  ? "Backend terhubung"
                  : "Menghubungkan"}
            </span>
            <span className="top-separator" />
            <Link
              to="/system"
              className="icon-button"
              aria-label="Bantuan dan status sistem"
            >
              <CircleHelp size={19} />
            </Link>
            <div className="avatar small owner">Z</div>
          </div>
        </header>
        <main id="main">
          <Routes>
            <Route
              path="/"
              element={<Inbox onCreate={() => setCreate(true)} />}
            />
            <Route
              path="/tickets"
              element={<Inbox onCreate={() => setCreate(true)} />}
            />
            <Route path="/tickets/:id" element={<TicketDetail />} />
            <Route path="/overview" element={<OverviewPage />} />
            <Route path="/policies" element={<PoliciesPage />} />
            <Route path="/evaluation" element={<EvaluationPage />} />
            <Route path="/system" element={<SystemPage />} />
            <Route
              path="*"
              element={
                <div className="empty">
                  <h1>Halaman tidak ditemukan</h1>
                  <Link to="/tickets">Kembali ke inbox</Link>
                </div>
              }
            />
          </Routes>
        </main>
        <footer className="footer">
          <span>
            TicketOps <span className="footer-dot">·</span> Dibangun untuk
            keputusan yang lebih terarah.
          </span>
          <span>
            Data simulasi <span className="footer-dot">·</span> Portofolio AI
            Engineer
          </span>
        </footer>
      </div>
      <CreateModal open={create} onOpenChange={setCreate} />
    </div>
  );
}

function Inbox({ onCreate }: { onCreate: () => void }) {
  const [params, setParams] = useSearchParams();
  const [filters, setFilters] = useState(false);
  const set = (key: string, value: string) => {
    const next = new URLSearchParams(params);
    if (value) next.set(key, value);
    else next.delete(key);
    if (key !== "page") next.delete("page");
    setParams(next, { replace: true });
  };
  const query = useQuery({
    queryKey: ["tickets", params.toString()],
    queryFn: () => api.tickets(params),
    refetchInterval: (q) =>
      q.state.data?.items.some(activeJob) ? 2000 : false,
  });
  const overview = useQuery({ queryKey: ["overview"], queryFn: api.overview });
  const o = overview.data;
  return (
    <div className="page inbox-page">
      <PageHeading
        eyebrow="CUSTOMER OPERATIONS"
        title="Inbox tiket"
        description="Semua keluhan, bukti, dan langkah berikutnya. Dalam satu tempat."
        action={
          <button className="button primary" onClick={onCreate}>
            <Plus size={17} />
            Buat tiket
          </button>
        }
      />
      <div className="welcome-strip">
        <div className="welcome-symbol">
          <Sparkles size={22} />
        </div>
        <div>
          <strong>Dari keluhan menjadi langkah yang jelas.</strong>
          <p>
            {SHOWCASE
              ? "Jelajahi contoh tersimpan. Edit dan persetujuan disimulasikan hanya di sesi browser ini."
              : "AI menyiapkan kategori dan draf. Keputusan akhir tetap di tangan operator."}
          </p>
        </div>
        <span className="mode-label">
          <span className="status-dot" />
          {SHOWCASE ? "Contoh tersimpan" : "Analisis lokal aktif"}
        </span>
      </div>
      <div className="stats-grid">
        <Stat
          icon={<InboxIcon size={19} />}
          label="Total tiket"
          value={o?.total}
          foot="Seluruh tiket di workspace"
        />
        <Stat
          icon={<Clock3 size={19} />}
          label="Menunggu penanganan"
          value={o?.new}
          foot="Siap untuk diperiksa"
        />
        <Stat
          icon={<ShieldCheck size={19} />}
          label="Perlu ditinjau"
          value={o?.review}
          foot="Membutuhkan keputusanmu"
        />
        <Stat
          icon={<CheckCheck size={19} />}
          label="Tiket selesai"
          value={o?.resolved}
          foot="Sudah ditangani operator"
        />
      </div>
      <section className="panel inbox-panel" aria-label="Daftar tiket">
        <div className="inbox-toolbar">
          <div className="tabs" role="tablist" aria-label="Status tiket">
            {[
              ["", "Semua tiket", o?.total],
              ["baru", "Baru", o?.new],
              ["ditinjau", "Perlu ditinjau", o?.review],
              ["selesai", "Selesai", o?.resolved],
            ].map(([key, label, count]) => (
              <button
                key={key}
                role="tab"
                aria-selected={(params.get("status") || "") === key}
                className={(params.get("status") || "") === key ? "active" : ""}
                onClick={() => set("status", String(key))}
              >
                {label}
                <span>{count ?? "—"}</span>
              </button>
            ))}
          </div>
          <button
            className={
              "button subtle filter-button " + (filters ? "selected" : "")
            }
            onClick={() => setFilters(!filters)}
            aria-expanded={filters}
          >
            <SlidersHorizontal size={15} />
            Filter
          </button>
        </div>
        <div className="search-row">
          <div className="search-input">
            <Search size={17} />
            <input
              aria-label="Cari tiket"
              placeholder="Cari tiket, pelanggan, atau nomor pesanan..."
              value={params.get("q") || ""}
              onChange={(e) => set("q", e.target.value)}
            />
            {params.get("q") && (
              <button
                aria-label="Hapus pencarian"
                className="icon-button"
                onClick={() => set("q", "")}
              >
                <X size={15} />
              </button>
            )}
          </div>
          <span className="search-caption">
            <span className="tiny-dot" />
            Prioritas tertinggi lebih dulu
          </span>
        </div>
        {filters && (
          <div className="filter-row">
            <label>
              Kategori
              <select
                value={params.get("category") || ""}
                onChange={(e) => set("category", e.target.value)}
              >
                <option value="">Semua kategori</option>
                {Object.entries(CATEGORIES).map(([v, l]) => (
                  <option key={v} value={v}>
                    {l}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Prioritas
              <select
                value={params.get("priority") || ""}
                onChange={(e) => set("priority", e.target.value)}
              >
                <option value="">Semua prioritas</option>
                {["P1", "P2", "P3"].map((p) => (
                  <option key={p}>{p}</option>
                ))}
              </select>
            </label>
            <label>
              Tim
              <select
                value={params.get("team") || ""}
                onChange={(e) => set("team", e.target.value)}
              >
                <option value="">Semua tim</option>
                {Object.entries(TEAMS).map(([v, l]) => (
                  <option key={v} value={v}>
                    {l}
                  </option>
                ))}
              </select>
            </label>
            <button className="text-button" onClick={() => setParams({})}>
              Reset filter
            </button>
          </div>
        )}
        {query.isLoading ? (
          <Loading />
        ) : query.isError ? (
          <ErrorBox error={query.error} retry={() => query.refetch()} />
        ) : (
          <>
            <div className="table-scroll">
              <table className="ticket-table">
                <thead>
                  <tr>
                    <th>TIKET & PELANGGAN</th>
                    <th>KATEGORI</th>
                    <th>PRIORITAS</th>
                    <th>STATUS</th>
                    <th>MASUK</th>
                    <th>
                      <span className="sr-only">Buka</span>
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {query.data?.items.map((t) => (
                    <tr key={t.id}>
                      <td>
                        <div className="ticket-title-row">
                          <span
                            className={
                              "avatar customer color-" + (t.number % 4)
                            }
                          >
                            {initials(t.customer)}
                          </span>
                          <div>
                            <Link
                              className="ticket-title"
                              to={"/tickets/" + t.id}
                            >
                              {t.subject}
                            </Link>
                            <div className="ticket-meta">
                              <span>#{t.number}</span>
                              <span>·</span>
                              <span>{t.customer}</span>
                            </div>
                          </div>
                        </div>
                      </td>
                      <td>
                        <span className="category-pill">
                          {t.category
                            ? CATEGORIES[t.category]
                            : "Menunggu analisis"}
                        </span>
                      </td>
                      <td>
                        <Priority value={t.priority} />
                      </td>
                      <td>
                        {activeJob(t) ? (
                          <Badge tone="teal">
                            <LoaderCircle size={12} className="spin" />
                            {t.job!.stage}
                          </Badge>
                        ) : (
                          <StatusBadge status={t.status} />
                        )}
                      </td>
                      <td className="date-cell">{date(t.created_at)}</td>
                      <td>
                        <Link
                          className="row-arrow"
                          aria-label={"Buka tiket " + t.number}
                          to={"/tickets/" + t.id}
                        >
                          <ArrowUpRight size={17} />
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {!query.data?.items.length && (
              <div className="empty">
                <Search size={26} />
                <h3>Tiket tidak ditemukan</h3>
                <p>Coba kata kunci lain atau sesuaikan filter.</p>
                <button className="button subtle" onClick={() => setParams({})}>
                  Reset pencarian
                </button>
              </div>
            )}
            <div className="table-footer">
              <span>
                Menampilkan {query.data?.items.length ?? 0} dari{" "}
                {query.data?.total ?? 0} tiket
              </span>
              <div className="pagination">
                <button
                  className="icon-button"
                  aria-label="Halaman sebelumnya"
                  disabled={(query.data?.page ?? 1) <= 1}
                  onClick={() =>
                    set("page", String((query.data?.page ?? 1) - 1))
                  }
                >
                  <ChevronLeft size={16} />
                </button>
                <span>{query.data?.page ?? 1}</span>
                <button
                  className="icon-button"
                  aria-label="Halaman berikutnya"
                  disabled={
                    (query.data?.page ?? 1) * 20 >= (query.data?.total ?? 0)
                  }
                  onClick={() =>
                    set("page", String((query.data?.page ?? 1) + 1))
                  }
                >
                  <ChevronRight size={16} />
                </button>
              </div>
            </div>
          </>
        )}
      </section>
      <div className="bottom-note">
        <ShieldCheck size={14} />
        <span>
          {SHOWCASE
            ? "Semua nama dan pesanan merupakan data simulasi. Tidak ada pesan yang dikirim."
            : "Semua draf memerlukan persetujuan operator. Data demo bukan data pelanggan nyata."}
        </span>
        <Link to="/evaluation">
          Lihat evaluasi model <ArrowRight size={13} />
        </Link>
      </div>
    </div>
  );
}
function Stat({
  icon,
  label,
  value,
  foot,
}: {
  icon: ReactNode;
  label: string;
  value?: number;
  foot: string;
}) {
  return (
    <div className="stat-card">
      <div className="stat-top">
        <span>{label}</span>
        <span className="stat-icon">{icon}</span>
      </div>
      <strong>
        {value ?? "—"}
        <span>tiket</span>
      </strong>
      <small>{foot}</small>
    </div>
  );
}

const ticketSchema = z.object({
  subject: z.string().trim().min(3, "Judul minimal 3 karakter.").max(200),
  customer: z.string().trim().min(1, "Nama wajib diisi.").max(100),
  message: z
    .string()
    .trim()
    .min(10, "Pesan minimal 10 karakter.")
    .max(4000, "Pesan maksimal 4.000 karakter."),
  order_code: z
    .string()
    .max(40)
    .regex(
      /^[A-Za-z0-9_-]*$/,
      "Gunakan huruf, angka, tanda hubung atau garis bawah.",
    ),
});
type TicketForm = z.infer<typeof ticketSchema>;
function CreateModal({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (v: boolean) => void;
}) {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const form = useForm<TicketForm>({
    resolver: zodResolver(ticketSchema),
    defaultValues: {
      subject: "",
      customer: "Pelanggan demo",
      message: "",
      order_code: "",
    },
  });
  const mutation = useMutation({
    mutationFn: api.create,
    onSuccess: async (data) => {
      await qc.invalidateQueries();
      onOpenChange(false);
      form.reset();
      navigate("/tickets/" + data.ticket.id);
    },
  });
  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="dialog-overlay" />
        <Dialog.Content className="dialog-content">
          <Dialog.Close
            className="icon-button dialog-close"
            aria-label="Tutup formulir"
          >
            <X size={20} />
          </Dialog.Close>
          <div className="dialog-symbol">
            <Plus size={24} />
          </div>
          <Dialog.Title>Buat tiket baru</Dialog.Title>
          <Dialog.Description>
            {SHOWCASE
              ? "Showcase menggunakan contoh tersimpan. Pembuatan dan analisis tiket bebas tersedia di versi lokal."
              : "Masukkan keluhan pelanggan. AI akan menyiapkan analisis dan draf untuk kamu tinjau."}
          </Dialog.Description>
          {SHOWCASE ? (
            <>
              <div className="notice">
                <Cpu size={20} />
                <div>
                  <strong>Jalankan pipeline lengkap di laptop</strong>
                  <p>
                    Versi lokal menyediakan backend FastAPI, classifier
                    terlatih, dan generation Qwen melalui Ollama.
                  </p>
                </div>
              </div>
              <button
                className="button primary full"
                onClick={() => {
                  onOpenChange(false);
                  navigate("/system");
                }}
              >
                Lihat cara menjalankan <ArrowRight size={16} />
              </button>
            </>
          ) : (
            <form onSubmit={form.handleSubmit((data) => mutation.mutate(data))}>
              <label>
                Judul tiket
                <input
                  {...form.register("subject")}
                  placeholder="Contoh: Barang diterima dalam keadaan rusak"
                />
                {form.formState.errors.subject && (
                  <span className="field-error">
                    {form.formState.errors.subject.message}
                  </span>
                )}
              </label>
              <div className="form-columns">
                <label>
                  Nama pelanggan
                  <input {...form.register("customer")} />
                  {form.formState.errors.customer && (
                    <span className="field-error">
                      {form.formState.errors.customer.message}
                    </span>
                  )}
                </label>
                <label>
                  Nomor pesanan <span className="muted">(opsional)</span>
                  <input
                    {...form.register("order_code")}
                    placeholder="DEMO-1001"
                  />
                  {form.formState.errors.order_code && (
                    <span className="field-error">
                      {form.formState.errors.order_code.message}
                    </span>
                  )}
                </label>
              </div>
              <label>
                Pesan pelanggan
                <textarea
                  {...form.register("message")}
                  rows={6}
                  placeholder="Tuliskan kendala yang dialami pelanggan..."
                />
                {form.formState.errors.message && (
                  <span className="field-error">
                    {form.formState.errors.message.message}
                  </span>
                )}
              </label>
              {mutation.isError && <ErrorBox error={mutation.error} />}
              <button
                className="button primary full"
                disabled={mutation.isPending}
              >
                {mutation.isPending ? (
                  <LoaderCircle size={16} className="spin" />
                ) : (
                  <Sparkles size={16} />
                )}
                Buat & analisis tiket
              </button>
              <p className="form-help">
                Gunakan data simulasi. Jangan masukkan OTP atau informasi
                pembayaran rahasia.
              </p>
            </form>
          )}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}

function TicketDetail() {
  const { id = "" } = useParams();
  const qc = useQueryClient();
  const [tab, setTab] = useState("pesan");
  const [body, setBody] = useState("");
  const [feedback, setFeedback] = useState("");
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);
  const q = useQuery({
    queryKey: ["ticket", id],
    queryFn: () => api.ticket(id),
    refetchInterval: (q) => (activeJob(q.state.data) ? 2000 : false),
  });
  const t = q.data;
  const draft = t?.drafts?.[0];
  useEffect(() => {
    setBody(draft?.body || "");
  }, [draft?.id, draft?.version]);
  const mutation = useMutation<void, Error, () => Promise<unknown>>({
    mutationFn: async (fn) => {
      setError("");
      setFeedback("");
      await fn();
    },
    onSuccess: async () => {
      await qc.invalidateQueries();
      setFeedback(
        SHOWCASE
          ? "Perubahan simulasi disimpan di sesi browser."
          : "Perubahan tersimpan.",
      );
    },
    onError: (e) => setError(e.message),
  });
  const act = (fn: () => Promise<unknown>) => mutation.mutate(fn);
  if (q.isLoading)
    return (
      <div className="page">
        <Loading />
      </div>
    );
  if (q.isError || !t)
    return (
      <div className="page">
        <Link to="/tickets" className="back-link">
          <ArrowLeft size={15} />
          Inbox tiket
        </Link>
        <ErrorBox error={q.error} retry={() => q.refetch()} />
      </div>
    );
  const stale =
    !!draft && (draft.revision !== t.revision || draft.status === "stale");
  return (
    <div className="page detail-page">
      <Link to="/tickets" className="back-link">
        <ArrowLeft size={15} />
        Kembali ke inbox
      </Link>
      <div className="detail-heading">
        <div>
          <div className="eyebrow">
            TIKET #{t.number} <span>·</span>{" "}
            {t.order_code || "TANPA NOMOR PESANAN"}
          </div>
          <h1>{t.subject}</h1>
          <div className="detail-meta">
            <StatusBadge status={t.status} />
            <Priority value={t.priority} />
            <span>Dibuat {date(t.created_at)}</span>
          </div>
        </div>
        <button
          className="button subtle"
          disabled={mutation.isPending || activeJob(t)}
          onClick={() => act(() => api.generate(id, "analyses"))}
        >
          <RefreshCw size={15} />
          Analisis ulang
        </button>
      </div>
      {SHOWCASE && (
        <div className="notice compact">
          <Sparkles size={16} />
          <span>
            Contoh tersimpan. Edit dan persetujuan disimulasikan di browser;
            analisis ulang tersedia di versi lokal.
          </span>
        </div>
      )}
      {activeJob(t) && (
        <div className="notice compact">
          <LoaderCircle size={17} className="spin" />
          <span>
            {t.job!.stage}. Progres mengikuti tahap yang sedang berjalan.
          </span>
        </div>
      )}
      {t.job?.status === "failed" && (
        <div className="notice danger">
          <TriangleAlert size={18} />
          <span>
            Analisis gagal:{" "}
            {t.job.error === "CLASSIFIER_NOT_READY"
              ? "classifier belum disiapkan. Jalankan skrip training baseline."
              : "periksa layanan lokal dan coba analisis ulang."}
          </span>
        </div>
      )}
      {error && <ErrorBox error={new Error(error)} />}{" "}
      {feedback && (
        <div className="notice success compact" role="status">
          <CheckCircle2 size={16} />
          {feedback}
        </div>
      )}
      <div className="mobile-tabs tabs">
        {["pesan", "analisis", "jawaban"].map((v) => (
          <button
            key={v}
            className={tab === v ? "active" : ""}
            onClick={() => setTab(v)}
          >
            {v[0].toUpperCase() + v.slice(1)}
          </button>
        ))}
      </div>
      <div className="detail-grid">
        <section
          className={
            "panel detail-panel " + (tab === "pesan" ? "mobile-active" : "")
          }
        >
          <div className="panel-heading">
            <h2>
              <MessageSquareText size={17} />
              Pesan pelanggan
            </h2>
            <Badge>Asli</Badge>
          </div>
          <div className="panel-body">
            <div className="sender">
              <span className="avatar customer color-0">
                {initials(t.customer)}
              </span>
              <div>
                <strong>{t.customer}</strong>
                <small>Formulir tiket · {date(t.created_at)}</small>
              </div>
            </div>
            <div className="customer-message">{t.message}</div>
            <h3 className="section-label">DATA PESANAN</h3>
            {t.order ? (
              <div className="order-box">
                <div className="order-title">
                  <FileText size={17} />
                  <strong>{t.order_code}</strong>
                  <Badge>Simulasi</Badge>
                </div>
                {Object.entries(t.order)
                  .filter(([k]) => k !== "simulated")
                  .map(([k, v]) => (
                    <div className="key-value" key={k}>
                      <span>
                        {{
                          status: "Status pesanan",
                          payment_status: "Pembayaran",
                          overdue_hours: "Terlambat (jam)",
                          item: "Barang",
                        }[k] || k}
                      </span>
                      <strong>{String(v)}</strong>
                    </div>
                  ))}
              </div>
            ) : (
              <div className="empty-inline">
                <CircleHelp size={18} />
                <span>
                  Data pesanan belum tersedia. Minta informasi tambahan bila
                  diperlukan.
                </span>
              </div>
            )}
            <h3 className="section-label">RIWAYAT TIKET</h3>
            <div className="timeline">
              {t.events?.map((e) => (
                <div className="timeline-item" key={e.id}>
                  <i />
                  <strong>{e.action}</strong>
                  <small>{date(e.created_at)}</small>
                </div>
              ))}
            </div>
          </div>
        </section>
        <section
          className={
            "panel detail-panel " + (tab === "analisis" ? "mobile-active" : "")
          }
        >
          <div className="panel-heading">
            <h2>
              <Sparkles size={17} />
              Analisis & routing
            </h2>
            <Badge tone="teal">AI assist</Badge>
          </div>
          <div className="panel-body">
            <div className="analysis-caption">
              Saran yang dapat kamu koreksi.
            </div>
            <label>
              Kategori utama
              <select
                value={t.category || ""}
                disabled={mutation.isPending || activeJob(t)}
                onChange={(e) =>
                  act(() =>
                    api.update(id, {
                      revision: t.revision,
                      category: e.target.value,
                      team: (
                        {
                          status_pengiriman: "logistik",
                          barang_rusak: "retur",
                          barang_tidak_sesuai: "retur",
                          retur_refund: "retur",
                          pembayaran: "billing",
                          akun: "customer_care",
                          pembatalan: "customer_care",
                          lainnya: "customer_care",
                        } as Record<string, string>
                      )[e.target.value],
                    }),
                  )
                }
              >
                <option disabled value="">
                  Menunggu analisis
                </option>
                {Object.entries(CATEGORIES).map(([v, l]) => (
                  <option key={v} value={v}>
                    {l}
                  </option>
                ))}
              </select>
            </label>
            <div className="score-box">
              <span>Skor prediksi awal</span>
              <strong>
                {t.analysis?.score == null ? "—" : pct(t.analysis.score)}
              </strong>
              {t.analysis?.category && t.analysis.category !== t.category && (
                <small>
                  Skor ini milik prediksi {CATEGORIES[t.analysis.category]},
                  sebelum koreksi operator.
                </small>
              )}
              <small>
                {t.analysis?.source === "stored_example"
                  ? "Kategori pada contoh ini ditetapkan dalam skenario, bukan prediksi langsung."
                  : t.analysis?.calibration === "sigmoid"
                    ? "Probabilitas dikalibrasi pada data sintetis. Bukan jaminan kebenaran."
                    : "Periksa status kalibrasi pada halaman evaluasi."}
              </small>
            </div>
            {t.analysis?.needs_review && (
              <div className="review-hint">
                <ShieldCheck size={16} />
                <span>Kategori perlu diperiksa operator.</span>
              </div>
            )}
            <div className="divider" />
            <label>
              Tim penanganan
              <select
                value={t.team}
                disabled={mutation.isPending || activeJob(t)}
                onChange={(e) =>
                  act(() =>
                    api.update(id, {
                      revision: t.revision,
                      team: e.target.value,
                    }),
                  )
                }
              >
                {Object.entries(TEAMS).map(([v, l]) => (
                  <option key={v} value={v}>
                    {l}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Prioritas
              <select
                value={t.priority}
                disabled={mutation.isPending || activeJob(t)}
                onChange={(e) =>
                  act(() =>
                    api.update(id, {
                      revision: t.revision,
                      priority: e.target.value,
                    }),
                  )
                }
              >
                {["P1", "P2", "P3"].map((p, i) => (
                  <option value={p} key={p}>
                    {p} — {["Tinggi", "Sedang", "Normal"][i]}
                  </option>
                ))}
              </select>
            </label>
            <p className="subtle-note">
              {t.analysis?.priority_reason ||
                "Prioritas memakai aturan dan data pesanan, bukan nada marah pelanggan."}
            </p>
            <div className="model-foot">
              <Cpu size={14} />
              <div>
                <span>
                  {t.analysis?.classifier_version || "Menunggu classifier"}
                </span>
                <small>Revisi tiket {t.revision}</small>
              </div>
            </div>
          </div>
        </section>
        <section
          className={
            "panel detail-panel answer-panel " +
            (tab === "jawaban" ? "mobile-active" : "")
          }
        >
          <div className="panel-heading">
            <h2>
              <FileText size={17} />
              Draf jawaban
            </h2>
            {draft && (
              <Badge tone="teal">
                {draft.source === "ollama"
                  ? "Qwen lokal"
                  : draft.source === "template"
                    ? "Template"
                    : "Contoh tersimpan"}
              </Badge>
            )}
          </div>
          <div className="panel-body">
            {draft ? (
              <>
                {stale && (
                  <div className="notice warning compact">
                    <TriangleAlert size={17} />
                    <span>
                      Draf ini memerlukan pembaruan setelah koreksi tiket.
                    </span>
                  </div>
                )}
                <label className="sr-only" htmlFor="draft-body">
                  Isi draf jawaban
                </label>
                <textarea
                  id="draft-body"
                  className="draft-editor"
                  rows={10}
                  value={body}
                  disabled={stale || mutation.isPending || activeJob(t)}
                  onChange={(e) => setBody(e.target.value)}
                />
                <div className="draft-tools">
                  <span>
                    {body.length} karakter · Versi {draft.version}
                  </span>
                  <button
                    className="text-button"
                    onClick={async () => {
                      try {
                        await navigator.clipboard.writeText(body);
                        setCopied(true);
                        setTimeout(() => setCopied(false), 2000);
                      } catch {
                        setError(
                          "Salin manual dari kotak draf. Akses clipboard tidak tersedia.",
                        );
                      }
                    }}
                  >
                    {copied ? <Check size={14} /> : <Copy size={14} />}{" "}
                    {copied ? "Tersalin" : "Salin"}
                  </button>
                </div>
                <div className="draft-actions">
                  <button
                    className="button subtle"
                    disabled={
                      mutation.isPending ||
                      stale ||
                      activeJob(t) ||
                      body === draft.body ||
                      body.trim().length < 10
                    }
                    onClick={() =>
                      act(() =>
                        api.saveDraft(draft.id, {
                          version: draft.version,
                          body,
                        }),
                      )
                    }
                  >
                    Simpan edit
                  </button>
                  <button
                    className="button subtle"
                    disabled={mutation.isPending || activeJob(t)}
                    onClick={() => act(() => api.generate(id, "drafts"))}
                  >
                    <RefreshCw size={14} />
                    Buat ulang
                  </button>
                </div>
                <h3 className="section-label">
                  KEBIJAKAN SUMBER <span>{draft.policy_refs.length}</span>
                </h3>
                <div className="source-list">
                  {draft.policy_refs.map((p) => (
                    <details key={p.id}>
                      <summary>
                        <BookOpen size={15} />
                        <span>
                          {p.title}
                          <small>
                            {p.id} · v{p.version}
                          </small>
                        </span>
                        <ChevronDown size={14} />
                      </summary>
                      <p>{p.body}</p>
                    </details>
                  ))}
                </div>
                {draft.missing_information.length > 0 && (
                  <p className="subtle-note">
                    Informasi yang perlu dilengkapi:{" "}
                    {draft.missing_information.join(", ")}.
                  </p>
                )}
                {draft.review_flags.map((flag, i) => (
                  <p key={i} className="subtle-note">
                    <TriangleAlert size={13} /> {flag}
                  </p>
                ))}
                <div className="approval-box">
                  <ShieldCheck size={19} />
                  <p>
                    Pastikan isi jawaban sesuai bukti. Persetujuan disimpan
                    dalam aplikasi.
                  </p>
                </div>
                <button
                  className="button primary full"
                  disabled={
                    mutation.isPending ||
                    stale ||
                    activeJob(t) ||
                    body !== draft.body ||
                    draft.status === "approved"
                  }
                  onClick={() =>
                    act(() => api.approve(draft.id, draft.version))
                  }
                >
                  {mutation.isPending ? (
                    <LoaderCircle size={16} className="spin" />
                  ) : (
                    <CheckCheck size={16} />
                  )}{" "}
                  {draft.status === "approved"
                    ? "Draf sudah disetujui"
                    : "Setujui draf"}
                </button>
                {draft.status === "approved" && t.status !== "selesai" && (
                  <button
                    className="button subtle full resolve-button"
                    disabled={mutation.isPending}
                    onClick={() =>
                      act(() =>
                        api.update(id, {
                          revision: t.revision,
                          status: "selesai",
                        }),
                      )
                    }
                  >
                    <CheckCircle2 size={16} />
                    Tandai tiket selesai
                  </button>
                )}
                {t.status === "selesai" && (
                  <button
                    className="button subtle full resolve-button"
                    disabled={mutation.isPending}
                    onClick={() =>
                      act(() =>
                        api.update(id, {
                          revision: t.revision,
                          status: "ditinjau",
                        }),
                      )
                    }
                  >
                    Buka kembali tiket
                  </button>
                )}
              </>
            ) : (
              <div className="empty">
                <FileText size={27} />
                <h3>Draf sedang disiapkan</h3>
                <p>
                  {activeJob(t)
                    ? "Draf akan muncul setelah analisis selesai."
                    : "Jalankan analisis untuk menyiapkan jawaban."}
                </p>
              </div>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}

function OverviewPage() {
  const q = useQuery({ queryKey: ["overview"], queryFn: api.overview });
  const o = q.data;
  const tickets = useQuery({
    queryKey: ["tickets", ""],
    queryFn: () => api.tickets(new URLSearchParams()),
  });
  if (q.isLoading)
    return (
      <div className="page">
        <Loading />
      </div>
    );
  if (q.isError || !o)
    return (
      <div className="page">
        <ErrorBox error={q.error} />
      </div>
    );
  const categories = Object.entries(o.categories)
    .filter(([, v]) => v > 0)
    .map(([key, value]) => ({ name: CATEGORIES[key as Category], value }));
  const statuses = [
    { name: "Baru", value: o.new },
    { name: "Ditinjau", value: o.review },
    { name: "Disetujui", value: o.approved },
    { name: "Selesai", value: o.resolved },
  ];
  return (
    <div className="page">
      <PageHeading
        eyebrow="WORKSPACE OVERVIEW"
        title="Ringkasan operasional"
        description="Lihat beban penanganan dan keputusan yang sudah dibuat."
        action={
          <Link to="/tickets" className="button subtle">
            Buka inbox <ArrowRight size={15} />
          </Link>
        }
      />
      <div className="stats-grid">
        <Stat
          icon={<InboxIcon size={19} />}
          label="Seluruh tiket"
          value={o.total}
          foot="Data pada workspace ini"
        />
        <Stat
          icon={<Clock3 size={19} />}
          label="Menunggu penanganan"
          value={o.new}
          foot="Belum ditinjau operator"
        />
        <Stat
          icon={<CheckCheck size={19} />}
          label="Draf disetujui"
          value={o.approved}
          foot="Menunggu penyelesaian"
        />
        <Stat
          icon={<Tag size={19} />}
          label="Koreksi operator"
          value={o.corrections}
          foot="Kandidat data pelatihan berikutnya"
        />
      </div>
      <div className="charts-grid">
        <section className="panel">
          <div className="panel-heading">
            <h2>Volume tiket harian</h2>
            <Badge>Seluruh periode</Badge>
          </div>
          <div className="chart-wrap">
            <ResponsiveContainer width="100%" height={250}>
              <AreaChart data={o.daily}>
                <defs>
                  <linearGradient id="tealFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#0f766e" stopOpacity={0.2} />
                    <stop offset="100%" stopColor="#0f766e" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid vertical={false} stroke="#edf1f2" />
                <XAxis
                  dataKey="date"
                  tick={{ fontSize: 11 }}
                  tickFormatter={(v) =>
                    new Date(v).toLocaleDateString("id-ID", {
                      day: "numeric",
                      month: "short",
                    })
                  }
                />
                <YAxis
                  allowDecimals={false}
                  tick={{ fontSize: 11 }}
                  width={25}
                />
                <Tooltip />
                <Area
                  type="monotone"
                  dataKey="count"
                  name="Tiket"
                  stroke="#0f766e"
                  strokeWidth={2.5}
                  fill="url(#tealFill)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </section>
        <section className="panel">
          <div className="panel-heading">
            <h2>Distribusi kategori</h2>
            <Tag size={16} />
          </div>
          <div className="donut-layout">
            <div className="donut">
              <ResponsiveContainer width="100%" height={190}>
                <PieChart>
                  <Pie
                    data={categories}
                    dataKey="value"
                    innerRadius={58}
                    outerRadius={79}
                    paddingAngle={4}
                  >
                    {categories.map((_, i) => (
                      <Cell key={i} fill={palette[i]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
              <div className="donut-label">
                <strong>{o.total}</strong>
                <span>tiket</span>
              </div>
            </div>
            <div className="chart-legend">
              {categories.map((v, i) => (
                <div key={v.name}>
                  <i style={{ background: palette[i] }} />
                  <span>{v.name}</span>
                  <strong>{v.value}</strong>
                </div>
              ))}
            </div>
          </div>
        </section>
      </div>
      <div className="charts-grid lower">
        <section className="panel">
          <div className="panel-heading">
            <h2>Status penanganan</h2>
            <Activity size={17} />
          </div>
          <div className="chart-wrap">
            <ResponsiveContainer width="100%" height={210}>
              <BarChart data={statuses} barSize={32}>
                <CartesianGrid vertical={false} stroke="#edf1f2" />
                <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                <YAxis
                  allowDecimals={false}
                  width={25}
                  tick={{ fontSize: 11 }}
                />
                <Tooltip />
                <Bar
                  dataKey="value"
                  name="Tiket"
                  fill="#0f766e"
                  radius={[5, 5, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>
        <section className="panel">
          <div className="panel-heading">
            <h2>Perlu perhatian</h2>
            <Badge tone="warning">Prioritas tinggi</Badge>
          </div>
          <div className="attention-list">
            {tickets.data?.items
              .filter((t) => t.priority === "P1" && t.status !== "selesai")
              .map((t) => (
                <Link to={"/tickets/" + t.id} key={t.id}>
                  <span className="attention-icon">
                    <TriangleAlert size={18} />
                  </span>
                  <div>
                    <strong>{t.subject}</strong>
                    <small>
                      #{t.number} · {t.customer}
                    </small>
                  </div>
                  <ArrowUpRight size={17} />
                </Link>
              ))}
          </div>
        </section>
      </div>
      <div className="bottom-note">
        <CircleHelp size={14} />
        Statistik menghitung aktivitas aplikasi. Data demo tidak mengukur dampak
        bisnis nyata.
      </div>
    </div>
  );
}

function PoliciesPage() {
  const q = useQuery({ queryKey: ["policies"], queryFn: api.policies });
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const rows = q.data?.filter(
    (p) =>
      (!category || p.category === category) &&
      (!search ||
        (p.title + " " + p.body).toLowerCase().includes(search.toLowerCase())),
  );
  return (
    <div className="page">
      <PageHeading
        eyebrow="KNOWLEDGE BASE"
        title="Kebijakan toko"
        description="Sumber jawaban yang bisa dibaca, diperiksa, dan ditelusuri."
        action={
          <Badge tone="teal">
            <ShieldCheck size={13} />
            Versi kebijakan tetap
          </Badge>
        }
      />
      <div className="notice compact">
        <BookOpen size={17} />
        <span>
          Kebijakan Toko Senada adalah simulasi untuk demo. Setiap draf
          menyimpan versi sumber yang digunakan.
        </span>
      </div>
      <div className="policy-tools">
        <div className="search-input">
          <Search size={17} />
          <input
            aria-label="Cari kebijakan"
            placeholder="Cari pengiriman, retur, pembayaran..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <select
          aria-label="Kategori kebijakan"
          value={category}
          onChange={(e) => setCategory(e.target.value)}
        >
          <option value="">Semua kategori</option>
          {Object.entries(CATEGORIES).map(([v, l]) => (
            <option key={v} value={v}>
              {l}
            </option>
          ))}
        </select>
      </div>
      {q.isLoading ? (
        <Loading />
      ) : q.isError ? (
        <ErrorBox error={q.error} />
      ) : (
        <div className="policy-grid">
          {rows?.map((p) => (
            <article className="panel policy-card" key={p.id}>
              <div className="policy-top">
                <div className="policy-icon">
                  <BookOpen size={20} />
                </div>
                <Badge>v{p.version}</Badge>
              </div>
              <div className="eyebrow">
                {p.category ? CATEGORIES[p.category] : "Kebijakan"}
              </div>
              <h2>{p.title}</h2>
              <p>{p.body}</p>
              <div className="policy-id">
                <ShieldCheck size={13} />
                {p.id}
              </div>
            </article>
          ))}
        </div>
      )}
      {rows?.length === 0 && (
        <div className="empty">
          <Search />
          <h3>Kebijakan tidak ditemukan</h3>
          <p>Sesuaikan kata kunci atau kategori.</p>
        </div>
      )}
    </div>
  );
}

function EvaluationPage() {
  const q = useQuery({ queryKey: ["evaluations"], queryFn: api.evaluations });
  const [selected, setSelected] = useState("");
  const [compare, setCompare] = useState("");
  const rows = q.data || [];
  const e =
    rows.find((e) => e.id === selected) ||
    rows.find((e) => e.id === "tfidf-calibrated-v1") ||
    rows[0];
  const other = rows.find((e) => e.id === compare);
  return (
    <div className="page">
      <PageHeading
        eyebrow="MODEL INTELLIGENCE"
        title="Evaluasi model"
        description="Lihat hasil pengujian, perbandingan, dan batas kemampuan model."
        action={
          e && (
            <button
              className="button subtle"
              onClick={() => downloadJSON(e, "ticketops-" + e.id + ".json")}
            >
              <Download size={15} />
              Unduh laporan
            </button>
          )
        }
      />
      {q.isLoading ? (
        <Loading />
      ) : q.isError ? (
        <ErrorBox error={q.error} />
      ) : !e ? (
        <div className="panel empty">
          <Activity size={32} />
          <h2>Belum ada hasil eksperimen</h2>
          <p>
            Jalankan pipeline evaluasi lokal. Hasil yang belum diukur tidak
            ditampilkan sebagai skor.
          </p>
          <Link to="/system" className="button subtle">
            Lihat petunjuk lokal <ArrowRight size={15} />
          </Link>
        </div>
      ) : (
        <>
          <div className="notice warning">
            <TriangleAlert size={19} />
            <div>
              <strong>
                Benchmark sintetis — belum membuktikan performa pada pelanggan
                nyata
              </strong>
              <p>
                {e.test_count} contoh uji ·{" "}
                {e.reviewed_by_human
                  ? "Ditinjau manusia"
                  : "Belum ditinjau manusia"}{" "}
                · {e.dataset_version}. Threshold dan hasil harus diuji ulang
                pada data berizin yang representatif.
              </p>
            </div>
          </div>
          <div className="evaluation-selectors">
            <label>
              Eksperimen utama
              <select
                value={e.id}
                onChange={(event) => setSelected(event.target.value)}
              >
                {rows.map((e) => (
                  <option key={e.id} value={e.id}>
                    {e.model}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Bandingkan dengan
              <select
                value={compare}
                onChange={(event) => setCompare(event.target.value)}
              >
                <option value="">Pilih eksperimen pembanding</option>
                {rows
                  .filter((r) => r.id !== e.id)
                  .map((r) => (
                    <option key={r.id} value={r.id}>
                      {r.model}
                    </option>
                  ))}
              </select>
            </label>
          </div>
          <div className="metric-grid">
            <Metric
              label="Macro-F1"
              value={pct(e.macro_f1)}
              icon={<TrendingUp size={18} />}
              note="Rata-rata seluruh kategori"
            />
            <Metric
              label="Akurasi"
              value={pct(e.accuracy)}
              icon={<CheckCircle2 size={18} />}
              note="Pada test sintetis yang sama"
            />
            <Metric
              label="Latency p50"
              value={e.latency_p50_ms.toFixed(1) + " ms"}
              icon={<Clock3 size={18} />}
              note="Inferensi hangat · CPU lokal"
            />
            <Metric
              label="Latency p95"
              value={e.latency_p95_ms.toFixed(1) + " ms"}
              icon={<Cpu size={18} />}
              note="Model dan preprocessing"
            />
          </div>
          {other && (
            <section className="panel comparison">
              <div className="panel-heading">
                <h2>Perbandingan eksperimen</h2>
              </div>
              <div className="table-scroll">
                <table>
                  <thead>
                    <tr>
                      <th>Model</th>
                      <th>Macro-F1</th>
                      <th>Akurasi</th>
                      <th>Latency p95</th>
                    </tr>
                  </thead>
                  <tbody>
                    {[e, other].map((r) => (
                      <tr key={r.id}>
                        <td>{r.model}</td>
                        <td>{pct(r.macro_f1)}</td>
                        <td>{pct(r.accuracy)}</td>
                        <td>{r.latency_p95_ms.toFixed(1)} ms</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          )}
          <div className="evaluation-grid">
            <section className="panel">
              <div className="panel-heading">
                <h2>Confusion matrix</h2>
                <Badge>Aktual ↓ · Prediksi →</Badge>
              </div>
              <div className="matrix-wrap">
                <table className="matrix">
                  <thead>
                    <tr>
                      <th />
                      {e.labels.map((l, i) => (
                        <th key={l} title={CATEGORIES[l]}>
                          {i + 1}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {e.labels.map((l, i) => (
                      <tr key={l}>
                        <th>
                          {i + 1}. {CATEGORIES[l]}
                        </th>
                        {e.confusion_matrix[i].map((n, j) => (
                          <td
                            key={j}
                            style={{
                              background: n
                                ? "rgba(15,118,110," +
                                  (0.08 + Math.min(n / 40, 1) * 0.6) +
                                  ")"
                                : "#f8fafc",
                              color: n > 20 ? "white" : "#52716e",
                            }}
                          >
                            {n}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <p className="matrix-caption">
                Nomor kolom mengikuti urutan kategori pada baris.
              </p>
            </section>
            <section className="panel">
              <div className="panel-heading">
                <h2>F1 per kategori</h2>
                <Tag size={17} />
              </div>
              <div className="class-scores">
                {e.labels.map((l, i) => (
                  <div key={l}>
                    <div>
                      <span>
                        {i + 1}. {CATEGORIES[l]}
                      </span>
                      <strong>{pct(e.per_class[l]["f1-score"])}</strong>
                    </div>
                    <span className="score-track">
                      <i
                        style={{
                          width: e.per_class[l]["f1-score"] * 100 + "%",
                          background: palette[i],
                        }}
                      />
                    </span>
                  </div>
                ))}
              </div>
            </section>
          </div>
          <section className="panel errors-panel">
            <div className="panel-heading">
              <h2>Contoh kesalahan klasifikasi</h2>
              <Badge>{e.errors.length} ditampilkan</Badge>
            </div>
            {e.errors.length ? (
              <div className="table-scroll">
                <table>
                  <thead>
                    <tr>
                      <th>Pesan</th>
                      <th>Label referensi sintetis</th>
                      <th>Prediksi model</th>
                    </tr>
                  </thead>
                  <tbody>
                    {e.errors.slice(0, 12).map((r, i) => (
                      <tr key={i}>
                        <td>{r.text}</td>
                        <td>{CATEGORIES[r.expected]}</td>
                        <td>{CATEGORIES[r.predicted]}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="empty-inline">
                <CheckCircle2 size={18} />
                <p>
                  Tidak ada kesalahan pada kumpulan uji ini. Periksa keragaman
                  data sebelum menarik kesimpulan.
                </p>
              </div>
            )}
          </section>
          <div className="evaluation-notes">
            <h3>Catatan pengujian</h3>
            {e.notes.map((n, i) => (
              <p key={i}>
                <Circle size={7} />
                {n}
              </p>
            ))}
            <p>Waktu eksperimen: {date(e.created_at)}</p>
          </div>
        </>
      )}
    </div>
  );
}
function Metric({
  label,
  value,
  icon,
  note,
}: {
  label: string;
  value: string;
  icon: ReactNode;
  note: string;
}) {
  return (
    <div className="stat-card">
      <div className="stat-top">
        <span>{label}</span>
        <span className="stat-icon">{icon}</span>
      </div>
      <strong>{value}</strong>
      <small>{note}</small>
    </div>
  );
}
function downloadJSON(data: unknown, name: string) {
  const url = URL.createObjectURL(
    new Blob([JSON.stringify(data, null, 2)], { type: "application/json" }),
  );
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
  URL.revokeObjectURL(url);
}
function SystemPage() {
  const q = useQuery({ queryKey: ["readiness"], queryFn: api.readiness });
  const qc = useQueryClient();
  const s = q.data;
  return (
    <div className="page">
      <PageHeading
        eyebrow="WORKSPACE SETTINGS"
        title="Status sistem"
        description="Ketahui komponen yang berjalan dan asal hasil yang ditampilkan."
        action={
          <button className="button subtle" onClick={() => q.refetch()}>
            <RefreshCw size={15} />
            Periksa kembali
          </button>
        }
      />
      {q.isError ? (
        <ErrorBox error={q.error} />
      ) : (
        <>
          <div className="system-hero">
            <div className="system-symbol">
              <Cpu size={30} />
            </div>
            <div>
              <Badge tone="teal">
                {SHOWCASE ? "Mode showcase" : "Mode lokal"}
              </Badge>
              <h2>
                {SHOWCASE
                  ? "Jelajahi alurnya. Periksa buktinya."
                  : "Pipeline lokal, kendali di tanganmu."}
              </h2>
              <p>
                {SHOWCASE
                  ? "Halaman ini menampilkan skenario tersimpan dan laporan eksperimen. Tidak ada inferensi langsung di hosting."
                  : "Analisis berjalan di backend lokal. Qwen menyusun draf, operator mengambil keputusan."}
              </p>
            </div>
          </div>
          <div className="system-grid">
            {[
              ["API", s?.api || "Memeriksa", <Activity size={20} />],
              ["Database", s?.database || "Memeriksa", <InboxIcon size={20} />],
              [
                "Classifier",
                s?.classifier.version || "Memeriksa",
                <Tag size={20} />,
              ],
              [
                "Generation",
                SHOWCASE
                  ? "Aktifkan versi lokal"
                  : s?.ollama
                    ? "Ollama tersedia"
                    : "Template fallback",
                <Sparkles size={20} />,
              ],
            ].map(([label, value, icon], i) => (
              <div className="panel system-card" key={i}>
                <div className="stat-icon">{icon}</div>
                <small>{label}</small>
                <strong>{value}</strong>
              </div>
            ))}
          </div>
          <div className="charts-grid system-info">
            <section className="panel">
              <div className="panel-heading">
                <h2>Jalankan versi lengkap</h2>
                <Cpu size={18} />
              </div>
              <div className="panel-body">
                <p className="subtle-note">
                  Dari folder source TicketOps, gunakan Windows PowerShell.
                  Skrip menyiapkan dependency dan baseline pada penggunaan
                  pertama.
                </p>
                <pre>
                  <code>powershell -File scripts/start-local.ps1 -Install</code>
                </pre>
                <div className="setup-steps">
                  <div>
                    <span>1</span>
                    <div>
                      <strong>Frontend React</strong>
                      <p>Inbox, editor draf, dan dashboard pada port 5178.</p>
                    </div>
                  </div>
                  <div>
                    <span>2</span>
                    <div>
                      <strong>Backend + worker</strong>
                      <p>
                        FastAPI dan antrean tersimpan. SQLite untuk quickstart;
                        PostgreSQL melalui Docker.
                      </p>
                    </div>
                  </div>
                  <div>
                    <span>3</span>
                    <div>
                      <strong>Model lokal</strong>
                      <p>
                        TF-IDF bootstrap tersedia. Qwen3 4B melalui Ollama;
                        training IndoBERT disediakan untuk Colab.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </section>
            <section className="panel">
              <div className="panel-heading">
                <h2>Transparansi demo</h2>
                <ShieldCheck size={18} />
              </div>
              <div className="panel-body transparency">
                <p>
                  <CheckCircle2 size={17} />
                  Nama, pesanan, dan kebijakan merupakan simulasi.
                </p>
                <p>
                  <CheckCircle2 size={17} />
                  Dataset bootstrap belum ditinjau manusia.
                </p>
                <p>
                  <CheckCircle2 size={17} />
                  Draf tetap memerlukan pemeriksaan fakta oleh operator.
                </p>
                <p>
                  <CheckCircle2 size={17} />
                  Tidak ada integrasi pengiriman pesan atau transaksi.
                </p>
                <p>
                  <CheckCircle2 size={17} />
                  Koreksi tidak langsung melatih ulang model.
                </p>
                {SHOWCASE && (
                  <button
                    className="button subtle"
                    onClick={async () => {
                      api.reset();
                      await qc.invalidateQueries();
                    }}
                  >
                    Reset perubahan simulasi <RefreshCw size={14} />
                  </button>
                )}
              </div>
            </section>
          </div>
        </>
      )}
    </div>
  );
}
