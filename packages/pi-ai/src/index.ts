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

export interface AiProvider {
  readonly name: string;
  complete(request: CompletionRequest): Promise<CompletionResponse>;
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
