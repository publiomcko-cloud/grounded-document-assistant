import { ProtectedAppShell } from "@/components/protected-app-shell";

export default function AppPage() {
  return (
    <main className="mx-auto flex min-h-screen w-full max-w-6xl flex-col px-6 py-10 sm:px-10 lg:px-12">
      <ProtectedAppShell />
    </main>
  );
}
