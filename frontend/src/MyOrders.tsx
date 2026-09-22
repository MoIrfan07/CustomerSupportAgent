import { Package } from "lucide-react";
import type { ReactNode } from "react";
import "./SidebarPage.css";

type MyOrdersProps = { customerId: string; orders: Array<Record<string, unknown>>; loading: boolean; error: string };

export default function MyOrders({ customerId, orders, loading, error }: MyOrdersProps) {
  return (
    <Page title="My orders" description={`Orders connected to ${customerId || "your account"}.`}>
      <div className="sidebar-page-card-header">ORDER HISTORY</div>
      {loading ? <div className="sidebar-page-empty">Loading order data...</div> : error ? <div className="sidebar-page-empty">{error}</div> : orders.map((order) => (
        <div className="sidebar-page-row" key={String(order.order_id)}>
          <div className="sidebar-page-icon"><Package size={17} /></div>
          <div><strong>{String(order.product || "Order")}</strong><span>{String(order.order_id)} · ${String(order.amount ?? "")} · {String(order.order_date || "Date unavailable")}</span></div>
          <span className="sidebar-page-status">{String(order.status || "Unknown")}</span>
        </div>
      ))}
    </Page>
  );
}

function Page({ title, description, children }: { title: string; description: string; children: ReactNode }) {
  return <section className="sidebar-page"><div className="sidebar-page-inner"><header className="sidebar-page-header"><div><span className="conversation-label">MY SUPPORT</span><h2>{title}</h2></div><p>{description}</p></header><div className="sidebar-page-card">{children}</div></div></section>;
}
