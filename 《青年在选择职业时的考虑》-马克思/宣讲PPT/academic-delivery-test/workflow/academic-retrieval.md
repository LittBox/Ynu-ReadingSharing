# C逐页联合检索操作

## 三路职责

1. 关键词召回：中文二元词/英文词BM25，匹配明确标签。
2. 向量召回：真实中文句嵌入余弦相似度，匹配措辞不同但结构相近的描述。本地适配器使用macOS NaturalLanguage zh-Hans sentenceEmbedding；不上传用户内容、不需API key。不是TF-IDF/哈希向量。
3. 语义检索与判读：当前agent阅读本页真实文本、上下文、R01–R20及召回候选，逐项判断关系、容量、证据和适用边界，再重排。此通道是有解释的模型判读，不伪称另一个向量模型，也不把标签筛选称为语义理解。

只有三路都完成，才写layout_confirmed。分数不能覆盖硬边界。颜色不参与布局相关度，配色由用户输入绑定。

## 每页实际执行

仅轮到本页时生成`pages/NN/input.json`，字段：

```json
{"page_id":"stable-id","source_page":5,"text":"实际原文和说明","roles":[{"text":"具体句子","role":"claim","reason":"表达判断而非类别名"}],"features":{"purpose":"argument","relation":"parallel","density":"short","group_count":3,"evidence":["text"],"image_required":false},"retrieval_query":"概括本页表达任务、关系、材料形态和容量的自然语言；不可只复制主题关键词"}
```

运行：

```bash
python3 scripts/retrieve-academic-layouts.py pages/NN/input.json --index work/layout-index.json --output pages/NN/recall.json
```

脚本按真实逻辑冲突、必要证据和容量边界排除不适用候选；purpose只是语义提示，不作为预先锁模板的硬过滤。分别取关键词与向量前四的并集，保留两路得分、排序和排除理由。agent随后必须阅读候选及规则正文，写`semantic.json`：page_id、input_sha256和rules_sha256取自recall；assessments逐个包含id、eligible、semantic_score(0–1)、reason；另含selected_id、selection_reason、layout_confirmed:true。分数是agent判断记录，不是经验标定的概率。

```bash
python3 scripts/retrieve-academic-layouts.py pages/NN/input.json --index work/layout-index.json --semantic-review pages/NN/semantic.json --output pages/NN/decision.json
```

脚本校验来源哈希与候选覆盖，再融合关键词排名20%、向量排名30%、语义判断50%；权重是可解释默认，不是效果承诺。agent可基于具体边界选择非首位候选，但必须写理由。确认之后才记录image_decision并考虑调用imagegen。最后制作/验证本页，再轮到下一页；不能先批量做完所有页决定后一次排版。

## 索引、失败与维护

规则JSON变化或模型revision/dimension变化自动重建索引。项目缓存放work，不提交用户文本到Skill库。模型不可用则脚本明确失败；不能悄悄切关键词并声称三路完成。其它系统可实现真实嵌入适配器，需记录模型/版本/维度并验证，不能编造向量结果。

本页无合适候选时，回到语义分析或在库中登记可解释变体及反例，然后重新检索。不得以代码自动选中分数第一替代agent语义判读。模板C01–C06是运行结构族，不限制仅能设计六种几何，也不要求一份稿各用一次。
