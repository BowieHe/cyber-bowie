import { FormEvent, KeyboardEvent, useEffect, useRef, useState } from "react";

interface SkillMetadata {
  name: string;
  description: string;
}

interface SkillsResponse {
  skills: SkillMetadata[];
  soul: string;
}

interface ChatResponse {
  reply: string;
  skills: string[];
}

interface Message {
  id: string;
  role: "user" | "assistant";
  name: string;
  content: string;
}

const initialMessage: Message = {
  id: "welcome",
  role: "assistant",
  name: "Bowie",
  content:
    "现在这页已经接上你的本地 agent 了。你可以直接输入需求，我会用中文回你；如果内容适合，superpower 也会一起帮你把问题整理得更像一个能真的推进的项目。"
};

export function App() {
  const [messages, setMessages] = useState<Message[]>([initialMessage]);
  const [skills, setSkills] = useState<SkillMetadata[]>([]);
  const [soulPreview, setSoulPreview] = useState("载入中...");
  const [draft, setDraft] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);
  const messageEndRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    void loadMeta();
  }, []);

  useEffect(() => {
    autoResize();
    messageEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [draft, messages]);

  async function loadMeta(): Promise<void> {
    const response = await fetch("/api/skills");
    const data = (await response.json()) as SkillsResponse;
    setSkills(data.skills);

    const soulLines = data.soul
      .split("\n")
      .filter((line) => line.trim().length > 0 && !line.startsWith("#"))
      .slice(0, 5);

    setSoulPreview(soulLines.join(" / "));
  }

  function autoResize(): void {
    const textarea = textareaRef.current;

    if (!textarea) {
      return;
    }

    textarea.style.height = "0px";
    textarea.style.height = `${Math.min(textarea.scrollHeight, 220)}px`;
  }

  async function submitMessage(message: string): Promise<void> {
    setMessages((current) => [
      ...current,
      {
        id: `user-${Date.now()}`,
        role: "user",
        name: "你",
        content: message
      }
    ]);

    setIsLoading(true);

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ message })
      });

      const data = (await response.json()) as ChatResponse | { error?: string };

      if (!response.ok || !("reply" in data)) {
        throw new Error("error" in data && data.error ? data.error : "请求失败");
      }

      setMessages((current) => [
        ...current,
        {
          id: `assistant-${Date.now()}`,
          role: "assistant",
          name: "Bowie",
          content: data.reply
        }
      ]);
    } catch (error: unknown) {
      setMessages((current) => [
        ...current,
        {
          id: `error-${Date.now()}`,
          role: "assistant",
          name: "系统",
          content: `出了点问题：${error instanceof Error ? error.message : String(error)}`
        }
      ]);
    } finally {
      setDraft("");
      setIsLoading(false);
      textareaRef.current?.focus();
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    const message = draft.trim();

    if (!message || isLoading) {
      return;
    }

    await submitMessage(message);
  }

  async function handleKeyDown(
    event: KeyboardEvent<HTMLTextAreaElement>
  ): Promise<void> {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      const message = draft.trim();

      if (!message || isLoading) {
        return;
      }

      await submitMessage(message);
    }
  }

  function resetChat(): void {
    setMessages([initialMessage]);
    setDraft("");
    textareaRef.current?.focus();
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="brand-mark">CB</div>
          <div>
            <p className="eyebrow">Local Agent</p>
            <h1>Cyber Bowie</h1>
          </div>
        </div>

        <button className="new-chat-button" onClick={resetChat} type="button">
          开启新对话
        </button>

        <section className="sidebar-panel">
          <p className="panel-label">已启用技能</p>
          <div className="tag-list">
            {skills.map((skill) => (
              <span className="tag" key={skill.name}>
                {skill.name}
              </span>
            ))}
          </div>
        </section>

        <section className="sidebar-panel">
          <p className="panel-label">人格摘要</p>
          <p className="soul-preview">{soulPreview}</p>
        </section>
      </aside>

      <main className="chat-stage">
        <header className="stage-header">
          <div>
            <p className="eyebrow">Chat View</p>
            <h2>像 ChatGPT 一样聊天，但人格是你自己的</h2>
          </div>
          <div className="status-pill">
            <span className="status-dot"></span>
            本地运行
          </div>
        </header>

        <section className="messages">
          {messages.map((message) => (
            <article
              className={`message ${message.role === "user" ? "message-user" : "message-assistant"} ${
                message.id === "welcome" ? "hero-message" : ""
              }`}
              key={message.id}
            >
              <div className="avatar">{message.role === "user" ? "你" : "B"}</div>
              <div className="bubble">
                <p className="message-role">{message.name}</p>
                <div className="message-content">{message.content}</div>
              </div>
            </article>
          ))}
          <div ref={messageEndRef}></div>
        </section>

        <form className={`composer ${isLoading ? "is-loading" : ""}`} onSubmit={handleSubmit}>
          <label className="composer-shell" htmlFor="prompt-input">
            <textarea
              id="prompt-input"
              name="message"
              placeholder="输入你现在想做的事，例如：帮我把这个 agent 变成一个真正可接模型的产品"
              ref={textareaRef}
              rows={1}
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              onKeyDown={(event) => {
                void handleKeyDown(event);
              }}
              disabled={isLoading}
            />
            <button className="send-button" disabled={isLoading} type="submit">
              {isLoading ? "思考中..." : "送出"}
            </button>
          </label>
          <p className="composer-tip">Enter 送出，Shift + Enter 换行</p>
        </form>
      </main>
    </div>
  );
}
