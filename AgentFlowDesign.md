1. 架构总览与流转拓扑
   系统的整体流转遵循**“生成 -> 质检 -> 纠错 -> 深度对抗 -> 最终裁决”**的逻辑。

主干流程图：

User Input ->

Intent_Router (意图路由) ->

Retriever_Agent (检索智能体) ⟷ Search_Harness (搜索质检门) ->

Drafter_Node (初稿主笔) ⟷ Fact_Check_Harness (事实质检门) ->

Debater_Agent (多方辩论智能体) ->

Synthesizer_Node (最终法官) -> Output

2. 全局状态字典 (Global State)
   系统中的所有组件无状态运行，全部依赖读写这一个数据结构。

Python
class AssistantState(TypedDict): # 1. 业务上下文
user_query: str # 用户输入
intent: str # 路由意图 (普通闲聊 / 深度投研)
retrieved_context: list[str] # 检索到的事实切片
draft: str # 主笔初稿
debate_log: list[str] # 辩论实录
final_answer: str # 最终交付文本

    # 2. Harness 监管状态 (用于自纠错和记忆)
    attempted_queries: list[str]    # [防死循环] 已尝试过的搜索词
    correction_log: list[str]       # [防重复犯错] 历次被打回的具体原因记录
    harness_status: str             # 当前门控状态 (PASSED, NEEDS_RETRY, PARTIAL_ACCEPT)
    retry_count: int                # 当前环节的重试计数器
    missing_info: str               # 妥协放行时，记录系统缺失的客观数据盲区

3. 核心角色与功能边界详细设计
   以下是系统中各个组件的具体设计。注意区分它们的形态（Node vs. Agent）。

模块 A：Intent Router (意图路由节点)
形态： 普通 Node (单次 LLM 调用)

功能职责： 系统的前台接待员。判断用户是要简单聊天（天气、打招呼）还是要进行复杂的金融/知识查询。

输入/输出： 读取 user_query，写入 intent。

边界约束： 绝对不回答具体问题，只输出枚举值（如 CHAT, RESEARCH），引导 LangGraph 的下一步走向。

模块 B：Retriever Agent (信息检索智能体)
形态： Agent (微型 SubGraph，包含工具调用闭环)

功能职责： 系统的“情报专员”。负责根据用户问题制定搜索词，调用 Web Search API 或向量数据库获取真实资料。

动态 Prompt 注入： 每次启动前，必须检查 attempted_queries。如果发现是被 Harness 打回重做的，系统提示词必须强调：“禁止使用历史搜索词，请从行业上下游或宏观政策等侧面重新制定搜索策略。”

输出： 写入 retrieved_context 和 attempted_queries。

模块 C：Search Harness (搜索质检网关)
形态： 监管 Node (结构化输出模型)

功能职责： 评估 retrieved_context 的质量。

执行逻辑：

通过： 信息充足，写入 harness_status = PASSED，清空重试计数器。

打回： 毫不相干，写入 harness_status = NEEDS_RETRY，重试次数 +1，并在 correction_log 写入建议的搜索方向。

妥协： 重试达 3 次依然无果，写入 harness_status = PARTIAL_ACCEPT，并在 missing_info 中总结缺失了什么关键数据（例如：“全网缺乏该基金经理 2026 年的最新持仓数据”）。

模块 D：Drafter Node (主笔分析师)
形态： 普通 Node (单次长文本生成)

功能职责： 系统的“撰稿人”。基于经过质检的 retrieved_context 写出包含明确观点的初稿。

动态 Prompt 注入： \* 必须读取 correction_log。如果上次因为伪造数据被 Harness 骂了，这次 Prompt 里必须带上红字警告。

必须读取 missing_info。如果有值，必须在初稿开头声明风险：“基于现有公开数据，目前无法获知 XXX，仅根据现有趋势分析如下……”

输出： 写入 draft。

模块 E：Fact-Check Harness (事实核查网关)
形态： 监管 Node (零容忍质检员)

功能职责： 防治大模型幻觉的核心武器。

执行逻辑： 拿着 draft 逐字逐句去对比 retrieved_context。发现任何无中生有的数据（比如编造收益率），立刻输出 NEEDS_RETRY，并将造假细节写入 correction_log，打回 Drafter 重写。

模块 F：Debater SubGraph (红蓝多方辩论智能体)
形态： Agent (内部包含两个 LLM 节点的循环子图)

功能职责： 系统的“风控与投研智囊团”。为初稿提供深度和多维度的视角。

子角色划分：

红方 (Red Team / 牛派)： 职责是“找机会”。阅读初稿，补充积极的宏观信号、潜在的超额收益点。

蓝方 (Blue Team / 熊派)： 职责是“挑毛病”。专门盯着初稿里的逻辑漏洞、历史高回撤、政策打压风险进行反驳。

执行流转： 红蓝双方基于 draft 进行回合制发言（建议硬编码最多循环 2-3 个回合）。每一次的发言都追加写入 debate_log。

边界约束： 它们绝对不直接给用户下结论，只负责把各自视角的论据拉满。

模块 G：Synthesizer (最终法官/整合者)
形态： 普通 Node

功能职责： 系统的“最终发言人”。

执行逻辑： 将 draft（核心基调）和 debate_log（风险与机会补充）进行中和与排版。向用户交付一份既有主线逻辑，又兼顾多方风险提示的高质量深度回答。

输出： 写入 final_answer，系统结束流转。

4. 架构设计的核心优势总结
   这套设计完全规避了传统单体大模型（一问一答）容易产生的“胡编乱造”和“视角单一”的问题：

彻底分离了“干活的人”与“挑错的人”： Retriever 和 Drafter 只管输出，Harness 专职找茬，符合大模型“评估能力远大于生成能力”的特质。

状态透明，死循环免疫： attempted_queries 和 retry_count 的引入，加上 PARTIAL_ACCEPT 的优雅降级机制，保证了系统在真实互联网碎片化信息面前的鲁棒性。

MoE (混合专家) 级的信息密度： Debater 环节的红蓝对抗，强制模型进行极端视角的角色扮演，能逼出很多平庸 Prompt 无法生成的长尾金融洞察。
