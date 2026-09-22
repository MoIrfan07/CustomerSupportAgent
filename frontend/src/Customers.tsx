import { Users } from "lucide-react";
import "./SidebarPage.css";
import type { CustomerRecord } from "./workspaceApi";

export default function Customers({ customers, loading, error }: { customers: CustomerRecord[]; loading: boolean; error: string }) {
  return <section className="sidebar-page"><div className="sidebar-page-inner"><header className="sidebar-page-header"><div><span className="conversation-label">WORKSPACE</span><h2>Customers</h2></div><p>Customer profiles available to authorized staff.</p></header><div className="sidebar-page-card"><div className="sidebar-page-card-header">CUSTOMER DIRECTORY</div>{loading ? <div className="sidebar-page-empty">Loading customer data...</div> : error ? <div className="sidebar-page-empty">{error}</div> : customers.map((customer) => <div className="sidebar-page-row" key={customer.customer_id}><div className="sidebar-page-icon"><Users size={17} /></div><div><strong>{customer.name || customer.full_name || customer.customer_id}</strong><span>{customer.customer_id} · Created {customer.created_at || "Date unavailable"}</span></div><span>{customer.plan || "—"}</span></div>)}</div></div></section>;
}
