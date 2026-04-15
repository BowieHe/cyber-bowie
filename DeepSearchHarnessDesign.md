架构设计与实现文档：基于 LLM-as-a-Judge 的智能体自纠错与监管框架 (Harness v1.1)
1. 核心设计理念 (Architecture Philosophy)
在本多智能体协作网络中，Harness 扮演**“质量控制网关（Quality Control Gate）”。它不是执行具体业务（如写代码、查资料）的工人，而是具有一票否决权的主管**。

核心约束与原则：

结构化输出先行： Harness 节点的每一次评判，必须输出严格的 JSON 格式（借助 Pydantic 约束），绝不允许输出自由文本，以便系统进行条件路由（Conditional Edge）。

容错与妥协（Graceful Degradation）： 当达到最大重试次数时，Harness 必须学会接受“不完美”，通过识别并声明“信息盲区”来打破死循环。

动态记忆注入： Harness 的报错必须以“错题本”的形式，动态注入到被惩罚节点的下一次 System Prompt 中。

2. 全局状态与数据字典 (Global State Definition)
在构建 StateGraph 时，必须严格按照以下结构定义全局状态字典。这是所有 Agent 交互的唯一真理来源（Single Source of Truth）。

Python
from typing import TypedDict, Annotated, List, Optional
import operator
from pydantic import BaseModel, Field

class AssistantState(TypedDict):
    # --- 1. 核心业务数据 ---
    user_query: str                 # 用户的原始提问
    retrieved_context: List[str]    # 检索器抓取到的原始文本切片列表
    draft: str                      # 主笔生成的初稿
    final_output: str               # 最终回复
    
    # --- 2. 监管控制数据 (Harness 专用) ---
    attempted_queries: Annotated[List[str], operator.add] # [记忆] 已执行过的搜索词
    correction_log: Annotated[List[str], operator.add]    # [记忆] 历次失败的打回原因（错题本）
    search_retry_count: int                               # 检索环节已重试次数
    draft_retry_count: int                                # 撰写环节已重试次数
    
    # --- 3. 路由状态指示器 ---
    current_harness_status: str     # 当前门控状态枚举：PASSED | NEEDS_RETRY | PARTIAL_ACCEPT
3. Harness 评估器 Schema 设计 (Structured Output)
为了保证路由的稳定性，要求大模型作为裁判（LLM-as-a-Judge）时，必须绑定以下 Pydantic Schema 进行输出约束。

Python
class HarnessEvaluation(BaseModel):
    status: str = Field(
        description="评估结果枚举值，必须是以下三个之一：'PASSED', 'NEEDS_RETRY', 'PARTIAL_ACCEPT'"
    )
    reasoning: str = Field(
        description="一步步思考的逻辑过程，解释为什么给出该 status。"
    )
    correction_directive: Optional[str] = Field(
        description="如果 status 为 NEEDS_RETRY，这里必须写明针对被评估节点的明确修改指令（如：'缺少XXX数据，请更换搜索词' 或 '第2段第3行伪造了收益率，请删除'）。如果通过则为空。"
    )
    missing_information: Optional[str] = Field(
        description="如果 status 为 PARTIAL_ACCEPT，这里必须总结出当前全网无法搜到/系统缺失的核心信息盲区。供下游环节进行风险提示。"
    )
4. 节点实现规范与 Prompt 模板 (Node Implementations)
请 Coding Agent 按照以下规范实现相应的 LangGraph 节点：

4.1. 搜索质量监管节点 (Search_Harness_Node)
位置： 在 Retriever_Node 之后。
职责： 评估搜到的 retrieved_context 能否支撑解答 user_query。

Python
# System Prompt 模板
SEARCH_HARNESS_PROMPT = """
你是一个严苛的金融信息质量审查员。
你的任务是评估系统检索到的【上下文】能否足够解答用户的【原始问题】。

评估规则：
1. 若信息充足且直接相关，输出 status: PASSED。
2. 若信息完全无关或过时，且重试次数小于 3 次，输出 status: NEEDS_RETRY，并在 correction_directive 中给出建议的新搜索角度。
3. 若重试次数已达上限（当前已重试 {retry_count} 次），但仍未找到完美信息，请输出 status: PARTIAL_ACCEPT，并在 missing_information 中清晰列出“当前查不到的数据盲区”。

用户问题：{user_query}
当前检索到的上下文：{retrieved_context}
"""
4.2. 事实核查监管节点 (Fact_Check_Harness_Node)
位置： 在 Drafter_Node（初稿生成）之后。
职责： 防治大模型幻觉，确保初稿完全忠于上下文。

Python
# System Prompt 模板
FACT_CHECK_HARNESS_PROMPT = """
你是一个以“零容忍”著称的事实核查程序的底层逻辑。
请将【初稿】与【参考上下文】进行逐字对比。

评估规则：
1. 忠实度：初稿中的任何具体数值、实体名称、趋势判断，必须能在上下文中找到明确对应。
2. 若发现任何一处“无中生有”或“篡改数据”，立即输出 status: NEEDS_RETRY，并在 correction_directive 中指出具体的造假位置。
3. 若所有事实均有出处，输出 status: PASSED。

初稿：{draft}
上下文：{retrieved_context}
"""
4.3. 动态错误注入与节点重塑 (Dynamic Prompt Injection)
在业务节点（如 Drafter_Node）被 Harness 打回重新执行时，其输入 Prompt 必须经过如下处理：

Python
def drafter_node(state: AssistantState):
    base_prompt = "基于以下上下文撰写分析报告：\n" + "\n".join(state["retrieved_context"])
    
    # 【核心逻辑】动态读取错题本，强行注入
    if state["correction_log"]:
        errors = "\n- ".join(state["correction_log"])
        base_prompt += f"\n\n【🚨 严重监管警告 🚨】\n你之前的尝试被审核程序驳回，你犯了以下严重错误：\n- {errors}\n本次重写请务必规避上述所有问题！否则系统将崩溃。"
        
    if state["current_harness_status"] == "PARTIAL_ACCEPT":
         # 处理妥协放行的情况
         blind_spot = state.get("missing_information", "")
         base_prompt += f"\n\n【⚠️ 风险提示指令】\n由于系统检索能力限制，目前缺失以下信息：{blind_spot}。请在报告中以客观口吻明确向用户指出这一信息盲区，切勿自行推测编造。"
         
    # 调用 LLM 生成 ...
5. LangGraph 路由编排 (Topology & Conditional Edges)
利用 harness_status 控制图的边（Edges），形成安全的局部状态机反馈循环。

Python
# 示例：搜索循环的路由控制
def search_harness_router(state: AssistantState) -> str:
    status = state["current_harness_status"]
    
    if status == "PASSED":
        return "continue_to_draft"
    elif status == "PARTIAL_ACCEPT":
        return "continue_to_draft_with_warning"
    elif status == "NEEDS_RETRY":
        if state["search_retry_count"] >= 3:
            # 极限兜底：如果 Harness 崩溃或者死循环，强行切断
            return "force_quit" 
        return "rewrite_search_query"
    else:
        return "force_quit"

# 绑定路由
workflow.add_conditional_edges(
    "search_harness", 
    search_harness_router, 
    {
        "continue_to_draft": "drafter_node",
        "continue_to_draft_with_warning": "drafter_node",
        "rewrite_search_query": "retriever_node",
        "force_quit": "error_handling_node"
    }
)
6. 给 Coding Agent 的开发备注 (Notes for Implementation Agent)
纯净函数原则： 所有 Node 必须是无状态的纯函数，一切记忆（如已搜过的词、报过的错）只能通过读写传入的 state 字典实现。

使用 LangChain with_structured_output： 在实现 Harness 节点的大模型调用时，务必使用此方法绑定 HarnessEvaluation 模型，以保证状态机的路由永远能拿到合法的枚举值。

状态追加隔离： 在处理 attempted_queries 和 correction_log 时，注意使用 operator.add 实现增量 Append，绝对不要覆盖历史数据，以此维持完整的决策轨迹以备系统调试（Tracing）。