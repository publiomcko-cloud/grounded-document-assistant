import { ChatWorkspace } from "@/components/chat-workspace";

export default function ChatPage() {
  return (
    <main className="mx-auto flex min-h-screen w-full max-w-7xl flex-col px-6 py-10 sm:px-10 lg:px-12">
      <ChatWorkspace />
    </main>
  );
}
