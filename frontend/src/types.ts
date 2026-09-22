export type ActivityItem = {
  id: number;
  label: string;
  type: "tool" | "agent" | "success" | "approval";
  status: "running" | "completed" | "waiting";
};
