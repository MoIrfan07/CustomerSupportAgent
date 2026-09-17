import { ShieldCheck } from "lucide-react";
import "./SidebarPage.css";

export default function Approvals() {
  return <section className="sidebar-page"><div className="sidebar-page-inner"><header className="sidebar-page-header"><div><span className="conversation-label">WORKSPACE</span><h2>Approvals</h2></div><p>Review sensitive actions that require authorization.</p></header><div className="sidebar-page-card"><div className="sidebar-page-row"><div className="sidebar-page-icon"><ShieldCheck size={17} /></div><div><strong>No pending approvals</strong><span>New approval requests will appear here.</span></div></div></div></div></section>;
}
