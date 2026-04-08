import test from "node:test";
import assert from "node:assert/strict";
import { mkdtemp, mkdir, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import type { AiProvider, CompletionRequest, CompletionResponse } from "@cyber-persona/pi-ai";
import { ChatService, loadSoulTextForPersona } from "./chat-service.js";

class RecordingProvider implements AiProvider {
  public readonly name: string;

  public constructor(private readonly id: number) {
    this.name = `provider-${id}`;
  }

  public async complete(request: CompletionRequest): Promise<CompletionResponse> {
    return {
      text: `provider=${this.id};messages=${request.messages.length}`,
      model: this.name
    };
  }
}

async function createFixture(): Promise<string> {
  const cwd = await mkdtemp(join(tmpdir(), "cyber-bowie-test-"));
  await mkdir(join(cwd, "souls"));
  await writeFile(join(cwd, "SOUL.md"), "# SOUL\n\nName: 呱吉\n");
  await writeFile(join(cwd, "souls", "critic.md"), "# SOUL\n\nName: 挑刺版呱吉\n");
  await writeFile(join(cwd, "souls", "researcher.md"), "# SOUL\n\nName: 研究版呱吉\n");
  await writeFile(
    join(cwd, "personas.json"),
    JSON.stringify(
      {
        personas: [
          {
            id: "bowie",
            displayName: "呱吉",
            skills: ["orchestrate", "default_chat"],
            specialties: ["产品方向", "项目拆分"]
          },
          {
            id: "critic",
            displayName: "挑刺版呱吉",
            skills: ["risk_analysis", "logic_check"],
            specialties: ["风险识别"]
          },
          {
            id: "researcher",
            displayName: "研究版呱吉",
            skills: ["search", "deep_research"],
            specialties: ["资料整理"]
          }
        ]
      },
      null,
      2
    )
  );
  return cwd;
}

test("loadSoulTextForPersona 优先读取 souls/<persona>.md", async () => {
  const cwd = await createFixture();
  const soul = await loadSoulTextForPersona(cwd, "critic");

  assert.match(soul, /挑刺版呱吉/);
});

test("loadSoulTextForPersona 找不到 persona 时回退到根 SOUL.md", async () => {
  const cwd = await createFixture();
  const soul = await loadSoulTextForPersona(cwd, "missing");

  assert.match(soul, /呱吉/);
});

test("ChatService 会按 personaId + sessionId 复用会话", async () => {
  const cwd = await createFixture();
  let providerCount = 0;
  const service = new ChatService({
    cwd,
    providerFactory: () => new RecordingProvider(++providerCount)
  });

  const first = await service.buildReply("你好", {
    personaId: "bowie",
    sessionId: "session-1"
  });
  const second = await service.buildReply("继续", {
    personaId: "bowie",
    sessionId: "session-1"
  });
  const third = await service.buildReply("换个人格", {
    personaId: "critic",
    sessionId: "session-1"
  });

  assert.match(first.reply, /provider=1;messages=2/);
  assert.match(second.reply, /provider=1;messages=4/);
  assert.match(third.reply, /provider=2;messages=2/);
});

test("ChatService 会列出根 persona 和 souls 目录里的 persona", async () => {
  const cwd = await createFixture();
  const service = new ChatService({
    cwd,
    providerFactory: () => new RecordingProvider(1)
  });

  const personas = await service.listPersonas();

  assert.deepEqual(
    personas.map((persona) => persona.id).sort(),
    ["bowie", "critic", "researcher"]
  );
  assert.equal(personas.find((persona) => persona.id === "critic")?.displayName, "挑刺版呱吉");
  assert.deepEqual(personas.find((persona) => persona.id === "bowie")?.specialties, [
    "产品方向",
    "项目拆分"
  ]);
  assert.deepEqual(personas.find((persona) => persona.id === "bowie")?.skills, [
    "orchestrate",
    "default_chat"
  ]);
});

test("ChatService 会使用 Orchestrator 模式生成多条消息", async () => {
  const cwd = await createFixture();
  const service = new ChatService({
    cwd,
    providerFactory: () => ({
      name: "orchestrator-provider",
      async complete(request) {
        const prompt = request.messages[request.messages.length - 1]?.content ?? "";
        
        // 模拟 Orchestrator 返回执行计划
        if (prompt.includes("调度中心") || prompt.includes("你是调度中心")) {
          return {
            text: JSON.stringify({
              reasoning: "需要搜索和分析",
              steps: [
                { type: "announce", text: "我安排研究型和挑刺型一起看看" },
                { type: "persona", personaId: "researcher", dependsOn: [] },
                { type: "persona", personaId: "critic", dependsOn: [] }
              ]
            }),
            model: "orchestrator-provider"
          };
        }
        
        // 其他 persona 的回复
        return {
          text: `回复：${prompt.substring(0, 30)}...`,
          model: "orchestrator-provider"
        };
      }
    })
  });

  const messages: string[] = [];
  for await (const item of service.orchestrateReply("帮我分析这个项目", {
    personaId: "bowie",
    sessionId: "test-session"
  })) {
    if (item.type === "announce") {
      messages.push(`[Orchestrator] ${item.text}`);
    } else {
      messages.push(`[${item.displayName}] ${item.text}`);
    }
  }

  assert.ok(messages.length >= 3, "应该生成多条消息");
  assert.ok(messages.some(m => m.includes("研究型")), "应该包含研究型回复");
  assert.ok(messages.some(m => m.includes("挑刺型")), "应该包含挑刺型回复");
});
