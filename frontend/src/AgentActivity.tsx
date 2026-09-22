import { Activity, CheckCircle2 } from "lucide-react";
import type { ActivityItem } from "./types";
import "./SidebarPage.css";

export default function AgentActivity({ activities }: { activities: ActivityItem[] }) {
  return <section className="sidebar-page"><div className="sidebar-page-inner"><header className="sidebar-page-header"><div><span className="conversation-label">WORKSPACE</span><h2>Agent activity</h2></div><p>Recent agent, tool, and approval events.</p></header><div className="sidebar-page-card"><div className="sidebar-page-card-header">LIVE ACTIVITY</div>{activities.length === 0 ? <div className="sidebar-page-empty">Activities will appear here after a request is processed.</div> : activities.map((item) => <div className="sidebar-page-row" key={item.id}><div className="sidebar-page-icon"><Activity size={17} /></div><div><strong>{item.label}</strong><span>{item.type}</span></div><CheckCircle2 color="#16a34a" size={17} /></div>)}</div></div></section>;
}
