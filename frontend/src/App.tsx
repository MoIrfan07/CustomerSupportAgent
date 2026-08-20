import { useState } from "react";
import {
  Bot,
  Send,
  User,
  ShieldCheck,
  Activity,
  Users,
  MessageSquare,
  Settings,
  CreditCard,
  Package,
  Ticket,
  CheckCircle2,
  Loader2,
  ChevronRight,
} from "lucide-react";

import "./App.css";

type Message = {
  id: number;
  role: "user" | "assistant";
  content: string;
};

type ActivityItem = {
  id: number;
  label: string;
  type: "tool" | "agent" | "success";
  status: "running" | "completed";
};

const initialMessages: Message[] = [
  {
    id: 1,
    role: "assistant",
    content:
      "Hello! I'm your customer support AI agent. I can investigate customers, orders, payments, invoices, tickets, refunds, and other support requests.",
  },
];

function App() {
  const [messages, setMessages] =
    useState<Message[]>(initialMessages);

  const [input, setInput] = useState("");

  const [loading, setLoading] =
    useState(false);

  const [activities, setActivities] =
    useState<ActivityItem[]>([]);

  const [customer, setCustomer] =
    useState({
      name: "No customer selected",
      id: "—",
      status: "—",
      plan: "—",
    });

  const sendMessage = async () => {
    const text = input.trim();

    if (!text || loading) {
      return;
    }

    const userMessage: Message = {
      id: Date.now(),
      role: "user",
      content: text,
    };

    setMessages((previous) => [
      ...previous,
      userMessage,
    ]);

    setInput("");
    setLoading(true);

    setActivities([
      {
        id: Date.now(),
        label: "Understanding request",
        type: "agent",
        status: "running",
      },
    ]);

    try {
      /*
       * This will connect to your FastAPI backend.
       *
       * Expected backend endpoint:
       *
       * POST http://127.0.0.1:8000/chat
       *
       * Body:
       * {
       *   "message": text,
       *   "thread_id": "customer-support-session"
       * }
       */

      const response = await fetch(
        "http://127.0.0.1:8000/chat",
        {
          method: "POST",
          headers: {
            "Content-Type":
              "application/json",
          },
          body: JSON.stringify({
            message: text,
            thread_id:
              "customer-support-session",
          }),
        }
      );

      if (!response.ok) {
        throw new Error(
          "Backend request failed."
        );
      }

      const data = await response.json();

      setMessages((previous) => [
        ...previous,
        {
          id: Date.now() + 1,
          role: "assistant",
          content:
            data.response ||
            "No response received.",
        },
      ]);

      if (data.customer) {
        setCustomer(data.customer);
      }

      setActivities((previous) =>
        previous.map((item) => ({
          ...item,
          status: "completed",
        }))
      );

      if (data.activities) {
        setActivities(
          data.activities
        );
      }
    } catch (error) {
      console.error(error);

      setMessages((previous) => [
        ...previous,
        {
          id: Date.now() + 1,
          role: "assistant",
          content:
            "I couldn't connect to the customer support backend. Please make sure the FastAPI server is running.",
        },
      ]);

      setActivities((previous) =>
        previous.map((item) => ({
          ...item,
          status: "completed",
        }))
      );
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (
    event: React.KeyboardEvent<HTMLTextAreaElement>
  ) => {
    if (
      event.key === "Enter" &&
      !event.shiftKey
    ) {
      event.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="app">

      {/* ================= SIDEBAR ================= */}

      <aside className="sidebar">

        <div className="brand">
          <div className="brand-icon">
            <Bot size={22} />
          </div>

          <div>
            <div className="brand-name">
              CustomerAI
            </div>

            <div className="brand-subtitle">
              Support Agent
            </div>
          </div>
        </div>

        <button className="new-chat">
          <MessageSquare size={17} />
          New conversation
        </button>

        <nav className="navigation">

          <div className="nav-section">
            Workspace
          </div>

          <button className="nav-item active">
            <MessageSquare size={18} />
            Conversations
          </button>

          <button className="nav-item">
            <Users size={18} />
            Customers
          </button>

          <button className="nav-item">
            <Activity size={18} />
            Agent activity
          </button>

          <button className="nav-item">
            <ShieldCheck size={18} />
            Approvals
          </button>

          <div className="nav-section">
            System
          </div>

          <button className="nav-item">
            <Settings size={18} />
            Settings
          </button>

        </nav>

        <div className="sidebar-bottom">

          <div className="role-card">

            <div className="role-avatar">
              M
            </div>

            <div className="role-info">
              <strong>Manager</strong>
              <span>Authorized user</span>
            </div>

            <ChevronRight
              size={16}
            />

          </div>

          <div className="system-status">
            <span className="status-dot" />
            Agent system online
          </div>

        </div>

      </aside>


      {/* ================= MAIN ================= */}

      <main className="main">

        {/* HEADER */}

        <header className="topbar">

          <div>
            <h1>
              Customer Support
            </h1>

            <span className="online-status">
              <span className="status-dot" />
              AI agent online
            </span>
          </div>

          <div className="topbar-actions">

            <div className="security-badge">
              <ShieldCheck size={16} />
              Manager access
            </div>

            <div className="profile">
              <div className="profile-avatar">
                M
              </div>
            </div>

          </div>

        </header>


        {/* CONTENT */}

        <div className="content">

          {/* CHAT */}

          <section className="chat-section">

            <div className="conversation-header">
              <div>
                <span className="conversation-label">
                  AI CONVERSATION
                </span>

                <h2>
                  Customer investigation
                </h2>
              </div>

              <span className="session-id">
                Session active
              </span>
            </div>


            <div className="messages">

              {messages.map(
                (message) => (

                  <div
                    key={message.id}
                    className={`message-row ${message.role
                      }`}
                  >

                    <div className="message-avatar">

                      {message.role ===
                        "assistant" ? (
                        <Bot size={17} />
                      ) : (
                        <User size={17} />
                      )}

                    </div>

                    <div className="message-content">

                      <div className="message-author">
                        {message.role ===
                          "assistant"
                          ? "CustomerAI"
                          : "You"}
                      </div>

                      <div className="message-text">
                        {message.content}
                      </div>

                    </div>

                  </div>

                )
              )}


              {loading && (

                <div className="message-row assistant">

                  <div className="message-avatar">
                    <Bot size={17} />
                  </div>

                  <div className="message-content">

                    <div className="message-author">
                      CustomerAI
                    </div>

                    <div className="thinking">

                      <Loader2
                        size={16}
                        className="spin"
                      />

                      Agent is working...

                    </div>

                  </div>

                </div>

              )}

            </div>


            {/* INPUT */}

            <div className="composer">

              <textarea
                value={input}
                onChange={(event) =>
                  setInput(
                    event.target.value
                  )
                }
                onKeyDown={
                  handleKeyDown
                }
                placeholder="Ask the customer support agent anything..."
                rows={1}
              />

              <button
                className="send-button"
                onClick={sendMessage}
                disabled={
                  loading ||
                  !input.trim()
                }
              >
                <Send size={18} />
              </button>

            </div>

            <div className="composer-hint">
              Press Enter to send ·
              Shift + Enter for a new line
            </div>

          </section>


          {/* RIGHT PANEL */}

          <aside className="right-panel">

            {/* CUSTOMER */}

            <div className="panel-card">

              <div className="panel-title">
                <span>
                  CUSTOMER
                </span>

                <Users size={16} />
              </div>

              <div className="customer-header">

                <div className="customer-avatar">
                  {customer.name !==
                    "No customer selected"
                    ? customer.name
                      .charAt(0)
                      .toUpperCase()
                    : "?"}
                </div>

                <div>
                  <h3>
                    {customer.name}
                  </h3>

                  <p>
                    {customer.id}
                  </p>
                </div>

              </div>


              <div className="customer-status">

                <span className="active-pill">
                  {customer.status}
                </span>

                <span className="plan-pill">
                  {customer.plan}
                </span>

              </div>

            </div>


            {/* QUICK STATS */}

            <div className="panel-card">

              <div className="panel-title">
                <span>
                  CUSTOMER OVERVIEW
                </span>
              </div>

              <div className="stats-grid">

                <div className="stat">
                  <Package size={17} />
                  <strong>—</strong>
                  <span>Orders</span>
                </div>

                <div className="stat">
                  <CreditCard size={17} />
                  <strong>—</strong>
                  <span>Payments</span>
                </div>

                <div className="stat">
                  <CreditCard size={17} />
                  <strong>—</strong>
                  <span>Invoices</span>
                </div>

                <div className="stat">
                  <Ticket size={17} />
                  <strong>—</strong>
                  <span>Tickets</span>
                </div>

              </div>

            </div>


            {/* AGENT ACTIVITY */}

            <div className="panel-card activity-card">

              <div className="panel-title">

                <span>
                  AGENT ACTIVITY
                </span>

                <Activity size={16} />

              </div>


              <div className="activity-list">

                {activities.length ===
                  0 ? (

                  <div className="empty-activity">
                    Agent activity will appear here.
                  </div>

                ) : (

                  activities.map(
                    (activity) => (

                      <div
                        key={activity.id}
                        className="activity-item"
                      >

                        <div className="activity-icon">

                          {activity.status ===
                            "completed" ? (
                            <CheckCircle2
                              size={15}
                            />
                          ) : (
                            <Loader2
                              size={15}
                              className="spin"
                            />
                          )}

                        </div>

                        <div>
                          <strong>
                            {activity.label}
                          </strong>

                          <span>
                            {activity.type ===
                              "tool"
                              ? "MCP tool"
                              : activity.type ===
                                "agent"
                                ? "Agent"
                                : "Completed"}
                          </span>
                        </div>

                      </div>

                    )
                  )

                )}

              </div>

            </div>


            {/* SECURITY */}

            <div className="security-card">

              <ShieldCheck size={19} />

              <div>

                <strong>
                  Secure session
                </strong>

                <span>
                  Authorization and approval
                  controls are active.
                </span>

              </div>

            </div>

          </aside>

        </div>

      </main>

    </div>
  );
}

export default App;