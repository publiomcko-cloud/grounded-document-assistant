import { EvaluationWorkspace } from "@/components/evaluation-workspace";

export default function EvaluationsPage() {
  return (
    <main className="mx-auto flex min-h-screen w-full max-w-7xl flex-col px-6 py-10 sm:px-10 lg:px-12">
      <EvaluationWorkspace />
    </main>
  );
}
