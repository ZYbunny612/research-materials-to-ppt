# 单页内容契约与项目记录

在内容或提示词阶段读取本文件。采用JSON或等价结构，字段可按实际复杂度扩充，不强制未用目录和空占位文件。

## 项目

`project_id`、`version`、`requested_stage`、`sources`、`references`、`pages`。

- `sources`：每项含`id`、`path`或`url`、`role`、可取得时的`sha256`。角色如`raw_notes`、`prior_report`、`style_reference`、`data`。样式参考不授权复制其科研内容。
- `references`：稳定`id`、题录、`url`、`verification_level`（metadata/abstract/fulltext/inherited）。来源访问不成功也须明确记录，不填verified=true冒充。
- 本地相对路径按project.json所在目录解析；引用的外部文件只读。输出不得递归覆盖输入目录。

## 每页

```json
{
  "id": "p03",
  "title": "该页标题",
  "claim": "一条具体且可证伪/可核对的核心主张",
  "claim_status": "proposed",
  "source_ids": ["meeting"],
  "reference_ids": [],
  "text_runs": [{"id":"p03_title","text":"该页标题"}],
  "formulas": [],
  "nodes": [{"id":"input","label":"输入"},{"id":"output","label":"输出"}],
  "edges": [{"id":"e1","from":"input","to":"output","relation":"transforms","arrow":"end"}],
  "layout": {"canvas":[1600,900],"description":"输入在左、输出在右；箭头不穿过文字"},
  "prompt": {"path":"prompts/pages/p03.md","status":"draft"},
  "image": null,
  "ppt_objects": [],
  "visual_review": null
}
```

`claim_status`明确`established`、`proposed`或`illustrative`。研究方案的示意曲线不能使用`established`暗示实验效果；真实结果还须绑定数据和分析源。

公式项含`id`、`canonical`、`definitions`、`assumptions`；需要生成/重建时再加入LaTeX、单位、bbox、route和对象ID。符号必须在本页或稳定的符号表定义。图中文字与公式的批准值以内容契约为源，不由生成图的OCR反向覆盖。

`image`只有真实生成/提供后才填写`path`、`sha256`、`origin`、`prompt_path`。拒收、已批准和被替代版本都保留；文件存在不能自动表示科学内容已批准。

`ppt_objects`每项包含`id`（同时作为PPT对象name）、`kind`（text/shape/connector/plot/formula/image）、`representation`、`semantic_unit_count`、`expected_text`或资产来源。`native_*`表示原生内部编辑；`isolated_image`仅能移动/替换；SVG也不自动等于PPT内部路径可编辑。

## 门禁

- 内容完整是提示词的前置条件，但草案不冒充用户确认。
- 需要等用户看提示词/看图时，记录`awaiting_user_review`并停在指定阶段。
- `visual_review`分别记录科学内容和视觉布局，由实际检查填写；自动脚本不得生成“已审查”结论。
- 成品`ppt`记录`path`、独立逐页渲染目录及正式验证结果位置。用户仅要内容/提示词时不要求填ppt。
