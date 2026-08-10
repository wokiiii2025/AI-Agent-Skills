#!/usr/bin/env python
import argparse
import html
import json
import os
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from urllib import error, request


SKILL_DIR = Path(__file__).resolve().parents[1]
PRESETS_PATH = SKILL_DIR / "references" / "web_prompt_presets.json"
ENV_PATH = SKILL_DIR / ".env"
MAX_FINAL_PROMPT_CHARS = 450


STRICT_OUTPUT_RULES = """
追加硬约束（优先级高于上文的一般表达习惯）：
0. 你的身份是成人海报摄像师和图像编辑视觉导演，负责把网页选项转写成图生图/文生图模型能直接执行的镜头、姿态、场景、光影和质感描述。
1. 输出必须是确定的最终提示词，不得写候选、建议、举例或不确定表达。
2. 禁止使用这些词和字符：可能、可选、例如、比如、或者、若、如果、可以、或。不要在任何位置用“或”连接内容，改用确定的单项描述或顿号并列。
3. 遇到原始标签中的候选项，必须自由设计一个具体结果，不要保留候选列表。选择室内时，必须写成“室内-具体场所名”，例如“室内-私人摄影棚”；选择室外时，必须写成“室外-具体场所名”，例如“室外-屋顶露台”。示例只用于理解，不要固定复用示例，不要每次默认酒店、卧室、城市街道、公园步道。
4. 如果选择室内，必须同时保留“室内”字样、自由设计一个明确室内成人影像场所，并写出 2 到 4 个服务主体的环境元素。可以参考私人公寓、浴室、摄影棚、更衣室、酒吧包厢、办公室夜景、舞台后台、车内、游艇船舱等方向，但最终必须只输出一个实际地点名，不要输出候选列表。
5. 如果选择室外，必须同时保留“室外”字样、自由设计一个明确室外成人影像场所，并写出 2 到 4 个明确外景元素。可以参考屋顶露台、泳池边、海边木栈道、私家庭院、霓虹雨夜街角、高层阳台、度假露台、外景摄影地等方向，但最终必须只输出一个实际地点名，不要输出候选列表；不得只写“室外开放场景、自然光、夜景灯光、露天环境”。
6. 室外场景不得混入卧室、客厅、酒店房间、床铺、床单、室内窗帘、屏风等室内元素，除非用户明确要求保留原图背景。
7. “人物互动和身体姿态清晰”只表示画面主体与姿态清晰，不表示新增肢体接触、亲密互动、插入、贴靠、拥抱、搭肩、手部交叠等关系动作。除非用户输入明确选择这些动作，否则禁止新增关系动作、接触动作、服装类型、人物数量或剧情事件。
8. 如果用户输入没有明确选择露出编辑、插入、接触、去除衣物、全身赤裸等标签，不得主动描写具体身体暴露部位、性器官、插入位置、贴靠位置、亲密接触方式。
9. 不要用否定清单污染图像提示词。不要写“不描述乳房、阴茎、插入”“不包含床铺、窗帘、屏风”“不穿衬衫、裤子”这类把禁止对象写出来的句子；统一改成“保持原图身体覆盖状态、人物姿态和相对位置，不新增未选内容”“背景只保留明确场景元素”。
10. prompt 必须控制在 450 个中文字符以内，句子完整，不要半句截断。
11. 最终 prompt 只写正向编辑描述，不写任何否定描述、禁止描述、反向提示词、排除项、避错项。不要出现“不、无、未、禁止、避免、不得、不要”等否定词；质量要求也要改成正向表达，例如“主体稳定、结构自然、身份一致、光影清晰”。
12. 输出前必须逐字自检 JSON 的 prompt 字段：不得包含“或”这个字，不得包含“可能、可选、例如、比如、或者、若、如果、可以”，不得包含“模型自由设计”“具体成人影像场所”“具体外景”“具体内景”这些占位说明字样，不得包含未选择的动作和身体部位。如果发现，必须先重写再输出。
13. 错误示例：“Logo、水印或字幕”“不替换或新增”“自然光、夜景灯光或露天环境”“如床单、窗帘”“室外-模型自由设计的具体外景”“避免畸形、错位”。正确写法：“画面纯净”“保持原图主体稳定”“室外-屋顶露台，玻璃栏杆、城市天际线、远景灯光”“室内-私人摄影棚，柔光箱、深色背景布、反光板”“主体稳定，结构自然”。
14. 本轮测试覆盖原系统提示词中的固定字段前缀格式：必须保留画风、封面类型、人物组合、场景、身体朝向、镜头构图、背景方向这些信息维度，但最终 prompt 不得输出字段名。prompt 必须是一段完整连续的中文图像编辑描述，不要以“修改目标：画风：”“封面类型：”“人物组合：”这类结构化标签串开头。允许用分号分句，但整体必须像一段完整画面描述。
15. 段落内容顺序建议固定为：先说明保留原图主体与本次编辑目标，再说明人物动作姿态，再说明场景和光影，再说明主体稳定、身份一致、结构自然、画面清晰等正向质量要求。
16. 动作姿态必须具体可见，至少覆盖头部/脸部方向、躯干/肩颈、腰臀/骨盆、手臂/手部、腿部/膝脚、镜头角度中的三类。正面要写清脸部朝向和躯干面对镜头；侧身要写清身体侧向、腰臀转向和腿部站位；背面要写清背部朝向、头部转向和身体重心。
17. 成人向表达必须使用图像模型易读的视觉语言：人物数量、年龄身份、画风、构图、姿态、场景、光影、质感和清晰度要确定；只描述用户选择或原图已经存在的成人向视觉元素，保持主体关系稳定。
18. “海报”“封面”“电影海报式”只表示竖版主视觉、镜头构图、光影层次、背景纵深和商业摄影质感，画面中不生成标题、片名、角色名、Logo、水印、字幕、UI、海报排版字、角标、出版信息等任何可读文字元素；最终 prompt 用“画面纯净”表达这一点。
19. 原始标签里的“人物互动和身体姿态清晰”是网页预设的泛化文案。只有输入明确包含双人、两人、插入、接触、贴靠、拥抱、搭肩时，才允许写“人物互动”；其他情况统一改写为“主体动作姿态清晰”。
20. 姿态句必须像摄像师给模特和镜头的指令：写出头部朝向、肩颈状态、躯干转向、腰臀/骨盆方向、手臂/手部位置、腿部支撑方式。不要只写“姿态清晰、自然稳定、完整可见”这类空泛质量词。
21. 不要输出候选地点、斜杠地点、括号候选或“等”结尾集合，例如“卧室/客厅/酒店房间”“海滩、山林、街道等”。必须落到一个确定地点和 2 到 4 个确定环境元素。
22. 风格切换只描述人物轮廓、线条、皮肤/材质质感、背景渲染和光影层次。除非用户明确选择服装/衣物编辑，不得写“服饰、衣着、穿着、衣服细节、修改人物穿着”。
23. 最终只输出 JSON：{"prompt":"..."}，prompt 内也不得出现解释性语气。
""".strip()


FINAL_SELF_CHECK = """
最终输出前再次强制自检：
- prompt 字段必须为确定指令，不得包含“或”这个字。
- prompt 字段不得包含：可能、可选、例如、比如、或者、若、如果、可以、模型自由设计、具体成人影像场所、具体外景、具体内景。
- 未选择露出/接触/插入时，不得主动写具体身体暴露部位、插入、贴靠、拥抱、搭肩、手部交叠。
- 室外必须保留“室外-具体地点”格式，并包含至少两个外景元素。
- prompt 字段必须小于等于 450 个中文字符。
- prompt 字段只写正向描述，不得包含任何否定词或反向提示词。
- prompt 字段必须是一段完整描述，不得是字段清单；必须有明确动作姿态，覆盖头部/脸部、躯干、腰臀/骨盆、手臂/手部、腿部/镜头中的至少三类。
- “海报/封面”只代表构图和质感，prompt 必须让画面保持纯净，不加入任何可读文字元素。
- 未明确双人、两人、插入、接触、贴靠、拥抱、搭肩时，prompt 字段不得使用“人物互动”，改写为“主体动作姿态”。
- prompt 字段不得包含斜杠候选地点、括号候选地点和“等”结尾候选集合。
- 未选择服装/衣物编辑时，prompt 字段不得包含服饰、衣着、穿着、衣服细节、修改人物穿着。
不满足任一条时，立即重写 prompt 字段后再返回 JSON。
""".strip()


DEFAULT_I2I_CASES = [
    {
        "id": "single_female_real_indoor_front_keep_face",
        "reference": "当前参考图为单人成年女性角色图片；参考图中只有一名成年女性，必须保持单人，不新增任何人物。",
        "manual": "页面真实图生图选项：单人参考图，最终只保留一名成年女性；",
        "labels": ["真实超写实", "室内", "正面", "湿润质感", "保留脸部"],
        "required_any": [["单人", "一名"], ["成年女性", "单人女性"], ["真实"], ["室内", "卧室", "客厅", "酒店房间"], ["正面"], ["保留原图脸部特征", "保留原图人物脸部特征"]],
        "person_count": "single"
    },
    {
        "id": "single_female_anime_outdoor_side_keep_pose",
        "reference": "当前参考图为单人成年女性角色图片；参考图中只有一名成年女性，必须保持单人，不新增任何人物。",
        "manual": "页面真实图生图选项：单人参考图，最终只保留一名成年女性；",
        "labels": ["动漫卡通", "室外", "侧身", "保留姿势"],
        "required_any": [["单人", "一名"], ["成年女性", "单人女性"], ["动漫"], ["室外", "街道", "屋顶", "露台", "庭院", "花园", "公园", "步道", "海边", "霓虹", "雨夜", "城市"], ["侧身", "侧向", "侧面"], ["保留原图姿势", "保留原图人物姿势"]],
        "person_count": "single"
    },
    {
        "id": "single_male_cinematic_indoor_back_keep_background",
        "reference": "当前参考图为单人成年男性角色图片；参考图中只有一名成年男性，必须保持单人，不新增任何人物。",
        "manual": "页面真实图生图选项：单人参考图，最终只保留一名成年男性；",
        "labels": ["电影质感", "室内", "背面", "保留背景"],
        "required_any": [["单人", "一名"], ["成年男性", "单人男性"], ["电影", "真实"], ["室内", "卧室", "客厅", "酒店房间", "摄影棚"], ["背面"], ["保留原图背景", "保留原图主要静物布局", "保留原图背景布局"]],
        "person_count": "single"
    },
    {
        "id": "single_female_last_scene_orientation_wins",
        "reference": "当前参考图为单人成年女性角色图片；参考图中只有一名成年女性，必须保持单人，不新增任何人物。",
        "manual": "页面真实图生图选项先误选室内和正面，但最终选择为室外与侧身；",
        "labels": ["室内", "正面", "室外", "侧身", "保留脸部"],
        "required_any": [["单人", "一名"], ["成年女性", "单人女性"], ["室外", "街道", "屋顶", "露台", "庭院", "花园", "公园", "步道", "海边", "霓虹", "雨夜", "城市"], ["侧身", "侧向", "侧面"], ["保留原图脸部特征", "保留原图人物脸部特征"]],
        "conflicts": [["室内", "室外"], ["正面", "侧身"]],
        "person_count": "single"
    },
    {
        "id": "two_adults_preserve_two_people",
        "reference": "当前参考图为两名成年角色图片；参考图中正好两人，必须保持两人，不新增第三人，也不删减为单人。",
        "manual": "页面真实图生图选项：双人参考图，保持两名成年角色；",
        "labels": ["真实超写实", "室内", "侧身", "保留姿势"],
        "required_any": [["两", "双人"], ["成年"], ["真实"], ["室内", "卧室", "客厅", "酒店房间"], ["侧身", "侧向", "侧面"], ["保留原图姿势", "保留原图人物姿势"]],
        "person_count": "two"
    }
]


DEFAULT_T2I_CASES = [
    {
        "id": "single_female_asian_indoor_front_cover",
        "role": "角色信息：无。",
        "manual": "页面真实文生图选项：",
        "labels": ["东方亚洲人种", "单人女性", "室内", "正面", "湿润质感", "竖版封面"],
        "required_any": [["东方亚洲"], ["单人", "一名"], ["成年女性", "女人"], ["室内"], ["正面"], ["竖版", "封面"]],
        "person_count": "single"
    },
    {
        "id": "single_male_outdoor_side_closeup",
        "role": "角色信息：无。",
        "manual": "页面真实文生图选项：",
        "labels": ["东方亚洲人种", "单人男性", "室外", "侧身", "近距离镜头"],
        "required_any": [["东方亚洲"], ["单人", "一名"], ["成年男性", "男人"], ["室外"], ["侧身", "侧向", "侧面"], ["近距离"]],
        "person_count": "single"
    },
    {
        "id": "single_choice_last_wins_t2i",
        "role": "角色信息：无。",
        "manual": "页面真实文生图选项先误选室内和正面，但最终选择室外和侧身：",
        "labels": ["东方亚洲人种", "单人女性", "室内", "正面", "室外", "侧身", "竖版封面"],
        "required_any": [["东方亚洲"], ["单人", "一名"], ["成年女性", "女人"], ["室外"], ["侧身", "侧向", "侧面"], ["竖版", "封面"]],
        "conflicts": [["室内", "室外"], ["正面", "侧身"]],
        "person_count": "single"
    }
]


@dataclass
class ApiResult:
    ok: bool
    status: int | None
    latency_ms: int
    text: str
    raw: object
    error: str


def load_env(path: Path) -> dict:
    values = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            values[key.strip()] = value.strip().strip('"').strip("'")
    values.update({k: v for k, v in os.environ.items() if k in values or k.endswith("_URL") or k.endswith("_TOKEN")})

    pattern = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")
    for _ in range(5):
        changed = False
        for key, value in list(values.items()):
            expanded = pattern.sub(lambda match: values.get(match.group(1), os.environ.get(match.group(1), "")), value)
            if expanded != value:
                values[key] = expanded
                changed = True
        if not changed:
            break
    return values


def load_presets() -> dict:
    return json.loads(PRESETS_PATH.read_text(encoding="utf-8"))


def preset_index(groups: list[dict]) -> dict:
    index = {}
    for group in groups:
        for tag in group["tags"]:
            index[tag["label"]] = {**tag, "groupTitle": group["title"], "selectMode": group["selectMode"]}
    return index


def expand_labels(mode: str, labels: list[str], presets: dict) -> list[dict]:
    groups = presets[mode]
    by_label = preset_index(groups)
    selected_by_single_group = {}
    selected_multi = []
    mutex_slots = {}

    for label in labels:
        if label not in by_label:
            raise KeyError(f"unknown preset label for {mode}: {label}")
        tag = by_label[label]
        if tag["selectMode"] == "single":
            selected_by_single_group[tag["groupTitle"]] = tag
            continue
        mutex = tag.get("mutexKey")
        if mutex:
            mutex_slots[(tag["groupTitle"], mutex)] = tag
        else:
            selected_multi.append(tag)

    ordered = []
    for group in groups:
        title = group["title"]
        if title in selected_by_single_group:
            ordered.append(selected_by_single_group[title])
        for tag in selected_multi:
            if tag["groupTitle"] == title:
                ordered.append(tag)
        for (slot_title, _), tag in mutex_slots.items():
            if slot_title == title:
                ordered.append(tag)
    return ordered


def build_user_input(mode: str, case: dict, presets: dict) -> str:
    expanded = "，".join(tag["prompt"] for tag in expand_labels(mode, case["labels"], presets))
    return re.sub(r"\s+", " ", expanded).strip()


def extract_system_prompt(project: Path, mode: str) -> str:
    merged_doc = project / "docs" / "NSFW系统提示词.merged.md"
    doc = merged_doc if merged_doc.exists() else project / "docs" / "NSFW系统提示词.md"
    text = doc.read_text(encoding="utf-8")
    section = "## 2. 输出画面提示词（用于图生图）" if mode == "image_to_image" else "## 1. 输出画面提示词（用于文生图）"
    start = text.index(section)
    fence_start = text.index("```text", start) + len("```text")
    fence_end = text.index("```", fence_start)
    return text[fence_start:fence_end].strip()


def adapt_system_prompt_for_prompt_assist(system_prompt: str, mode: str) -> str:
    if mode == "image_to_image":
        replacement = (
            "最终提示词必须是一段完整自然的图生图编辑描述，不输出“修改目标、画风、封面类型、人物组合、场景、身体朝向、镜头构图、背景方向”等字段名。"
            "必须把画风、封面类型、人物组合、场景、身体朝向、镜头构图、背景方向这些信息维度自然融合进同一段文字；如果某项用户未指定，可以自然写成保留原图对应内容，且不得在后文改写成冲突内容。"
        )
        system_prompt = re.sub(
            r"最终提示词必须以明确的修改目标前缀开头，格式为“修改目标：.*?不得在后文改写成冲突内容。",
            replacement,
            system_prompt,
            flags=re.S,
        )
    else:
        replacement = (
            "最终提示词必须是一段完整自然的文生图画面描述，不输出“画风、封面类型、人物组合、人种/肤色、场景、身体朝向、镜头构图、背景方向”等字段名。"
            "必须把画风、封面类型、人物组合、人种/肤色、场景、身体朝向、镜头构图、背景方向这些信息维度自然融合进同一段文字；如果某项用户未指定，可以省略该项，且不得在后文改写成冲突内容。"
        )
        system_prompt = re.sub(
            r"最终提示词必须以明确的段落前缀开头，格式为“画风：.*?不得在后文改写成冲突内容。",
            replacement,
            system_prompt,
            flags=re.S,
        )
    system_prompt = system_prompt.replace(
        "固定结构：前缀；主体；姿态和器官归属；场景光影；质量约束。",
        "固定结构：保留与修改目标；主体；动作姿态；场景光影；质量约束。"
    )
    return system_prompt


def build_ollama_prompt(mode: str, system_prompt: str, user_input: str) -> str:
    task = "图生图修改提示词" if mode == "image_to_image" else "文生图画面提示词"
    return (
        f"请严格按照下面系统提示词生成{task}。\n"
        "只返回 JSON，不要解释，JSON 格式必须是 {\"prompt\":\"最终提示词\"}。\n\n"
        f"系统提示词：\n{system_prompt}\n\n"
        f"用户输入：\n{user_input}\n"
    )


def post_json(url: str, payload: dict, headers: dict | None, timeout: int) -> ApiResult:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req_headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if headers:
        req_headers.update(headers)
    req = request.Request(url, data=body, headers=req_headers, method="POST")
    started = time.perf_counter()
    try:
        with request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            latency = round((time.perf_counter() - started) * 1000)
            parsed = parse_json(raw)
            return ApiResult(True, resp.status, latency, extract_prompt(parsed), parsed, "")
    except error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        latency = round((time.perf_counter() - started) * 1000)
        parsed = parse_json(raw)
        return ApiResult(False, exc.code, latency, extract_prompt(parsed), parsed, f"HTTP {exc.code}")
    except Exception as exc:
        latency = round((time.perf_counter() - started) * 1000)
        return ApiResult(False, None, latency, "", None, repr(exc))


def parse_json(raw: str) -> object:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw[:2000]


def extract_prompt(parsed: object) -> str:
    if isinstance(parsed, str):
        return parsed.strip()
    if not isinstance(parsed, dict):
        return ""
    for key in ("prompt", "data", "result", "message", "content", "text"):
        value = parsed.get(key)
        if isinstance(value, str):
            return value.strip()
        if isinstance(value, dict):
            nested = extract_prompt(value)
            if nested:
                return nested
    response = parsed.get("response")
    if isinstance(response, str):
        try:
            decoded = json.loads(response)
        except json.JSONDecodeError:
            return response.strip()
        return extract_prompt(decoded) or response.strip()
    return ""


def rewrite_structured_to_paragraph(text: str) -> tuple[str, bool]:
    field_hits = re.findall(r"(修改目标|画风|封面类型|人物组合|场景|身体朝向|镜头构图|背景方向|细节要求)[：:]", text)
    if len(field_hits) < 3 and not text.lstrip().startswith("修改目标："):
        return text, False
    rewritten = text.strip()
    rewritten = re.sub(r"^\s*修改目标[：:]\s*", "", rewritten)
    replacements = [
        (r"(^|[；。])\s*画风[：:]\s*", r"\1修改为"),
        (r"(^|[；。])\s*封面类型[：:]\s*", r"\1采用"),
        (r"(^|[；。])\s*人物组合[：:]\s*", r"\1画面保持"),
        (r"(^|[；。])\s*人种/肤色[：:]\s*", r"\1人物呈现"),
        (r"(^|[；。])\s*场景[：:]\s*", r"\1置于"),
        (r"(^|[；。])\s*身体朝向[：:]\s*", r"\1人物姿态为"),
        (r"(^|[；。])\s*镜头构图[：:]\s*", r"\1镜头采用"),
        (r"(^|[；。])\s*背景方向[：:]\s*", r"\1背景"),
        (r"(^|[；。])\s*细节要求[：:]\s*", r"\1细节"),
    ]
    for pattern, repl in replacements:
        rewritten = re.sub(pattern, repl, rewritten)
    rewritten = re.sub(r"；\s*；+", "；", rewritten)
    rewritten = re.sub(r"([；。])\s+", r"\1", rewritten)
    rewritten = rewritten.strip("；。 \n") + "。"
    return rewritten, True


def normalize_final_prompt(text: str, input_text: str) -> tuple[str, list[str]]:
    fixes = []
    normalized = text.strip()
    normalized, rewrote_structured = rewrite_structured_to_paragraph(normalized)
    if rewrote_structured:
        fixes.append("rewrite_structured_fields_to_paragraph")
    if "只有一名成年女性" in input_text and not contains_any(normalized, ["单人", "一名"]):
        normalized = "保留原图单人成年女性主体，" + normalized
        fixes.append("restore_single_female_count_phrase")
    if "只有一名成年男性" in input_text and not contains_any(normalized, ["单人", "一名"]):
        normalized = "保留原图单人成年男性主体，" + normalized
        fixes.append("restore_single_male_count_phrase")
    if "正好两人" in input_text and not contains_any(normalized, ["两人", "两名", "双人", "两名成年角色"]):
        normalized = "保留原图两名成年角色，" + normalized
        fixes.append("restore_two_people_count_phrase")
    if "或" in normalized.replace("Logo", ""):
        normalized = normalized.replace("或", "、")
        fixes.append("replace_or_with_enumeration")
    for uncertain in ["可能", "可选", "例如", "比如", "或者", "若", "如果", "可以"]:
        if uncertain in normalized:
            normalized = normalized.replace(uncertain, "")
            fixes.append("remove_uncertain_wording")
    positive_replacements = {
        "不抢占人物主体": "服务人物主体",
        "不遮挡人物主体": "衬托人物主体",
        "不被背景抢占": "主体视觉清晰",
        "不改变": "保留",
        "不要改变": "保留",
        "不得": "",
        "禁止": "",
    }
    for source, target in positive_replacements.items():
        if source in normalized:
            normalized = normalized.replace(source, target)
            fixes.append("positive_rewrite_negative_phrase")
    if not contains_any(input_text, ["插入", "露出", "裸露", "去除衣物", "全身赤裸", "性器", "接触", "贴靠", "拥抱", "搭肩"]):
        patterns = [
            r"所有肢体接触、遮挡、暴露关系均基于原图主体延续，未指定露出、接触动作时，不新增具体性器部位、贴靠位置、插入行为。",
            r"不主动描写女性乳房、乳头、外阴、阴道口、阴蒂等具体性暴露部位，保持服装覆盖状态；",
            r"不得描述乳房、乳头、外阴、阴道口、阴蒂等具体性器部位的可见情况，",
            r"不提及任何身体接触、插入、贴靠、手部交叠关系。",
            r"所有身体接触、姿态关系及性器官暴露均按原图保持，未指定时不得新增。",
            r"不新增任何身体暴露部位、性器官、插入关系、亲密接触方式；",
            r"无穿插、贴靠、手部交叠动作；",
            r"不新增肢体接触、贴靠、搭肩、手部交叠、亲密动作关系。",
            r"不描述乳房、乳头、外阴、阴道口、阴蒂、阴茎、阴囊、肛门等身体暴露部位，不出现插入动作、贴靠姿态。",
            r"不新增任何人物互动、接触动作、亲密关系、身体暴露部位，[^；。]*具体性器描述；",
            r"避免引入人物互动接触动作、贴靠、搭肩、手部交叠、插入关系。",
            r"所有身体接触关系、器官暴露及动作细节均符合解剖逻辑，不新增任何亲密互动、贴靠、插入、服装类型变化。",
            r"不新增人物互动、肢体接触、亲密动作、服装类型、性器官暴露描述；",
            r"未主动描写具体身体暴露部位、性器官露出、插入动作、亲密接触关系。",
            r"不主动描述乳房、乳头、外阴、阴道口、阴蒂、阴囊、肛门、性器官的暴露情况，",
        ]
        for pattern in patterns:
            next_text = re.sub(pattern, "保持原图身体覆盖状态、人物姿态和相对位置，不新增未选动作。", normalized)
            if next_text != normalized:
                normalized = next_text
                fixes.append("collapse_unrequested_body_contact_negative_clause")
    outdoor_cleanup = [
        r"背景中不出现室内元素如床单、窗帘、屏风、家具、织物等，仅增强环境材质与空间纵深感；",
        r"背景中不出现室内元素如床单、窗帘、屏风、家具、室内光源；",
        r"不引入室内家具、床铺、窗帘、屏风等冲突内容。",
        r"背景为室外开放场景，自然光与夜景灯光结合，不包含室内元素如床铺、窗帘、屏风、织物、镜面、家具。",
        r"不替换为其他场景、引入床铺、窗帘、屏风、家具、织物、镜面、窗景、城市夜景、雨雾、花影、烛光、霓虹、远景光源等。",
    ]
    for pattern in outdoor_cleanup:
        next_text = re.sub(pattern, "背景只保留明确外景元素，增强环境材质与空间纵深感；", normalized)
        if next_text != normalized:
            normalized = next_text
            fixes.append("collapse_negated_indoor_scene_terms")
    if not contains_any(input_text, ["内衣", "衬衫", "裤子", "睡衣", "长裙", "礼服", "旗袍", "外套", "服装", "穿着"]):
        clothing_cleanup = [
            r"不要改变人物服装状态，保持原图穿着的[^；。]*。",
            r"保持原图穿着的[^；。]*。",
            r"不新增任何人物互动、接触动作、亲密关系、服装类型变化。",
        ]
        for pattern in clothing_cleanup:
            next_text = re.sub(pattern, "保持原图服装覆盖状态，不新增未选服装类型。", normalized)
            if next_text != normalized:
                normalized = next_text
                fixes.append("collapse_invented_clothing_terms")
    # Remove leftover negative clauses that enumerate forbidden visual tokens; image models may still attend to them.
    negative_enum_patterns = [
        r"不新增[^；。]*(乳房|乳头|外阴|阴道|阴蒂|阴茎|阴囊|肛门|性器|插入|贴靠|搭肩|手部交叠|床铺|窗帘|屏风|家具|衬衫|裤子)[^；。]*[；。]",
        r"不描述[^；。]*(乳房|乳头|外阴|阴道|阴蒂|阴茎|阴囊|肛门|性器|插入|贴靠|搭肩|手部交叠)[^；。]*[；。]",
        r"不包含[^；。]*(床铺|窗帘|屏风|家具|室内)[^；。]*[；。]",
        r"无[^；。]*(贴靠|手部交叠|插入|身体穿插)[^；。]*[；。]",
    ]
    for pattern in negative_enum_patterns:
        next_text = re.sub(pattern, "保持原图主体状态，不新增未选内容。", normalized)
        if next_text != normalized:
            normalized = next_text
            fixes.append("remove_negative_forbidden_token_enumeration")
    preserve_phrases = [
        ("保留原图人物脸部特征", ["保留原图人物脸部特征", "保留原图脸部特征"]),
        ("保留原图人物姿势", ["保留原图人物姿势", "保留原图姿势"]),
        ("保留原图背景布局", ["保留原图背景", "保留原图主要静物布局", "保留原图背景布局"]),
    ]
    for phrase, triggers in preserve_phrases:
        if any(trigger in input_text for trigger in triggers) and not any(trigger in normalized for trigger in triggers):
            if len(normalized.rstrip("；。") + "；" + phrase + "。") <= MAX_FINAL_PROMPT_CHARS:
                normalized = normalized.rstrip("；。") + "；" + phrase + "。"
                fixes.append("restore_required_preserve_phrase")
    normalized = normalized.replace("、正面遮挡", "")
    normalized = remove_negative_clauses(normalized)
    if len(normalized) > MAX_FINAL_PROMPT_CHARS:
        normalized = truncate_prompt_complete(normalized, MAX_FINAL_PROMPT_CHARS)
        fixes.append("truncate_to_450_chars")
    normalized = ensure_positive_quality_tail(normalized, MAX_FINAL_PROMPT_CHARS)
    normalized = re.sub(r"(不新增未选动作。){2,}", "不新增未选动作。", normalized)
    return normalized, fixes


def remove_negative_clauses(text: str) -> str:
    clauses = re.split(r"([；。])", text)
    kept = []
    negative_markers = ("不", "无", "未", "避免", "禁止", "不得", "不要", "防止", "排除")
    for index in range(0, len(clauses), 2):
        clause = clauses[index].strip()
        delim = clauses[index + 1] if index + 1 < len(clauses) else "；"
        if not clause:
            continue
        if any(marker in clause for marker in negative_markers):
            continue
        kept.append(clause + delim)
    result = "".join(kept).strip("；。 \n")
    return result + "。" if result else text


def truncate_prompt_complete(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    parts = re.split(r"(?<=[；。])", text)
    out = ""
    for part in parts:
        if len(out) + len(part) > limit:
            break
        out += part
    if out:
        return out.rstrip("；。") + "。"
    return text[:limit].rstrip("，；。") + "。"


def ensure_positive_quality_tail(text: str, limit: int) -> str:
    tail = "主体稳定，身份一致，结构自然，光影清晰。"
    if "主体稳定" in text or len(text) + len(tail) > limit:
        return text
    return text.rstrip("；。") + "；" + tail


def sanitize_case_specific_terms(text: str, case: dict) -> tuple[str, list[str]]:
    fixes = []
    sanitized = text
    case_hint = " ".join([case.get("reference", ""), case.get("role", ""), case.get("manual", "")])
    expects_male = contains_any(case_hint, ["成年男性", "单人成年男性", "男性角色"])
    expects_female = contains_any(case_hint, ["成年女性", "单人成年女性", "女性角色"])
    gender_unspecified = not expects_male and not expects_female
    if case.get("person_count") == "single" and "人物互动" in sanitized:
        sanitized = sanitized.replace("人物互动和身体姿态清晰", "主体动作姿态清晰")
        sanitized = sanitized.replace("人物互动与身体姿态清晰", "主体动作姿态清晰")
        sanitized = sanitized.replace("人物互动", "主体动作")
        fixes.append("rewrite_single_person_interaction_to_action_pose")
    if expects_male:
        gender_replacements = {
            "女人的": "男性的",
            "女人": "男性",
            "女性身体": "男性身体",
            "女性主体": "男性主体",
        }
        for source, target in gender_replacements.items():
            if source in sanitized:
                sanitized = sanitized.replace(source, target)
                fixes.append("rewrite_gender_conflict_to_male")
    if expects_female:
        gender_replacements = {
            "男人的": "女性的",
            "男人": "女性",
            "男性身体": "女性身体",
            "男性主体": "女性主体",
        }
        for source, target in gender_replacements.items():
            if source in sanitized:
                sanitized = sanitized.replace(source, target)
                fixes.append("rewrite_gender_conflict_to_female")
    if gender_unspecified and case.get("person_count") == "two":
        for source in ["女性身体", "男性身体", "女人的", "男人的", "女性", "男性", "女人", "男人"]:
            if source in sanitized:
                sanitized = sanitized.replace(source, "成年角色")
                fixes.append("rewrite_ungrounded_gender_to_adult_role")
    clothing_replacements = {
        "人物服饰": "人物轮廓",
        "服饰细节": "轮廓细节",
        "衣着细节": "身体轮廓细节",
        "衣服细节": "身体轮廓细节",
        "修改人物穿着": "强化人物轮廓",
    }
    for source, target in clothing_replacements.items():
        if source in sanitized:
            sanitized = sanitized.replace(source, target)
            fixes.append("rewrite_unselected_clothing_to_body_outline")
    sanitized = sanitized.replace("保留原图人物组合", "保留原图主体数量与身份")
    sanitized = sanitized.replace("保留参考图人物组合", "保留参考图主体数量与身份")
    if sanitized != text and "rewrite_single_person_interaction_to_action_pose" not in fixes:
        fixes.append("rewrite_placeholder_subject_phrase")
    return sanitized, fixes


def enforce_input_coverage(text: str, input_text: str) -> tuple[str, list[str]]:
    fixes = []
    covered = text
    prefixes = []
    if "动漫卡通" in input_text and "动漫" not in covered:
        prefixes.append("修改为动漫卡通风格")
        fixes.append("restore_anime_style_from_input")
    if "真实超写实" in input_text and "真实超写实" not in covered:
        prefixes.append("修改为真实超写实风格")
        fixes.append("restore_photoreal_style_from_input")
    if "电影级光影" in input_text and not contains_any(covered, ["电影", "高端写真"]):
        prefixes.append("增强电影级光影和高端写真质感")
        fixes.append("restore_cinematic_style_from_input")
    if "室外开放场景" in input_text and not contains_any(covered, ["室外", "屋顶", "露台", "庭院", "海边", "泳池", "街角", "阳台"]):
        prefixes.append("场景调整为室外-屋顶露台，玻璃栏杆、城市天际线、远景灯光")
        fixes.append("restore_outdoor_scene_from_input")
    if "室内私密场景" in input_text and not contains_any(covered, ["室内", "摄影棚", "公寓", "浴室", "更衣室", "包厢", "船舱"]):
        prefixes.append("场景调整为室内-私人摄影棚，柔光箱、深色背景布、反光板")
        fixes.append("restore_indoor_scene_from_input")
    if prefixes:
        covered = "，".join(prefixes) + "，" + covered
    if len(covered) > MAX_FINAL_PROMPT_CHARS:
        covered = truncate_prompt_complete(covered, MAX_FINAL_PROMPT_CHARS)
        fixes.append("truncate_after_input_coverage")
    return covered, fixes


def enforce_case_subject_anchor(text: str, case: dict, input_text: str) -> tuple[str, list[str]]:
    fixes = []
    anchored, sanitize_fixes = sanitize_case_specific_terms(text, case)
    fixes.extend(sanitize_fixes)
    anchored, coverage_fixes = enforce_input_coverage(anchored, input_text)
    fixes.extend(coverage_fixes)
    case_hint = " ".join([case.get("reference", ""), case.get("role", ""), case.get("manual", "")])
    if case.get("person_count") == "single" and not contains_any(anchored, ["单人", "一名"]):
        if contains_any(case_hint, ["成年男性", "单人成年男性", "一名成年男性", "男性角色"]):
            anchored = "保留原图单人成年男性主体，" + anchored
            fixes.append("restore_single_male_count_phrase")
        else:
            anchored = "保留原图单人成年女性主体，" + anchored
            fixes.append("restore_single_female_count_phrase")
    if case.get("person_count") == "two" and not contains_any(anchored, ["两人", "两名", "双人"]):
        anchored = "保留原图两名成年角色，" + anchored
        fixes.append("restore_two_people_count_phrase")
    if len(anchored) > MAX_FINAL_PROMPT_CHARS:
        anchored = truncate_prompt_complete(anchored, MAX_FINAL_PROMPT_CHARS)
        fixes.append("truncate_after_subject_anchor")
    return anchored, fixes


def call_ollama(config: dict, mode: str, system_prompt: str, user_input: str, timeout: int) -> ApiResult:
    payload = {
        "model": config["OLLAMA_MODEL"],
        "stream": False,
        "think": False,
        "format": {
            "type": "object",
            "additionalProperties": False,
            "properties": {"prompt": {"type": "string"}},
            "required": ["prompt"]
        },
        "prompt": build_ollama_prompt(mode, system_prompt, user_input),
        "options": {"temperature": 0.22, "top_p": 0.8, "num_ctx": 8192}
    }
    return post_json(config["OLLAMA_GENERATE_URL"], payload, None, timeout)


def call_current(config: dict, mode: str, user_input: str, timeout: int) -> ApiResult:
    headers = {}
    token = config.get("CURRENT_PROMPT_AUTH_TOKEN", "")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    payload = {"type": mode, "prompt": user_input}
    return post_json(config["CURRENT_PROMPT_API_URL"], payload, headers, timeout)


def contains_any(text: str, terms: list[str]) -> bool:
    return any(term in text for term in terms)


def final_label_choice(case: dict, candidates: list[str]) -> str | None:
    chosen = None
    for label in case.get("labels", []):
        if label in candidates:
            chosen = label
    return chosen


def pose_coverage(output: str, input_text: str, case: dict) -> dict:
    buckets = {
        "head_face": ["脸部", "面部", "头部", "视线", "眼神", "回头", "朝向镜头", "看向镜头", "侧脸", "背对镜头"],
        "torso_shoulder": ["躯干", "上身", "肩", "肩颈", "胸廓", "背部", "身体正对", "身体侧向", "身体背向"],
        "waist_pelvis": ["腰", "腰线", "腰臀", "臀", "骨盆", "重心", "髋", "转向"],
        "arms_hands": ["手臂", "手部", "双手", "手指", "前臂", "抬手", "扶", "自然下垂"],
        "legs_feet": ["腿", "膝", "脚", "站位", "步伐", "坐姿", "站姿", "跪姿", "仰躺", "侧躺"],
        "camera": ["镜头", "近景", "中景", "全身", "半身", "俯拍", "仰拍", "平视", "构图", "视角"],
    }
    hit_buckets = [name for name, terms in buckets.items() if contains_any(output, terms)]
    problems = []
    if len(hit_buckets) < 3:
        problems.append("pose_action_not_enough")
    concrete_pose_terms = [
        "微侧", "侧转", "转向", "前倾", "后仰", "垂落", "抬起", "扶", "托", "搭在", "支撑",
        "轻搭", "微屈", "半屈", "屈膝", "伸展", "站立", "落地", "面向", "朝向", "背对", "轻靠", "收拢", "对齐"
    ]
    if sum(1 for term in concrete_pose_terms if term in output) < 3:
        problems.append("pose_action_too_generic")
    orientation = final_label_choice(case, ["正面", "侧身", "背面"])
    if orientation == "正面" and not contains_any(output, ["正面", "朝向镜头", "看向镜头", "身体正对", "面对镜头", "躯干面对镜头"]):
        problems.append("front_pose_not_concrete")
    if orientation == "侧身" and not contains_any(output, ["侧身", "侧向", "侧脸", "身体侧向", "腰臀转向", "侧面轮廓"]):
        problems.append("side_pose_not_concrete")
    if orientation == "背面" and not contains_any(output, ["背面", "背对", "背部", "身体背向", "从背后", "背影"]):
        problems.append("back_pose_not_concrete")
    return {"hit_buckets": hit_buckets, "bucket_count": len(hit_buckets), "problems": problems}


def structured_output_problems(output: str) -> list[str]:
    problems = []
    if re.match(r"^\s*(修改目标|画风|封面类型|人物组合|场景|身体朝向|镜头构图|背景方向|细节要求)[：:]", output):
        problems.append("structured_field_prefix")
    field_hits = re.findall(r"(画风|封面类型|人物组合|场景|身体朝向|镜头构图|背景方向|细节要求)[：:]", output)
    if len(field_hits) >= 4:
        problems.append("too_structured_not_paragraph")
    return problems


def score(case: dict, input_text: str, output: str) -> dict:
    problems = []
    if len(output) > MAX_FINAL_PROMPT_CHARS:
        problems.append(f"over_length:{len(output)}>{MAX_FINAL_PROMPT_CHARS}")
    negative_markers = ["不", "无", "未", "避免", "禁止", "不得", "不要", "防止", "排除"]
    found_negative = [term for term in negative_markers if term in output]
    if found_negative:
        problems.append("negative_wording:" + ",".join(found_negative))
    required_any = case.get("required_any", [])
    missing = ["/".join(group) for group in required_any if not any(term in output for term in group)]
    if missing:
        problems.append("missing:" + ",".join(missing))

    paragraph_problems = structured_output_problems(output)
    problems.extend(paragraph_problems)

    candidate_patterns = [
        r"卧室/客厅/酒店房间",
        r"电影海报/小说封面",
        r"[\u4e00-\u9fa5]{2,12}、[\u4e00-\u9fa5]{2,12}、[\u4e00-\u9fa5]{2,12}等",
        r"（[^）]*(?:/|、|等)[^）]*）",
        r"\([^)]*(?:/|、|等)[^)]*\)",
    ]
    if any(re.search(pattern, output) for pattern in candidate_patterns):
        problems.append("candidate_list_or_slash_options")
    if contains_any(output, ["保留原图人物组合", "保留参考图人物组合"]):
        problems.append("placeholder_subject_phrase")

    pose = pose_coverage(output, input_text, case)
    problems.extend(pose["problems"])

    if case.get("person_count") == "single":
        multi_terms = ["双人", "两人", "两名", "多人", "第三人", "新增人物", "新增角色"]
        negated_multi = bool(re.search(r"(不|不得|禁止|不要|不能)(新增|加入|添加).{0,12}(人物|角色|第二|第三|多人|双人|两人)", output))
        quality_guard_multi = "多人主体混淆" in output and not contains_any(output.replace("多人主体混淆", ""), multi_terms)
        if contains_any(output, multi_terms) and not negated_multi and not quality_guard_multi:
            problems.append("single_person_risk")
        if not contains_any(output, ["单人", "一名", "只有一名", "不新增任何人物", "保持参考图人物数量"]):
            problems.append("single_person_not_explicit")
        if "人物互动" in output:
            problems.append("single_person_interaction_wording")

    if case.get("person_count") == "two":
        if not contains_any(output, ["两人", "两名", "双人", "正好两人"]):
            problems.append("two_people_not_explicit")
        if "单人构图" in output:
            problems.append("two_people_reduced_to_single")

    case_hint = " ".join([case.get("reference", ""), case.get("role", ""), case.get("manual", "")])
    expects_male = contains_any(case_hint, ["成年男性", "单人成年男性", "男性角色"])
    expects_female = contains_any(case_hint, ["成年女性", "单人成年女性", "女性角色"])
    if expects_male and contains_any(output, ["成年女性", "女人", "女性主体"]):
        problems.append("gender_conflict_expected_male")
    if expects_female and contains_any(output, ["成年男性", "男人", "男性主体"]):
        problems.append("gender_conflict_expected_female")

    for old_term, final_term in case.get("conflicts", []):
        transition_ok = bool(re.search(rf"(从|由|先|误选).{{0,16}}{old_term}.{{0,16}}(调整|转|改|切换|最终).{{0,16}}{final_term}", output))
        if old_term in output and final_term in output and not transition_ok:
            problems.append(f"conflict:{old_term}/{final_term}")

    explicit_body_or_contact = contains_any(input_text, ["插入", "露出", "裸露", "去除衣物", "全身赤裸", "性器", "接触", "贴靠", "拥抱", "搭肩"])
    if "插入" in output and "插入" not in input_text:
        problems.append("unrequested_relationship_action")
    body_detail_terms = ["乳头", "外阴", "阴道", "阴茎", "阴蒂", "性器", "插入位置", "贴靠", "搭肩", "拥抱", "手部交叠"]
    if not explicit_body_or_contact and contains_any(output, body_detail_terms):
        problems.append("unrequested_body_or_contact_detail")

    clothing_terms = ["睡衣", "内衣", "长裙", "礼服", "旗袍", "外套", "衬衫", "裤子", "服饰", "修改人物穿着"]
    if not contains_any(input_text, clothing_terms) and contains_any(output, clothing_terms):
        problems.append("invented_clothing")

    uncertain_terms = ["可能", "可选", "例如", "比如", "或者", "若", "如果", "可以"]
    found_uncertain = [term for term in uncertain_terms if term in output]
    output_without_logo = output.replace("Logo", "")
    if "或" in output_without_logo:
        found_uncertain.append("或")
    scene_choice_pattern = r"卧室、客厅或酒店房间|自然光、夜景灯光或露天环境"
    if found_uncertain or re.search(scene_choice_pattern, output):
        details = found_uncertain[:]
        if re.search(scene_choice_pattern, output):
            details.append("scene_or_background_choice")
        problems.append("uncertain_or_candidate_wording:" + ",".join(details))

    if "室外" in input_text:
        outdoor_anchors = ["街道", "屋顶", "露台", "庭院", "花园", "公园", "步道", "海边", "霓虹", "雨夜", "城市", "天际线", "路灯", "树影", "石板", "远景光源", "广场"]
        generic_only = "室外开放场景" in output and not contains_any(output, outdoor_anchors)
        if not contains_any(output, outdoor_anchors) or generic_only:
            problems.append("outdoor_scene_not_concrete")
        indoor_leaks = ["卧室", "客厅", "酒店房间", "床铺", "床单", "室内窗帘", "屏风"]
        if contains_any(output, indoor_leaks) and "保留原图背景" not in input_text:
            problems.append("outdoor_scene_contains_indoor_elements")

    if re.search(r"\b(?!Logo\b|HDR\b)[A-Za-z]{2,}\b", output):
        problems.append("english_leak")

    return {
        "pass": not problems,
        "missing_required": missing,
        "problems": problems,
        "length": len(output),
        "pose_coverage": pose,
        "paragraph_problems": paragraph_problems,
    }


def compact(result: ApiResult, case: dict, input_text: str) -> dict:
    final_prompt = result.text.strip() if result.text else ""
    return {
        "ok": result.ok,
        "status": result.status,
        "latency_ms": result.latency_ms,
        "error": result.error,
        "prompt": final_prompt,
        "original_prompt": result.text,
        "postprocess_fixes": [],
        "score": score(case, input_text, final_prompt) if final_prompt else {"pass": False, "problems": ["empty_output"], "length": 0}
    }


def raw_preview(raw: object) -> object:
    if isinstance(raw, dict):
        preview = {}
        for key, value in raw.items():
            if key == "context" and isinstance(value, list):
                preview[key] = f"<omitted {len(value)} token ids; see raw file>"
            elif isinstance(value, str) and len(value) > 2000:
                preview[key] = value[:2000] + "... <truncated; see raw file>"
            else:
                preview[key] = raw_preview(value)
        return preview
    if isinstance(raw, list):
        if len(raw) > 30:
            return [raw_preview(item) for item in raw[:30]] + [f"<omitted {len(raw) - 30} items; see raw file>"]
        return [raw_preview(item) for item in raw]
    if isinstance(raw, str) and len(raw) > 2000:
        return raw[:2000] + "... <truncated; see raw file>"
    return raw


def as_pretty_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2)


def file_uri(path: str) -> str:
    return Path(path).resolve().as_uri()


def html_block(text: str) -> str:
    return html.escape(text or "")


def render_html_report(report: dict, html_path: Path, raw_dir: Path) -> None:
    title = f"Prompt Assist API Compare - {report['mode']}"
    system_prompt = report.get("system_prompt", "")
    strict_rules = report.get("strict_output_rules", "")
    final_self_check = report.get("final_self_check", "")
    if not system_prompt:
        try:
            system_prompt = extract_system_prompt(Path(report["project"]), report["mode"])
        except Exception:
            system_prompt = "系统提示词未写入报告，且无法从项目文档重新读取。"
    prompt_panel_text = "\n\n".join(part for part in [system_prompt, strict_rules, final_self_check] if part)
    styles = """
    body { margin: 24px; font-family: Arial, "Microsoft YaHei", sans-serif; color: #202124; background: #fafafa; }
    h1 { font-size: 22px; margin: 0 0 12px; }
    h2 { font-size: 16px; margin: 18px 0 8px; }
    .meta, .muted { color: #5f6368; font-size: 13px; margin: 4px 0; }
    .summary { margin: 14px 0 18px; font-size: 13px; }
    .summary span { display: inline-block; margin: 0 14px 6px 0; }
    .toolbar { margin: 14px 0; }
    button { border: 1px solid #d8dee4; background: #fff; border-radius: 4px; padding: 7px 12px; cursor: pointer; }
    button:hover { background: #f6f8fa; }
    #systemPromptPanel { display: none; margin: 10px 0 18px; }
    .table-wrap { width: 100%; overflow-x: auto; }
    table.compare { width: 100%; min-width: 1600px; border-collapse: collapse; table-layout: fixed; background: white; }
    table.compare th, table.compare td { border: 1px solid #d8dee4; padding: 8px; vertical-align: top; font-size: 13px; }
    table.compare th { position: sticky; top: 0; background: #f6f8fa; z-index: 2; text-align: left; }
    .cell-input { width: 24%; }
    .cell-output { width: 22%; }
    .cell-check { width: 15%; }
    .cell-score { width: 13%; }
    .cell-result { width: 8%; text-align: center; }
    .pass { color: #137333; font-weight: 700; }
    .fail { color: #b3261e; font-weight: 700; }
    pre, .prompt { white-space: pre-wrap; word-break: break-word; background: #f6f8fa; border: 1px solid #d8dee4; padding: 8px; max-height: 170px; overflow: auto; margin: 6px 0; }
    code { background: #f1f3f4; border-radius: 4px; padding: 1px 4px; }
    details { margin-top: 8px; }
    summary { cursor: pointer; font-weight: 600; }
    .labels span { display: inline-block; border: 1px solid #d8dee4; border-radius: 999px; padding: 2px 7px; margin: 2px; background: #fff; font-size: 12px; }
    .metric { font-size: 12px; color: #5f6368; margin: 4px 0; }
    .result-pill { display: inline-block; border-radius: 999px; padding: 6px 12px; font-weight: 800; }
    .result-pill.pass { background: #e6f4ea; }
    .result-pill.fail { background: #fce8e6; }
    a { color: #0b57d0; text-decoration: none; }
    a:hover { text-decoration: underline; }
    """
    parts = [
        "<!doctype html><html><head><meta charset='utf-8'>",
        f"<title>{html.escape(title)}</title><style>{styles}</style></head><body>",
        f"<h1>{html.escape(title)}</h1>",
        f"<div class='meta'>Generated at {html.escape(report['generated_at'])} | Project: <code>{html.escape(report['project'])}</code></div>",
        f"<div class='meta'>Raw response directory: <a href='{file_uri(str(raw_dir))}'>{html.escape(str(raw_dir))}</a></div>",
        "<div class='toolbar'><button onclick=\"const p=document.getElementById('systemPromptPanel'); p.style.display=p.style.display==='none'?'block':'none';\">查看当前系统提示词</button></div>",
        f"<div id='systemPromptPanel'><h2>当前系统提示词</h2><pre>{html_block(prompt_panel_text)}</pre></div>",
        "<div class='summary'>",
    ]
    for provider, item in report["summary"].items():
        parts.append(
            f"<span><b>{html.escape(provider)}</b>: Passed {item['passed']}/{item['available']}</span>"
            f"<span>Pass rate <b>{item['pass_rate']}</b></span>"
            f"<span>Avg latency <b>{html.escape(str(item['avg_latency_ms']))} ms</b></span>"
            f"<span>Status <code>{html.escape(', '.join(item['statuses']))}</code></span>"
        )
    parts.append("</div>")

    provider_order = list(report.get("providers") or report.get("summary", {}).keys())
    ollama_provider = next((p for p in provider_order if p == "ollama"), "ollama")
    non_ollama_provider = next((p for p in provider_order if p != "ollama"), None)
    parts.append("<div class='table-wrap'><table class='compare'>")
    parts.append(
        "<tr>"
        "<th>输入文本</th>"
        "<th>ollama输出文本</th>"
        "<th>非ollama输出文本</th>"
        "<th>选项检测</th>"
        "<th>输出评分（Codex本地判定）</th>"
        "<th>是否合规的结果</th>"
        "</tr>"
    )

    for row in report["rows"]:
        case = row["case"]
        labels = "".join(f"<span>{html.escape(label)}</span>" for label in case.get("labels", []))
        ollama = row["providers"].get(ollama_provider, {})
        non_ollama = row["providers"].get(non_ollama_provider, {}) if non_ollama_provider else {}
        scored_providers = [item for item in [ollama, non_ollama] if item]
        all_pass = bool(scored_providers) and all(item.get("score", {}).get("pass") for item in scored_providers)
        result_class = "pass" if all_pass else "fail"
        parts.append("<tr>")
        parts.append(
            "<td class='cell-input'>"
            f"<b>{html.escape(case['id'])}</b>"
            f"<div class='labels'>{labels}</div>"
            f"<pre>{html_block(row['input'])}</pre>"
            "</td>"
        )
        def output_cell(provider_name: str | None, result: dict) -> str:
            if not result:
                label = provider_name or "non-ollama"
                return f"<td class='cell-output muted'>{html.escape(label)} not run</td>"
            score = result["score"]
            status_class = "pass" if score.get("pass") else "fail"
            raw_file = result.get("raw_response_file", "")
            raw_link = f"<a href='{file_uri(raw_file)}'>{html.escape(raw_file)}</a>" if raw_file else ""
            return (
                "<td class='cell-output'>"
                f"<div><b>{html.escape(provider_name or 'non-ollama')}</b> <span class='{status_class}'>{'PASS' if score.get('pass') else 'FAIL'}</span></div>"
                f"<div class='metric'>Status {html.escape(str(result.get('status')))} | {html.escape(str(result.get('latency_ms')))} ms | 主显示为本地评分文本</div>"
                f"<pre>{html_block(result.get('prompt', ''))}</pre>"
                f"<details><summary>接口原始输出 / raw 文件</summary><pre>{html_block(result.get('original_prompt', result.get('prompt', '')))}</pre><div class='metric'>{raw_link}</div></details>"
                "</td>"
            )
        parts.append(output_cell("ollama", ollama))
        parts.append(output_cell(non_ollama_provider, non_ollama))
        detection_chunks = []
        score_chunks = []
        for provider_name, result in [("ollama", ollama), (non_ollama_provider or "non-ollama", non_ollama)]:
            if not result:
                detection_chunks.append(f"<b>{html.escape(provider_name)}</b>: not run")
                score_chunks.append(f"<b>{html.escape(provider_name)}</b>: not run")
                continue
            score = result["score"]
            detection_chunks.append(
                f"<b>{html.escape(provider_name)}</b>"
                f"<div class='metric'>Missing: <code>{html.escape(', '.join(score.get('missing_required', [])) or 'none')}</code></div>"
                f"<div class='metric'>Problems: <code>{html.escape(', '.join(score.get('problems', [])) or 'none')}</code></div>"
            )
            score_chunks.append(
                f"<b>{html.escape(provider_name)}</b>"
                f"<div class='metric'>Judge: <code>Codex local rules</code></div>"
                f"<div class='metric'>Length: <code>{html.escape(str(score.get('length')))}</code></div>"
                f"<div class='metric'>Pose: <code>{html.escape(str(score.get('pose_coverage', {}).get('bucket_count', 0)))}/6</code> "
                f"{html.escape(', '.join(score.get('pose_coverage', {}).get('hit_buckets', [])) or 'none')}</div>"
                f"<div class='metric'>Latency: <code>{html.escape(str(result.get('latency_ms')))} ms</code></div>"
                f"<div class='metric'>Fixes: <code>{html.escape(', '.join(result.get('postprocess_fixes', [])) or 'none')}</code></div>"
            )
        parts.append(f"<td class='cell-check'>{'<hr>'.join(detection_chunks)}</td>")
        parts.append(f"<td class='cell-score'>{'<hr>'.join(score_chunks)}</td>")
        parts.append(
            "<td class='cell-result'>"
            f"<span class='result-pill {result_class}'>{'合规' if all_pass else '不合规'}</span>"
            "<details><summary>Raw API preview</summary>"
        )
        for provider_name, result in [("ollama", ollama), (non_ollama_provider or "non-ollama", non_ollama)]:
            if result:
                parts.append(
                    f"<b>{html.escape(provider_name)}</b>"
                    f"<pre>{html_block(as_pretty_json(result.get('raw_response_preview')))}</pre>"
                )
        parts.append(
                "</details>"
                "</td>"
        )
        parts.append("</tr>")

    parts.append("</table></div>")

    parts.append("</body></html>")
    html_path.write_text("\n".join(parts), encoding="utf-8")


def load_cases(path: str | None, mode: str) -> list[dict]:
    if path:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    return DEFAULT_I2I_CASES if mode == "image_to_image" else DEFAULT_T2I_CASES


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["image_to_image", "text_to_image"], default="image_to_image")
    parser.add_argument("--project", default=None)
    parser.add_argument("--providers", default="ollama,current", help="comma-separated: ollama,current")
    parser.add_argument("--cases", default=None, help="JSON case file")
    parser.add_argument("--out-dir", default=None)
    parser.add_argument("--render-html-only", default=None, help="Render an existing JSON report to HTML without API calls")
    args = parser.parse_args()

    if args.render_html_only:
        report_path = Path(args.render_html_only)
        report = json.loads(report_path.read_text(encoding="utf-8"))
        html_path = report_path.with_suffix(".html")
        raw_dir = report_path.with_suffix("")
        render_html_report(report, html_path, raw_dir)
        print(f"html_report={html_path}")
        return 0

    config = load_env(ENV_PATH)
    project = Path(args.project or config.get("DEFAULT_PROJECT", r"C:\Project\comfyui-3"))
    timeout = int(config.get("REQUEST_TIMEOUT_SECONDS", "180"))
    providers = [p.strip() for p in args.providers.split(",") if p.strip()]
    presets = load_presets()
    cases = load_cases(args.cases, args.mode)
    source_system_prompt = extract_system_prompt(project, args.mode)
    system_prompt = source_system_prompt

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_root = Path(args.out_dir) if args.out_dir else project / "reports"
    raw_dir = out_root / f"prompt_assist_api_compare_{args.mode}_{stamp}"
    raw_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    for case in cases:
        input_text = build_user_input(args.mode, case, presets)
        row = {"case": case, "input": input_text, "providers": {}}
        print(f"== {case['id']} ==")
        if "ollama" in providers:
            result = call_ollama(config, args.mode, system_prompt, input_text, timeout)
            row["providers"]["ollama"] = compact(result, case, input_text)
            raw_file = raw_dir / f"{case['id']}.ollama.raw.json"
            raw_file.write_text(json.dumps(result.raw, ensure_ascii=False, indent=2), encoding="utf-8")
            row["providers"]["ollama"]["raw_response_file"] = str(raw_file)
            row["providers"]["ollama"]["raw_response_preview"] = raw_preview(result.raw)
            print(f"ollama: status={result.status} pass={row['providers']['ollama']['score']['pass']} latency={result.latency_ms}ms")
        if "current" in providers:
            result = call_current(config, args.mode, input_text, timeout)
            row["providers"]["current"] = compact(result, case, input_text)
            raw_file = raw_dir / f"{case['id']}.current.raw.json"
            raw_file.write_text(json.dumps(result.raw, ensure_ascii=False, indent=2), encoding="utf-8")
            row["providers"]["current"]["raw_response_file"] = str(raw_file)
            row["providers"]["current"]["raw_response_preview"] = raw_preview(result.raw)
            print(f"current: status={result.status} pass={row['providers']['current']['score']['pass']} latency={result.latency_ms}ms")
        rows.append(row)

    summary = {}
    for provider in providers:
        provider_rows = [row["providers"][provider] for row in rows if provider in row["providers"]]
        available = [row for row in provider_rows if row["ok"] and row["prompt"]]
        passed = [row for row in available if row["score"]["pass"]]
        summary[provider] = {
            "cases": len(provider_rows),
            "available": len(available),
            "passed": len(passed),
            "pass_rate": round(len(passed) / len(available), 3) if available else 0,
            "avg_latency_ms": round(sum(row["latency_ms"] for row in available) / len(available)) if available else None,
            "statuses": sorted({str(row["status"]) for row in provider_rows})
        }

    report = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "mode": args.mode,
        "project": str(project),
        "providers": providers,
        "current_auth_token_provided": bool(config.get("CURRENT_PROMPT_AUTH_TOKEN")),
        "system_prompt": system_prompt,
        "source_system_prompt": source_system_prompt,
        "strict_output_rules": "",
        "final_self_check": "",
        "summary": summary,
        "rows": rows
    }
    report_path = out_root / f"prompt_assist_api_compare_{args.mode}_{stamp}.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    html_path = out_root / f"prompt_assist_api_compare_{args.mode}_{stamp}.html"
    render_html_report(report, html_path, raw_dir)
    print(f"report={report_path}")
    print(f"html_report={html_path}")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
