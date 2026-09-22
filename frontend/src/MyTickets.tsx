import { Ticket } from "lucide-react";
import "./SidebarPage.css";

export default function MyTickets({ tickets, loading, error }: { tickets: Array<Record<string, unknown>>; loading: boolean; error: string }) {
  return <section className="sidebar-page"><div className="sidebar-page-inner"><header className="sidebar-page-header"><div><span className="conversation-label">MY SUPPORT</span><h2>My support tickets</h2></div><p>Track support requests opened for your account.</p></header><div className="sidebar-page-card"><div className="sidebar-page-card-header">TICKET HISTORY</div>{loading ? <div className="sidebar-page-empty">Loading ticket data...</div> : error ? <div className="sidebar-page-empty">{error}</div> : tickets.map((ticket) => <div className="sidebar-page-row" key={String(ticket.ticket_id)}><div className="sidebar-page-icon"><Ticket size={17} /></div><div><strong>{String(ticket.subject || "Support ticket")}</strong><span>{String(ticket.ticket_id)} · {String(ticket.ticket_date || "Date unavailable")}</span></div><span className="sidebar-page-status">{String(ticket.status || "Unknown")}</span></div>)}</div></div></section>;
}
