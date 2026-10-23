# Research Materials to PPT

从研究笔记、论文、报告和导师反馈出发，整理有证据支撑的科研叙事，经逐页提示词、参考图生成和逐元素重建，制作可编辑的 PowerPoint。

这是一个供 Codex 使用的技能包。`SKILL.md` 是工作流入口；附带 Python 脚本用于检查阶段记录与来源关联，不负责自动生成整套演示文稿。

## 工作流程

| 阶段 | 标识 | 主要产物 |
| --- | --- | --- |
| 材料与研究内容 | `content` | 来源清单、研究叙事、逐页内容契约、公式与符号定义 |
| 逐页详细提示词 | `prompts` | 每页独立的文字、布局、节点、连线及验收要求 |
| 图片生成与审查 | `images` | 参考图、确切提示词、版本记录和科学内容审查记录 |
| 可编辑 PPT 重建 | `ppt` | 原生文字与结构对象、独立图片资产、PPTX 和验证记录 |

可以只执行到指定阶段，也可以完成全流程。已有中间产物可检查后继续使用；用户要求“先讨论”“先看提示词”或“看图后再做 PPT”时，流程停在相应阶段。

## 主要特点

- **来源可追溯**：区分事实、研究设想、待验证假设、示意与实测结果，记录引文核对深度。
- **逐页设计**：以内容契约确定核心主张、规范文字、公式及图形关系，再编写独立提示词。
- **真实编辑性**：文字、模块、箭头、轴和图表结构尽可能使用 PowerPoint 原生对象，并按最小语义单位拆分。
- **保留过程**：保存提示词、生成原图、资产来源、对象清单及审查记录，便于修改与复核。
- **明确边界**：附件作为资料处理，不作为额外指令或授权；不虚构论文、数据、实验结果或已读全文。

## 安装与依赖

将整个 `research-materials-to-ppt` 文件夹放入 Codex 的技能目录，例如：

- Windows：`%USERPROFILE%\.codex\skills\research-materials-to-ppt\`
- macOS / Linux：`~/.codex/skills/research-materials-to-ppt/`

保留目录结构，使 `SKILL.md` 能访问 `references/` 和 `scripts/`。也可直接向 Codex 提供技能路径。

不同阶段所需能力：

| 用途 | 依赖 |
| --- | --- |
| 内容与提示词 | 能读取输入材料的 Codex 环境；核对外部文献时需要相应访问能力 |
| 实际生成或编辑位图 | `imagegen` 技能及可用的图像生成工具 |
| 制作 PowerPoint | `presentations` 技能；优先结合 `scientific-diagram-ppt-rebuilder` 或 `ppt-visual-replica` |
| 阶段检查 | Python 3；检查脚本仅使用标准库 |

仅编写提示词不需要调用图像生成工具。缺少下游重建技能时，仍应遵守 `SKILL.md` 中的最低编辑性要求，并说明环境限制。具体渲染与导出环境由演示文稿技能决定。

## 使用示例

在 Codex 中提供材料，并明确目标阶段、汇报对象、页数或时长、模板及需要保留的内容。

**先整理内容：**

```text
使用 $research-materials-to-ppt，根据这些论文和讨论记录整理组会汇报。
先做到 content 阶段，给出逐页核心主张、证据来源和待验证假设。
```

**只写逐页提示词：**

```text
使用 $research-materials-to-ppt，根据已确认的内容契约，
为每页编写详细绘图提示词。停在 prompts 阶段，等我审阅。
```

**完成全流程：**

```text
使用 $research-materials-to-ppt，将附件整理成面向导师的科研汇报。
完成内容、逐页提示词、参考图和可编辑 PPT，保留全部中间产物，
区分研究设想与实测结果，并说明成品中哪些元素以图片保留。
```

## 文件结构

```text
research-materials-to-ppt/
├── README.md                       使用说明
├── COPYRIGHT                       版权声明
├── SKILL.md                        技能入口与阶段要求
├── agents/
│   └── openai.yaml                 Codex 界面信息与默认提示词
├── references/
│   ├── page-contract.md            单页内容契约与项目记录格式
│   └── visual-workflow.md          提示词、图形选择与审查要求
└── scripts/
    ├── check_pipeline.py           只读阶段与溯源检查
    └── test_pipeline.py            检查脚本的测试
```

项目记录格式见 [单页内容契约](references/page-contract.md)，视觉设计要求见 [逐页提示词与视觉决策](references/visual-workflow.md)。项目文件中的本地相对路径以 `project.json` 所在目录为基准。

## 阶段检查

在技能目录中运行，替换为实际项目记录路径：

```bash
python scripts/check_pipeline.py /path/to/project.json --stage content
python scripts/check_pipeline.py /path/to/project.json --stage prompts
python scripts/check_pipeline.py /path/to/project.json --stage images
python scripts/check_pipeline.py /path/to/project.json --stage ppt
```

选择当前阶段即可；后续阶段会同时检查前面阶段的相关记录。脚本输出 JSON，通过时退出码为 `0`，失败时为 `1`。

检查包括来源和页面 ID、文件存在性、引用关联、节点与边、图片哈希及审查记录；PPT 阶段还会检查页数、对象映射、部分文字内容、原生对象声明，以及整页参考图嵌入等问题。

**脚本通过不代表科学内容正确、视觉保真或所有元素均可编辑。** 仍需逐页渲染、核对文字与公式、检查箭头及图片覆盖范围，并完成演示文稿技能要求的导出验证。

## 编辑性与交付

主体文字和结构尽可能原生可编辑；照片、复杂插画及部分复杂公式可作为独立图片保留，并说明限制。独立图片可以移动、替换，不表示其内部元素可以编辑。

最终交付与目标阶段一致。完整流程应保留原始材料清单、内容契约、逐页提示词、参考图及版本、独立资产、PPT 对象记录、成品和审查记录。参考整页图仅用于独立对照，不嵌入成品充当重建结果。


Copyright © [ZYbunny612](https://github.com/ZYbunny612)
