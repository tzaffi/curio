import json
import os
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from curio.cli import app
from curio.llm_caller import (
    KeyringSecretStore,
    LlmCallerError,
    ProviderName,
    SdkOpenAiApiTransport,
    SubprocessCodexCliRunner,
    build_llm_caller_client,
)
from curio.translate import Block, TranslationError, TranslationRequest
from live_smoke_helpers import (
    SmokeCase,
    build_smoke_translation_service,
    redacted_caller_summary,
    select_codex_smoke_caller,
    write_smoke_artifacts,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO_ROOT / "config.example.codex_cli.json"
SMOKE_ROOT = REPO_ROOT / "tmp" / "translate-smoke"
LIVE_OPERATOR_GUIDANCE = (
    "Live Codex CLI smoke test failed. Confirm CURIO_LIVE_CODEX_CLI_TESTS=1, "
    "`codex` is installed, Codex CLI is logged in with ChatGPT auth, network access is available, "
    "and config.example.codex_cli.json contains the selected llm_callers.NAME."
)
CODEX_SMOKE_CALLERS = (
    "translator_codex_gpt_54_mini",
    "translator_codex_gpt_54",
    "translator_codex_gpt_55",
)


@dataclass(frozen=True, slots=True)
class LiveSmokeCase:
    smoke_case: SmokeCase
    source_language_hint: str | None
    translation_required: bool


LIVE_SMOKE_CASES = (
    LiveSmokeCase(
        smoke_case=SmokeCase(
            case_id="Z-CN-01",
            source_text=(
                "目前用过最好用的 Hermes WebUI，把会话管理、工作区文件浏览、自动化任务、长期记忆、多 Profiles "
                "等常用能力都搬进了浏览器。你在 TUI 和 Telegram 里的会话，也可以直接在 Web 里无缝续聊。\n\n"
                "对我来说最爽的是：可以随时切换工作目录和 Profiles。我建了几个 Profiles 当成不同的 AI 员工，按需切换，"
                "避免所有记忆和 skills 都堆在一个 Profile 里，把上下文搞得一团糟。\n\n"
                "这个项目本身只是纯 UI 层，对接你现有的 Hermes 服务，数据都还在原来的 Hermes Agent 机器上。\n\n"
                "如果 Hermes 装在本机，一条命令就能启动 WebUI；如果装在远程服务器，就用 SSH 隧道连过来：本机执行\n"
                "ssh -N -L 8787:127.0.0.1:8787 user@your.server.com\n"
                "然后浏览器打开 http://localhost:8787 即可。\n\n"
                "macOS 上还可以配合这个用 Swift 写的 3M 小客户端，体验更好："
                "https://github.com/hermes-webui/hermes-swift-mac \n\n"
                "项目地址：https://github.com/nesquena/hermes-webui \n"
                "作者：\n"
                "@nesquena"
            ),
            expected_translation_intent=(
                "Translate into natural English while preserving commands, URLs, product names, and the handle."
            ),
            preservation_requirements=(
                "ssh -N -L 8787:127.0.0.1:8787 user@your.server.com",
                "http://localhost:8787",
                "https://github.com/hermes-webui/hermes-swift-mac",
                "https://github.com/nesquena/hermes-webui",
                "@nesquena",
            ),
        ),
        source_language_hint="zh",
        translation_required=True,
    ),
    LiveSmokeCase(
        smoke_case=SmokeCase(
            case_id="Z-CN-02",
            source_text=(
                "谷歌 Gemini 团队主管 Addy Osmani 最近开源了一个叫 Agent Skills 的项目，短时间内在 GitHub 上拿到了 "
                "18000 多个 Star，热度很高。\n\n"
                "这个项目做的事情说起来也不复杂：把资深工程师多年积累的工作流程和开发规范，整理成一套标准化的技能库，"
                "让 AI 编程助手在写代码的每个环节都能按照统一的高标准来执行。你可以理解为，它给 AI 配了一本老工程师的操作手册。\n\n"
                "整套技能库围绕软件开发的完整生命周期来设计，从最早的需求定义，到规划、构建、验证、评审，一直到最后的发布上线，"
                "六个阶段总共包含 20 个核心技能。每个阶段该做什么、该注意什么，都有对应的规范。\n\n"
                "用起来也很直观，项目提供了 7 个触发命令。比如输入 /spec 就开始写需求文档，/plan 自动拆解任务，"
                "/build 进入编码阶段，/test 跑测试，/ship 走部署流程。每个命令背后会自动调用相关的技能组合，不需要你手动一个个去配置。\n\n"
                "兼容性方面，目前支持 Claude Code、Gemini CLI、Codex、Cursor 这些主流的 AI 编程工具，覆盖面已经很广了。\n\n"
                "如果你已经在日常开发中用上了 AI 辅助工具，可以试试把这套 Skills 接进去，看看交付质量能不能再上一个台阶。\n\n"
                "传送门："
            ),
            expected_translation_intent=(
                "Translate into clear English while preserving tool names, numerals, and slash commands."
            ),
            preservation_requirements=(
                "Agent Skills",
                "18000",
                "/spec",
                "/plan",
                "/build",
                "/test",
                "/ship",
                "Claude Code",
                "Gemini CLI",
                "Codex",
                "Cursor",
            ),
        ),
        source_language_hint="zh",
        translation_required=True,
    ),
    LiveSmokeCase(
        smoke_case=SmokeCase(
            case_id="Z-EN-01",
            source_text=(
                "It happened.\n\n"
                "An open weights model just dropped that benchmarks higher than Opus 4.6 is out\n\n"
                "If you have 2 Mac Studios w/ 512gb, you can run Opus 4.6 level intelligence completely for free on your desk\n\n"
                "I warned you this would happen months ago. Now Mac Studios and Mac Minis are sold out\n\n"
                "The next Mac Studio has been delayed until Q3/Q4. The price will be significantly higher\n\n"
                "I told you this was going to happen. Intelligence explosion. Hardware bottleneck. Increased efficiency\n\n"
                "Luckily I picked up 2 Mac Studio 512gbs, 2 Mac Minis, and a DGX Spark\n\n"
                "I will be loading this up in the next couple of days and will have completely private super intelligence running for me 24/7\n\n"
                "I’m telling you right now by end of year we will have a local version of Mythos. It’s 100% guaranteed\n\n"
                "You called me crazy but every single prediction I’ve made has turned out to be true\n\n"
                "These models will only get more efficient and require less hardware. But that hardware is only going to get more expensive\n\n"
                "Local/open source is so obviously the future and if you’re still denying this now you are delusional"
            ),
            expected_translation_intent="Treat as English and leave untranslated without normalizing claims or tone.",
            preservation_requirements=("Opus 4.6", "Mac Studios", "Mac Minis", "DGX Spark", "Mythos"),
        ),
        source_language_hint="en",
        translation_required=False,
    ),
    LiveSmokeCase(
        smoke_case=SmokeCase(
            case_id="Z-KO-01",
            source_text=(
                "개인으로 사용중인 로컬LLM 세팅 공유:\n\n"
                "장비 : MacStudio M2 Ultra 64gb\n\n"
                "모델 온로드 \n"
                "- SuperQwen3.6 35b mlx 4bit (90tok/s)\n"
                "- Ernie Image Turbo (이미지 생성모델)\n\n"
                "Hermes Agent + MLX-LM\n\n"
                "+ GPT Codex (코딩), Gemini (대화, 이미지)"
            ),
            expected_translation_intent="Translate Korean portions while preserving mixed English model and tool names.",
            preservation_requirements=(
                "MacStudio M2 Ultra 64gb",
                "SuperQwen3.6 35b mlx 4bit",
                "90tok/s",
                "Ernie Image Turbo",
                "Hermes Agent + MLX-LM",
                "GPT Codex",
                "Gemini",
            ),
        ),
        source_language_hint="ko",
        translation_required=True,
    ),
    LiveSmokeCase(
        smoke_case=SmokeCase(
            case_id="Z-AR-01",
            source_text=(
                'انتهت حجة "ما عندي كرت شاشة قوي عشان أشغل ذكاء اصطناعي محلي".\n\n'
                "علي بابا نزلت موديل Qwen3.6 بهندسة MoE. حجمه الكلي 35B (يعطيك ذكاء عالي جداً)، "
                "لكن وقت الـ Inference يستهلك 3B فقط! \n"
                "يعني أداء Enterprise على جهازك الشخصي، وسرعة خرافية في كتابة الكود. \n\n"
                "الـ Local Agents جالسة تدمر الـ Cloud APIs أسرع مما توقعنا."
            ),
            expected_translation_intent=(
                "Translate colloquial Arabic into idiomatic English while preserving English technical terms and numbers."
            ),
            preservation_requirements=("Qwen3.6", "MoE", "35B", "3B", "Inference", "Enterprise", "Local Agents", "Cloud APIs"),
        ),
        source_language_hint="ar",
        translation_required=True,
    ),
    LiveSmokeCase(
        smoke_case=SmokeCase(
            case_id="Z-HE-01",
            source_text=(
                "תודה ללוחמים שלנו שפועלים בשטח. שתהיה להם שבת שלום, כולנו מתפללים עבורם. "
                "אנחנו נביא גם ביטחון וגם שלום - ונחזיר את הביטחון לתושבי הצפון."
            ),
            expected_translation_intent=(
                "Translate accurately into English without adding context, softening, or intensifying political language."
            ),
            preservation_requirements=("security", "peace", "residents of the north"),
        ),
        source_language_hint="he",
        translation_required=True,
    ),
    LiveSmokeCase(
        smoke_case=SmokeCase(
            case_id="Z-HE-02",
            source_text=(
                "פרפורי הגסיסה הכי ארוכים בהסטוריה. \n"
                "התולעים מכרסמות אותך בעודי מפרפר, \n"
                "המיץ מהריקבון נוזל לך , \n"
                "תחנת המוות עולה ממך\n"
                "ואוכלי הנבלות חגים סביבך מנסים לנגוס לפני שהתולעים לא ישאירו גרגר ממך. \n"
                "אנחנו\n"
                "עם ישראל \n"
                "מבטיחים לך\n"
                "שלעולם לא נשכח\n"
                "ולא נסלח\n"
                "ואת הקבר שלך נדאג למרוח בחרא כמו שאתה"
            ),
            expected_translation_intent=(
                "Translate accurately into English while preserving abusive and graphic tone without sanitizing or escalating."
            ),
            preservation_requirements=("graphic tone", "profanity", "we will never forget", "we will not forgive"),
        ),
        source_language_hint="he",
        translation_required=True,
    ),
    LiveSmokeCase(
        smoke_case=SmokeCase(
            case_id="C-JA-01",
            source_text="明日 10:00 JST に v2.1 を公開します。README.md と /deploy を確認してね 🚀 #Hermes https://example.com/release",
            expected_translation_intent=(
                "Translate Japanese into concise English while preserving release metadata, emoji, hashtag, and URL."
            ),
            preservation_requirements=("10:00 JST", "v2.1", "README.md", "/deploy", "🚀", "#Hermes", "https://example.com/release"),
        ),
        source_language_hint="ja",
        translation_required=True,
    ),
    LiveSmokeCase(
        smoke_case=SmokeCase(
            case_id="C-HI-01",
            source_text=(
                "kal PR #482 merge mat करना; tests flaky हैं, पहले uv run pytest tests/test_translate.py -q चलाओ "
                "और फिर deploy_notes.md update करो."
            ),
            expected_translation_intent=(
                "Translate Hindi/Hinglish into English while preserving PR number, command, file path, and imperative intent."
            ),
            preservation_requirements=("PR #482", "uv run pytest tests/test_translate.py -q", "deploy_notes.md"),
        ),
        source_language_hint="hi",
        translation_required=True,
    ),
    LiveSmokeCase(
        smoke_case=SmokeCase(
            case_id="C-ES-01",
            source_text='@maria dijo: "No traduzcas el endpoint /v1/chat/completions"; revisa https://api.example.dev antes del viernes.',
            expected_translation_intent=(
                "Translate Spanish into English while preserving quote boundaries, handle, endpoint, URL, and deadline."
            ),
            preservation_requirements=("@maria", '"No traduzcas el endpoint /v1/chat/completions"', "https://api.example.dev", "viernes"),
        ),
        source_language_hint="es",
        translation_required=True,
    ),
)


@pytest.fixture(scope="session")
def live_smoke_run_root() -> Path:
    run_id = os.environ.get("CURIO_TRANSLATE_SMOKE_RUN_ID")
    if run_id is None:
        timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
        run_id = f"{timestamp}-{_short_git_sha()}"
    run_root = SMOKE_ROOT / run_id
    run_root.mkdir(parents=True, exist_ok=True)
    (run_root / "schemas").mkdir(parents=True, exist_ok=True)
    _write_manifest(run_root)
    return run_root


@pytest.mark.live_codex_cli
@pytest.mark.parametrize("case", LIVE_SMOKE_CASES, ids=lambda case: case.smoke_case.case_id)
@pytest.mark.parametrize("caller", CODEX_SMOKE_CALLERS)
def test_live_codex_cli_translate_case_matrix(
    live_smoke_run_root: Path,
    case: LiveSmokeCase,
    caller: str,
) -> None:
    config, caller_config = select_codex_smoke_caller(CONFIG_PATH, caller)
    assert caller_config.pricing_config is not None
    service = build_smoke_translation_service(
        build_llm_caller_client(
            caller,
            config,
            secret_store=KeyringSecretStore(),
            codex_runner=SubprocessCodexCliRunner(),
            openai_transport=SdkOpenAiApiTransport(),
            codex_working_directory=REPO_ROOT,
            codex_output_schema_dir=live_smoke_run_root / "schemas",
        ),
        caller_config,
    )
    request = TranslationRequest(
        request_id=f"smoke-{case.smoke_case.case_id}-{caller}",
        blocks=[
            Block(
                block_id=1,
                name=case.smoke_case.case_id,
                source_language_hint=case.source_language_hint,
                text=case.smoke_case.source_text,
            )
        ],
        llm_caller=caller,
    )

    try:
        response = service.translate(request)
    except (LlmCallerError, TranslationError) as exc:
        pytest.fail(f"{LIVE_OPERATOR_GUIDANCE}\nOriginal error: {exc}")

    write_smoke_artifacts(
        run_root=live_smoke_run_root,
        case=case.smoke_case,
        caller_config=caller_config,
        request=request,
        response=response,
        pricing=caller_config.pricing_config,
    )
    assert response.request_id == request.request_id
    assert response.llm.provider == ProviderName.CODEX_CLI
    assert response.llm.model == caller_config.model
    assert len(response.blocks) == 1
    assert response.blocks[0].block_id == 1
    assert response.blocks[0].translation_required is case.translation_required
    if case.translation_required:
        assert response.blocks[0].translated_text is not None
    else:
        assert response.blocks[0].translated_text is None


@pytest.mark.live_codex_cli
def test_live_codex_cli_translate_cli_default_and_explicit_caller(live_smoke_run_root: Path) -> None:
    runner = CliRunner()
    default_result = runner.invoke(
        app,
        [
            "translate",
            "--config",
            str(CONFIG_PATH),
            "--json",
            "--source-language",
            "ja",
            "こんにちは",
        ],
    )
    explicit_result = runner.invoke(
        app,
        [
            "translate",
            "--config",
            str(CONFIG_PATH),
            "--json",
            "--source-language",
            "ja",
            "--llm-caller",
            "translator_codex_gpt_54_mini",
            "こんにちは",
        ],
    )

    _write_cli_result(live_smoke_run_root, "default-caller", default_result.output)
    _write_cli_result(live_smoke_run_root, "explicit-caller", explicit_result.output)
    _assert_cli_success(default_result.exit_code, default_result.output, "configured translate.llm_caller")
    _assert_cli_success(explicit_result.exit_code, explicit_result.output, "explicit --llm-caller")
    default_payload = json.loads(default_result.output)
    explicit_payload = json.loads(explicit_result.output)
    assert default_payload["llm"]["provider"] == ProviderName.CODEX_CLI
    assert explicit_payload["llm"]["provider"] == ProviderName.CODEX_CLI
    assert default_payload["llm"]["model"] == "gpt-5.4-mini"
    assert explicit_payload["llm"]["model"] == "gpt-5.4-mini"
    assert default_payload["blocks"][0]["translation_required"] is True
    assert explicit_payload["blocks"][0]["translation_required"] is True
    assert default_payload["blocks"][0]["translated_text"]
    assert explicit_payload["blocks"][0]["translated_text"]


def _write_manifest(run_root: Path) -> None:
    _, caller_config = select_codex_smoke_caller(CONFIG_PATH)
    caller_summaries: list[dict[str, Any]] = []
    for caller in CODEX_SMOKE_CALLERS:
        _, current_caller_config = select_codex_smoke_caller(CONFIG_PATH, caller)
        caller_summaries.append(redacted_caller_summary(current_caller_config))
    manifest = {
        "run_root": str(run_root),
        "git_commit": _git_commit(),
        "config_path": str(CONFIG_PATH.relative_to(REPO_ROOT)),
        "environment_opt_ins": {"CURIO_LIVE_CODEX_CLI_TESTS": os.environ.get("CURIO_LIVE_CODEX_CLI_TESTS")},
        "selected_cases": [case.smoke_case.case_id for case in LIVE_SMOKE_CASES],
        "selected_callers": list(CODEX_SMOKE_CALLERS),
        "default_caller": caller_config.name,
        "redacted_callers": caller_summaries,
    }
    (run_root / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def _write_cli_result(run_root: Path, name: str, output: str) -> None:
    cli_dir = run_root / "cli"
    cli_dir.mkdir(parents=True, exist_ok=True)
    (cli_dir / f"{name}.stdout").write_text(output, encoding="utf-8")


def _assert_cli_success(exit_code: int, output: str, label: str) -> None:
    if exit_code != 0:
        pytest.fail(f"{LIVE_OPERATOR_GUIDANCE}\nCLI path: {label}\nExit code: {exit_code}\nOutput:\n{output}")


def _short_git_sha() -> str:
    commit = _git_commit()
    return "nogit" if commit is None else commit[:12]


def _git_commit() -> str | None:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    commit = completed.stdout.strip()
    return commit or None
