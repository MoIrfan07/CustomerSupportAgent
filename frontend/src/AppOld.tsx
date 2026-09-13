import { useState, useEffect, useRef } from "react";
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
  LogOut,
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
  type: "tool" | "agent" | "success" | "approval";
  status: "running" | "completed" | "waiting";
};

const initialMessages: Message[] = [
  {
    id: 1,
    role: "assistant",
    content:
      "Hello! I'm your customer support AI agent. I can investigate customers, orders, payments, invoices, tickets, refunds, and other support requests.",
  },
];

const ACCESS_TOKEN_KEY = "customer_support_access_token";

function App() {
  const [messages, setMessages] =
    useState<Message[]>(initialMessages);

  const messagesEndRef =
    useRef<HTMLDivElement | null>(null);

  const [input, setInput] = useState("");

  const [loading, setLoading] =
    useState(false);

  const [userRole, setUserRole] =
    useState("guest");

  const [username, setUsername] =
    useState("guest");

  const [accessToken, setAccessToken] =
    useState("");

  const [showLogin, setShowLogin] =
    useState(true);

  const [loginUsername, setLoginUsername] =
    useState("");

  const [loginPassword, setLoginPassword] =
    useState("");

  const [loginError, setLoginError] =
    useState("");

  const [loginLoading, setLoginLoading] =
    useState(false);

  const displayRole =
    userRole.charAt(0).toUpperCase() +
    userRole.slice(1);

  useEffect(() => {
    const storedToken =
      localStorage.getItem(ACCESS_TOKEN_KEY);

    if (!storedToken) {
      setUserRole("guest");
      setUsername("guest");
      setAccessToken("");
      setShowLogin(true);
      return;
    }

    try {
      const tokenPayload = JSON.parse(
        atob(storedToken.split(".")[1])
      );

      const currentTime = Math.floor(
        Date.now() / 1000
      );

      if (
        tokenPayload.exp &&
        tokenPayload.exp <= currentTime
      ) {
        console.log(
          "[AUTH] Stored session has expired."
        );

        localStorage.removeItem(
          ACCESS_TOKEN_KEY
        );

        setAccessToken("");
        setUsername("guest");
        setUserRole("guest");
        setShowLogin(true);

        return;
      }

      console.log(
        "[AUTH] Restoring stored session:",
        tokenPayload.sub,
        "role:",
        tokenPayload.role
      );

      setAccessToken(storedToken);

      setUsername(
        tokenPayload.sub || "guest"
      );

      setUserRole(
        tokenPayload.role || "guest"
      );

      setShowLogin(false);
    } catch (error) {
      console.error(
        "[AUTH] Invalid stored session:",
        error
      );

      localStorage.removeItem(
        ACCESS_TOKEN_KEY
      );

      setAccessToken("");
      setUsername("guest");
      setUserRole("guest");
      setShowLogin(true);
    }
  }, []);

  const [activities, setActivities] =
    useState<ActivityItem[]>([]);

  const [customer, setCustomer] =
    useState({
      name: "No customer selected",
      id: "—",
      status: "—",
      plan: "—",
    });

  useEffect(() => {
    console.log(
      "[CUSTOMER] Current customer:",
      customer.name
    );
  }, [customer]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [messages, loading]);

  const handleLogin = async (
    event: React.FormEvent<HTMLFormElement>
  ) => {
    event.preventDefault();

    if (
      !loginUsername.trim() ||
      !loginPassword
    ) {
      setLoginError(
        "Please enter your username or customer ID and password."
      );
      return;
    }

    console.log(
      "[AUTH] Login attempt:",
      loginUsername.trim()
    );

    setLoginLoading(true);
    setLoginError("");

    try {
      const body = new URLSearchParams();

      body.append(
        "username",
        loginUsername.trim()
      );

      body.append(
        "password",
        loginPassword
      );

      console.log(
        "[AUTH] Sending login request..."
      );

      const response = await fetch(
        "http://127.0.0.1:8000/auth/login",
        {
          method: "POST",
          headers: {
            "Content-Type":
              "application/x-www-form-urlencoded",
          },
          body: body.toString(),
        }
      );

      console.log(
        "[AUTH] Login response status:",
        response.status
      );

      if (!response.ok) {
        console.warn(
          "[AUTH] Login rejected:",
          response.status
        );

        setLoginError(
          "Incorrect username, customer ID, or password."
        );

        return;
      }

      const data = await response.json();

      console.log(
        "[AUTH] Login response received."
      );

      if (!data.access_token) {
        console.error(
          "[AUTH] Login failed: no access token."
        );

        setLoginError(
          "Login failed. No access token was returned."
        );

        return;
      }

      const tokenPayload = JSON.parse(
        atob(data.access_token.split(".")[1])
      );

      console.log(
        "[AUTH] Login successful:",
        tokenPayload.sub,
        "role:",
        tokenPayload.role,
        "customer:",
        tokenPayload.customer_id
      );

      localStorage.setItem(
        ACCESS_TOKEN_KEY,
        data.access_token
      );

      setAccessToken(data.access_token);

      setUsername(
        tokenPayload.sub ||
        loginUsername.trim()
      );

      setUserRole(
        tokenPayload.role || "user"
      );

      setShowLogin(false);
      setLoginPassword("");
      setLoginError("");

    } catch (error) {
      console.error(
        "[AUTH] Login request failed:",
        error
      );

      setLoginError(
        "Unable to connect to the authentication service."
      );
    } finally {
      setLoginLoading(false);
    }
  };

  const logout = () => {
    console.log(
      "[AUTH] Logging out:",
      username
    );

    localStorage.removeItem(
      ACCESS_TOKEN_KEY
    );

    setAccessToken("");
    setUsername("guest");
    setUserRole("guest");

    setLoginUsername("");
    setLoginPassword("");
    setLoginError("");

    setMessages(initialMessages);
    setActivities([]);

    setCustomer({
      name: "No customer selected",
      id: "—",
      status: "—",
      plan: "—",
    });

    setInput("");

    setShowLogin(true);
  };

  const skipLogin = () => {
    console.log(
      "[AUTH] Continuing as guest"
    );

    localStorage.removeItem(
      ACCESS_TOKEN_KEY
    );

    setAccessToken("");
    setUsername("guest");
    setUserRole("guest");

    setLoginUsername("");
    setLoginPassword("");
    setLoginError("");

    setShowLogin(false);
  };

  const openLogin = () => {
    console.log(
      "[AUTH] Opening login dialog"
    );

    setLoginError("");
    setShowLogin(true);
  };

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
      console.log(
        "[CHAT] Sending message:",
        text
      );

      console.log(
        "[CHAT] User:",
        username
      );

      console.log(
        "[CHAT] Role:",
        userRole
      );

      console.log(
        "[CHAT] Authentication:",
        accessToken
          ? "authenticated"
          : "guest"
      );

      const response = await fetch(
        "http://127.0.0.1:8000/chat",
        {
          method: "POST",
          headers: {
            "Content-Type":
              "application/json",

            ...(accessToken
              ? {
                Authorization:
                  `Bearer ${accessToken}`,
              }
              : {}),
          },

          body: JSON.stringify({
            message: text,
            thread_id:
              "customer-support-session",
          }),
        }
      );

      console.log(
        "[CHAT] Response status:",
        response.status
      );

      const data = await response.json();

      console.log(
        "[CHAT] Backend response:",
        data
      );

      if (
        response.status === 401 &&
        accessToken
      ) {
        console.warn(
          "[AUTH] Session is no longer valid."
        );

        logout();

        return;
      }

      if (!response.ok) {
        console.error(
          "[CHAT] Backend request failed:",
          response.status,
          data
        );

        throw new Error(
          data.detail ||
          data.message ||
          "Backend request failed."
        );
      }

      console.log(
        "[CHAT] Agent response:",
        data.response
      );

      setUserRole(
        data.user_role || userRole
      );

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
      console.error(
        "[CHAT] Request error:",
        error
      );

      const errorMessage =
        error instanceof Error
          ? error.message
          : "An unexpected error occurred.";

      setMessages((previous) => [
        ...previous,
        {
          id: Date.now() + 1,
          role: "assistant",
          content: errorMessage,
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

          <button
            type="button"
            className="role-card"
            onClick={openLogin}
            title={
              username
                ? `Logged in as ${username}`
                : "Login"
            }
            style={{
              width: "100%",
              border: "none",
              textAlign: "left",
              cursor: "pointer",
            }}
          >

            <div className="role-avatar">
              {displayRole
                .charAt(0)
                .toUpperCase()}
            </div>

            <div className="role-info">
              <strong>
                {displayRole}
              </strong>

              <span>
                Authorized user
              </span>
            </div>

            <ChevronRight size={16} />

          </button>

          {accessToken && (
            <button
              type="button"
              className="nav-item"
              onClick={logout}
              style={{
                marginTop: "4px",
                color: "#fca5a5",
              }}
            >
              <LogOut size={17} />
              Logout
            </button>
          )}

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
              {displayRole} access
            </div>

            <button
              type="button"
              className="profile"
              onClick={openLogin}
              title={
                username
                  ? `Logged in as ${username}`
                  : "Login"
              }
              style={{
                border: "none",
                background: "transparent",
                padding: 0,
                cursor: "pointer",
              }}
            >
              <div className="profile-avatar">
                {displayRole
                  .charAt(0)
                  .toUpperCase()}
              </div>
            </button>

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
                  Customer Investigation
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
                    className={`message-row ${message.role}`}
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

              <div ref={messagesEndRef} />

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

            {/* <div className="panel-card">

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

            </div> */}


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
                  ACTIVITY
                </span>

                <Activity size={16} />

              </div>

              <div className="activity-list">

                {activities.length ===
                  0 ? (

                  <div className="empty-activity">
                    Activities will appear here.
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
                            <CheckCircle2 size={15} />
                          ) : activity.status ===
                            "waiting" ? (
                            <ShieldCheck size={15} />
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
                                : activity.type ===
                                  "approval"
                                  ? "Approval"
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


      {showLogin && (

        <div
          className="login-overlay"
          role="dialog"
          aria-modal="true"
          aria-labelledby="login-title"
        >

          <div className="login-popup">

            <div className="login-popup-header">

              <div className="login-popup-icon">
                <ShieldCheck size={20} />
              </div>

              <div>

                <h2 id="login-title">
                  Sign in
                </h2>

                <p>
                  Use your username or customer ID
                  to access an authorized support role.
                </p>

              </div>

            </div>

            <form
              className="login-form"
              onSubmit={handleLogin}
            >

              <div className="login-field">

                <label htmlFor="login-username">
                  Username or Customer ID
                </label>

                <input
                  id="login-username"
                  type="text"
                  value={loginUsername}
                  onChange={(event) =>
                    setLoginUsername(
                      event.target.value
                    )
                  }
                  autoComplete="username"
                  placeholder="CUST-1001, manager, or support"
                  disabled={loginLoading}
                />

              </div>

              <div className="login-field">

                <label htmlFor="login-password">
                  Password
                </label>

                <input
                  id="login-password"
                  type="password"
                  value={loginPassword}
                  onChange={(event) =>
                    setLoginPassword(
                      event.target.value
                    )
                  }
                  autoComplete="current-password"
                  placeholder="Enter your password"
                  disabled={loginLoading}
                />

              </div>

              {loginError && (

                <p
                  className="login-error"
                  role="alert"
                >
                  {loginError}
                </p>

              )}

              <button
                className="login-submit"
                type="submit"
                disabled={loginLoading}
              >
                {loginLoading
                  ? "Signing in..."
                  : "Sign in"}
              </button>

            </form>

            <div className="login-divider">
              <span>OR</span>
            </div>

            <button
              className="login-skip"
              type="button"
              onClick={skipLogin}
              disabled={loginLoading}
            >
              Continue as default user
            </button>

          </div>

        </div>

      )}

    </div>
  );
}

export default App;