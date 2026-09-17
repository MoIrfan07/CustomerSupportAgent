import { CreditCard, FileText } from "lucide-react";
import type { ReactNode } from "react";
import "./SidebarPage.css";

type BillingData = {
  invoices?: Array<Record<string, unknown>>;
  payments?: Array<Record<string, unknown>>;
  billing?: {
    invoices?: Array<Record<string, unknown>>;
    payments?: Array<Record<string, unknown>>;
  };
};

export default function MyBilling({
  customerId,
  data,
  loading,
  error,
}: {
  customerId: string;
  data: BillingData;
  loading: boolean;
  error: string;
}) {
  const invoices =
    data.invoices && data.invoices.length > 0
      ? data.invoices
      : data.billing?.invoices ?? [];
  const payments =
    data.payments && data.payments.length > 0
      ? data.payments
      : data.billing?.payments ?? [];

  return (
    <section className="sidebar-page">
      <div className="sidebar-page-inner">
        <header className="sidebar-page-header">
          <div>
            <span className="conversation-label">MY SUPPORT</span>
            <h2>My billing</h2>
          </div>
          <p>Invoices and payments for {customerId || "your account"}.</p>
        </header>
        {loading ? (
          <div className="sidebar-page-card">
            <div className="sidebar-page-empty">Loading billing data...</div>
          </div>
        ) : error ? (
          <div className="sidebar-page-card">
            <div className="sidebar-page-empty">{error}</div>
          </div>
        ) : (
          <div className="billing-sections">
            <BillingSection
              title="INVOICES"
              icon={<FileText size={17} />}
              empty="No invoices found."
              rows={invoices.map((item) => ({
                id: item.invoice_id ?? item.id,
                label: "Invoice",
                amount: item.amount,
                status: item.status,
                date: item.invoice_date,
              }))}
            />
            <BillingSection
              title="PAYMENTS"
              icon={<CreditCard size={17} />}
              empty="No payments found."
              rows={payments.map((item) => ({
                id: item.payment_id ?? item.id,
                label: "Payment",
                amount: item.amount,
                status: item.status,
                date: item.payment_date,
              }))}
            />
          </div>
        )}
      </div>
    </section>
  );
}

function BillingSection({
  title,
  icon,
  empty,
  rows,
}: {
  title: string;
  icon: ReactNode;
  empty: string;
  rows: Array<Record<string, unknown>>;
}) {
  return (
    <div className="sidebar-page-card billing-section">
      <div className="sidebar-page-card-header">{title}</div>
      {rows.length === 0 ? (
        <div className="sidebar-page-empty">{empty}</div>
      ) : (
        rows.map((item) => (
          <div className="sidebar-page-row" key={String(item.id)}>
            <div className="sidebar-page-icon">{icon}</div>
            <div>
              <strong>{String(item.label)}</strong>
              <span>
                {String(item.id)} · ${String(item.amount ?? "")} ·{" "}
                {String(item.date || "Date unavailable")}
              </span>
            </div>
            <span className="sidebar-page-status">
              {String(item.status || "Unknown")}
            </span>
          </div>
        ))
      )}
    </div>
  );
}
