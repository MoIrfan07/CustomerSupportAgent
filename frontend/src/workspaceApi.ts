const API_BASE = "http://127.0.0.1:8000";

async function workspaceFetch<T>(path: string, token: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!response.ok) {
    let detail: string | undefined;
    try {
      const body = await response.json() as { detail?: string; message?: string };
      detail = body.detail || body.message || "";
    } catch {
      // Use the status-based message below when the response is not JSON.
    }
    throw new Error(detail || `Workspace data request failed (${response.status}).`);
  }
  return response.json() as Promise<T>;
}

export type CustomerRecord = {
  customer_id: string;
  name?: string;
  full_name?: string;
  plan?: string;
  created_at?: string;
};

export type WorkspaceData = {
  customer_id: string;
  orders: Array<Record<string, unknown>>;
  invoices: Array<Record<string, unknown>>;
  payments: Array<Record<string, unknown>>;
  tickets: Array<Record<string, unknown>>;
};

export function fetchCustomers(token: string) {
  return workspaceFetch<{ customers: CustomerRecord[] }>("/workspace/customers", token);
}

export async function fetchCustomerData(token: string): Promise<WorkspaceData> {
  const data = await workspaceFetch<Partial<WorkspaceData>>("/workspace/customer-data", token);
  return {
    customer_id: typeof data.customer_id === "string" ? data.customer_id : "",
    orders: Array.isArray(data.orders) ? data.orders : [],
    invoices: Array.isArray(data.invoices) ? data.invoices : [],
    payments: Array.isArray(data.payments) ? data.payments : [],
    tickets: Array.isArray(data.tickets) ? data.tickets : [],
  };
}
