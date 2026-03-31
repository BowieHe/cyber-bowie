import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { dirname, extname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { MockProvider } from "@cyber-bowie/pi-ai";
import {
  AgentSession,
  createDefaultSystemPrompt,
  loadSoulFile
} from "@cyber-bowie/pi-agent-core";
import { superpowerSkill } from "@cyber-bowie/pi-skills-superpower";

const port = Number(process.env.PORT ?? 3000);
const host = process.env.HOST ?? "127.0.0.1";
const currentFile = fileURLToPath(import.meta.url);
const packageRoot = join(dirname(currentFile), "..");
const publicDir = join(packageRoot, "web", "dist");

interface ChatRequestBody {
  message?: string;
}

function createAgentSession(): AgentSession {
  const session = new AgentSession(
    new MockProvider("pi-web-chat-mock"),
    createDefaultSystemPrompt()
  );

  session.registerSkill(superpowerSkill);
  return session;
}

async function buildAgentReply(message: string): Promise<{
  reply: string;
  skills: string[];
}> {
  const session = createAgentSession();
  const soulPath = join(process.cwd(), "SOUL.md");
  session.setSoul(await loadSoulFile(soulPath));

  const result = await session.run({
    goal: message,
    constraints: [
      "所有输出都使用中文",
      "优先给出小而可用的方案",
      "保持语气自然，像真实的人在解释"
    ],
    context: [
      "这是一个本地 web agent 界面",
      "需要保留 SOUL 定义的人格",
      "如果 superpower 有帮助，可以把它纳入回答"
    ]
  });

  const skillBlock =
    result.skillResults.length > 0
      ? [
          "",
          "这次用到的能力：",
          ...result.skillResults.map((skill) => `- ${skill.skillName}: ${skill.summary}`)
        ].join("\n")
      : "";

  return {
    reply: `${result.raw}${skillBlock}`,
    skills: result.skillResults.map((skill) => skill.skillName)
  };
}

function jsonResponse(data: unknown, statusCode = 200): ResponseSpec {
  return {
    statusCode,
    headers: {
      "Content-Type": "application/json; charset=utf-8"
    },
    body: JSON.stringify(data)
  };
}

interface ResponseSpec {
  statusCode: number;
  headers: Record<string, string>;
  body: string | Buffer;
}

async function serveStatic(pathname: string): Promise<ResponseSpec> {
  const normalizedPath = pathname === "/" ? "/index.html" : pathname;
  const filePath = join(publicDir, normalizedPath);
  const file = await readFile(filePath);
  const extension = extname(filePath);

  const mimeTypeMap: Record<string, string> = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8"
  };

  return {
    statusCode: 200,
    headers: {
      "Content-Type": mimeTypeMap[extension] ?? "application/octet-stream"
    },
    body: file
  };
}

createServer(async (request, response) => {
  try {
    const url = new URL(request.url ?? "/", `http://${request.headers.host}`);

    if (request.method === "GET" && url.pathname === "/api/skills") {
      const skills = createAgentSession().listSkills();
      const soul = await loadSoulFile(join(process.cwd(), "SOUL.md"));
      const payload = jsonResponse({
        skills,
        soul
      });

      response.writeHead(payload.statusCode, payload.headers);
      response.end(payload.body);
      return;
    }

    if (request.method === "POST" && url.pathname === "/api/chat") {
      const chunks: Buffer[] = [];

      for await (const chunk of request) {
        chunks.push(Buffer.from(chunk));
      }

      const rawBody = Buffer.concat(chunks).toString("utf8");
      const body = JSON.parse(rawBody) as ChatRequestBody;
      const message = body.message?.trim();

      if (!message) {
        const payload = jsonResponse(
          {
            error: "message 不能为空"
          },
          400
        );

        response.writeHead(payload.statusCode, payload.headers);
        response.end(payload.body);
        return;
      }

      const chatResult = await buildAgentReply(message);
      const payload = jsonResponse(chatResult);

      response.writeHead(payload.statusCode, payload.headers);
      response.end(payload.body);
      return;
    }

    if (request.method === "GET") {
      const payload = await serveStatic(url.pathname);
      response.writeHead(payload.statusCode, payload.headers);
      response.end(payload.body);
      return;
    }

    const payload = jsonResponse(
      {
        error: "不支持的请求"
      },
      404
    );

    response.writeHead(payload.statusCode, payload.headers);
    response.end(payload.body);
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : String(error);
    const payload = jsonResponse(
      {
        error: message
      },
      500
    );

    response.writeHead(payload.statusCode, payload.headers);
    response.end(payload.body);
  }
}).listen(port, host, () => {
  process.stdout.write(`pi-web-chat running at http://${host}:${port}\n`);
});
