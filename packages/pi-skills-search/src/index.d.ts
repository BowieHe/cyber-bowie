import type { AgentSkill } from "@cyber-bowie/pi-agent-core";
export type SearchFocus = "financial" | "news" | "manager" | "risk" | "competitor" | "macro" | "technical";
export interface PortableSearchInput {
    entity: string;
    focus?: SearchFocus[];
    previousGaps?: string[];
    isRetry?: boolean;
    maxQueries?: number;
}
export interface PortableSearchResultItem {
    title: string;
    url?: string;
    snippet?: string;
    source?: string;
    publishedAt?: string;
}
export interface PortableResearchBoard {
    proposal: {
        mainQuestion: string;
        subQuestions: string[];
        priorityOrder: string[];
    };
    knownFacts: Array<{
        claim: string;
        source: string;
        confidence: number;
        gapCovered?: string;
    }>;
    informationGaps: string[];
    hypotheses: Array<{
        gap: string;
        rationale: string;
        targetSources: string[];
        queryPatterns: string[];
    }>;
    searchedQueries: string[];
    failedPaths: Array<{
        query: string;
        reason: string;
    }>;
    coveredGaps: Array<{
        gap: string;
        query: string;
        evidence: string[];
        confidence: number;
    }>;
    stopReason?: string;
}
export interface PortableSearchData {
    entityInfo: {
        name: string;
        code?: string;
        type?: string;
        manager?: string;
        company?: string;
        summary?: string;
    };
    news: Array<{
        title: string;
        source?: string;
        date?: string;
        sentiment: "positive" | "neutral" | "negative";
        summary?: string;
    }>;
    risks: string[];
    sources: string[];
    searchQueries: string[];
    acceptedResults: PortableSearchResultItem[];
    plan: SearchPlan;
    iterations: SearchIteration[];
    confidence: number;
    gaps: string[];
    researchBoard: PortableResearchBoard;
}
export interface SearchPlanStep {
    label: string;
    queryPatterns: string[];
    targetGap: string;
}
export interface SearchPlan {
    mainGoal: string;
    steps: SearchPlanStep[];
}
export interface SearchIteration {
    query: string;
    accepted: boolean;
    informationDelta: number;
    reason: string;
    keptCount: number;
    rejectedCount: number;
    coveredGaps: string[];
}
export interface SearchSkillRuntime {
    search(query: string): Promise<PortableSearchResultItem[]>;
    enrich?(input: {
        entity: string;
        acceptedResults: PortableSearchResultItem[];
        board: PortableResearchBoard;
    }): Promise<Partial<PortableSearchData["entityInfo"]>>;
    log?(level: "info" | "warn" | "error", message: string, meta?: unknown): void;
}
export interface McpSearchRuntimeOptions {
    serverUrl: string;
    toolName?: string;
    authToken?: string;
    authHeader?: string;
    resultCount?: number;
    clientName?: string;
}
export interface FinpalSkillLike {
    metadata: {
        name: string;
        description: string;
        triggers?: string[];
        version?: string;
        requiredTools?: string[];
    };
    execute(input: PortableSearchInput & {
        entity: string;
    }, onProgress?: (event: unknown) => void): Promise<{
        success: boolean;
        data?: PortableSearchData;
        error?: string;
        confidence: number;
        completeness: number;
        gaps: string[];
        suggestions?: string[];
        metadata?: {
            durationMs: number;
            toolsUsed: string[];
            sources?: string[];
        };
    }>;
}
export declare function runPortableDeepSearch(input: PortableSearchInput, runtime: SearchSkillRuntime): Promise<PortableSearchData>;
export declare function createCyberBowieSearchSkill(runtime: SearchSkillRuntime): AgentSkill;
export declare function createFinpalCompatibleSearchSkill(runtime: SearchSkillRuntime): FinpalSkillLike;
export declare const searchSkillMetadata: {
    name: string;
    description: string;
    triggers: string[];
    version: string;
    requiredTools: string[];
};
export declare function createMcpSearchRuntime(options: McpSearchRuntimeOptions): SearchSkillRuntime;
