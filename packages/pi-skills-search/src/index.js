import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamableHttp.js";
const METADATA = {
    name: "portable-deep-search",
    description: "从 finpal 深度搜索流程抽出的可插拔搜索 skill。",
    triggers: ["搜索", "研究", "查资料", "深度搜索", "分析资产"],
    version: "0.1.0",
    requiredTools: ["search"]
};
const DEFAULT_MAX_QUERIES = 6;
const CONFIDENCE_THRESHOLD = 0.8;
function log(runtime, level, message, meta) {
    runtime.log?.(level, message, meta);
}
function normalizeQuery(query) {
    return query.replace(/\s+/g, " ").trim().toLowerCase();
}
function isNearDuplicateQuery(query, searchedQueries) {
    const normalized = normalizeQuery(query);
    return searchedQueries.some((previous) => {
        const normalizedPrevious = normalizeQuery(previous);
        return (normalizedPrevious === normalized ||
            normalizedPrevious.includes(normalized) ||
            normalized.includes(normalizedPrevious));
    });
}
function inferSentiment(text) {
    if (/上涨|增长|看好|利好|强劲|新高/.test(text)) {
        return "positive";
    }
    if (/风险|下跌|回撤|承压|波动|担忧|利空/.test(text)) {
        return "negative";
    }
    return "neutral";
}
function createProposal(entity, focus) {
    const isFund = /\d{6}/.test(entity);
    const subQuestions = [
        isFund ? "基金基础信息是否完整" : "资产当前价格与趋势如何",
        "近期市场新闻和催化因素有哪些",
        "主要风险信号是什么"
    ];
    if (!focus || focus.includes("financial")) {
        subQuestions.push(isFund ? "最新财报和净值表现如何" : "收益表现和宏观驱动如何");
    }
    if (isFund && (!focus || focus.includes("manager"))) {
        subQuestions.push("基金经理与管理人背景如何");
    }
    return {
        mainQuestion: `围绕 ${entity} 构建研究底稿`,
        subQuestions,
        priorityOrder: [...subQuestions]
    };
}
function createBoard(entity, focus, previousGaps) {
    return {
        proposal: createProposal(entity, focus),
        knownFacts: [],
        informationGaps: previousGaps?.length
            ? [...previousGaps]
            : ["最新新闻动态", "风险信号", "基础信息完整性"],
        hypotheses: [],
        searchedQueries: [],
        failedPaths: [],
        coveredGaps: []
    };
}
function createSearchPlan(entity, queries, gaps) {
    const effectiveGaps = gaps?.length ? gaps : ["基础信息完整性", "最新新闻动态", "风险信号"];
    return {
        mainGoal: `围绕 ${entity} 建立足够可靠的研究底稿，并把置信度提高到 80% 以上`,
        steps: effectiveGaps.map((gap, index) => ({
            label: `处理缺口: ${gap}`,
            targetGap: gap,
            queryPatterns: queries.slice(index, index + 2)
        }))
    };
}
function generateQueries(input) {
    const queries = [];
    const { entity, focus, previousGaps, isRetry } = input;
    const isFund = /\d{6}/.test(entity);
    const isAsset = /黄金|白银|原油|比特币|美股|港股|A股/i.test(entity);
    if (isRetry && previousGaps?.length) {
        if (previousGaps.some((gap) => gap.includes("财报") || gap.includes("业绩"))) {
            queries.push(isFund ? `${entity} 基金 财报 业绩 净值` : `${entity} 价格走势 历史数据`);
        }
        if (previousGaps.some((gap) => gap.includes("新闻") || gap.includes("动态"))) {
            queries.push(`${entity} 最新 新闻 动态`);
            queries.push(`${entity} 市场消息 分析`);
        }
        if (previousGaps.some((gap) => gap.includes("风险") || gap.includes("回撤"))) {
            queries.push(`${entity} 风险 下跌 回撤 波动`);
        }
        if (previousGaps.some((gap) => gap.includes("经理") || gap.includes("管理"))) {
            queries.push(`${entity} 基金经理 履历 业绩`);
        }
    }
    if (!isRetry || queries.length === 0) {
        queries.push(isFund ? `${entity} 基金 最新` : `${entity} 最新 价格 走势`);
        if (!focus || focus.includes("financial")) {
            queries.push(isFund ? `${entity} 基金 财报 业绩` : `${entity} 投资分析 收益`);
        }
        if (!focus || focus.includes("news")) {
            queries.push(`${entity} 新闻 最新动态`);
        }
        if (!focus || focus.includes("risk")) {
            queries.push(`${entity} 风险`);
        }
        if ((!focus || focus.includes("manager")) && isFund) {
            queries.push(`${entity} 基金 基金经理`);
        }
    }
    if (isAsset && (!focus || focus.includes("macro"))) {
        queries.push(`${entity} 宏观经济 政策影响`);
    }
    return [...new Set(queries)];
}
function detectGaps(data) {
    const gaps = [];
    if (data.news.length === 0) {
        gaps.push("缺少最新新闻动态");
    }
    else if (data.news.length < 3) {
        gaps.push("新闻数量较少");
    }
    if (data.risks.length === 0) {
        gaps.push("未识别风险因素");
    }
    if (!data.entityInfo.summary) {
        gaps.push("缺少基础摘要");
    }
    if (!data.entityInfo.type) {
        gaps.push("缺少资产类型信息");
    }
    return gaps;
}
function calculateConfidence(data) {
    let score = 0;
    if (data.entityInfo.name)
        score += 0.2;
    if (data.entityInfo.type)
        score += 0.1;
    if (data.entityInfo.summary)
        score += 0.15;
    if (data.plan.steps.length >= 3)
        score += 0.05;
    if (data.news.length >= 5)
        score += 0.25;
    else if (data.news.length >= 3)
        score += 0.18;
    else if (data.news.length > 0)
        score += 0.1;
    if (data.risks.length >= 3)
        score += 0.15;
    else if (data.risks.length > 0)
        score += 0.08;
    if (data.sources.length >= 5)
        score += 0.15;
    else if (data.sources.length >= 3)
        score += 0.08;
    if (data.researchBoard.coveredGaps.length >= 3)
        score += 0.1;
    else if (data.researchBoard.coveredGaps.length > 0)
        score += 0.05;
    return Math.min(score, 1);
}
function evaluateResults(results) {
    const accepted = [];
    const seenTitles = new Set();
    const seenUrls = new Set();
    let rejectedCount = 0;
    for (const item of results) {
        const title = normalizeQuery(item.title);
        const url = item.url ?? "";
        const snippet = item.snippet ?? "";
        if (!title || snippet.length < 20) {
            rejectedCount += 1;
            continue;
        }
        if (seenTitles.has(title) || (url && seenUrls.has(url))) {
            rejectedCount += 1;
            continue;
        }
        if (/广告|推广|下载app|开户链接/i.test(`${item.title} ${snippet}`)) {
            rejectedCount += 1;
            continue;
        }
        accepted.push(item);
        seenTitles.add(title);
        if (url) {
            seenUrls.add(url);
        }
    }
    return {
        accepted,
        rejectedCount
    };
}
function mergeKnownFacts(board, results) {
    for (const item of results.slice(0, 3)) {
        const source = item.url || item.source || "";
        if (!source) {
            continue;
        }
        if (board.knownFacts.some((fact) => fact.claim === item.title && fact.source === source)) {
            continue;
        }
        board.knownFacts.push({
            claim: item.title,
            source,
            confidence: item.snippet && item.snippet.length > 80 ? 0.8 : 0.65
        });
    }
}
function deriveHypotheses(entity, queries, gaps, isRetry) {
    const effectiveGaps = gaps?.length ? gaps : ["基础面", "新闻动态", "风险信号"];
    return effectiveGaps.map((gap, index) => ({
        gap,
        rationale: isRetry
            ? `上一轮仍存在“${gap}”缺口，因此缩小搜索范围并更换关键词路径`
            : `先验证“${gap}”是否能通过公开网页信息补齐`,
        targetSources: gap.includes("财报")
            ? ["基金公告", "公司财报", "交易所披露"]
            : gap.includes("经理")
                ? ["基金公司官网", "公开简历", "第三方资料页"]
                : ["新闻站点", "研究文章", "行情页"],
        queryPatterns: queries.slice(index, index + 2)
    }));
}
function updateCoveredGaps(board, query, results) {
    const joined = results.map((item) => `${item.title} ${item.snippet ?? ""}`).join("\n");
    const signals = [
        { gap: "缺少最新新闻动态", test: /新闻|快讯|动态|消息|走势|价格|行情/i },
        { gap: "未识别风险因素", test: /风险|回撤|波动|下跌|警示/i },
        { gap: "缺少基础摘要", test: /基金|资产|公司|行业|配置|概况/i }
    ];
    for (const signal of signals) {
        if (!signal.test.test(joined)) {
            continue;
        }
        const existing = board.coveredGaps.find((entry) => entry.gap === signal.gap);
        const evidence = results.slice(0, 2).map((item) => item.title);
        if (existing) {
            existing.evidence = [...new Set([...existing.evidence, ...evidence])].slice(0, 4);
            existing.confidence = Math.max(existing.confidence, 0.7);
            continue;
        }
        board.coveredGaps.push({
            gap: signal.gap,
            query,
            evidence,
            confidence: 0.7
        });
    }
}
function criticReview(query, results, board) {
    const coveredGaps = board.coveredGaps
        .filter((entry) => entry.query === query)
        .map((entry) => entry.gap);
    const rejectedCount = Math.max(0, 10 - results.length);
    const informationDelta = Math.min(1, results.length / 5 + coveredGaps.length * 0.15);
    const accepted = results.length > 0;
    return {
        query,
        accepted,
        informationDelta,
        reason: accepted
            ? `保留 ${results.length} 条高价值结果，覆盖 ${coveredGaps.length} 个缺口`
            : `查询“${query}”没有带来有效信息增量`,
        keptCount: results.length,
        rejectedCount,
        coveredGaps
    };
}
function shouldStopSearching(data) {
    if (data.confidence >= CONFIDENCE_THRESHOLD) {
        return `当前置信度 ${(data.confidence * 100).toFixed(0)}% 已达到目标阈值`;
    }
    if (data.gaps.length === 0) {
        return "核心信息缺口已补齐";
    }
    const lowValueIterations = data.iterations.filter((iteration) => !iteration.accepted || iteration.informationDelta < 0.3).length;
    if (lowValueIterations >= 3 && data.iterations.length >= 4) {
        return "连续多轮搜索信息增量过低，继续搜索的收益已经不高";
    }
    if (data.searchQueries.length >= DEFAULT_MAX_QUERIES && data.confidence >= 0.65) {
        return "已达到搜索预算上限，且当前信息已具备基本分析价值";
    }
    return null;
}
function pickType(entity, summary) {
    const combined = `${entity} ${summary ?? ""}`;
    if (/基金|ETF|LOF|FOF/i.test(combined)) {
        return "基金";
    }
    if (/黄金|白银|原油|比特币|BTC|ETH/i.test(combined)) {
        return "资产";
    }
    if (/指数|index|沪深|上证|纳斯达克|标普/i.test(combined)) {
        return "指数";
    }
    return undefined;
}
export async function runPortableDeepSearch(input, runtime) {
    const searchQueries = generateQueries(input).slice(0, input.maxQueries ?? DEFAULT_MAX_QUERIES);
    const board = createBoard(input.entity, input.focus, input.previousGaps);
    board.hypotheses = deriveHypotheses(input.entity, searchQueries, input.previousGaps, !!input.isRetry);
    const plan = createSearchPlan(input.entity, searchQueries, input.previousGaps);
    const acceptedResults = [];
    const sources = new Set();
    const news = new Map();
    const risks = new Set();
    const iterations = [];
    let data = {
        entityInfo: {
            name: input.entity
        },
        news: [],
        risks: [],
        sources: [],
        searchQueries: [],
        acceptedResults: [],
        plan,
        iterations,
        confidence: 0,
        gaps: [],
        researchBoard: board
    };
    for (const query of searchQueries) {
        if (isNearDuplicateQuery(query, board.searchedQueries)) {
            continue;
        }
        board.searchedQueries.push(query);
        log(runtime, "info", "search.query", { query });
        const rawResults = await runtime.search(query);
        const reviewResult = evaluateResults(rawResults);
        const accepted = reviewResult.accepted;
        if (accepted.length === 0) {
            board.failedPaths.push({
                query,
                reason: "no_useful_results"
            });
            continue;
        }
        mergeKnownFacts(board, accepted);
        updateCoveredGaps(board, query, accepted);
        const iteration = criticReview(query, accepted, board);
        iteration.rejectedCount = Math.max(iteration.rejectedCount, reviewResult.rejectedCount);
        iterations.push(iteration);
        for (const item of accepted) {
            acceptedResults.push(item);
            if (item.url) {
                sources.add(item.url);
            }
            else if (item.source) {
                sources.add(item.source);
            }
            const combined = `${item.title} ${item.snippet ?? ""}`;
            if (/新闻|快讯|动态|消息|价格|走势|行情|财报|业绩/i.test(combined)) {
                news.set(item.title, {
                    title: item.title,
                    source: item.source,
                    date: item.publishedAt,
                    sentiment: inferSentiment(combined),
                    summary: item.snippet
                });
            }
            if (/风险|回撤|波动|下跌|警示|承压|利空/i.test(combined)) {
                risks.add(item.title);
            }
        }
        data = {
            entityInfo: {
                ...data.entityInfo
            },
            news: [...news.values()].slice(0, 10),
            risks: [...risks].slice(0, 5),
            sources: [...sources].slice(0, 10),
            searchQueries: board.searchedQueries,
            acceptedResults: acceptedResults.slice(0, 20),
            plan,
            iterations,
            confidence: 0,
            gaps: [],
            researchBoard: board
        };
        data.gaps = detectGaps(data);
        data.confidence = calculateConfidence(data);
        data.researchBoard.informationGaps = data.gaps;
        const stopReason = shouldStopSearching(data);
        if (stopReason) {
            board.stopReason = stopReason;
            break;
        }
    }
    const enriched = runtime.enrich
        ? await runtime.enrich({
            entity: input.entity,
            acceptedResults,
            board
        })
        : undefined;
    data = {
        entityInfo: {
            name: input.entity,
            ...enriched,
            type: enriched?.type ?? pickType(input.entity, enriched?.summary)
        },
        news: [...news.values()].slice(0, 10),
        risks: [...risks].slice(0, 5),
        sources: [...sources].slice(0, 10),
        searchQueries: board.searchedQueries,
        acceptedResults: acceptedResults.slice(0, 20),
        plan,
        iterations,
        confidence: 0,
        gaps: [],
        researchBoard: board
    };
    data.gaps = detectGaps(data);
    data.confidence = calculateConfidence(data);
    data.researchBoard.informationGaps = data.gaps;
    data.researchBoard.stopReason =
        shouldStopSearching(data) ??
            (data.gaps.length === 0
                ? "核心信息缺口已补齐"
                : `当前置信度 ${(data.confidence * 100).toFixed(0)}%，还没有到 80%，建议继续补充搜索`);
    return data;
}
function extractEntityFromTask(task) {
    return task.goal.replace(/^.*?(搜索|研究|分析|查一下)?\s*/u, "").trim() || task.goal;
}
export function createCyberBowieSearchSkill(runtime) {
    return {
        metadata: METADATA,
        async execute(task) {
            const entity = extractEntityFromTask(task);
            const data = await runPortableDeepSearch({
                entity
            }, runtime);
            return {
                skillName: METADATA.name,
                summary: `已为 ${entity} 生成搜索研究底稿，当前置信度 ${(data.confidence * 100).toFixed(0)}%。`,
                details: [
                    `任务拆分数: ${data.plan.steps.length}`,
                    `搜索查询数: ${data.searchQueries.length}`,
                    `搜索轮次: ${data.iterations.length}`,
                    `新闻条数: ${data.news.length}`,
                    `风险条数: ${data.risks.length}`,
                    `主要缺口: ${data.gaps.join(" / ") || "无"}`,
                    `停止原因: ${data.researchBoard.stopReason ?? "未提前停止"}`
                ],
                data
            };
        }
    };
}
export function createFinpalCompatibleSearchSkill(runtime) {
    return {
        metadata: METADATA,
        async execute(input) {
            const startTime = Date.now();
            try {
                const data = await runPortableDeepSearch(input, runtime);
                return {
                    success: true,
                    data,
                    confidence: data.confidence,
                    completeness: 1 - data.gaps.length / 5,
                    gaps: data.gaps,
                    suggestions: data.gaps.length > 0
                        ? ["建议补充信息缺口后再继续分析"]
                        : ["信息较完整，可以进入下一阶段"],
                    metadata: {
                        durationMs: Date.now() - startTime,
                        toolsUsed: ["search"],
                        sources: data.sources
                    }
                };
            }
            catch (error) {
                return {
                    success: false,
                    error: error instanceof Error ? error.message : String(error),
                    confidence: 0,
                    completeness: 0,
                    gaps: ["搜索执行失败"],
                    suggestions: ["请检查搜索后端配置"],
                    metadata: {
                        durationMs: Date.now() - startTime,
                        toolsUsed: ["search"]
                    }
                };
            }
        }
    };
}
export const searchSkillMetadata = METADATA;
export function createMcpSearchRuntime(options) {
    let clientPromise = null;
    async function getClient() {
        if (clientPromise) {
            return clientPromise;
        }
        clientPromise = (async () => {
            const client = new Client({
                name: options.clientName ?? "cyber-bowie",
                version: "0.1.0"
            });
            const headers = {};
            if (options.authToken) {
                headers[options.authHeader ?? "Authorization"] =
                    (options.authHeader ?? "Authorization").toLowerCase() === "authorization"
                        ? `Bearer ${options.authToken}`
                        : options.authToken;
            }
            const transport = new StreamableHTTPClientTransport(new URL(options.serverUrl), {
                requestInit: {
                    headers
                }
            });
            await client.connect(transport);
            return client;
        })();
        return clientPromise;
    }
    return {
        async search(query) {
            const client = await getClient();
            const response = await client.callTool({
                name: options.toolName ?? "bailian_web_search",
                arguments: {
                    query,
                    count: options.resultCount ?? 10
                }
            });
            const content = response.content;
            const textContent = content.find((item) => item.type === "text")?.text ?? "[]";
            let parsed;
            try {
                parsed = JSON.parse(textContent);
            }
            catch {
                parsed = [];
            }
            const resultItems = Array.isArray(parsed)
                ? parsed
                : typeof parsed === "object" && parsed && "pages" in parsed && Array.isArray(parsed.pages)
                    ? parsed.pages
                    : [];
            return resultItems.map((item) => ({
                title: String(item.title ?? "No title"),
                url: item.url ? String(item.url) : undefined,
                snippet: item.snippet ? String(item.snippet) : item.description ? String(item.description) : undefined,
                source: item.source ? String(item.source) : undefined
            }));
        }
    };
}
//# sourceMappingURL=index.js.map