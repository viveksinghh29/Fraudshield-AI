import { useState, useRef, useEffect } from "react";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Bot, User, SendHorizontal } from "lucide-react";
import { cn } from "./ui/utils";

export interface ChatMessage {
  id: string;
  role: "assistant" | "user";
  content: string;
}

interface ExplanationChatProps {
  initialAssistantMessage: string;
  contextHint?: string;
  className?: string;
}

export function ExplanationChat({
  initialAssistantMessage,
  contextHint,
  className,
}: ExplanationChatProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "0",
      role: "assistant",
      content: initialAssistantMessage,
    },
  ]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  const reply = (userText: string) => {
    const lower = userText.toLowerCase();
    if (lower.includes("why") || lower.includes("flag")) {
      return contextHint
        ? `In short: ${contextHint} If you need policy language for your case file, I can draft a one-paragraph summary for compliance.`
        : "The model weighed amount, geography, merchant category, and velocity against this customer’s baseline. The largest lift came from features that diverged sharply from recent history.";
    }
    if (lower.includes("false") || lower.includes("legit")) {
      return "If you believe this is a false positive, compare against recent legitimate merchants in the same MCC and check device or 3DS signals. I can list similar approved transactions on request.";
    }
    return "I can elaborate on any feature bar in the SHAP chart, compare to cohort baselines, or suggest next investigative steps. What would you like to dig into?";
  };

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || isTyping) return;

    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: trimmed,
    };
    setMessages((m) => [...m, userMsg]);
    setInput("");
    setIsTyping(true);

    setTimeout(() => {
      setMessages((m) => [
        ...m,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: reply(trimmed),
        },
      ]);
      setIsTyping(false);
    }, 600);
  };

  return (
    <div
      className={cn(
        "flex flex-col rounded-xl border border-border bg-card overflow-hidden min-h-[280px] max-h-[420px]",
        className,
      )}
    >
      <div className="px-4 py-2 border-b border-border bg-muted/30">
        <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
          Why this transaction is flagged
        </p>
        <p className="text-sm text-foreground">GenAI assistant</p>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={cn(
              "flex gap-2",
              msg.role === "user" ? "justify-end" : "justify-start",
            )}
          >
            {msg.role === "assistant" && (
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-violet-500 to-indigo-600 flex items-center justify-center shrink-0">
                <Bot className="w-4 h-4 text-white" />
              </div>
            )}
            <div
              className={cn(
                "max-w-[85%] rounded-2xl px-3 py-2 text-sm leading-relaxed shadow-sm",
                msg.role === "assistant"
                  ? "bg-muted/80 text-foreground rounded-tl-sm border border-border/60"
                  : "bg-primary text-primary-foreground rounded-tr-sm",
              )}
            >
              {msg.role === "user" && (
                <User className="w-3.5 h-3.5 inline mr-1.5 opacity-80 align-middle" />
              )}
              {msg.content}
            </div>
          </div>
        ))}
        {isTyping && (
          <div className="flex gap-2 items-center text-muted-foreground text-xs pl-10">
            <span className="inline-flex gap-1">
              <span className="animate-bounce">·</span>
              <span className="animate-bounce [animation-delay:120ms]">·</span>
              <span className="animate-bounce [animation-delay:240ms]">·</span>
            </span>
            Assistant is typing…
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <form
        onSubmit={handleSend}
        className="p-3 border-t border-border bg-muted/20 flex gap-2"
      >
        <Input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a follow-up…"
          className="text-sm bg-background"
          aria-label="Message to assistant"
        />
        <Button type="submit" size="icon" disabled={isTyping || !input.trim()}>
          <SendHorizontal className="w-4 h-4" />
        </Button>
      </form>
    </div>
  );
}
