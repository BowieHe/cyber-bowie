export interface CompletionMessage {
  role: "system" | "user" | "assistant";
  content: string;
}

export interface CompletionRequest {
  messages: CompletionMessage[];
  temperature?: number;
  maxTokens?: number;
}

export interface CompletionResponse {
  text: string;
  model: string;
}

export interface CompletionChunk {
  textDelta: string;
  model?: string;
}

export interface AiProvider {
  readonly name: string;
  complete(request: CompletionRequest): Promise<CompletionResponse>;
  streamComplete?(
    request: CompletionRequest
  ): AsyncIterable<CompletionChunk>;
}

export interface OpenAiProviderOptions {
  apiKey: string;
  model: string;
  baseUrl?: string;
  temperature?: number;
}

export class MockProvider implements AiProvider {
  public readonly name: string;

  public constructor(name = "mock-provider") {
    this.name = name;
  }

  public async complete(request: CompletionRequest): Promise<CompletionResponse> {
    const latestUserMessage = [...request.messages]
      .reverse()
      .find((message) => message.role === "user");

    const prompt = latestUserMessage?.content ?? "No user prompt supplied.";
    const text = [
      "Plan:",
      "1. Understand the request.",
      "2. Break the work into small safe steps.",
      "3. Return a practical first implementation.",
      "",
      `Task: ${prompt}`
    ].join("\n");

    return {
      text,
      model: this.name
    };
  }
}

export class OpenAiProvider implements AiProvider {
  public readonly name: string;
  private readonly apiKey: string;
  private readonly baseUrl: string;
  private readonly temperature?: number;

  public constructor(options: OpenAiProviderOptions) {
    this.name = options.model;
    this.apiKey = options.apiKey;
    this.baseUrl = (options.baseUrl ?? "https://api.openai.com/v1").replace(/\/$/, "");
    this.temperature = options.temperature;
  }

  private maskApiKey(): string {
    if (this.apiKey.length <= 8) {
      return `${this.apiKey.slice(0, 2)}***`;
    }

    return `${this.apiKey.slice(0, 6)}...${this.apiKey.slice(-4)}`;
  }

  private buildDiagnostics(): string {
    return [
      `url=${this.baseUrl}/chat/completions`,
      `model=${this.name}`,
      `apiKey=${this.maskApiKey()}`
    ].join(" ");
  }

  public async complete(request: CompletionRequest): Promise<CompletionResponse> {
    let response: Response;

    try {
      response = await fetch(`${this.baseUrl}/chat/completions`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${this.apiKey}`
        },
        body: JSON.stringify({
          model: this.name,
          messages: request.messages,
          temperature: request.temperature ?? this.temperature ?? 0.4,
          max_tokens: request.maxTokens
        })
      });
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : String(error);
      throw new Error(
        `无法连接 OpenAI 接口，请检查网络、OPENAI_BASE_URL 或 API Key。${this.buildDiagnostics()} 原始错误: ${message}`
      );
    }

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(
        `OpenAI 请求失败: ${response.status} ${errorText} ${this.buildDiagnostics()}`
      );
    }

    const data = (await response.json()) as {
      choices?: Array<{
        message?: {
          content?: string | Array<{ type?: string; text?: string }>;
        };
      }>;
      model?: string;
    };

    const content = data.choices?.[0]?.message?.content;
    const text =
      typeof content === "string"
        ? content
        : Array.isArray(content)
          ? content
              .map((part) => ("text" in part && typeof part.text === "string" ? part.text : ""))
              .join("")
          : "";

    if (!text) {
      throw new Error(`OpenAI 返回了空内容 ${this.buildDiagnostics()}`);
    }

    return {
      text,
      model: data.model ?? this.name
    };
  }

  public async *streamComplete(
    request: CompletionRequest
  ): AsyncIterable<CompletionChunk> {
    let response: Response;

    try {
      response = await fetch(`${this.baseUrl}/chat/completions`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${this.apiKey}`
        },
        body: JSON.stringify({
          model: this.name,
          messages: request.messages,
          temperature: request.temperature ?? this.temperature ?? 0.4,
          max_tokens: request.maxTokens,
          stream: true,
          stream_options: {
            include_usage: false
          }
        })
      });
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : String(error);
      throw new Error(
        `无法连接 OpenAI 接口，请检查网络、OPENAI_BASE_URL 或 API Key。${this.buildDiagnostics()} 原始错误: ${message}`
      );
    }

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(
        `OpenAI 请求失败: ${response.status} ${errorText} ${this.buildDiagnostics()}`
      );
    }

    if (!response.body) {
      throw new Error(`OpenAI 流式响应为空 ${this.buildDiagnostics()}`);
    }

    const decoder = new TextDecoder();
    let buffer = "";

    for await (const chunk of response.body) {
      buffer += decoder.decode(chunk, { stream: true });
      const events = buffer.split("\n\n");
      buffer = events.pop() ?? "";

      for (const event of events) {
        const dataLines = event
          .split("\n")
          .filter((line) => line.startsWith("data:"))
          .map((line) => line.slice(5).trim());

        for (const dataLine of dataLines) {
          if (!dataLine || dataLine === "[DONE]") {
            continue;
          }

          let parsed: {
            model?: string;
            choices?: Array<{
              delta?: {
                content?: string;
              };
            }>;
          };

          try {
            parsed = JSON.parse(dataLine);
          } catch {
            continue;
          }

          const textDelta = parsed.choices?.[0]?.delta?.content ?? "";

          if (!textDelta) {
            continue;
          }

          yield {
            textDelta,
            model: parsed.model ?? this.name
          };
        }
      }
    }
  }
}
