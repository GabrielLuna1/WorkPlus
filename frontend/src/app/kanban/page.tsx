import { Metadata } from "next";
import KanbanBoard from "@/components/kanban/KanbanBoard";

export const metadata: Metadata = {
  title: "Kanban | WorkHunter",
  description: "Gerencie suas candidaturas em um Pipeline visual",
};

export default function KanbanPage() {
  return (
    <div className="h-full bg-canvas flex flex-col">
      <KanbanBoard />
    </div>
  );
}
