You are the Checkpoint 8G textify evaluator for Curio.

Use only the JSON payload in this prompt. Do not browse. Do not run commands.
Judge OCR/text extraction fidelity, source-language preservation, suggested filenames/extensions/paths, multiple-file handling, warning quality, and cost.

Return Markdown only, with:

## Evaluator Summary

## Evaluator Output Matrix
| Case ID | Caller | Cost | Text Fidelity | Structure | Filenames | Instruction Following | Total | Preferred? | Warnings / Failures | Evaluator Notes |

## Final Recommendation

Payload:
```json
{
  "record_count": 72,
  "records": [
    {
      "caller": "textifier_codex_gpt_54_mini",
      "case_id": "C-IMG-TXT-01",
      "expected_output_format": "txt",
      "expected_status": "converted",
      "expected_suggested_paths": [
        "note.txt"
      ],
      "expected_textification_intent": "Extract a plain text note without inventing Markdown headings.",
      "fixture_metadata": {
        "mime_type": "image/png",
        "name": "plain-note.png",
        "path": "/Users/zeph/github/tzaffi/curio/tmp/textify-smoke/20260428-132551-09c3fa3c8f75/cases/C-IMG-TXT-01/fixtures/plain-note.png",
        "sha256": "c895ee9f1e59ac6618167a67d3439fc309ff0fbf4df05bc82da08d5a299b5c59",
        "source_language_hint": null
      },
      "ground_truth_text": "DEPLOY NOTE\nRUN UV SYNC\nTHEN MAKE CHECK\nKEEP README.MD OPEN",
      "model_importance": 1,
      "output_format": [
        "txt"
      ],
      "participates_in_model_ranking": true,
      "preservation_requirements": [
        "RUN UV SYNC",
        "MAKE CHECK",
        "README.MD"
      ],
      "rendered_textified_text": "DEPLOY NOTE\nRUN UV SYNC\nTHEN MAKE CHECK\nKEEP README.MD OPEN",
      "response_path": "runs/C-IMG-TXT-01/textifier_codex_gpt_54_mini/response.json",
      "response_warnings": [],
      "status": "converted",
      "suggested_files": [
        {
          "output_format": "txt",
          "suggested_path": "note.txt",
          "text": "DEPLOY NOTE\nRUN UV SYNC\nTHEN MAKE CHECK\nKEEP README.MD OPEN"
        }
      ],
      "usage": {
        "api_equivalent_cost_usd": 0.021207900000000002,
        "basis": "api_equivalent",
        "cached_input_price_per_million": 0.075,
        "cached_input_tokens": 22912,
        "completed_at": "2026-04-28T13:25:57.632389Z",
        "currency": "USD",
        "input_price_per_million": 0.75,
        "input_tokens": 24828,
        "metered_objects": [],
        "output_price_per_million": 4.5,
        "output_tokens": 193,
        "reasoning_tokens": 88,
        "started_at": "2026-04-28T13:25:51.582268Z",
        "thinking_seconds": null,
        "total_tokens": 25021,
        "wall_seconds": 6.050121
      }
    },
    {
      "caller": "textifier_codex_gpt_54_mini",
      "case_id": "C-IMG-CODE-01",
      "expected_output_format": "txt",
      "expected_status": "converted",
      "expected_suggested_paths": [
        "foo.py"
      ],
      "expected_textification_intent": "Extract the visible Python file and preserve the visible filename foo.py.",
      "fixture_metadata": {
        "mime_type": "image/png",
        "name": "foo.py.png",
        "path": "/Users/zeph/github/tzaffi/curio/tmp/textify-smoke/20260428-132551-09c3fa3c8f75/cases/C-IMG-CODE-01/fixtures/foo.py.png",
        "sha256": "eaf0ff4c9968e18d4ff4ea8692c524431a5e45a04030a76b9ba26bff79e68f96",
        "source_language_hint": null
      },
      "ground_truth_text": "FILE: foo.py\nDEF GREET(NAME):\n    PRINT(\"HOLA\", NAME)\nGREET(\"CURIO\")",
      "model_importance": 1,
      "output_format": [
        "txt"
      ],
      "participates_in_model_ranking": true,
      "preservation_requirements": [
        "foo.py",
        "DEF GREET(NAME):",
        "PRINT(\"HOLA\", NAME)",
        "GREET(\"CURIO\")"
      ],
      "rendered_textified_text": "FILE: FOO.PY\nDEF GREET(NAME):\n    PRINT(\"HOLA\", NAME)\nGREET(\"CURIO\")",
      "response_path": "runs/C-IMG-CODE-01/textifier_codex_gpt_54_mini/response.json",
      "response_warnings": [],
      "status": "converted",
      "suggested_files": [
        {
          "output_format": "txt",
          "suggested_path": "foo.py",
          "text": "FILE: FOO.PY\nDEF GREET(NAME):\n    PRINT(\"HOLA\", NAME)\nGREET(\"CURIO\")"
        }
      ],
      "usage": {
        "api_equivalent_cost_usd": 0.021195150000000003,
        "basis": "api_equivalent",
        "cached_input_price_per_million": 0.075,
        "cached_input_tokens": 22912,
        "completed_at": "2026-04-28T13:26:04.828834Z",
        "currency": "USD",
        "input_price_per_million": 0.75,
        "input_tokens": 24847,
        "metered_objects": [],
        "output_price_per_million": 4.5,
        "output_tokens": 187,
        "reasoning_tokens": 72,
        "started_at": "2026-04-28T13:25:57.673976Z",
        "thinking_seconds": null,
        "total_tokens": 25034,
        "wall_seconds": 7.154858
      }
    },
    {
      "caller": "textifier_codex_gpt_54_mini",
      "case_id": "C-IMG-CODE-02",
      "expected_output_format": "txt",
      "expected_status": "converted",
      "expected_suggested_paths": [
        "hello_curio.py"
      ],
      "expected_textification_intent": "Extract Python code and infer a safe .py filename from the script purpose.",
      "fixture_metadata": {
        "mime_type": "image/png",
        "name": "python-script-no-name.png",
        "path": "/Users/zeph/github/tzaffi/curio/tmp/textify-smoke/20260428-132551-09c3fa3c8f75/cases/C-IMG-CODE-02/fixtures/python-script-no-name.png",
        "sha256": "06ae9ca9570cdac8b591816c2f31d8ee526596d7845c7fa652c659b81affc484",
        "source_language_hint": null
      },
      "ground_truth_text": "DEF HELLO_CURIO():\n    RETURN \"HELLO CURIO\"\nPRINT(HELLO_CURIO())",
      "model_importance": 1,
      "output_format": [
        "txt"
      ],
      "participates_in_model_ranking": true,
      "preservation_requirements": [
        "HELLO_CURIO",
        "RETURN \"HELLO CURIO\"",
        "PRINT(HELLO_CURIO())"
      ],
      "rendered_textified_text": "DEF HELLO_CURIO():\n    RETURN \"HELLO CURIO\"\nPRINT(HELLO_CURIO())",
      "response_path": "runs/C-IMG-CODE-02/textifier_codex_gpt_54_mini/response.json",
      "response_warnings": [],
      "status": "converted",
      "suggested_files": [
        {
          "output_format": "txt",
          "suggested_path": "hello_curio.py",
          "text": "DEF HELLO_CURIO():\n    RETURN \"HELLO CURIO\"\nPRINT(HELLO_CURIO())"
        }
      ],
      "usage": {
        "api_equivalent_cost_usd": 0.0213204,
        "basis": "api_equivalent",
        "cached_input_price_per_million": 0.075,
        "cached_input_tokens": 22912,
        "completed_at": "2026-04-28T13:26:15.610876Z",
        "currency": "USD",
        "input_price_per_million": 0.75,
        "input_tokens": 24858,
        "metered_objects": [],
        "output_price_per_million": 4.5,
        "output_tokens": 213,
        "reasoning_tokens": 99,
        "started_at": "2026-04-28T13:26:04.872782Z",
        "thinking_seconds": null,
        "total_tokens": 25071,
        "wall_seconds": 10.738094
      }
    },
    {
      "caller": "textifier_codex_gpt_54_mini",
      "case_id": "C-IMG-MULTI-01",
      "expected_output_format": "txt",
      "expected_status": "converted",
      "expected_suggested_paths": [
        "scripts/setup.sh",
        "scripts/run.sh",
        "scripts/cleanup.sh"
      ],
      "expected_textification_intent": "Split three visible shell script snippets into three safe relative .sh files.",
      "fixture_metadata": {
        "mime_type": "image/png",
        "name": "three-shell-scripts.png",
        "path": "/Users/zeph/github/tzaffi/curio/tmp/textify-smoke/20260428-132551-09c3fa3c8f75/cases/C-IMG-MULTI-01/fixtures/three-shell-scripts.png",
        "sha256": "8e66a9bd958ff978ca977166b50e98e4644531fb7e2024f66679f15cfdd5c5cb",
        "source_language_hint": null
      },
      "ground_truth_text": "FILE: scripts/setup.sh\nECHO SETUP\n\nFILE: scripts/run.sh\nECHO RUN\n\nFILE: scripts/cleanup.sh\nECHO CLEANUP",
      "model_importance": 1,
      "output_format": [
        "sh",
        "sh",
        "sh"
      ],
      "participates_in_model_ranking": true,
      "preservation_requirements": [
        "scripts/setup.sh",
        "scripts/run.sh",
        "scripts/cleanup.sh",
        "ECHO CLEANUP"
      ],
      "rendered_textified_text": "echo setup\n\necho run\n\necho cleanup",
      "response_path": "runs/C-IMG-MULTI-01/textifier_codex_gpt_54_mini/response.json",
      "response_warnings": [],
      "status": "converted",
      "suggested_files": [
        {
          "output_format": "sh",
          "suggested_path": "scripts/setup.sh",
          "text": "echo setup"
        },
        {
          "output_format": "sh",
          "suggested_path": "scripts/run.sh",
          "text": "echo run"
        },
        {
          "output_format": "sh",
          "suggested_path": "scripts/cleanup.sh",
          "text": "echo cleanup"
        }
      ],
      "usage": {
        "api_equivalent_cost_usd": 0.02122365,
        "basis": "api_equivalent",
        "cached_input_price_per_million": 0.075,
        "cached_input_tokens": 22912,
        "completed_at": "2026-04-28T13:26:26.555821Z",
        "currency": "USD",
        "input_price_per_million": 0.75,
        "input_tokens": 24975,
        "metered_objects": [],
        "output_price_per_million": 4.5,
        "output_tokens": 172,
        "reasoning_tokens": 41,
        "started_at": "2026-04-28T13:26:15.664396Z",
        "thinking_seconds": null,
        "total_tokens": 25147,
        "wall_seconds": 10.891425
      }
    },
    {
      "caller": "textifier_codex_gpt_54_mini",
      "case_id": "C-IMG-POST-01",
      "expected_output_format": "markdown",
      "expected_status": "converted",
      "expected_suggested_paths": [
        "social-post.md"
      ],
      "expected_textification_intent": "Preserve a social post's handle, timestamp, URL, emoji marker, and source language.",
      "fixture_metadata": {
        "mime_type": "image/png",
        "name": "social-post-es.png",
        "path": "/Users/zeph/github/tzaffi/curio/tmp/textify-smoke/20260428-132551-09c3fa3c8f75/cases/C-IMG-POST-01/fixtures/social-post-es.png",
        "sha256": "b3d6f2d21646f9fab10a3b6b44e888db7845ee31af66630d8bc50fbbeba922f1",
        "source_language_hint": "es"
      },
      "ground_truth_text": "@MARIA 2026-04-27 10:15\nNO TRADUZCAS /V1/CHAT\nVISITA HTTPS://EXAMPLE.COM\nEMOJI: ROCKET",
      "model_importance": 1,
      "output_format": [
        "markdown"
      ],
      "participates_in_model_ranking": true,
      "preservation_requirements": [
        "@MARIA",
        "2026-04-27 10:15",
        "/V1/CHAT",
        "HTTPS://EXAMPLE.COM",
        "ROCKET"
      ],
      "rendered_textified_text": "@MARIA 2026-04-27 10:15\nNO TRADUZCAS ´V1/CHAT\nVISITA HTTPS://EXAMPLE.COM\nEMOJI: ROCKET",
      "response_path": "runs/C-IMG-POST-01/textifier_codex_gpt_54_mini/response.json",
      "response_warnings": [
        "OCR uncertainty on the symbol before `V1/CHAT`."
      ],
      "status": "converted",
      "suggested_files": [
        {
          "output_format": "markdown",
          "suggested_path": "social-post.md",
          "text": "@MARIA 2026-04-27 10:15\nNO TRADUZCAS ´V1/CHAT\nVISITA HTTPS://EXAMPLE.COM\nEMOJI: ROCKET"
        }
      ],
      "usage": {
        "api_equivalent_cost_usd": 0.021891900000000002,
        "basis": "api_equivalent",
        "cached_input_price_per_million": 0.075,
        "cached_input_tokens": 22912,
        "completed_at": "2026-04-28T13:26:46.710281Z",
        "currency": "USD",
        "input_price_per_million": 0.75,
        "input_tokens": 24876,
        "metered_objects": [],
        "output_price_per_million": 4.5,
        "output_tokens": 337,
        "reasoning_tokens": 196,
        "started_at": "2026-04-28T13:26:26.661417Z",
        "thinking_seconds": null,
        "total_tokens": 25213,
        "wall_seconds": 20.048864
      }
    },
    {
      "caller": "textifier_codex_gpt_54_mini",
      "case_id": "C-PDF-DOC-01",
      "expected_output_format": "markdown",
      "expected_status": "converted",
      "expected_suggested_paths": [
        "document.md"
      ],
      "expected_textification_intent": "Extract a one-page document with title, headings, paragraphs, and bullets.",
      "fixture_metadata": {
        "mime_type": "application/pdf",
        "name": "document-layout.pdf",
        "path": "/Users/zeph/github/tzaffi/curio/tmp/textify-smoke/20260428-132551-09c3fa3c8f75/cases/C-PDF-DOC-01/fixtures/document-layout.pdf",
        "sha256": "e04a909ad3499bb0f6252bc0eb6c765bbfbdb541d2b9d867341cdec7cbc1bbd0",
        "source_language_hint": null
      },
      "ground_truth_text": "Curio Release Plan\nGoals\n- Keep smoke tests opt-in\n- Preserve source language\nNext Steps\nRun make check",
      "model_importance": 1,
      "output_format": [
        "markdown"
      ],
      "participates_in_model_ranking": true,
      "preservation_requirements": [
        "Curio Release Plan",
        "Goals",
        "Keep smoke tests opt-in",
        "Run make check"
      ],
      "rendered_textified_text": "# Curio Release Plan\n\n## Goals\n\n- Keep smoke tests opt-in\n- Preserve source language\n\n## Next Steps\n\n- Run make check",
      "response_path": "runs/C-PDF-DOC-01/textifier_codex_gpt_54_mini/response.json",
      "response_warnings": [],
      "status": "converted",
      "suggested_files": [
        {
          "output_format": "markdown",
          "suggested_path": "document.md",
          "text": "# Curio Release Plan\n\n## Goals\n\n- Keep smoke tests opt-in\n- Preserve source language\n\n## Next Steps\n\n- Run make check"
        }
      ],
      "usage": {
        "api_equivalent_cost_usd": 0.15278385,
        "basis": "api_equivalent",
        "cached_input_price_per_million": 0.075,
        "cached_input_tokens": 174208,
        "completed_at": "2026-04-28T13:27:12.456726Z",
        "currency": "USD",
        "input_price_per_million": 0.75,
        "input_tokens": 179043,
        "metered_objects": [],
        "output_price_per_million": 4.5,
        "output_tokens": 1208,
        "reasoning_tokens": 253,
        "started_at": "2026-04-28T13:26:46.719780Z",
        "thinking_seconds": null,
        "total_tokens": 180251,
        "wall_seconds": 25.736946
      }
    },
    {
      "caller": "textifier_codex_gpt_54_mini",
      "case_id": "C-PDF-TABLE-01",
      "expected_output_format": "markdown",
      "expected_status": "converted",
      "expected_suggested_paths": [
        "table.md"
      ],
      "expected_textification_intent": "Extract a small table without swapping rows or columns.",
      "fixture_metadata": {
        "mime_type": "application/pdf",
        "name": "table-layout.pdf",
        "path": "/Users/zeph/github/tzaffi/curio/tmp/textify-smoke/20260428-132551-09c3fa3c8f75/cases/C-PDF-TABLE-01/fixtures/table-layout.pdf",
        "sha256": "766f1e57d76f62eb7a837862b1354f1c6714aa69a797c15f18bb635455333ec2",
        "source_language_hint": null
      },
      "ground_truth_text": "Service | Count | Status\nCodex | 3 | Ready\nDocAI | 1 | Punted\nOpenAI API | 0 | Punted",
      "model_importance": 1,
      "output_format": [
        "markdown"
      ],
      "participates_in_model_ranking": true,
      "preservation_requirements": [
        "Codex | 3 | Ready",
        "DocAI | 1 | Punted",
        "OpenAI API | 0 | Punted"
      ],
      "rendered_textified_text": "| Service | Count | Status |\n|---|---:|---|\n| Codex | 3 | Ready |\n| DocAI | 1 | Punted |\n| OpenAI API | 0 | Punted |",
      "response_path": "runs/C-PDF-TABLE-01/textifier_codex_gpt_54_mini/response.json",
      "response_warnings": [],
      "status": "converted",
      "suggested_files": [
        {
          "output_format": "markdown",
          "suggested_path": "table.md",
          "text": "| Service | Count | Status |\n|---|---:|---|\n| Codex | 3 | Ready |\n| DocAI | 1 | Punted |\n| OpenAI API | 0 | Punted |"
        }
      ],
      "usage": {
        "api_equivalent_cost_usd": 0.19724385,
        "basis": "api_equivalent",
        "cached_input_price_per_million": 0.075,
        "cached_input_tokens": 226688,
        "completed_at": "2026-04-28T13:27:49.772048Z",
        "currency": "USD",
        "input_price_per_million": 0.75,
        "input_tokens": 232409,
        "metered_objects": [],
        "output_price_per_million": 4.5,
        "output_tokens": 1319,
        "reasoning_tokens": 212,
        "started_at": "2026-04-28T13:27:12.466668Z",
        "thinking_seconds": null,
        "total_tokens": 233728,
        "wall_seconds": 37.30538
      }
    },
    {
      "caller": "textifier_codex_gpt_54_mini",
      "case_id": "C-IMG-RECEIPT-01",
      "expected_output_format": "markdown",
      "expected_status": "converted",
      "expected_suggested_paths": [
        "receipt.md"
      ],
      "expected_textification_intent": "Extract dense receipt-like labels, dates, amounts, and totals.",
      "fixture_metadata": {
        "mime_type": "image/png",
        "name": "receipt.png",
        "path": "/Users/zeph/github/tzaffi/curio/tmp/textify-smoke/20260428-132551-09c3fa3c8f75/cases/C-IMG-RECEIPT-01/fixtures/receipt.png",
        "sha256": "dacd233925e84d3f58cd4f21d6f9b967226de5d73e1723ce09d41e44a7aafb56",
        "source_language_hint": null
      },
      "ground_truth_text": "CURIO CAFE\nDATE 2026-04-27\nLATTE 4.50\nSANDWICH 8.25\nTOTAL 12.75",
      "model_importance": 1,
      "output_format": [
        "markdown"
      ],
      "participates_in_model_ranking": true,
      "preservation_requirements": [
        "2026-04-27",
        "LATTE 4.50",
        "SANDWICH 8.25",
        "TOTAL 12.75"
      ],
      "rendered_textified_text": "CURIO CAFE\nDATE 2026-04-27\nLATTE 4.50\nSANDWICH 8.25\nTOTAL 12.75",
      "response_path": "runs/C-IMG-RECEIPT-01/textifier_codex_gpt_54_mini/response.json",
      "response_warnings": [],
      "status": "converted",
      "suggested_files": [
        {
          "output_format": "markdown",
          "suggested_path": "receipt.md",
          "text": "CURIO CAFE\nDATE 2026-04-27\nLATTE 4.50\nSANDWICH 8.25\nTOTAL 12.75"
        }
      ],
      "usage": {
        "api_equivalent_cost_usd": 0.021270900000000002,
        "basis": "api_equivalent",
        "cached_input_price_per_million": 0.075,
        "cached_input_tokens": 22912,
        "completed_at": "2026-04-28T13:27:55.805111Z",
        "currency": "USD",
        "input_price_per_million": 0.75,
        "input_tokens": 24852,
        "metered_objects": [],
        "output_price_per_million": 4.5,
        "output_tokens": 203,
        "reasoning_tokens": 80,
        "started_at": "2026-04-28T13:27:49.788853Z",
        "thinking_seconds": null,
        "total_tokens": 25055,
        "wall_seconds": 6.016258
      }
    },
    {
      "caller": "textifier_codex_gpt_54_mini",
      "case_id": "C-IMG-NO-TEXT-01",
      "expected_output_format": "markdown",
      "expected_status": "no_text_found",
      "expected_suggested_paths": [],
      "expected_textification_intent": "Return no_text_found for an image with no readable text and do not invent alt text.",
      "fixture_metadata": {
        "mime_type": "image/png",
        "name": "no-readable-text.png",
        "path": "/Users/zeph/github/tzaffi/curio/tmp/textify-smoke/20260428-132551-09c3fa3c8f75/cases/C-IMG-NO-TEXT-01/fixtures/no-readable-text.png",
        "sha256": "519ad675a14d7e9b1658dfe5d2e175c4a4ad9f35d946f9e04185940e1a1eb818",
        "source_language_hint": null
      },
      "ground_truth_text": "",
      "model_importance": 1,
      "output_format": [],
      "participates_in_model_ranking": true,
      "preservation_requirements": [
        "no invented description",
        "compact warning"
      ],
      "rendered_textified_text": "",
      "response_path": "runs/C-IMG-NO-TEXT-01/textifier_codex_gpt_54_mini/response.json",
      "response_warnings": [],
      "status": "no_text_found",
      "suggested_files": [],
      "usage": {
        "api_equivalent_cost_usd": 0.02100915,
        "basis": "api_equivalent",
        "cached_input_price_per_million": 0.075,
        "cached_input_tokens": 22912,
        "completed_at": "2026-04-28T13:28:07.564807Z",
        "currency": "USD",
        "input_price_per_million": 0.75,
        "input_tokens": 24839,
        "metered_objects": [],
        "output_price_per_million": 4.5,
        "output_tokens": 147,
        "reasoning_tokens": 74,
        "started_at": "2026-04-28T13:27:55.835353Z",
        "thinking_seconds": null,
        "total_tokens": 24986,
        "wall_seconds": 11.729454
      }
    },
    {
      "caller": "textifier_codex_gpt_54_mini",
      "case_id": "R-IMG-DASH-01",
      "expected_output_format": "markdown",
      "expected_status": "converted",
      "expected_suggested_paths": [
        "claude-code-usage-dashboard.md"
      ],
      "expected_textification_intent": "Extract the dashboard title, filters, metric cards, charts, recent-session table, and visible numeric values into Markdown.",
      "fixture_metadata": {
        "mime_type": "image/jpeg",
        "name": "r-img-dash-01.jpg",
        "path": "/Users/zeph/github/tzaffi/curio/tmp/textify-smoke/20260428-132551-09c3fa3c8f75/cases/R-IMG-DASH-01/fixtures/r-img-dash-01.jpg",
        "sha256": "a74c7cb477b123bfc87dd97eb0c634786b6a4f537d387c2a96e5739d31d3118a",
        "source_language_hint": null
      },
      "ground_truth_text": "Claude Code Usage Dashboard\nSessions 440\nTurns 18.0K\nInput tokens 617.2K\nOutput tokens 4.75M\nCache read 1.95B\nEst. cost $1588.30",
      "model_importance": 9,
      "output_format": [
        "markdown"
      ],
      "participates_in_model_ranking": true,
      "preservation_requirements": [
        "Claude Code Usage Dashboard",
        "440",
        "18.0K",
        "617.2K",
        "4.75M",
        "$1588.30"
      ],
      "rendered_textified_text": "# Claude Code Usage Dashboard\n\nUpdated: 2026-04-07 20:56:27 · Auto-refresh in 30s\n\n## Models\n- `claude-opus-4-6`\n- `claude-sonnet-4-6`\n- `claude-haiku-4-5-20251001`\n- `All`\n- `None`\n\n## Range\n- `7d`\n- `30d`\n- `90d`\n- `All`\n\n## Metrics\n| Metric | Value | Note |\n|---|---:|---|\n| Sessions | 440 | last 30 days |\n| Turns | 18.0K | last 30 days |\n| Input Tokens | 617.2K | last 30 days |\n| Output Tokens | 4.75M | last 30 days |\n| Cache Read | 1.95B | from prompt cache |\n| Cache Creation | 74.66M | writes to prompt cache |\n| Est. Cost | $1588.30 | API pricing, Apr 2026 |\n\n## Daily Token Usage - Last 30 Days\nLegend: Input, Output, Cache Read, Cache Creation\n\nVisible x-axis dates:\n- 2026-03-08\n- 2026-03-10\n- 2026-03-14\n- 2026-03-16\n- 2026-03-18\n- 2026-03-20\n- 2026-03-22\n- 2026-03-24\n- 2026-03-26\n- 2026-03-28\n- 2026-03-30\n- 2026-04-01\n- 2026-04-03\n- 2026-04-05\n- 2026-04-07\n\nVisible y-axis labels:\n- 0\n- 100.00M\n- 200.00M\n- 300.00M\n- 400.00M\n- 500.00M\n- 600.00M\n- 700.00M\n- 800.00M\n\n## By Model\n- `claude-opus-4-6`\n- `claude-sonnet-4-6`\n- `claude-haiku-4-5-20251001`\n\n## Top Projects by Tokens\nLegend: Input, Output\n\nVisible projects:\n- Workspace/Editor\n- Artifacts/hassid\n- GitHub/SwarmProtocol\n- Dell/Desktop\n- ...e/agent-second-brain\n- worktrees/happy-wilson\n- worktrees/busy-curran\n- GitHub/Chatbot\n- ...rees/adoring-hermann\n- ...trees/trusting-raman\n\nVisible x-axis labels:\n- 0\n- 500.0K\n- 1.00M\n- 1.50M\n- 2.00M\n- 2.50M\n- 3.00M\n\n## Recent Sessions\n| Session | Project | Last Active | Duration | Model | Turns | Input | Output | Est. Cost |\n|---|---|---|---:|---|---:|---:|---:|---:|\n| 0d1902c1... | Dell/Desktop | 2026-04-07 17:09 | 7.8m | `claude-sonnet-4-6` | 22 | 734 | 16.4K | $0.8485 |\n",
      "response_path": "runs/R-IMG-DASH-01/textifier_codex_gpt_54_mini/response.json",
      "response_warnings": [
        "Some small chart labels and table text are partially cropped or low-resolution.",
        "The recent sessions section appears truncated; only the first row is clearly readable."
      ],
      "status": "converted",
      "suggested_files": [
        {
          "output_format": "markdown",
          "suggested_path": "claude-code-usage-dashboard.md",
          "text": "# Claude Code Usage Dashboard\n\nUpdated: 2026-04-07 20:56:27 · Auto-refresh in 30s\n\n## Models\n- `claude-opus-4-6`\n- `claude-sonnet-4-6`\n- `claude-haiku-4-5-20251001`\n- `All`\n- `None`\n\n## Range\n- `7d`\n- `30d`\n- `90d`\n- `All`\n\n## Metrics\n| Metric | Value | Note |\n|---|---:|---|\n| Sessions | 440 | last 30 days |\n| Turns | 18.0K | last 30 days |\n| Input Tokens | 617.2K | last 30 days |\n| Output Tokens | 4.75M | last 30 days |\n| Cache Read | 1.95B | from prompt cache |\n| Cache Creation | 74.66M | writes to prompt cache |\n| Est. Cost | $1588.30 | API pricing, Apr 2026 |\n\n## Daily Token Usage - Last 30 Days\nLegend: Input, Output, Cache Read, Cache Creation\n\nVisible x-axis dates:\n- 2026-03-08\n- 2026-03-10\n- 2026-03-14\n- 2026-03-16\n- 2026-03-18\n- 2026-03-20\n- 2026-03-22\n- 2026-03-24\n- 2026-03-26\n- 2026-03-28\n- 2026-03-30\n- 2026-04-01\n- 2026-04-03\n- 2026-04-05\n- 2026-04-07\n\nVisible y-axis labels:\n- 0\n- 100.00M\n- 200.00M\n- 300.00M\n- 400.00M\n- 500.00M\n- 600.00M\n- 700.00M\n- 800.00M\n\n## By Model\n- `claude-opus-4-6`\n- `claude-sonnet-4-6`\n- `claude-haiku-4-5-20251001`\n\n## Top Projects by Tokens\nLegend: Input, Output\n\nVisible projects:\n- Workspace/Editor\n- Artifacts/hassid\n- GitHub/SwarmProtocol\n- Dell/Desktop\n- ...e/agent-second-brain\n- worktrees/happy-wilson\n- worktrees/busy-curran\n- GitHub/Chatbot\n- ...rees/adoring-hermann\n- ...trees/trusting-raman\n\nVisible x-axis labels:\n- 0\n- 500.0K\n- 1.00M\n- 1.50M\n- 2.00M\n- 2.50M\n- 3.00M\n\n## Recent Sessions\n| Session | Project | Last Active | Duration | Model | Turns | Input | Output | Est. Cost |\n|---|---|---|---:|---|---:|---:|---:|---:|\n| 0d1902c1... | Dell/Desktop | 2026-04-07 17:09 | 7.8m | `claude-sonnet-4-6` | 22 | 734 | 16.4K | $0.8485 |\n"
        }
      ],
      "usage": {
        "api_equivalent_cost_usd": 0.025843650000000003,
        "basis": "api_equivalent",
        "cached_input_price_per_million": 0.075,
        "cached_input_tokens": 22912,
        "completed_at": "2026-04-28T13:28:19.815711Z",
        "currency": "USD",
        "input_price_per_million": 0.75,
        "input_tokens": 26281,
        "metered_objects": [],
        "output_price_per_million": 4.5,
        "output_tokens": 981,
        "reasoning_tokens": 76,
        "started_at": "2026-04-28T13:28:07.574942Z",
        "thinking_seconds": null,
        "total_tokens": 27262,
        "wall_seconds": 12.240769
      }
    },
    {
      "caller": "textifier_codex_gpt_54_mini",
      "case_id": "R-IMG-LLM-TABLE-01",
      "expected_output_format": "markdown",
      "expected_status": "converted",
      "expected_suggested_paths": [
        "local-llm-cheat-sheet.md"
      ],
      "expected_textification_intent": "Convert the dense local LLM cheat sheet into a Markdown table preserving model rows, weights, speed, context, use cases, and bottom line.",
      "fixture_metadata": {
        "mime_type": "image/jpeg",
        "name": "r-img-llm-table-01.jpg",
        "path": "/Users/zeph/github/tzaffi/curio/tmp/textify-smoke/20260428-132551-09c3fa3c8f75/cases/R-IMG-LLM-TABLE-01/fixtures/r-img-llm-table-01.jpg",
        "sha256": "9fc4f7a9c8958056c2aedac53d70614aeebfbffc64f1b9200b05a5eab1855de9",
        "source_language_hint": null
      },
      "ground_truth_text": "LOCAL LLM CHEAT SHEET\n128GB RAM\nQwen3.5-397B-A17B\nMistral Large 2411\nMiniMax-M2.7\nGLM-4.5-Air\nQwen3-VL-235B-A22B-Thinking\nBottom line: match it to your workflow.",
      "model_importance": 10,
      "output_format": [
        "markdown"
      ],
      "participates_in_model_ranking": true,
      "preservation_requirements": [
        "LOCAL LLM CHEAT SHEET",
        "128GB RAM",
        "Qwen3.5-397B-A17B",
        "MiniMax-M2.7",
        "Qwen3-VL-235B-A22B-Thinking",
        "Bottom line"
      ],
      "rendered_textified_text": "# Local LLM Cheat Sheet\n\n*April 24, 2026 • Mac Studio M-Ultra • Workstation Tier*\n\n## 128GB RAM\n\n### 1) General Purpose & All-Rounders\n\n| Model | Weights size | Speed | Context | Best pick | Best used for | Honest take |\n|---|---:|---|---|---|---|---|\n| Qwen3.5-397B-A17B UD-IQ1_M • Recommended<br>Qwen • Apache 2.0<br>LiveCodeBench 83.6 | 106.82 GB | Medium<br>397B total / 17B active MoE. | 262K<br>Native 262K context. | BEST OVERALL / GENERAL ASSISTANT | general assistant<br>hardest reasoning<br>research<br>complex agents | Best overall. Strongest all-rounder on 128GB for reasoning, research, and agentic work. |\n| Mistral Large 2411 Q4_K_M • Recommended<br>Mistral AI • MRL (research/non-commercial)<br>MMLU 84.0 • HumanEval 90.0<br>Multilingual SOTA • Fn calling native | 73.22 GB | Medium<br>Dense 123B at 4-bit. Heavier but still fast. | 128K<br>Best-in-class European multilingual. | BEST WRITING / MULTILINGUAL | creative writing<br>multilingual tasks<br>function calling<br>long-form prose | Excels on writing and multilingual tasks with strong function calling. Great for creative and business work. |\n\n### 2) Coding / Agent / Tool-Use Kings\n\n| Model | Weights size | Speed | Context | Best pick | Best used for | Honest take |\n|---|---:|---|---|---|---|---|\n| MiniMax-M2.7 UD-IQ2_XXS • Recommended<br>MiniMax • Apache 2.0<br>SWE-Bench Pro 56.2 • GPQA-D 77.7<br>SWE-Mult 76.5 | 65.38 GB | Fast<br>229B total / 10B active MoE. Low-latency agent loops. | 200K<br>Long enough for tool-call traces and agent loops. | AGENT LOOPS | tool calling<br>multi-step coding<br>autonomous tasks | Strong purpose-built agent model. Excellent for tool use and autonomous workflows on 128GB. |\n| GLM-4.5-Air Q6_K • Recommended<br>Zhipu AI • MIT<br>SWE-Bench Verified 64.2 • MMLU-Pro 79.1<br>IFeval strong | 99.01 GB | Medium<br>106B total / 12B active MoE. Great speed-quality balance. | 128K<br>Purpose-built for ARC, agent, and repo loops. | CODING | SWE tasks<br>agent tool loops<br>repo diffs | Excellent coding/agent model with a strong balance of reasoning, repo work, and tool use. |\n\n### 3) Math & Competition Reasoning\n\n| Model | Weights size | Speed | Context | Best pick | Best used for | Honest take |\n|---|---:|---|---|---|---|---|\n| Qwen3-235B-A22B-Thinking-2507 UD-Q2_K_XL • Recommended<br>Qwen • Apache 2.0<br>GPQA-D 81.1 • AIME’25 92.3<br>MMLU-Pro 84 • SWE-V 39 | 88.77 GB | Medium<br>235B total / 22B active MoE. Balanced reasoning language. | 256K<br>Room for long reasoning traces, tricky math, and code windows. | BEST MATH & REASONING PICK | competition math<br>structured solving<br>analysis<br>deep logic | Elite reasoning model for math and structured problem solving. Not the everyday general chat model. |\n| gpt-oss-120B Q8_0 • Recommended<br>OpenAI • Apache 2.0<br>MMLU-Pro 90.0 • AIME’25 97.9 (tool-assisted)<br>SWE-Bench Verified 62.4 | 63.39 GB | Fast<br>MXFP4-native weights; Q8_0. Is effectively full precision at 63 GB. | 128K<br>Solid long-context for reasoning; efficient on unified memory. | MATH & EFFICIENCY VETERAN | math olympiad<br>hard reasoning<br>general assistant<br>code | Excellent older model (Aug 2025). MXFP4-native means Q8_0 is full precision. Still extremely strong on math/olympiad tasks and efficient on unified memory. |\n\n### 4) Vision & Multimodal\n\n| Model | Weights size | Speed | Context | Best pick | Best used for | Honest take |\n|---|---:|---|---|---|---|---|\n| Qwen3-VL-235B-A22B-Thinking UD-IQ3_XXS • Recommended<br>Qwen • Apache 2.0<br>Vision Arena 2358<br>DocVQA high • multimodal reasoning strong | 94.73 GB | Medium<br>235B total / 22B active MoE. Vision agent overhead on long images. | 128K<br>Multimodal: image, text, native vision support via llama.cpp. | BEST VISION THINKER | image understanding<br>vision reasoning<br>charts & docs<br>OCR & layout | Same reasoning core as Qwen3-235B-Thinking plus vision. Great for docs, diagrams, charts, and technical reports. |\n\n### 5) Long-Context / Research / Fast Thinkers\n\n| Model | Weights size | Speed | Context | Best pick | Best used for | Honest take |\n|---|---:|---|---|---|---|---|\n| Llama-4-Scout 17Bx16 Q6_K • Recommended<br>Meta • Llama Community License<br>Context 10M • Llama 10M<br>GPQA-D 57.2 • Multimodal native | 88.43 GB | Fast<br>109B total / 17B active MoE. | 10M<br>Native 10M context window; best for huge codebases, corpora, and archives. | BEST LONG-CONTEXT RESEARCH PICK | massive documents<br>multimodal ingest<br>research corpora<br>long-context QA | Unmatched for huge-context work. Best when you truly need 10M context; weaker than top picks on raw reasoning. |\n| Qwen3-Next-80B-A3B-Thinking Q6_K • Recommended<br>Qwen • Apache 2.0<br>MMLU-Pro 82.8 • GPQA-D 77.2<br>AIME’25 87.8 • 3B active | 65.79 GB | Very fast<br>80B total / 3B active MoE. Hybrid attention keeps latency low on long context. | 256K<br>Hybrid attention keeps latency low on long context. | BEST FAST THINKER | fast reasoning<br>interactive math<br>long-context loops<br>agent planning | Best reasoning per-second on the sheet. Pick it for fast, responsive thinking and interactive use, not deepest reasoning. |\n\n## Bottom Line\n\n128GB advice: Model choice is highly use-case dependent. Qwen3.5-397B-A17B is the strongest all-rounder. Pick MiniMax-M2.7 or GLM-4.5-Air for agent/coding work, gpt-oss-120B for math/efficiency, and the specialists for vision or 10M+ context. There is no single “best” model - match it to your workflow.\n\n@gkisokay",
      "response_path": "runs/R-IMG-LLM-TABLE-01/textifier_codex_gpt_54_mini/response.json",
      "response_warnings": [
        "Dense infographic with small text; a few model names, metric values, and line wraps may be approximate."
      ],
      "status": "converted",
      "suggested_files": [
        {
          "output_format": "markdown",
          "suggested_path": "local-llm-cheat-sheet.md",
          "text": "# Local LLM Cheat Sheet\n\n*April 24, 2026 • Mac Studio M-Ultra • Workstation Tier*\n\n## 128GB RAM\n\n### 1) General Purpose & All-Rounders\n\n| Model | Weights size | Speed | Context | Best pick | Best used for | Honest take |\n|---|---:|---|---|---|---|---|\n| Qwen3.5-397B-A17B UD-IQ1_M • Recommended<br>Qwen • Apache 2.0<br>LiveCodeBench 83.6 | 106.82 GB | Medium<br>397B total / 17B active MoE. | 262K<br>Native 262K context. | BEST OVERALL / GENERAL ASSISTANT | general assistant<br>hardest reasoning<br>research<br>complex agents | Best overall. Strongest all-rounder on 128GB for reasoning, research, and agentic work. |\n| Mistral Large 2411 Q4_K_M • Recommended<br>Mistral AI • MRL (research/non-commercial)<br>MMLU 84.0 • HumanEval 90.0<br>Multilingual SOTA • Fn calling native | 73.22 GB | Medium<br>Dense 123B at 4-bit. Heavier but still fast. | 128K<br>Best-in-class European multilingual. | BEST WRITING / MULTILINGUAL | creative writing<br>multilingual tasks<br>function calling<br>long-form prose | Excels on writing and multilingual tasks with strong function calling. Great for creative and business work. |\n\n### 2) Coding / Agent / Tool-Use Kings\n\n| Model | Weights size | Speed | Context | Best pick | Best used for | Honest take |\n|---|---:|---|---|---|---|---|\n| MiniMax-M2.7 UD-IQ2_XXS • Recommended<br>MiniMax • Apache 2.0<br>SWE-Bench Pro 56.2 • GPQA-D 77.7<br>SWE-Mult 76.5 | 65.38 GB | Fast<br>229B total / 10B active MoE. Low-latency agent loops. | 200K<br>Long enough for tool-call traces and agent loops. | AGENT LOOPS | tool calling<br>multi-step coding<br>autonomous tasks | Strong purpose-built agent model. Excellent for tool use and autonomous workflows on 128GB. |\n| GLM-4.5-Air Q6_K • Recommended<br>Zhipu AI • MIT<br>SWE-Bench Verified 64.2 • MMLU-Pro 79.1<br>IFeval strong | 99.01 GB | Medium<br>106B total / 12B active MoE. Great speed-quality balance. | 128K<br>Purpose-built for ARC, agent, and repo loops. | CODING | SWE tasks<br>agent tool loops<br>repo diffs | Excellent coding/agent model with a strong balance of reasoning, repo work, and tool use. |\n\n### 3) Math & Competition Reasoning\n\n| Model | Weights size | Speed | Context | Best pick | Best used for | Honest take |\n|---|---:|---|---|---|---|---|\n| Qwen3-235B-A22B-Thinking-2507 UD-Q2_K_XL • Recommended<br>Qwen • Apache 2.0<br>GPQA-D 81.1 • AIME’25 92.3<br>MMLU-Pro 84 • SWE-V 39 | 88.77 GB | Medium<br>235B total / 22B active MoE. Balanced reasoning language. | 256K<br>Room for long reasoning traces, tricky math, and code windows. | BEST MATH & REASONING PICK | competition math<br>structured solving<br>analysis<br>deep logic | Elite reasoning model for math and structured problem solving. Not the everyday general chat model. |\n| gpt-oss-120B Q8_0 • Recommended<br>OpenAI • Apache 2.0<br>MMLU-Pro 90.0 • AIME’25 97.9 (tool-assisted)<br>SWE-Bench Verified 62.4 | 63.39 GB | Fast<br>MXFP4-native weights; Q8_0. Is effectively full precision at 63 GB. | 128K<br>Solid long-context for reasoning; efficient on unified memory. | MATH & EFFICIENCY VETERAN | math olympiad<br>hard reasoning<br>general assistant<br>code | Excellent older model (Aug 2025). MXFP4-native means Q8_0 is full precision. Still extremely strong on math/olympiad tasks and efficient on unified memory. |\n\n### 4) Vision & Multimodal\n\n| Model | Weights size | Speed | Context | Best pick | Best used for | Honest take |\n|---|---:|---|---|---|---|---|\n| Qwen3-VL-235B-A22B-Thinking UD-IQ3_XXS • Recommended<br>Qwen • Apache 2.0<br>Vision Arena 2358<br>DocVQA high • multimodal reasoning strong | 94.73 GB | Medium<br>235B total / 22B active MoE. Vision agent overhead on long images. | 128K<br>Multimodal: image, text, native vision support via llama.cpp. | BEST VISION THINKER | image understanding<br>vision reasoning<br>charts & docs<br>OCR & layout | Same reasoning core as Qwen3-235B-Thinking plus vision. Great for docs, diagrams, charts, and technical reports. |\n\n### 5) Long-Context / Research / Fast Thinkers\n\n| Model | Weights size | Speed | Context | Best pick | Best used for | Honest take |\n|---|---:|---|---|---|---|---|\n| Llama-4-Scout 17Bx16 Q6_K • Recommended<br>Meta • Llama Community License<br>Context 10M • Llama 10M<br>GPQA-D 57.2 • Multimodal native | 88.43 GB | Fast<br>109B total / 17B active MoE. | 10M<br>Native 10M context window; best for huge codebases, corpora, and archives. | BEST LONG-CONTEXT RESEARCH PICK | massive documents<br>multimodal ingest<br>research corpora<br>long-context QA | Unmatched for huge-context work. Best when you truly need 10M context; weaker than top picks on raw reasoning. |\n| Qwen3-Next-80B-A3B-Thinking Q6_K • Recommended<br>Qwen • Apache 2.0<br>MMLU-Pro 82.8 • GPQA-D 77.2<br>AIME’25 87.8 • 3B active | 65.79 GB | Very fast<br>80B total / 3B active MoE. Hybrid attention keeps latency low on long context. | 256K<br>Hybrid attention keeps latency low on long context. | BEST FAST THINKER | fast reasoning<br>interactive math<br>long-context loops<br>agent planning | Best reasoning per-second on the sheet. Pick it for fast, responsive thinking and interactive use, not deepest reasoning. |\n\n## Bottom Line\n\n128GB advice: Model choice is highly use-case dependent. Qwen3.5-397B-A17B is the strongest all-rounder. Pick MiniMax-M2.7 or GLM-4.5-Air for agent/coding work, gpt-oss-120B for math/efficiency, and the specialists for vision or 10M+ context. There is no single “best” model - match it to your workflow.\n\n@gkisokay"
        }
      ],
      "usage": {
        "api_equivalent_cost_usd": 0.0299799,
        "basis": "api_equivalent",
        "cached_input_price_per_million": 0.075,
        "cached_input_tokens": 22912,
        "completed_at": "2026-04-28T13:28:40.848624Z",
        "currency": "USD",
        "input_price_per_million": 0.75,
        "input_tokens": 26192,
        "metered_objects": [],
        "output_price_per_million": 4.5,
        "output_tokens": 1915,
        "reasoning_tokens": 93,
        "started_at": "2026-04-28T13:28:19.825045Z",
        "thinking_seconds": null,
        "total_tokens": 28107,
        "wall_seconds": 21.023579
      }
    },
    {
      "caller": "textifier_codex_gpt_54_mini",
      "case_id": "R-IMG-INFOGRAPHIC-01",
      "expected_output_format": "markdown",
      "expected_status": "converted",
      "expected_suggested_paths": [
        "hermes-agent.md"
      ],
      "expected_textification_intent": "Extract the chalkboard-style Hermes Agent infographic into structured Markdown with commands, section labels, provider lists, and gateway labels.",
      "fixture_metadata": {
        "mime_type": "image/jpeg",
        "name": "r-img-infographic-01.jpg",
        "path": "/Users/zeph/github/tzaffi/curio/tmp/textify-smoke/20260428-132551-09c3fa3c8f75/cases/R-IMG-INFOGRAPHIC-01/fixtures/r-img-infographic-01.jpg",
        "sha256": "0405a18638feeee817b4e4a3a71c39cfb2426fbb936f981bd8cd762768d7ebe3",
        "source_language_hint": null
      },
      "ground_truth_text": "Hermes Agent\nThe CLI AI Agent by Nous Research\nFrom zero to chat in 3 steps\ncurl -fsSL .../install.sh | bash\nPick Provider\nChat\nCore Tools\nAny model. No lock-in.\nMessaging gateways",
      "model_importance": 10,
      "output_format": [
        "markdown"
      ],
      "participates_in_model_ranking": true,
      "preservation_requirements": [
        "Hermes Agent",
        "curl -fsSL",
        "Pick Provider",
        "Core Tools",
        "Any model. No lock-in.",
        "Messaging gateways"
      ],
      "rendered_textified_text": "# Hermes Agent\n\nThe CLI AI Agent by Nous Research\n\nLearns. Remembers. Works everywhere.\n\n## From zero to chat in 3 steps\n\n1. `curl -fsSL .../install.sh | bash`\n2. Pick Provider\n   `hermes model`\n3. Chat\n   `hermes`\n   or `hermes --tui`\n\n## Core Tools\n\n- Terminal\n- Files\n- Web\n- Browser\n- Vision\n- Image Gen\n- TTS\n- MCP\n\n## What makes it an agent\n\n- Skills\n- Memory\n- Context Files\n- Cron\n- Delegation\n- Code Execution\n- Hooks\n- Batch\n- RL Training\n- Provider Routing\n\n## Any model. No lock-in.\n\n- Nous Portal\n- Anthropic\n- OpenRouter\n- OpenAI Codex\n- Qwen\n- Minimax\n- Google Gemini\n- xAI Grok\n- GitHub Copilot\n- Kimi\n- DeepSeek\n- Ollama\n- Hugging Face\n- NVIDIA NIM\n- Bedrock\n- + many more\n- `hermes model`\n- `Min context: 64K tokens`\n\n## Messaging gateways\n\n- Telegram\n- Slack\n- Signal\n- Email\n- Discord\n- WhatsApp\n- Matrix\n- SMS\n- Home Assistant\n- +more\n- `hermes gateway setup`\n\n## Sandbox when you want\n\n- local\n- docker\n- ssh\n- modal\n- daytona\n- singularity\n\n## Automate in plain English\n\n\"Every morning at 9am, check Hacker News for AI news and send me a summary on Telegram.\"\n\n→ Hermes sets up the cron job automatically.",
      "response_path": "runs/R-IMG-INFOGRAPHIC-01/textifier_codex_gpt_54_mini/response.json",
      "response_warnings": [
        "OCR is approximate for small text and stylized handwriting-like labels.",
        "Some provider names may be ambiguous due to image quality; 'Minimax' and 'Hermes model' were inferred from visible text."
      ],
      "status": "converted",
      "suggested_files": [
        {
          "output_format": "markdown",
          "suggested_path": "hermes-agent.md",
          "text": "# Hermes Agent\n\nThe CLI AI Agent by Nous Research\n\nLearns. Remembers. Works everywhere.\n\n## From zero to chat in 3 steps\n\n1. `curl -fsSL .../install.sh | bash`\n2. Pick Provider\n   `hermes model`\n3. Chat\n   `hermes`\n   or `hermes --tui`\n\n## Core Tools\n\n- Terminal\n- Files\n- Web\n- Browser\n- Vision\n- Image Gen\n- TTS\n- MCP\n\n## What makes it an agent\n\n- Skills\n- Memory\n- Context Files\n- Cron\n- Delegation\n- Code Execution\n- Hooks\n- Batch\n- RL Training\n- Provider Routing\n\n## Any model. No lock-in.\n\n- Nous Portal\n- Anthropic\n- OpenRouter\n- OpenAI Codex\n- Qwen\n- Minimax\n- Google Gemini\n- xAI Grok\n- GitHub Copilot\n- Kimi\n- DeepSeek\n- Ollama\n- Hugging Face\n- NVIDIA NIM\n- Bedrock\n- + many more\n- `hermes model`\n- `Min context: 64K tokens`\n\n## Messaging gateways\n\n- Telegram\n- Slack\n- Signal\n- Email\n- Discord\n- WhatsApp\n- Matrix\n- SMS\n- Home Assistant\n- +more\n- `hermes gateway setup`\n\n## Sandbox when you want\n\n- local\n- docker\n- ssh\n- modal\n- daytona\n- singularity\n\n## Automate in plain English\n\n\"Every morning at 9am, check Hacker News for AI news and send me a summary on Telegram.\"\n\n→ Hermes sets up the cron job automatically."
        }
      ],
      "usage": {
        "api_equivalent_cost_usd": 0.023497650000000002,
        "basis": "api_equivalent",
        "cached_input_price_per_million": 0.075,
        "cached_input_tokens": 22912,
        "completed_at": "2026-04-28T13:28:51.302998Z",
        "currency": "USD",
        "input_price_per_million": 0.75,
        "input_tokens": 25781,
        "metered_objects": [],
        "output_price_per_million": 4.5,
        "output_tokens": 543,
        "reasoning_tokens": 29,
        "started_at": "2026-04-28T13:28:40.894277Z",
        "thinking_seconds": null,
        "total_tokens": 26324,
        "wall_seconds": 10.408721
      }
    },
    {
      "caller": "textifier_codex_gpt_54_mini",
      "case_id": "R-IMG-PAPER-PAGE-01",
      "expected_output_format": "markdown",
      "expected_status": "converted",
      "expected_suggested_paths": [
        "openclaw-rl.md"
      ],
      "expected_textification_intent": "Extract the academic paper page with title, authors, GitHub link, abstract, figure caption, and diagram labels into Markdown.",
      "fixture_metadata": {
        "mime_type": "image/png",
        "name": "r-img-paper-page-01.png",
        "path": "/Users/zeph/github/tzaffi/curio/tmp/textify-smoke/20260428-132551-09c3fa3c8f75/cases/R-IMG-PAPER-PAGE-01/fixtures/r-img-paper-page-01.png",
        "sha256": "3989e8b2dbb1992196f6c3302667b3a98ff911c5c717773a101fd896e37e87b8",
        "source_language_hint": null
      },
      "ground_truth_text": "OpenClaw-RL: Train Any Agent Simply by Talking\nYinjie Wang\nhttps://github.com/Gen-Verse/OpenClaw-RL\nEvery agent interaction generates a next-state signal\nFigure 1 OpenClaw-RL infrastructure overview",
      "model_importance": 9,
      "output_format": [
        "markdown"
      ],
      "participates_in_model_ranking": true,
      "preservation_requirements": [
        "OpenClaw-RL",
        "Train Any Agent Simply by Talking",
        "Gen-Verse/OpenClaw-RL",
        "next-state signal",
        "Figure 1"
      ],
      "rendered_textified_text": "# Princeton University\n\n# OpenClaw-RL: Train Any Agent Simply by Talking\n\nYinjie Wang$^{*}$, Xuyang Chen$^{*}$, Xiaolong Jin$^{*}$, Mengdi Wang$^{*}$, Ling Yang$^{\\dagger}$\n\n<https://github.com/Gen-Verse/OpenClaw-RL>\n\nEvery agent interaction generates a next-state signal, namely the user reply, tool output, terminal or GUI state change that follows each action, yet no existing agentic RL system recovers it as a live, online learning source. We present OpenClaw-RL, a framework built on a simple observation: next-state signals are universal, and policy can learn from all of them simultaneously. Personal conversations, terminal executions, GUI interactions, SWE tasks, and tool-call traces are not separate training problems. They are all interactions that can be used to train the same policy in the same loop. Next-state signals encode two forms of information: evaluative signals, which indicate how well the action performed and are extracted as scalar rewards via a PRM judge; and directive signals, which indicate how the task should have been different and are recovered through Hindsight-Guided On-Policy Distillation (OPD). We extract textually hints from the next-state, construct an enhanced teacher context, and provide token-level directional advantage supervision that is richer than any scalar reward. Due to the asynchronous design, the model serves live requests, the PRM judges ongoing interactions, and the trainer updates the policy at the same time, with zero coordination overhead between them. Applied to personal agents, OpenClaw-RL enables an agent to improve simply by being used, recovering conversational signals from user-replies, corrections, and explicit feedback. Applied to general agents, the same infrastructure supports scalable RL across terminal, GUI, SWE, and tool-call settings, where we additionally demonstrate the utility of process rewards.\n\n## Diagram Labels\n\n- Personal Agents\n  - OpenClaw\n- General Agents\n  - Terminal Agent\n  - GUI Agent\n  - SWE Agent\n  - Tool-call Agent\n- Environment Servers\n  - Personal Devices\n    - Confidential API Keys\n  - Cloud Services\n    - Large Scale Environments\n- RL Server\n  - Slice Async Framework\n  - Zero Serving Interruption\n  - Graceful Weight Update\n- Training Engine (Megatron)\n- Policy Server (SGLang)\n- PRM Server (SGLang/API)\n- data\n\n## Figure 1\n\nOpenClaw-RL infrastructure overview. Interaction streams come from two agent types: Personal Agents (conversational, single-user), hosted on personal devices, and General Agents (terminal, GUI, SWE, and tool-call agents), hosted on cloud services. The collected samples flow into our RL server built on the asynchronous slim framework, which consists of four decoupled components: (1) the environment server, (2) PRM/Judge for reward computation, (3) Megatron for policy training, and (4) SGLang for policy serving. These components support graceful update and enable training with any agent framework. The environment server for personal agents is simply the users' personal devices, which connect to the RL server over HTTP with confidential API keys. The environments for general agents are hosted on cloud services to enable scalable parallelization.\n\n* Equal contribution; corresponding author: yangling0818@163.com",
      "response_path": "runs/R-IMG-PAPER-PAGE-01/textifier_codex_gpt_54_mini/response.json",
      "response_warnings": [
        "Some OCR text is uncertain in the title block, author markers, and figure labels due to resolution and small font size."
      ],
      "status": "converted",
      "suggested_files": [
        {
          "output_format": "markdown",
          "suggested_path": "openclaw-rl.md",
          "text": "# Princeton University\n\n# OpenClaw-RL: Train Any Agent Simply by Talking\n\nYinjie Wang$^{*}$, Xuyang Chen$^{*}$, Xiaolong Jin$^{*}$, Mengdi Wang$^{*}$, Ling Yang$^{\\dagger}$\n\n<https://github.com/Gen-Verse/OpenClaw-RL>\n\nEvery agent interaction generates a next-state signal, namely the user reply, tool output, terminal or GUI state change that follows each action, yet no existing agentic RL system recovers it as a live, online learning source. We present OpenClaw-RL, a framework built on a simple observation: next-state signals are universal, and policy can learn from all of them simultaneously. Personal conversations, terminal executions, GUI interactions, SWE tasks, and tool-call traces are not separate training problems. They are all interactions that can be used to train the same policy in the same loop. Next-state signals encode two forms of information: evaluative signals, which indicate how well the action performed and are extracted as scalar rewards via a PRM judge; and directive signals, which indicate how the task should have been different and are recovered through Hindsight-Guided On-Policy Distillation (OPD). We extract textually hints from the next-state, construct an enhanced teacher context, and provide token-level directional advantage supervision that is richer than any scalar reward. Due to the asynchronous design, the model serves live requests, the PRM judges ongoing interactions, and the trainer updates the policy at the same time, with zero coordination overhead between them. Applied to personal agents, OpenClaw-RL enables an agent to improve simply by being used, recovering conversational signals from user-replies, corrections, and explicit feedback. Applied to general agents, the same infrastructure supports scalable RL across terminal, GUI, SWE, and tool-call settings, where we additionally demonstrate the utility of process rewards.\n\n## Diagram Labels\n\n- Personal Agents\n  - OpenClaw\n- General Agents\n  - Terminal Agent\n  - GUI Agent\n  - SWE Agent\n  - Tool-call Agent\n- Environment Servers\n  - Personal Devices\n    - Confidential API Keys\n  - Cloud Services\n    - Large Scale Environments\n- RL Server\n  - Slice Async Framework\n  - Zero Serving Interruption\n  - Graceful Weight Update\n- Training Engine (Megatron)\n- Policy Server (SGLang)\n- PRM Server (SGLang/API)\n- data\n\n## Figure 1\n\nOpenClaw-RL infrastructure overview. Interaction streams come from two agent types: Personal Agents (conversational, single-user), hosted on personal devices, and General Agents (terminal, GUI, SWE, and tool-call agents), hosted on cloud services. The collected samples flow into our RL server built on the asynchronous slim framework, which consists of four decoupled components: (1) the environment server, (2) PRM/Judge for reward computation, (3) Megatron for policy training, and (4) SGLang for policy serving. These components support graceful update and enable training with any agent framework. The environment server for personal agents is simply the users' personal devices, which connect to the RL server over HTTP with confidential API keys. The environments for general agents are hosted on cloud services to enable scalable parallelization.\n\n* Equal contribution; corresponding author: yangling0818@163.com"
        }
      ],
      "usage": {
        "api_equivalent_cost_usd": 0.024756900000000002,
        "basis": "api_equivalent",
        "cached_input_price_per_million": 0.075,
        "cached_input_tokens": 22912,
        "completed_at": "2026-04-28T13:29:03.971194Z",
        "currency": "USD",
        "input_price_per_million": 0.75,
        "input_tokens": 25354,
        "metered_objects": [],
        "output_price_per_million": 4.5,
        "output_tokens": 894,
        "reasoning_tokens": 61,
        "started_at": "2026-04-28T13:28:51.339982Z",
        "thinking_seconds": null,
        "total_tokens": 26248,
        "wall_seconds": 12.631212
      }
    },
    {
      "caller": "textifier_codex_gpt_54_mini",
      "case_id": "R-IMG-CHARTS-01",
      "expected_output_format": "markdown",
      "expected_status": "converted",
      "expected_suggested_paths": [
        "agent-benchmarks.md"
      ],
      "expected_textification_intent": "Extract both benchmark bar charts into Markdown tables with system names and percentages.",
      "fixture_metadata": {
        "mime_type": "image/jpeg",
        "name": "r-img-charts-01.jpg",
        "path": "/Users/zeph/github/tzaffi/curio/tmp/textify-smoke/20260428-132551-09c3fa3c8f75/cases/R-IMG-CHARTS-01/fixtures/r-img-charts-01.jpg",
        "sha256": "6963044d99e19d448472a7e223c36cb85494db523b99b7547cfe6c9d13d0b778",
        "source_language_hint": null
      },
      "ground_truth_text": "SpreadsheetBench\nAutoAgent 96.5%\nTetra-Beta-2 94.2%\nTerminalBench (GPT-5)\nAutoAgent 55.1%\nCodex CLI 49.6%",
      "model_importance": 8,
      "output_format": [
        "markdown"
      ],
      "participates_in_model_ranking": true,
      "preservation_requirements": [
        "SpreadsheetBench",
        "TerminalBench",
        "AutoAgent 96.5%",
        "AutoAgent 55.1%",
        "Codex CLI 49.6%"
      ],
      "rendered_textified_text": "# SpreadsheetBench\n\n| System | Score |\n|---|---:|\n| AutoAgent | 96.5% |\n| Tetra-Beta-2 | 94.2% |\n| Noble Agent | 91.0% |\n| Qingqiu Agent | 89.2% |\n| Shortcut.ai | 86.0% |\n\n# TerminalBench (GPT-5)\n\n| System | Score |\n|---|---:|\n| AutoAgent | 55.1% |\n| Codex CLI | 49.6% |\n| OpenHands | 43.8% |\n| Terminus 2 | 35.2% |\n| Mini-SWE-Agent | 33.9% |",
      "response_path": "runs/R-IMG-CHARTS-01/textifier_codex_gpt_54_mini/response.json",
      "response_warnings": [],
      "status": "converted",
      "suggested_files": [
        {
          "output_format": "markdown",
          "suggested_path": "agent-benchmarks.md",
          "text": "# SpreadsheetBench\n\n| System | Score |\n|---|---:|\n| AutoAgent | 96.5% |\n| Tetra-Beta-2 | 94.2% |\n| Noble Agent | 91.0% |\n| Qingqiu Agent | 89.2% |\n| Shortcut.ai | 86.0% |\n\n# TerminalBench (GPT-5)\n\n| System | Score |\n|---|---:|\n| AutoAgent | 55.1% |\n| Codex CLI | 49.6% |\n| OpenHands | 43.8% |\n| Terminus 2 | 35.2% |\n| Mini-SWE-Agent | 33.9% |"
        }
      ],
      "usage": {
        "api_equivalent_cost_usd": 0.0225648,
        "basis": "api_equivalent",
        "cached_input_price_per_million": 0.075,
        "cached_input_tokens": 23424,
        "completed_at": "2026-04-28T13:29:12.986355Z",
        "currency": "USD",
        "input_price_per_million": 0.75,
        "input_tokens": 25386,
        "metered_objects": [],
        "output_price_per_million": 4.5,
        "output_tokens": 393,
        "reasoning_tokens": 136,
        "started_at": "2026-04-28T13:29:03.996178Z",
        "thinking_seconds": null,
        "total_tokens": 25779,
        "wall_seconds": 8.990177
      }
    },
    {
      "caller": "textifier_codex_gpt_54_mini",
      "case_id": "R-IMG-TERMINAL-01",
      "expected_output_format": "txt",
      "expected_status": "converted",
      "expected_suggested_paths": [
        "claude-code-listing.log"
      ],
      "expected_textification_intent": "Transcribe the terminal session as a log, preserving command lines, permissions columns, file sizes, timestamps, and filenames.",
      "fixture_metadata": {
        "mime_type": "image/png",
        "name": "r-img-terminal-01.png",
        "path": "/Users/zeph/github/tzaffi/curio/tmp/textify-smoke/20260428-132551-09c3fa3c8f75/cases/R-IMG-TERMINAL-01/fixtures/r-img-terminal-01.png",
        "sha256": "e1c5b1945a3db39ed228e143b3202da12b86f936f7c55f1407e9aa5fb617b7fa",
        "source_language_hint": null
      },
      "ground_truth_text": "ls -alht cli.js.map\nls -alht src\ntotal 2304\nmain.tsx\ncommands\nQueryEngine.ts\ncontext.ts",
      "model_importance": 8,
      "output_format": [
        "txt"
      ],
      "participates_in_model_ranking": true,
      "preservation_requirements": [
        "ls -alht",
        "total 2304",
        "main.tsx",
        "commands",
        "QueryEngine.ts",
        "context.ts"
      ],
      "rendered_textified_text": "shou@dev claude-code % ls -alht cli.js.map\n-rw-r--r--  1 shou  staff   57M Mar 31 01:16 cli.js.map\nshou@dev claude-code % ls -alht src\ntotal 2034\ndrwxr-xr-x   8 shou  staff   256B Mar 31 01:17 entrypoints\n-rw-r--r--   1 shou  staff   785K Mar 31 01:17 main.tsx\ndrwxr-xr-x  55 shou  staff   1.7K Mar 31 01:17 .\ndrwxr-xr-x  10 shou  staff   320B Mar 31 01:17 cli\ndrwxr-xr-x 103 shou  staff   3.2K Mar 31 01:17 commands\ndrwxr-xr-x 331 shou  staff    10K Mar 31 01:17 utils\ndrwxr-xr-x 146 shou  staff   4.6K Mar 31 01:17 components\n-rw-r--r--   1 shou  staff    46K Mar 31 01:17 QueryEngine.ts\n-rw-r--r--   1 shou  staff    20K Mar 31 01:17 setup.ts\n-rw-r--r--   1 shou  staff   160B Mar 31 01:17 .\ndrwxr-xr-x  13 shou  staff   416B Mar 31 01:17 migrations\ndrwxr-xr-x  16 shou  staff   512B Mar 31 01:17 keybindings\ndrwxr-xr-x   6 shou  staff   192B Mar 31 01:17 skills\ndrwxr-xr-x   4 shou  staff   128B Mar 31 01:17 plugins\ndrwxr-xr-x   1 shou  staff    22K Mar 31 01:17 dialogLaunchers.tsx\n-rw-r--r--   1 shou  staff   160B Mar 31 01:17 screens\ndrwxr-xr-x  87 shou  staff   2.7K Mar 31 01:17 hooks\n-rw-r--r--   1 shou  staff    56K Mar 31 01:17 interactiveHelpers.ts\ndrwxr-xr-x  38 shou  staff   1.2K Mar 31 01:17 services\n-rw-r--r--   1 shou  staff   3.4K Mar 31 01:17 replLauncher.tsx\n-rw-r--r--   1 shou  staff   617B Mar 31 01:17 costHook.ts\n-rw-r--r--   1 shou  staff    96B Mar 31 01:17 moreright?\ndrwxr-xr-x   3 shou  staff    96B Mar 31 01:17 assistant\ndrwxr-xr-x   6 shou  staff   192B Mar 31 01:17 remote\ndrwxr-xr-x   7 shou  staff   224B Mar 31 01:17 vim\ndrwxr-xr-x   8 shou  staff   256B Mar 31 01:17 buddy\ndrwxr-xr-x  33 shou  staff   1.0K Mar 31 01:17 bridge\ndrwxr-xr-x   8 shou  staff   256B Mar 31 01:17 state\ndrwxr-xr-x  11 shou  staff   352B Mar 31 01:17 context\ndrwxr-xr-x   4 shou  staff   128B Mar 31 01:17 upstreamproxy\ndrwxr-xr-x  23 shou  staff   736B Mar 31 01:17 constants\n-rw-r--r--   1 shou  staff   320B Mar 31 01:17 types\n-rw-r--r--   1 shou  staff   3.1K Mar 31 01:17 Task.ts\ndrwxr-xr-x  10 shou  staff   320B Mar 31 01:17 memdir\n-rw-r--r--   1 shou  staff    25K Mar 31 01:17 commands.ts\n-rw-r--r--   1 shou  staff   160B Mar 31 01:17 native-ts\n-rw-r--r--   1 shou  staff    14K Mar 31 01:17 history.ts\n-rw-r--r--   1 shou  staff   2.3K Mar 31 01:17 projectOnboardingState.ts\n-rw-r--r--   1 shou  staff    96B Mar 31 01:17 outputStyles\n-rw-r--r--   1 shou  staff    67K Mar 31 01:17 query.ts\ndrwxr-xr-x   6 shou  staff   192B Mar 31 01:17 query\n-rw-r--r--   1 shou  staff   352B Mar 31 01:17 tasks\n-rw-r--r--   1 shou  staff    17K Mar 31 01:17 tools.ts\ndrwxr-xr-x  45 shou  staff   1.4K Mar 31 01:17 tools\n-rw-r--r--   1 shou  staff    96B Mar 31 01:17 voice\n-rw-r--r--   1 shou  staff   1.3K Mar 31 01:17 tasks.ts\n-rw-r--r--   1 shou  staff    10K Mar 31 01:17 cost-tracker.ts\ndrwxr-xr-x   3 shou  staff    96B Mar 31 01:17 coordinator\ndrwxr-xr-x   6 shou  staff   6.3K Mar 31 01:17 context.ts\n-rw-r--r--   1 shou  staff   3.8K Mar 31 01:17 ink.ts\ndrwxr-xr-x  50 shou  staff   1.6K Mar 31 01:17 ink\n-rw-r--r--   1 shou  staff    29K Mar 31 01:17 Tool.ts\n-rw-r--r--   1 shou  staff    96B Mar 31 01:17 schemas\ndrwxr-xr-x  12 shou  staff   384B Mar 31 01:17 bootstrap",
      "response_path": "runs/R-IMG-TERMINAL-01/textifier_codex_gpt_54_mini/response.json",
      "response_warnings": [
        "OCR uncertain in several lower-right filenames and one or more entries may be slightly misread due image blur/cropping."
      ],
      "status": "converted",
      "suggested_files": [
        {
          "output_format": "txt",
          "suggested_path": "claude-code-listing.log",
          "text": "shou@dev claude-code % ls -alht cli.js.map\n-rw-r--r--  1 shou  staff   57M Mar 31 01:16 cli.js.map\nshou@dev claude-code % ls -alht src\ntotal 2034\ndrwxr-xr-x   8 shou  staff   256B Mar 31 01:17 entrypoints\n-rw-r--r--   1 shou  staff   785K Mar 31 01:17 main.tsx\ndrwxr-xr-x  55 shou  staff   1.7K Mar 31 01:17 .\ndrwxr-xr-x  10 shou  staff   320B Mar 31 01:17 cli\ndrwxr-xr-x 103 shou  staff   3.2K Mar 31 01:17 commands\ndrwxr-xr-x 331 shou  staff    10K Mar 31 01:17 utils\ndrwxr-xr-x 146 shou  staff   4.6K Mar 31 01:17 components\n-rw-r--r--   1 shou  staff    46K Mar 31 01:17 QueryEngine.ts\n-rw-r--r--   1 shou  staff    20K Mar 31 01:17 setup.ts\n-rw-r--r--   1 shou  staff   160B Mar 31 01:17 .\ndrwxr-xr-x  13 shou  staff   416B Mar 31 01:17 migrations\ndrwxr-xr-x  16 shou  staff   512B Mar 31 01:17 keybindings\ndrwxr-xr-x   6 shou  staff   192B Mar 31 01:17 skills\ndrwxr-xr-x   4 shou  staff   128B Mar 31 01:17 plugins\ndrwxr-xr-x   1 shou  staff    22K Mar 31 01:17 dialogLaunchers.tsx\n-rw-r--r--   1 shou  staff   160B Mar 31 01:17 screens\ndrwxr-xr-x  87 shou  staff   2.7K Mar 31 01:17 hooks\n-rw-r--r--   1 shou  staff    56K Mar 31 01:17 interactiveHelpers.ts\ndrwxr-xr-x  38 shou  staff   1.2K Mar 31 01:17 services\n-rw-r--r--   1 shou  staff   3.4K Mar 31 01:17 replLauncher.tsx\n-rw-r--r--   1 shou  staff   617B Mar 31 01:17 costHook.ts\n-rw-r--r--   1 shou  staff    96B Mar 31 01:17 moreright?\ndrwxr-xr-x   3 shou  staff    96B Mar 31 01:17 assistant\ndrwxr-xr-x   6 shou  staff   192B Mar 31 01:17 remote\ndrwxr-xr-x   7 shou  staff   224B Mar 31 01:17 vim\ndrwxr-xr-x   8 shou  staff   256B Mar 31 01:17 buddy\ndrwxr-xr-x  33 shou  staff   1.0K Mar 31 01:17 bridge\ndrwxr-xr-x   8 shou  staff   256B Mar 31 01:17 state\ndrwxr-xr-x  11 shou  staff   352B Mar 31 01:17 context\ndrwxr-xr-x   4 shou  staff   128B Mar 31 01:17 upstreamproxy\ndrwxr-xr-x  23 shou  staff   736B Mar 31 01:17 constants\n-rw-r--r--   1 shou  staff   320B Mar 31 01:17 types\n-rw-r--r--   1 shou  staff   3.1K Mar 31 01:17 Task.ts\ndrwxr-xr-x  10 shou  staff   320B Mar 31 01:17 memdir\n-rw-r--r--   1 shou  staff    25K Mar 31 01:17 commands.ts\n-rw-r--r--   1 shou  staff   160B Mar 31 01:17 native-ts\n-rw-r--r--   1 shou  staff    14K Mar 31 01:17 history.ts\n-rw-r--r--   1 shou  staff   2.3K Mar 31 01:17 projectOnboardingState.ts\n-rw-r--r--   1 shou  staff    96B Mar 31 01:17 outputStyles\n-rw-r--r--   1 shou  staff    67K Mar 31 01:17 query.ts\ndrwxr-xr-x   6 shou  staff   192B Mar 31 01:17 query\n-rw-r--r--   1 shou  staff   352B Mar 31 01:17 tasks\n-rw-r--r--   1 shou  staff    17K Mar 31 01:17 tools.ts\ndrwxr-xr-x  45 shou  staff   1.4K Mar 31 01:17 tools\n-rw-r--r--   1 shou  staff    96B Mar 31 01:17 voice\n-rw-r--r--   1 shou  staff   1.3K Mar 31 01:17 tasks.ts\n-rw-r--r--   1 shou  staff    10K Mar 31 01:17 cost-tracker.ts\ndrwxr-xr-x   3 shou  staff    96B Mar 31 01:17 coordinator\ndrwxr-xr-x   6 shou  staff   6.3K Mar 31 01:17 context.ts\n-rw-r--r--   1 shou  staff   3.8K Mar 31 01:17 ink.ts\ndrwxr-xr-x  50 shou  staff   1.6K Mar 31 01:17 ink\n-rw-r--r--   1 shou  staff    29K Mar 31 01:17 Tool.ts\n-rw-r--r--   1 shou  staff    96B Mar 31 01:17 schemas\ndrwxr-xr-x  12 shou  staff   384B Mar 31 01:17 bootstrap"
        }
      ],
      "usage": {
        "api_equivalent_cost_usd": 0.0355653,
        "basis": "api_equivalent",
        "cached_input_price_per_million": 0.075,
        "cached_input_tokens": 23424,
        "completed_at": "2026-04-28T13:29:50.774854Z",
        "currency": "USD",
        "input_price_per_million": 0.75,
        "input_tokens": 25308,
        "metered_objects": [],
        "output_price_per_million": 4.5,
        "output_tokens": 3295,
        "reasoning_tokens": 1645,
        "started_at": "2026-04-28T13:29:13.028593Z",
        "thinking_seconds": null,
        "total_tokens": 28603,
        "wall_seconds": 37.746261
      }
    },
    {
      "caller": "textifier_codex_gpt_54_mini",
      "case_id": "R-IMG-ASCII-DIAGRAM-01",
      "expected_output_format": "txt",
      "expected_status": "converted",
      "expected_suggested_paths": [
        "distributed-bloomberg-autoquant.txt"
      ],
      "expected_textification_intent": "Preserve the ASCII-style diagram layout and result box as plain text instead of summarizing it away.",
      "fixture_metadata": {
        "mime_type": "image/png",
        "name": "r-img-ascii-diagram-01.png",
        "path": "/Users/zeph/github/tzaffi/curio/tmp/textify-smoke/20260428-132551-09c3fa3c8f75/cases/R-IMG-ASCII-DIAGRAM-01/fixtures/r-img-ascii-diagram-01.png",
        "sha256": "353bc7c7e176f785ef3d09d0b8ae088c6f299c4e971010301ff2bd9d84f40c50",
        "source_language_hint": null
      },
      "ground_truth_text": "DISTRIBUTED BLOOMBERG\nAutoQuant\nAgent Macro Sector Alpha Risks\nDARWINIAN SELECTION\n4 factors · risk parity\nSharpe 1.32\n1,896 experiments in 36 hours",
      "model_importance": 8,
      "output_format": [
        "txt"
      ],
      "participates_in_model_ranking": true,
      "preservation_requirements": [
        "DISTRIBUTED BLOOMBERG",
        "AutoQuant",
        "DARWINIAN SELECTION",
        "Sharpe 1.32",
        "1,896 experiments"
      ],
      "rendered_textified_text": "┌────────────────────────────────────────────────────────────────────────────────────────────┐\n│                              DISTRIBUTED BLOOMBERG                                         │\n│                              AutoQuant                                                      │\n├────────────────────────────────────────────────────────────────────────────────────────────┤\n│                                                                                            │\n│    ┌──────────┐     ┌──────────┐     ┌──────────┐     × 135                               │\n│    │Agent     │     │Agent     │     │Agent     │                                         │\n│    │Macro     │     │Macro     │     │Macro     │                                         │\n│    │Sector    │     │Sector    │     │Sector    │                                         │\n│    │Alpha     │     │Alpha     │     │Alpha     │                                         │\n│    │Risk↳     │     │Risk↳     │     │Risk↳     │                                         │\n│    └──────────┘     └──────────┘     └──────────┘                                         │\n│          │              │              │                                                   │\n│          │      gossip  │ gossip       │                                                   │\n│          └──────▶  P2P   ◀──────┘      │                                                   │\n│                 Network                                                             │       │\n│                                                                                            │\n│    DARWINIAN SELECTION                                                                     │\n│    ├── 30 mutations compete                                                                │\n│    ├── Win rates tracked                                                                   │\n│    ├── Losers pruned, winners amplified                                                    │\n│    └── Network converges on optimal                                                        │\n│                                                                                            │\n│    RESULT (discovered autonomously):                                                       │\n│                                                                                            │\n│    ┌────────────────────────────────────────────────────────────┐                          │\n│    │  4 factors · risk parity                                   │                          │\n│    │  Sharpe 1.32 · 3× return                                    │                          │\n│    │  5.5% max drawdown                                           │                          │\n│    │  1,896 experiments in 36 hours                               │                          │\n│    └────────────────────────────────────────────────────────────┘                          │\n│                                                                                            │\n│    32,868 total commits across all domains:                                                │\n│    ML · Search · Skills · Finance · Network                                                 │\n└────────────────────────────────────────────────────────────────────────────────────────────┘",
      "response_path": "runs/R-IMG-ASCII-DIAGRAM-01/textifier_codex_gpt_54_mini/response.json",
      "response_warnings": [
        "Low-confidence OCR in ASCII art and box-drawing alignment; some glyphs may differ from the source.",
        "One cropped/right-edge region is partially unreadable.",
        "Arrow and symbol characters were inferred where exact rendering was unclear."
      ],
      "status": "converted",
      "suggested_files": [
        {
          "output_format": "txt",
          "suggested_path": "distributed-bloomberg-autoquant.txt",
          "text": "┌────────────────────────────────────────────────────────────────────────────────────────────┐\n│                              DISTRIBUTED BLOOMBERG                                         │\n│                              AutoQuant                                                      │\n├────────────────────────────────────────────────────────────────────────────────────────────┤\n│                                                                                            │\n│    ┌──────────┐     ┌──────────┐     ┌──────────┐     × 135                               │\n│    │Agent     │     │Agent     │     │Agent     │                                         │\n│    │Macro     │     │Macro     │     │Macro     │                                         │\n│    │Sector    │     │Sector    │     │Sector    │                                         │\n│    │Alpha     │     │Alpha     │     │Alpha     │                                         │\n│    │Risk↳     │     │Risk↳     │     │Risk↳     │                                         │\n│    └──────────┘     └──────────┘     └──────────┘                                         │\n│          │              │              │                                                   │\n│          │      gossip  │ gossip       │                                                   │\n│          └──────▶  P2P   ◀──────┘      │                                                   │\n│                 Network                                                             │       │\n│                                                                                            │\n│    DARWINIAN SELECTION                                                                     │\n│    ├── 30 mutations compete                                                                │\n│    ├── Win rates tracked                                                                   │\n│    ├── Losers pruned, winners amplified                                                    │\n│    └── Network converges on optimal                                                        │\n│                                                                                            │\n│    RESULT (discovered autonomously):                                                       │\n│                                                                                            │\n│    ┌────────────────────────────────────────────────────────────┐                          │\n│    │  4 factors · risk parity                                   │                          │\n│    │  Sharpe 1.32 · 3× return                                    │                          │\n│    │  5.5% max drawdown                                           │                          │\n│    │  1,896 experiments in 36 hours                               │                          │\n│    └────────────────────────────────────────────────────────────┘                          │\n│                                                                                            │\n│    32,868 total commits across all domains:                                                │\n│    ML · Search · Skills · Finance · Network                                                 │\n└────────────────────────────────────────────────────────────────────────────────────────────┘"
        }
      ],
      "usage": {
        "api_equivalent_cost_usd": 0.02433615,
        "basis": "api_equivalent",
        "cached_input_price_per_million": 0.075,
        "cached_input_tokens": 22912,
        "completed_at": "2026-04-28T13:30:00.907642Z",
        "currency": "USD",
        "input_price_per_million": 0.75,
        "input_tokens": 25891,
        "metered_objects": [],
        "output_price_per_million": 4.5,
        "output_tokens": 711,
        "reasoning_tokens": 51,
        "started_at": "2026-04-28T13:29:50.787650Z",
        "thinking_seconds": null,
        "total_tokens": 26602,
        "wall_seconds": 10.119992
      }
    },
    {
      "caller": "textifier_codex_gpt_54_mini",
      "case_id": "R-IMG-COMPARISON-TABLE-01",
      "expected_output_format": "markdown",
      "expected_status": "converted",
      "expected_suggested_paths": [
        "agent-comparison.md"
      ],
      "expected_textification_intent": "Extract the OpenClaw/Hermes/Paperclip comparison as a Markdown table preserving row and column alignment.",
      "fixture_metadata": {
        "mime_type": "image/png",
        "name": "r-img-comparison-table-01.png",
        "path": "/Users/zeph/github/tzaffi/curio/tmp/textify-smoke/20260428-132551-09c3fa3c8f75/cases/R-IMG-COMPARISON-TABLE-01/fixtures/r-img-comparison-table-01.png",
        "sha256": "26f885c49a5b46c7827858bd74e79ca5938ac4e083bae507712c64180299e509",
        "source_language_hint": null
      },
      "ground_truth_text": "Head-to-Head\nDimension | OpenClaw | Hermes | Paperclip\nWhat it is\nGitHub stars\nSecurity\nInstall",
      "model_importance": 8,
      "output_format": [
        "markdown"
      ],
      "participates_in_model_ranking": true,
      "preservation_requirements": [
        "Head-to-Head",
        "Dimension",
        "OpenClaw",
        "Hermes",
        "Paperclip",
        "GitHub stars",
        "Install"
      ],
      "rendered_textified_text": "# Head-to-Head\n\n| Dimension | OpenClaw | Hermes | Paperclip |\n|---|---|---|---|\n| What it is | Personal AI agent | Self-improving AI agent | Multi-agent orchestrator |\n| GitHub stars | 351K | ~31K | 49K |\n| Philosophy | System to be orchestrated | Mind to be developed | Company to be managed |\n| Skills | Static (ClawHub, 5,700+) | Self-created, auto-improving (94 built-in) | N/A (manages other agents) |\n| Memory | Plugin-based | Multi-level, persistent, deepening | Org-level (budgets, goals) |\n| Models | API-dependent | Runs on open models (Qwen 3.5) | Model-agnostic orchestration |\n| Security | Concerning (Snyk findings) | Better defaults | Governance + audit trail |\n| Best for | Tinkerers, ecosystem power | Simplicity, self-improvement | Running 5-50 agents together |\n| Install | npm global | 11-minute installer | npx paperclipai onboard |",
      "response_path": "runs/R-IMG-COMPARISON-TABLE-01/textifier_codex_gpt_54_mini/response.json",
      "response_warnings": [],
      "status": "converted",
      "suggested_files": [
        {
          "output_format": "markdown",
          "suggested_path": "agent-comparison.md",
          "text": "# Head-to-Head\n\n| Dimension | OpenClaw | Hermes | Paperclip |\n|---|---|---|---|\n| What it is | Personal AI agent | Self-improving AI agent | Multi-agent orchestrator |\n| GitHub stars | 351K | ~31K | 49K |\n| Philosophy | System to be orchestrated | Mind to be developed | Company to be managed |\n| Skills | Static (ClawHub, 5,700+) | Self-created, auto-improving (94 built-in) | N/A (manages other agents) |\n| Memory | Plugin-based | Multi-level, persistent, deepening | Org-level (budgets, goals) |\n| Models | API-dependent | Runs on open models (Qwen 3.5) | Model-agnostic orchestration |\n| Security | Concerning (Snyk findings) | Better defaults | Governance + audit trail |\n| Best for | Tinkerers, ecosystem power | Simplicity, self-improvement | Running 5-50 agents together |\n| Install | npm global | 11-minute installer | npx paperclipai onboard |"
        }
      ],
      "usage": {
        "api_equivalent_cost_usd": 0.0226422,
        "basis": "api_equivalent",
        "cached_input_price_per_million": 0.075,
        "cached_input_tokens": 23936,
        "completed_at": "2026-04-28T13:30:15.392237Z",
        "currency": "USD",
        "input_price_per_million": 0.75,
        "input_tokens": 25606,
        "metered_objects": [],
        "output_price_per_million": 4.5,
        "output_tokens": 365,
        "reasoning_tokens": 22,
        "started_at": "2026-04-28T13:30:00.916640Z",
        "thinking_seconds": null,
        "total_tokens": 25971,
        "wall_seconds": 14.475597
      }
    },
    {
      "caller": "textifier_codex_gpt_54_mini",
      "case_id": "R-IMG-NO-TEXT-REAL-01",
      "expected_output_format": "markdown",
      "expected_status": "no_text_found",
      "expected_suggested_paths": [],
      "expected_textification_intent": "Return no_text_found for a real photo with no readable text and do not invent a visual description.",
      "fixture_metadata": {
        "mime_type": "image/jpeg",
        "name": "r-img-no-text-real-01.jpg",
        "path": "/Users/zeph/github/tzaffi/curio/tmp/textify-smoke/20260428-132551-09c3fa3c8f75/cases/R-IMG-NO-TEXT-REAL-01/fixtures/r-img-no-text-real-01.jpg",
        "sha256": "80c99366dc83288925d6653b25e086ee894e8098469f7f785e6e1e984e761107",
        "source_language_hint": null
      },
      "ground_truth_text": "",
      "model_importance": 5,
      "output_format": [],
      "participates_in_model_ranking": true,
      "preservation_requirements": [
        "no_text_found",
        "no invented description"
      ],
      "rendered_textified_text": "",
      "response_path": "runs/R-IMG-NO-TEXT-REAL-01/textifier_codex_gpt_54_mini/response.json",
      "response_warnings": [],
      "status": "no_text_found",
      "suggested_files": [],
      "usage": {
        "api_equivalent_cost_usd": 0.021891900000000002,
        "basis": "api_equivalent",
        "cached_input_price_per_million": 0.075,
        "cached_input_tokens": 22912,
        "completed_at": "2026-04-28T13:30:20.695765Z",
        "currency": "USD",
        "input_price_per_million": 0.75,
        "input_tokens": 26088,
        "metered_objects": [],
        "output_price_per_million": 4.5,
        "output_tokens": 135,
        "reasoning_tokens": 56,
        "started_at": "2026-04-28T13:30:15.399489Z",
        "thinking_seconds": null,
        "total_tokens": 26223,
        "wall_seconds": 5.296276
      }
    },
    {
      "caller": "textifier_codex_gpt_54_mini",
      "case_id": "C-IMG-DIR-TREE-01",
      "expected_output_format": "mixed",
      "expected_status": "converted",
      "expected_suggested_paths": [
        "home/important/openclaw-rl.md",
        "home/important/agent-comparison.md",
        "home/trivial/claude-code-listing.log"
      ],
      "expected_textification_intent": "Split one composite screenshot into exactly three suggested files in the visible nested relative directory structure.",
      "fixture_metadata": {
        "mime_type": "image/png",
        "name": "c-img-dir-tree-01.png",
        "path": "/Users/zeph/github/tzaffi/curio/tmp/textify-smoke/20260428-132551-09c3fa3c8f75/cases/C-IMG-DIR-TREE-01/fixtures/c-img-dir-tree-01.png",
        "sha256": "0664c813d92eb3562bb8a6a990b9c05634f452a5b245233038aff43fafc42400",
        "source_language_hint": null
      },
      "ground_truth_text": "home/important/openclaw-rl.md\nOpenClaw-RL: Train Any Agent Simply by Talking\nhome/important/agent-comparison.md\nHead-to-Head\nhome/trivial/claude-code-listing.log\nls -alht src",
      "model_importance": 10,
      "output_format": [
        "markdown",
        "markdown",
        "text"
      ],
      "participates_in_model_ranking": true,
      "preservation_requirements": [
        "exactly three suggested files",
        "home/important/openclaw-rl.md",
        "home/important/agent-comparison.md",
        "home/trivial/claude-code-listing.log",
        "no cross-section bleed",
        "no extra generated files"
      ],
      "rendered_textified_text": "# OpenClaw-RL: Train Any Agent Simply by Talking\n\nYinjie Wang*, Xuyang Chen*, Xiaolong Jin*, Mengdi Wang*, Ling Yang*\n\nhttps://github.com/Gen-Verse/OpenClaw-RL\n\nEvery agent interaction generates a next-state signal, namely the user reply, tool output, terminal or GUI state change that follows each action, yet no existing agentic RL system recovers it as a live, online learning source. We present OpenClaw-RL, a framework built on a simple observation: next-state signals are universal, and policy can learn from all of them simultaneously. Personal conversations, terminal executions, GUI interactions, SWE tasks, and tool-call traces are not separate training problems. They are all interactions that can be used to train the same policy in the same loop. Next-state signals encode two forms of information: evaluative signals, which indicate how well the action performed and are extracted as scalar rewards via a PRM judge; and directive signals, which indicate how the action should be different and are recovered through Hindsight-Guided On-Policy Distillation (OPD). We extract textual hints from the next state, construct an enhanced teacher context, and provide token-level directional advantage supervision that is richer than any scalar reward. Due to the asynchronous design, the model serves live requests, the PRM judges ongoing interactions, and the trainer updates the policy at the same time, with zero coordination overhead between them. Applied to personal agents, OpenClaw-RL enables an agent to improve simply by being used, recovering conversational signals from user re-queries, corrections, and explicit feedback. Applied to general agents, the same infrastructure supports scalable RL across terminal, GUI, SWE, and tool-call settings, where we additionally demonstrate the utility of process rewards.\n\n![Figure 1](figure)\n\nFigure 1 | OpenClaw-RL infrastructure overview. Interaction streams come from two agent types: Personal Agents (conversational, single-user), hosted on personal devices, and General Agents (terminal, GUI, SWE, and tool-call agents), hosted on cloud services. The collected samples flow into our RL server built on the asynchronous slime framework, which consists of four decoupled components: (1) the environment server, (2) PRM/Judge layer and computation, (3) Megatron for policy training, and (4) SGLang for policy serving. These components support graceful weight updates and enable training with any agentic framework. The environment for personal agents is simply the users' personal devices, which connect to the RL server over HTTP with confidential API keys. The environments for general agents are hosted on cloud services to enable scalable parallelization.\n\n* Equal contribution; ** Corresponding authors; Main contact: yangl@princeton.edu\n\n# Head-to-Head\n\n| Dimension | OpenClaw | Hermes | Paperclip |\n|---|---|---|---|\n| What it is | Personal AI agent | Self-improving AI agent | Multi-agent orchestrator |\n| GitHub stars | 351K | ~31K | 49K |\n| Philosophy | System to be orchestrated | Mind to be developed | Company to be managed |\n| Skills | Static (ClawHub, 5,700+) | Self-created, auto-improving (94 built-in) | N/A (manages other agents) |\n| Memory | Plugin-based | Multi-level, persistent, deepening | Org-level (budgets, goals) |\n| Models | API-dependent | Runs on open models (Qwen 3.5) | Model-agnostic orchestration |\n| Security | Concerning (Snyk findings) | Better defaults | Governance + audit trail |\n| Best for | Tinkerers, ecosystem power | Simplicity, self-improvement | Running 5-50 agents together |\n| Install | npm global | 11-minute installer | npx paperclipai onboard |\n\n[shou@dev claude-code % ls -alht cli.js.map\n-rw-r--r-- 1 shou staff 57M Mar 31 01:16 cli.js.map\n[shou@dev claude-code % ls -alht src\ntotal 2304\n\ndrwxr-xr-x  8 shou staff  256B Mar 31 01:17 entrypoints\n-rw-r--r--  1 shou staff  785K Mar 31 01:17 main.tsx\n-rw-r--r-- 55 shou staff  1.7K Mar 31 01:17 cli\n-rw-r--r-- 10 shou staff  320B Mar 31 01:17 commands\n-rw-r--r-- 183 shou staff  3.2K Mar 31 01:17 commands\n-rw-r--r-- 331 shou staff  1.0K Mar 31 01:17 utils\n-rw-r--r-- 146 shou staff  4.6K Mar 31 01:17 components\n-rw-r--r--  1 shou staff   46K Mar 31 01:17 QueryEngine.ts\n-rw-r--r--  1 shou staff   20K Mar 31 01:17 setup.ts\n-rw-r--r--   5 shou staff  160B Mar 31 01:17 server\n-drwxr-xr-x  13 shou staff  416B Mar 31 01:17 migrations\n-drwxr-xr-x  16 shou staff  512B Mar 31 01:17 keybindings\n-drwxr-xr-x   6 shou staff  192B Mar 31 01:17 skills\n-drwxr-xr-x   4 shou staff  128B Mar 31 01:17 plugins\n-rw-r--r--   1 shou staff  22K Mar 31 01:17 dialogLaunchers.tsx\n-drwxr-xr-x   5 shou staff  160B Mar 31 01:17 screens\n-drwxr-xr-x  87 shou staff  2.7K Mar 31 01:17 hooks\n-rw-r--r--   1 shou staff  56K Mar 31 01:17 interactiveHelpers.ts\n-drwxr-xr-x  38 shou staff  1.2K Mar 31 01:17 services\n-rw-r--r--   1 shou staff  3.4K Mar 31 01:17 replLauncher.tsx\n-rw-r--r--   3 shou staff  617B Mar 31 01:17 costHook.ts\n-rw-r--r--   3 shou staff  96B Mar 31 01:17 moreright\n-rw-r--r--   96B Mar 31 01:17 assistant\n-drwxr-xr-x   6 shou staff  192B Mar 31 01:17 remote\n-rw-r--r--   7 shou staff  224B Mar 31 01:17 vim\n-rw-r--r--   6 shou staff  256B Mar 31 01:17 buddy\n-rw-r--r--  33 shou staff  1.0K Mar 31 01:17 bridge\n-rw-r--r--   8 shou staff  256B Mar 31 01:17 state\n-drwxr-xr-x  11 shou staff  352B Mar 31 01:17 context\n-rw-r--r--   4 shou staff  128B Mar 31 01:17 upstreamproxy\n-rw-r--r--  23 shou staff  736B Mar 31 01:17 constants\n-rw-r--r--  10 shou staff  320B Mar 31 01:17 types\n-rw-r--r--   1 shou staff  3.1K Mar 31 01:17 Task.ts\n-rw-r--r--  10 shou staff  320B Mar 31 01:17 memdir\n-rw-r--r--  25K Mar 31 01:17 commands.ts\n-rw-r--r--   5 shou staff  160B Mar 31 01:17 native-ts\n-rw-r--r--   1 shou staff  14K Mar 31 01:17 history.ts\n-rw-r--r--   2 shou staff  2.3K Mar 31 01:17 projectOnboardingState.ts\n-rw-r--r--   3 shou staff   96B Mar 31 01:17 outputStyles\n-rw-r--r--   1 shou staff   67K Mar 31 01:17 query.ts\n-rw-r--r--   6 shou staff  192B Mar 31 01:17 query\n-rw-r--r--  11 shou staff  352B Mar 31 01:17 tasks\n-rw-r--r--   3 shou staff  104B Mar 31 01:17 tools.ts\n-rw-r--r--  45 shou staff  1.4K Mar 31 01:17 tools\n-rw-r--r--   3 shou staff   96B Mar 31 01:17 voice\n-rw-r--r--   1 shou staff  1.3K Mar 31 01:17 tasks.ts\n-rw-r--r--   1 shou staff   16K Mar 31 01:17 cost-tracker.ts\n-rw-r--r--   96B Mar 31 01:17 coordinator\n-rw-r--r--   6.3K Mar 31 01:17 context.ts\n-rw-r--r--   3.8K Mar 31 01:17 ink.ts\n-rw-r--r--  50 shou staff  1.6K Mar 31 01:17 ink\n-rw-r--r--   1 shou staff   29K Mar 31 01:17 Tool.ts\n-rw-r--r--   3 shou staff   96B Mar 31 01:17 schemas\n-rw-r--r--   1 shou staff   96B Mar 31 01:17 bootstrap\n-rw-r--r--   384B Mar 31 01:17 .",
      "response_path": "runs/C-IMG-DIR-TREE-01/textifier_codex_gpt_54_mini/response.json",
      "response_warnings": [
        "OCR uncertainty in small text and terminal listing; some characters may be misread.",
        "Bottom terminal region is cropped; listing may be incomplete."
      ],
      "status": "converted",
      "suggested_files": [
        {
          "output_format": "markdown",
          "suggested_path": "home/important/openclaw-rl.md",
          "text": "# OpenClaw-RL: Train Any Agent Simply by Talking\n\nYinjie Wang*, Xuyang Chen*, Xiaolong Jin*, Mengdi Wang*, Ling Yang*\n\nhttps://github.com/Gen-Verse/OpenClaw-RL\n\nEvery agent interaction generates a next-state signal, namely the user reply, tool output, terminal or GUI state change that follows each action, yet no existing agentic RL system recovers it as a live, online learning source. We present OpenClaw-RL, a framework built on a simple observation: next-state signals are universal, and policy can learn from all of them simultaneously. Personal conversations, terminal executions, GUI interactions, SWE tasks, and tool-call traces are not separate training problems. They are all interactions that can be used to train the same policy in the same loop. Next-state signals encode two forms of information: evaluative signals, which indicate how well the action performed and are extracted as scalar rewards via a PRM judge; and directive signals, which indicate how the action should be different and are recovered through Hindsight-Guided On-Policy Distillation (OPD). We extract textual hints from the next state, construct an enhanced teacher context, and provide token-level directional advantage supervision that is richer than any scalar reward. Due to the asynchronous design, the model serves live requests, the PRM judges ongoing interactions, and the trainer updates the policy at the same time, with zero coordination overhead between them. Applied to personal agents, OpenClaw-RL enables an agent to improve simply by being used, recovering conversational signals from user re-queries, corrections, and explicit feedback. Applied to general agents, the same infrastructure supports scalable RL across terminal, GUI, SWE, and tool-call settings, where we additionally demonstrate the utility of process rewards.\n\n![Figure 1](figure)\n\nFigure 1 | OpenClaw-RL infrastructure overview. Interaction streams come from two agent types: Personal Agents (conversational, single-user), hosted on personal devices, and General Agents (terminal, GUI, SWE, and tool-call agents), hosted on cloud services. The collected samples flow into our RL server built on the asynchronous slime framework, which consists of four decoupled components: (1) the environment server, (2) PRM/Judge layer and computation, (3) Megatron for policy training, and (4) SGLang for policy serving. These components support graceful weight updates and enable training with any agentic framework. The environment for personal agents is simply the users' personal devices, which connect to the RL server over HTTP with confidential API keys. The environments for general agents are hosted on cloud services to enable scalable parallelization.\n\n* Equal contribution; ** Corresponding authors; Main contact: yangl@princeton.edu"
        },
        {
          "output_format": "markdown",
          "suggested_path": "home/important/agent-comparison.md",
          "text": "# Head-to-Head\n\n| Dimension | OpenClaw | Hermes | Paperclip |\n|---|---|---|---|\n| What it is | Personal AI agent | Self-improving AI agent | Multi-agent orchestrator |\n| GitHub stars | 351K | ~31K | 49K |\n| Philosophy | System to be orchestrated | Mind to be developed | Company to be managed |\n| Skills | Static (ClawHub, 5,700+) | Self-created, auto-improving (94 built-in) | N/A (manages other agents) |\n| Memory | Plugin-based | Multi-level, persistent, deepening | Org-level (budgets, goals) |\n| Models | API-dependent | Runs on open models (Qwen 3.5) | Model-agnostic orchestration |\n| Security | Concerning (Snyk findings) | Better defaults | Governance + audit trail |\n| Best for | Tinkerers, ecosystem power | Simplicity, self-improvement | Running 5-50 agents together |\n| Install | npm global | 11-minute installer | npx paperclipai onboard |"
        },
        {
          "output_format": "text",
          "suggested_path": "home/trivial/claude-code-listing.log",
          "text": "[shou@dev claude-code % ls -alht cli.js.map\n-rw-r--r-- 1 shou staff 57M Mar 31 01:16 cli.js.map\n[shou@dev claude-code % ls -alht src\ntotal 2304\n\ndrwxr-xr-x  8 shou staff  256B Mar 31 01:17 entrypoints\n-rw-r--r--  1 shou staff  785K Mar 31 01:17 main.tsx\n-rw-r--r-- 55 shou staff  1.7K Mar 31 01:17 cli\n-rw-r--r-- 10 shou staff  320B Mar 31 01:17 commands\n-rw-r--r-- 183 shou staff  3.2K Mar 31 01:17 commands\n-rw-r--r-- 331 shou staff  1.0K Mar 31 01:17 utils\n-rw-r--r-- 146 shou staff  4.6K Mar 31 01:17 components\n-rw-r--r--  1 shou staff   46K Mar 31 01:17 QueryEngine.ts\n-rw-r--r--  1 shou staff   20K Mar 31 01:17 setup.ts\n-rw-r--r--   5 shou staff  160B Mar 31 01:17 server\n-drwxr-xr-x  13 shou staff  416B Mar 31 01:17 migrations\n-drwxr-xr-x  16 shou staff  512B Mar 31 01:17 keybindings\n-drwxr-xr-x   6 shou staff  192B Mar 31 01:17 skills\n-drwxr-xr-x   4 shou staff  128B Mar 31 01:17 plugins\n-rw-r--r--   1 shou staff  22K Mar 31 01:17 dialogLaunchers.tsx\n-drwxr-xr-x   5 shou staff  160B Mar 31 01:17 screens\n-drwxr-xr-x  87 shou staff  2.7K Mar 31 01:17 hooks\n-rw-r--r--   1 shou staff  56K Mar 31 01:17 interactiveHelpers.ts\n-drwxr-xr-x  38 shou staff  1.2K Mar 31 01:17 services\n-rw-r--r--   1 shou staff  3.4K Mar 31 01:17 replLauncher.tsx\n-rw-r--r--   3 shou staff  617B Mar 31 01:17 costHook.ts\n-rw-r--r--   3 shou staff  96B Mar 31 01:17 moreright\n-rw-r--r--   96B Mar 31 01:17 assistant\n-drwxr-xr-x   6 shou staff  192B Mar 31 01:17 remote\n-rw-r--r--   7 shou staff  224B Mar 31 01:17 vim\n-rw-r--r--   6 shou staff  256B Mar 31 01:17 buddy\n-rw-r--r--  33 shou staff  1.0K Mar 31 01:17 bridge\n-rw-r--r--   8 shou staff  256B Mar 31 01:17 state\n-drwxr-xr-x  11 shou staff  352B Mar 31 01:17 context\n-rw-r--r--   4 shou staff  128B Mar 31 01:17 upstreamproxy\n-rw-r--r--  23 shou staff  736B Mar 31 01:17 constants\n-rw-r--r--  10 shou staff  320B Mar 31 01:17 types\n-rw-r--r--   1 shou staff  3.1K Mar 31 01:17 Task.ts\n-rw-r--r--  10 shou staff  320B Mar 31 01:17 memdir\n-rw-r--r--  25K Mar 31 01:17 commands.ts\n-rw-r--r--   5 shou staff  160B Mar 31 01:17 native-ts\n-rw-r--r--   1 shou staff  14K Mar 31 01:17 history.ts\n-rw-r--r--   2 shou staff  2.3K Mar 31 01:17 projectOnboardingState.ts\n-rw-r--r--   3 shou staff   96B Mar 31 01:17 outputStyles\n-rw-r--r--   1 shou staff   67K Mar 31 01:17 query.ts\n-rw-r--r--   6 shou staff  192B Mar 31 01:17 query\n-rw-r--r--  11 shou staff  352B Mar 31 01:17 tasks\n-rw-r--r--   3 shou staff  104B Mar 31 01:17 tools.ts\n-rw-r--r--  45 shou staff  1.4K Mar 31 01:17 tools\n-rw-r--r--   3 shou staff   96B Mar 31 01:17 voice\n-rw-r--r--   1 shou staff  1.3K Mar 31 01:17 tasks.ts\n-rw-r--r--   1 shou staff   16K Mar 31 01:17 cost-tracker.ts\n-rw-r--r--   96B Mar 31 01:17 coordinator\n-rw-r--r--   6.3K Mar 31 01:17 context.ts\n-rw-r--r--   3.8K Mar 31 01:17 ink.ts\n-rw-r--r--  50 shou staff  1.6K Mar 31 01:17 ink\n-rw-r--r--   1 shou staff   29K Mar 31 01:17 Tool.ts\n-rw-r--r--   3 shou staff   96B Mar 31 01:17 schemas\n-rw-r--r--   1 shou staff   96B Mar 31 01:17 bootstrap\n-rw-r--r--   384B Mar 31 01:17 ."
        }
      ],
      "usage": {
        "api_equivalent_cost_usd": 0.0346464,
        "basis": "api_equivalent",
        "cached_input_price_per_million": 0.075,
        "cached_input_tokens": 22912,
        "completed_at": "2026-04-28T13:30:42.424062Z",
        "currency": "USD",
        "input_price_per_million": 0.75,
        "input_tokens": 27626,
        "metered_objects": [],
        "output_price_per_million": 4.5,
        "output_tokens": 2713,
        "reasoning_tokens": 260,
        "started_at": "2026-04-28T13:30:20.706434Z",
        "thinking_seconds": null,
        "total_tokens": 30339,
        "wall_seconds": 21.717628
      }
    },
    {
      "caller": "textifier_codex_gpt_54_mini",
      "case_id": "R-PDF-PAPER-01",
      "expected_output_format": "markdown",
      "expected_status": "converted",
      "expected_suggested_paths": [
        "nemotron-3-super.md"
      ],
      "expected_textification_intent": "Extract the scientific PDF into Markdown with title, abstract, sections, tables or figure captions, and reading order.",
      "fixture_metadata": {
        "mime_type": "application/pdf",
        "name": "r-pdf-paper-01.pdf",
        "path": "/Users/zeph/github/tzaffi/curio/tmp/textify-smoke/20260428-132551-09c3fa3c8f75/cases/R-PDF-PAPER-01/fixtures/r-pdf-paper-01.pdf",
        "sha256": "fa7e8a9a1a8f9f716e38e46170371d4bc67c3f6d1ac3e4857c574e911f0e107f",
        "source_language_hint": null
      },
      "ground_truth_text": "Nemotron 3 Super: Open, Efficient Mixture-of-Experts Hybrid Mamba-Transformer Model for Agentic Reasoning\narXiv:2604.12374\nNVIDIA",
      "model_importance": 10,
      "output_format": [
        "markdown"
      ],
      "participates_in_model_ranking": true,
      "preservation_requirements": [
        "Nemotron 3 Super",
        "Mixture-of-Experts",
        "Hybrid Mamba-Transformer",
        "Agentic Reasoning",
        "NVIDIA"
      ],
      "rendered_textified_text": "# Nemotron 3 Super: Open, Efficient Mixture-of-Experts Hybrid Mamba-Transformer Model for Agentic Reasoning\n\nNVIDIA\n\n## Abstract\n\nWe describe the pre-training, post-training, and quantization of Nemotron 3 Super, a 120 billion (active 12 billion) parameter hybrid Mamba-Attention Mixture-of-Experts model. Nemotron 3 Super is the first model in the Nemotron 3 family to 1) be pre-trained in NVFP4, 2) leverage LatentMoE, a new Mixture-of-Experts architecture that optimizes for both accuracy per FLOP and accuracy per parameter, and 3) include MTP layers for inference acceleration through native speculative decoding. We pre-trained Nemotron 3 Super on 25 trillion tokens followed by post-training using supervised fine tuning (SFT) and reinforcement learning (RL). The final model supports up to 1M context length and achieves comparable accuracy on common benchmarks, while also achieving up to 2.2× and 7.5× higher inference throughput compared to GPT-OSS-120B and Qwen3.5-122B, respectively. Nemotron 3 Super datasets, along with the base, post-trained, and quantized checkpoints, are open-sourced on HuggingFace.\n\n## 1. Introduction\n\nThe last few years have seen a rise in the popularity of Mixture-of-Experts (MoE) based Large Language Models (LLMs) (DeepSeek-AI, 2025c; Yang et al., 2025; GLM-4.5-Team, 2025). MoEs help LLMs achieve higher accuracy at a lower active parameter count than regular dense models (Dai et al., 2024; Lepikhin et al., 2020). Orthogonal to MoEs, Hybrid Mamba-Attention models have shown promise in significantly improving inference throughput (NVIDIA, 2025c). We combine these two directions of improvement in Nemotron 3 (NVIDIA, 2025c). As part of our Nemotron 3 series of models, we present Nemotron 3 Super-a 12 billion active, 120 billion total parameter MoE hybrid Mamba-Attention model. Nemotron 3 Super achieves better or on-par benchmark accuracies than GPT-OSS-120B (OpenAI, 2025) and Qwen3.5-122B while achieving up to 2.2× and 7.5× higher inference throughput, respectively, on the 8k token input / 64k token output setting.\n\nNemotron 3 Super is our first model to use LatentMoE (Elango et al., 2026) - a novel MoE architecture that achieves better accuracy per parameter and per FLOP than regular MoEs. Nemotron 3 Super also incorporates Multi-Token-Prediction (MTP), which accelerates inference through speculative decoding while improving overall model quality. We pre-trained Nemotron 3 Super in NVFP4, demonstrating stable and accurate pre-training in low precision. Similar to Nemotron 3 Nano (NVIDIA, 2025a), we pre-trained Nemotron 3 Super on 25 trillion text tokens divided into 2 phases. The first phase accounted for 80% of pre-training (20 trillion tokens) and focused on diversity and broad coverage, while the second phase accounted for 20% of pre-training (5 trillion tokens) and focused on high-quality data and benchmark accuracy. Our base model achieves significantly better accuracy than similarly sized state-of-the-art base models, such as GLM-4.5-Air-Base (GLM-4.5-Team, 2025) and Ling-flash-Base-2.0 (Ling-Team, 2025).\n\nWe trained Nemotron 3 Super with a strong emphasis on agentic capabilities. To support this objective, we substantially scaled the breadth of our RL environments, the volume and quality of agentic training data, and the overall amount of post-training focused on multi-step tool-using behavior. To train effectively on this diverse set of long-horizon tasks, we made substantial improvements to the resiliency of our RL infrastructure, enabling large-scale asynchronous training. This expanded agentic training recipe yields substantial improvements over Nemotron 3 Nano across software engineering, terminal use, and general tool use benchmarks.\n\nWe are publicly sharing the training recipe for Nemotron 3 Super on the Nemotron Developer Repository. We are also openly releasing the following:\n\n### Checkpoints\n\n- Nemotron 3 Super 120B-A12B NVFP4 : post-trained and NVFP4 quantized model\n- Nemotron 3 Super 120B-A12B FP8 : post-trained and FP8 quantized model\n- Nemotron 3 Super 120B-A12B BF16 : post-trained model\n- Nemotron 3 Super 120B-A12B Base BF16 : base model\n- Qwen3-Nemotron-235B-A22B-GenRM-2603 : GenRM used for RLHF\n\n### Data\n\n- Nemotron-Pretraining-Specialized-v1.1 : a collection of synthetic datasets aimed to improve LLM capabilities in code concepts and algorithms, formal logic, economics, and multiple choice questions.\n- Nemotron-Super-Post-Training-Data : a collection of RL environments and SFT datasets targeting a broad range of agentic capabilities.\n\nThe report is organized into 3 broad sections: Pre-training (§2), Post-training (§3), and Quantization (§4), each describing in detail our approach.\n\n## 2. Pretraining\n\nIn this section, we highlight the key features of Nemotron 3 Super 120B-A12B Base, detailing its hybrid Mamba-Attention Mixture-of-Experts (MoE) architecture, NVFP4 pre-training, hyperparameter configurations, long-context extension, and the 25-trillion-token corpus used for pretraining. We also demonstrate that Nemotron-3 Super 120B A12B Base achieves superior accuracy compared to other public state-of-the-art models-including Ling-flash-Base-2.0 and GLM-4.5-Air-Base-across a comprehensive suite of benchmarks.\n\n### 2.1. Model Architecture\n\nNemotron-3-Super-120B-A12B\n\n- Mamba-2\n- Latent MoE\n- Mamba-2\n- Attention\n- Latent MoE\n- Mamba-2\n- Latent MoE\n- x4 x3\n- Mamba-2\n- Attention\n- Latent MoE\n- x1\n- Mamba-2\n- Latent MoE\n- x4\n- Mamba-2\n- Latent MoE\n- Mamba-2\n- Attention\n- Latent MoE\n- x3 x3 x4\n\nFigure 2 | Nemotron 3 Super layer pattern. Similar to Nemotron 3 Nano, we use a hybrid Mamba-Attention architecture, but Nemotron 3 Super is the first model to scale sparsely using LatentMoE layers rather than standard MoE layers.\n\n| Configuration | Nemotron 3 Super 120B-A12B Base |\n| --- | --- |\n| Total Layers | 88 |\n| Model Dimension | 4096 |\n| Q-Heads (nq) | 32 |\n| KV-Heads (nkv) | 2 |\n| Head Dimension | 128 |\n| Mamba State Dimension | 128 |\n| Mamba Groups | 8 |\n| Mamba Heads | 128 |\n| Mamba Head Dimension | 64 |\n| Expert Hidden Dimension | 2688 |\n| Shared Expert Intermediate Size | 5376 |\n| Total Experts per Layer | 512 |\n| Top-k (Activated Experts) | 22 |\n| MoE Latent Size | 1024 |\n| MTP layers (shared weight) | 2 |\n\nTable 1 | Nemotron 3 Super Architectural Dimensions. The model employs a hybrid Mamba-2 and MoE design with strategic global attention layers to optimize the balance between sequence modeling performance and inference throughput.\n\nNemotron 3 Super 120B-A12B Base scales up the hybrid Mamba-Attention Mixture-of-Experts (MoE) architecture introduced in Nemotron-3 Nano (NVIDIA, 2025c). We extend this foundation to 120.6B total parameters, maintaining a constrained active budget of 12.7B parameters (12.1B excluding embeddings) per forward pass. The architecture comprises three core pillars: sparse LatentMoE scaling (§2.1.1), Multi-Token Prediction (MTP) for inference acceleration (§2.1.2), and a periodic hybrid interleaving pattern (§2.1.3).\n\n## 3. Post-Training\n\nWe follow the same general recipe as Nemotron 3 Nano, with a stronger emphasis on agentic tasks. Figure 12 provides an overview of the pipeline. We begin with a Supervised Fine-Tuning (SFT) phase (§3.1), followed by a three-stage Reinforcement Learning phase-RLVR, SWE-RL, and RLHF (§3.2). We conclude with a final phase of MTP healing.\n\nIn SFT, we expand the training blend to cover a wider range of agentic harnesses and interaction scenarios. We also significantly improved our RL infrastructure, enabling reliable large-scale asynchronous training on thousands of GPUs. This infrastructure allows us to (1) train across 21 diverse environments, improving robustness across tasks, and (2) train on long-horizon SWE tasks, strengthening multi-step reasoning and problem solving in realistic agentic settings.\n\nBase\n1M Context\nSFT\n7M Samples\n80B Tokens\nRLVR\nRound 1\n25 env types\nRound 2\n30 env types\nwith Low Effort\nRound 3\n26 env types\nwith Low Effort\nAgentic Focussed\n37 environment types\nUp to 4,000 environment instances per batch\nSWE RL\n20B Tokens\nRLHF\nMTP healing 18B Tokens\nNemotron 3\nSuper\n\nFigure 12 | Overview of the post-training pipeline for Nemotron 3 Super.\n\n### 3.1. Supervised Fine Tuning\n\nFor Nemotron 3 Super SFT, we focused on improving dataset quality and diversity. In particular, we scaled up our agentic datasets and increased their share in the overall SFT blend. The chat\n\n### 3.2.4. Algorithm\n\nWe use an asynchronous GRPO setup in which training and inference are decoupled across separate GPU devices. Inference workers continuously generate trajectories, which are stored in a rollout buffer. Once enough trajectories are collected to form a batch, the batch is sent to the training engine for a model update. We push the updated weights to the inference workers as soon as a\n\nbegin training with a maximum generation length of 49K tokens and later increase it to 64K.\n\nAgentic RL - PivotRL: Post-training for long-horizon agentic capabilities has a tension between efficiency and accuracy. By long-horizon, we mean tasks that require many turns of interaction with an environment, such as conversational tool use, code editing, terminal interaction, and web search. SFT is cheap and simple for this task, but it often degrades performance outside of the target domain (OOD). End-to-end RL avoids that outcome to a large part, but it is costly because every update requires online interactive rollouts in complex environments. To address this, during the post-training of Super, we adopt PivotRL (Yi et al., 2026).\n\nPivotRL is an assistant-turn-level RL method that addresses this tradeoff by reusing offline SFT expert trajectories during RL. It focuses training on informative turns (called \"pivots\") within those SFT traces, where the policy has uncertainty over the next action, and it uses a domain-appropriate reward to match the policy’s action to the expert action, so the model gets credit for similar actions rather than the exact expert action. We notice that this method greatly improves the efficiency of our agentic RL, without facing the OOD degradation issues of SFT.\n\nWe apply PivotRL for all agentic domains: including for Agentic Programming, Search, Terminal Use, and Conversational Tool Use. We will have a manuscript with more details soon.\n\n### 3.2.5. Infrastructure\n\nRL at the frontier of model post-training is currently defined by scaling up to an increasing diversity of tasks or environments designed for the model to learn increasingly general capabilities. Scaling RL to many environments requires a high-performance, extensible, and standardized interface for\n\nvirtual environments and binaries (3) utilize caching in upstream repos like vLLM and flashinfer.\n\nParallel initialization exacerbated latent race conditions with port bindings in the post-training software stack, which became a significant failure point. Several components of the post-training software required ports: (1) Ray control plane (2) vLLM workers and OpenAI servers (3) TCP\n\nIDs, generated token IDs, and log probabilities, resulting in large payloads that benefit from orjson’s Rust-based implementation.\n\n### 3.3. Post-trained Model Evaluations\n\nWe evaluate Nemotron 3 Super on the same broad benchmark suite and evaluation stack as Nemotron 3 Nano (NVIDIA, 2025a), covering general knowledge, reasoning, agentic, instruction following, long-context, and multilingual capability. All evaluation results were collected via Nemo Evaluator\n\n## 4. Quantization For Inference\n\nWe apply post-training quantization (PTQ) using Model-Optimizer to quantize weights and activations to generate two efficient deployment checkpoints: FP8 (W8A8) for Hopper and NVFP4 (W4A4) for Blackwell.\n\n### 4.1. Nemotron 3 Super FP8 Checkpoint\n\nFor FP8 PTQ calibration, we used a small subset containing 256 samples with 65536 context length from the post-training SFT dataset. For FP8 quantization, we quantized MoE GEMMs, both routed and shared, and Mamba Linear layers. We also kept the KV Cache in FP8, whereas Mamba state cache has been quantized to FP16 for speedup. The precision assignments for the different operators in this checkpoint are summarized in Table 6.\n\nTable 6 | Precision settings for the FP8 checkpoint compared with the BF16 baseline.\n\n| Configuration | FP8 Checkpoint | BF16 Baseline |\n| --- | --- | --- |\n| Embedding | BF16 | BF16 |\n\n## 5. Conclusion\n\nWe introduce Nemotron 3 Super, a 12B active and 120B total parameter MoE hybrid Mamba-Attention model with strong agentic capabilities. Nemotron 3 Super employs LatentMoE to improve accuracy and incorporates MTP layers to accelerate inference via speculative decoding. We pretrained Nemotron 3 Super on 25 trillion text tokens with low-precision NVFP4, followed by post-training on",
      "response_path": "runs/R-PDF-PAPER-01/textifier_codex_gpt_54_mini/response.json",
      "response_warnings": [
        "in-process app-server event stream lagged; dropped 1 events",
        "in-process app-server event stream lagged; dropped 14 events",
        "in-process app-server event stream lagged; dropped 32 events",
        "in-process app-server event stream lagged; dropped 5 events",
        "in-process app-server event stream lagged; dropped 64 events",
        "in-process app-server event stream lagged; dropped 3 events",
        "in-process app-server event stream lagged; dropped 128 events",
        "in-process app-server event stream lagged; dropped 33 events",
        "in-process app-server event stream lagged; dropped 517 events",
        "in-process app-server event stream lagged; dropped 243 events",
        "in-process app-server event stream lagged; dropped 359 events",
        "in-process app-server event stream lagged; dropped 160 events",
        "Some later-page text is truncated where the source output was partially cut off; figure labels and equations may be incomplete."
      ],
      "status": "converted",
      "suggested_files": [
        {
          "output_format": "markdown",
          "suggested_path": "nemotron-3-super.md",
          "text": "# Nemotron 3 Super: Open, Efficient Mixture-of-Experts Hybrid Mamba-Transformer Model for Agentic Reasoning\n\nNVIDIA\n\n## Abstract\n\nWe describe the pre-training, post-training, and quantization of Nemotron 3 Super, a 120 billion (active 12 billion) parameter hybrid Mamba-Attention Mixture-of-Experts model. Nemotron 3 Super is the first model in the Nemotron 3 family to 1) be pre-trained in NVFP4, 2) leverage LatentMoE, a new Mixture-of-Experts architecture that optimizes for both accuracy per FLOP and accuracy per parameter, and 3) include MTP layers for inference acceleration through native speculative decoding. We pre-trained Nemotron 3 Super on 25 trillion tokens followed by post-training using supervised fine tuning (SFT) and reinforcement learning (RL). The final model supports up to 1M context length and achieves comparable accuracy on common benchmarks, while also achieving up to 2.2× and 7.5× higher inference throughput compared to GPT-OSS-120B and Qwen3.5-122B, respectively. Nemotron 3 Super datasets, along with the base, post-trained, and quantized checkpoints, are open-sourced on HuggingFace.\n\n## 1. Introduction\n\nThe last few years have seen a rise in the popularity of Mixture-of-Experts (MoE) based Large Language Models (LLMs) (DeepSeek-AI, 2025c; Yang et al., 2025; GLM-4.5-Team, 2025). MoEs help LLMs achieve higher accuracy at a lower active parameter count than regular dense models (Dai et al., 2024; Lepikhin et al., 2020). Orthogonal to MoEs, Hybrid Mamba-Attention models have shown promise in significantly improving inference throughput (NVIDIA, 2025c). We combine these two directions of improvement in Nemotron 3 (NVIDIA, 2025c). As part of our Nemotron 3 series of models, we present Nemotron 3 Super-a 12 billion active, 120 billion total parameter MoE hybrid Mamba-Attention model. Nemotron 3 Super achieves better or on-par benchmark accuracies than GPT-OSS-120B (OpenAI, 2025) and Qwen3.5-122B while achieving up to 2.2× and 7.5× higher inference throughput, respectively, on the 8k token input / 64k token output setting.\n\nNemotron 3 Super is our first model to use LatentMoE (Elango et al., 2026) - a novel MoE architecture that achieves better accuracy per parameter and per FLOP than regular MoEs. Nemotron 3 Super also incorporates Multi-Token-Prediction (MTP), which accelerates inference through speculative decoding while improving overall model quality. We pre-trained Nemotron 3 Super in NVFP4, demonstrating stable and accurate pre-training in low precision. Similar to Nemotron 3 Nano (NVIDIA, 2025a), we pre-trained Nemotron 3 Super on 25 trillion text tokens divided into 2 phases. The first phase accounted for 80% of pre-training (20 trillion tokens) and focused on diversity and broad coverage, while the second phase accounted for 20% of pre-training (5 trillion tokens) and focused on high-quality data and benchmark accuracy. Our base model achieves significantly better accuracy than similarly sized state-of-the-art base models, such as GLM-4.5-Air-Base (GLM-4.5-Team, 2025) and Ling-flash-Base-2.0 (Ling-Team, 2025).\n\nWe trained Nemotron 3 Super with a strong emphasis on agentic capabilities. To support this objective, we substantially scaled the breadth of our RL environments, the volume and quality of agentic training data, and the overall amount of post-training focused on multi-step tool-using behavior. To train effectively on this diverse set of long-horizon tasks, we made substantial improvements to the resiliency of our RL infrastructure, enabling large-scale asynchronous training. This expanded agentic training recipe yields substantial improvements over Nemotron 3 Nano across software engineering, terminal use, and general tool use benchmarks.\n\nWe are publicly sharing the training recipe for Nemotron 3 Super on the Nemotron Developer Repository. We are also openly releasing the following:\n\n### Checkpoints\n\n- Nemotron 3 Super 120B-A12B NVFP4 : post-trained and NVFP4 quantized model\n- Nemotron 3 Super 120B-A12B FP8 : post-trained and FP8 quantized model\n- Nemotron 3 Super 120B-A12B BF16 : post-trained model\n- Nemotron 3 Super 120B-A12B Base BF16 : base model\n- Qwen3-Nemotron-235B-A22B-GenRM-2603 : GenRM used for RLHF\n\n### Data\n\n- Nemotron-Pretraining-Specialized-v1.1 : a collection of synthetic datasets aimed to improve LLM capabilities in code concepts and algorithms, formal logic, economics, and multiple choice questions.\n- Nemotron-Super-Post-Training-Data : a collection of RL environments and SFT datasets targeting a broad range of agentic capabilities.\n\nThe report is organized into 3 broad sections: Pre-training (§2), Post-training (§3), and Quantization (§4), each describing in detail our approach.\n\n## 2. Pretraining\n\nIn this section, we highlight the key features of Nemotron 3 Super 120B-A12B Base, detailing its hybrid Mamba-Attention Mixture-of-Experts (MoE) architecture, NVFP4 pre-training, hyperparameter configurations, long-context extension, and the 25-trillion-token corpus used for pretraining. We also demonstrate that Nemotron-3 Super 120B A12B Base achieves superior accuracy compared to other public state-of-the-art models-including Ling-flash-Base-2.0 and GLM-4.5-Air-Base-across a comprehensive suite of benchmarks.\n\n### 2.1. Model Architecture\n\nNemotron-3-Super-120B-A12B\n\n- Mamba-2\n- Latent MoE\n- Mamba-2\n- Attention\n- Latent MoE\n- Mamba-2\n- Latent MoE\n- x4 x3\n- Mamba-2\n- Attention\n- Latent MoE\n- x1\n- Mamba-2\n- Latent MoE\n- x4\n- Mamba-2\n- Latent MoE\n- Mamba-2\n- Attention\n- Latent MoE\n- x3 x3 x4\n\nFigure 2 | Nemotron 3 Super layer pattern. Similar to Nemotron 3 Nano, we use a hybrid Mamba-Attention architecture, but Nemotron 3 Super is the first model to scale sparsely using LatentMoE layers rather than standard MoE layers.\n\n| Configuration | Nemotron 3 Super 120B-A12B Base |\n| --- | --- |\n| Total Layers | 88 |\n| Model Dimension | 4096 |\n| Q-Heads (nq) | 32 |\n| KV-Heads (nkv) | 2 |\n| Head Dimension | 128 |\n| Mamba State Dimension | 128 |\n| Mamba Groups | 8 |\n| Mamba Heads | 128 |\n| Mamba Head Dimension | 64 |\n| Expert Hidden Dimension | 2688 |\n| Shared Expert Intermediate Size | 5376 |\n| Total Experts per Layer | 512 |\n| Top-k (Activated Experts) | 22 |\n| MoE Latent Size | 1024 |\n| MTP layers (shared weight) | 2 |\n\nTable 1 | Nemotron 3 Super Architectural Dimensions. The model employs a hybrid Mamba-2 and MoE design with strategic global attention layers to optimize the balance between sequence modeling performance and inference throughput.\n\nNemotron 3 Super 120B-A12B Base scales up the hybrid Mamba-Attention Mixture-of-Experts (MoE) architecture introduced in Nemotron-3 Nano (NVIDIA, 2025c). We extend this foundation to 120.6B total parameters, maintaining a constrained active budget of 12.7B parameters (12.1B excluding embeddings) per forward pass. The architecture comprises three core pillars: sparse LatentMoE scaling (§2.1.1), Multi-Token Prediction (MTP) for inference acceleration (§2.1.2), and a periodic hybrid interleaving pattern (§2.1.3).\n\n## 3. Post-Training\n\nWe follow the same general recipe as Nemotron 3 Nano, with a stronger emphasis on agentic tasks. Figure 12 provides an overview of the pipeline. We begin with a Supervised Fine-Tuning (SFT) phase (§3.1), followed by a three-stage Reinforcement Learning phase-RLVR, SWE-RL, and RLHF (§3.2). We conclude with a final phase of MTP healing.\n\nIn SFT, we expand the training blend to cover a wider range of agentic harnesses and interaction scenarios. We also significantly improved our RL infrastructure, enabling reliable large-scale asynchronous training on thousands of GPUs. This infrastructure allows us to (1) train across 21 diverse environments, improving robustness across tasks, and (2) train on long-horizon SWE tasks, strengthening multi-step reasoning and problem solving in realistic agentic settings.\n\nBase\n1M Context\nSFT\n7M Samples\n80B Tokens\nRLVR\nRound 1\n25 env types\nRound 2\n30 env types\nwith Low Effort\nRound 3\n26 env types\nwith Low Effort\nAgentic Focussed\n37 environment types\nUp to 4,000 environment instances per batch\nSWE RL\n20B Tokens\nRLHF\nMTP healing 18B Tokens\nNemotron 3\nSuper\n\nFigure 12 | Overview of the post-training pipeline for Nemotron 3 Super.\n\n### 3.1. Supervised Fine Tuning\n\nFor Nemotron 3 Super SFT, we focused on improving dataset quality and diversity. In particular, we scaled up our agentic datasets and increased their share in the overall SFT blend. The chat\n\n### 3.2.4. Algorithm\n\nWe use an asynchronous GRPO setup in which training and inference are decoupled across separate GPU devices. Inference workers continuously generate trajectories, which are stored in a rollout buffer. Once enough trajectories are collected to form a batch, the batch is sent to the training engine for a model update. We push the updated weights to the inference workers as soon as a\n\nbegin training with a maximum generation length of 49K tokens and later increase it to 64K.\n\nAgentic RL - PivotRL: Post-training for long-horizon agentic capabilities has a tension between efficiency and accuracy. By long-horizon, we mean tasks that require many turns of interaction with an environment, such as conversational tool use, code editing, terminal interaction, and web search. SFT is cheap and simple for this task, but it often degrades performance outside of the target domain (OOD). End-to-end RL avoids that outcome to a large part, but it is costly because every update requires online interactive rollouts in complex environments. To address this, during the post-training of Super, we adopt PivotRL (Yi et al., 2026).\n\nPivotRL is an assistant-turn-level RL method that addresses this tradeoff by reusing offline SFT expert trajectories during RL. It focuses training on informative turns (called \"pivots\") within those SFT traces, where the policy has uncertainty over the next action, and it uses a domain-appropriate reward to match the policy’s action to the expert action, so the model gets credit for similar actions rather than the exact expert action. We notice that this method greatly improves the efficiency of our agentic RL, without facing the OOD degradation issues of SFT.\n\nWe apply PivotRL for all agentic domains: including for Agentic Programming, Search, Terminal Use, and Conversational Tool Use. We will have a manuscript with more details soon.\n\n### 3.2.5. Infrastructure\n\nRL at the frontier of model post-training is currently defined by scaling up to an increasing diversity of tasks or environments designed for the model to learn increasingly general capabilities. Scaling RL to many environments requires a high-performance, extensible, and standardized interface for\n\nvirtual environments and binaries (3) utilize caching in upstream repos like vLLM and flashinfer.\n\nParallel initialization exacerbated latent race conditions with port bindings in the post-training software stack, which became a significant failure point. Several components of the post-training software required ports: (1) Ray control plane (2) vLLM workers and OpenAI servers (3) TCP\n\nIDs, generated token IDs, and log probabilities, resulting in large payloads that benefit from orjson’s Rust-based implementation.\n\n### 3.3. Post-trained Model Evaluations\n\nWe evaluate Nemotron 3 Super on the same broad benchmark suite and evaluation stack as Nemotron 3 Nano (NVIDIA, 2025a), covering general knowledge, reasoning, agentic, instruction following, long-context, and multilingual capability. All evaluation results were collected via Nemo Evaluator\n\n## 4. Quantization For Inference\n\nWe apply post-training quantization (PTQ) using Model-Optimizer to quantize weights and activations to generate two efficient deployment checkpoints: FP8 (W8A8) for Hopper and NVFP4 (W4A4) for Blackwell.\n\n### 4.1. Nemotron 3 Super FP8 Checkpoint\n\nFor FP8 PTQ calibration, we used a small subset containing 256 samples with 65536 context length from the post-training SFT dataset. For FP8 quantization, we quantized MoE GEMMs, both routed and shared, and Mamba Linear layers. We also kept the KV Cache in FP8, whereas Mamba state cache has been quantized to FP16 for speedup. The precision assignments for the different operators in this checkpoint are summarized in Table 6.\n\nTable 6 | Precision settings for the FP8 checkpoint compared with the BF16 baseline.\n\n| Configuration | FP8 Checkpoint | BF16 Baseline |\n| --- | --- | --- |\n| Embedding | BF16 | BF16 |\n\n## 5. Conclusion\n\nWe introduce Nemotron 3 Super, a 12B active and 120B total parameter MoE hybrid Mamba-Attention model with strong agentic capabilities. Nemotron 3 Super employs LatentMoE to improve accuracy and incorporates MTP layers to accelerate inference via speculative decoding. We pretrained Nemotron 3 Super on 25 trillion text tokens with low-precision NVFP4, followed by post-training on"
        }
      ],
      "usage": {
        "api_equivalent_cost_usd": 0.43377734999999995,
        "basis": "api_equivalent",
        "cached_input_price_per_million": 0.075,
        "cached_input_tokens": 450688,
        "completed_at": "2026-04-28T13:32:40.345280Z",
        "currency": "USD",
        "input_price_per_million": 0.75,
        "input_tokens": 489573,
        "metered_objects": [],
        "output_price_per_million": 4.5,
        "output_tokens": 7288,
        "reasoning_tokens": 1986,
        "started_at": "2026-04-28T13:30:42.446623Z",
        "thinking_seconds": null,
        "total_tokens": 496861,
        "wall_seconds": 117.898657
      }
    },
    {
      "caller": "textifier_codex_gpt_54_mini",
      "case_id": "R-HTML-ARXIV-01",
      "expected_output_format": "markdown",
      "expected_status": "skipped_text_media",
      "expected_suggested_paths": [],
      "expected_textification_intent": "Coverage-only HTML source case: skip as deterministic text media without calling an LLM.",
      "fixture_metadata": {
        "mime_type": "text/html",
        "name": "r-html-arxiv-01.html",
        "path": "/Users/zeph/github/tzaffi/curio/tmp/textify-smoke/20260428-132551-09c3fa3c8f75/cases/R-HTML-ARXIV-01/fixtures/r-html-arxiv-01.html",
        "sha256": "102ef094fa45008eb53dac5d613950ec099ae29049fb561c77157f0420071f97",
        "source_language_hint": null
      },
      "ground_truth_text": "[2603.10165] OpenClaw-RL: Train Any Agent Simply by Talking",
      "model_importance": 1,
      "output_format": [],
      "participates_in_model_ranking": false,
      "preservation_requirements": [
        "skipped_text_media",
        "no provider call"
      ],
      "rendered_textified_text": "",
      "response_path": "runs/R-HTML-ARXIV-01/textifier_codex_gpt_54_mini/response.json",
      "response_warnings": [
        "source is deterministic text media"
      ],
      "status": "skipped_text_media",
      "suggested_files": [],
      "usage": null
    },
    {
      "caller": "textifier_codex_gpt_54_mini",
      "case_id": "R-HTML-GITHUB-README-01",
      "expected_output_format": "markdown",
      "expected_status": "skipped_text_media",
      "expected_suggested_paths": [],
      "expected_textification_intent": "Coverage-only complex HTML page case: skip as deterministic text media without calling an LLM.",
      "fixture_metadata": {
        "mime_type": "text/html",
        "name": "r-html-github-readme-01.html",
        "path": "/Users/zeph/github/tzaffi/curio/tmp/textify-smoke/20260428-132551-09c3fa3c8f75/cases/R-HTML-GITHUB-README-01/fixtures/r-html-github-readme-01.html",
        "sha256": "245700b82311141fcf9143e0f8844ca96d6efbd4f8d261148de4951ca291bd84",
        "source_language_hint": null
      },
      "ground_truth_text": "gstack/README.md",
      "model_importance": 1,
      "output_format": [],
      "participates_in_model_ranking": false,
      "preservation_requirements": [
        "skipped_text_media",
        "no provider call"
      ],
      "rendered_textified_text": "",
      "response_path": "runs/R-HTML-GITHUB-README-01/textifier_codex_gpt_54_mini/response.json",
      "response_warnings": [
        "source is deterministic text media"
      ],
      "status": "skipped_text_media",
      "suggested_files": [],
      "usage": null
    },
    {
      "caller": "textifier_codex_gpt_54_mini",
      "case_id": "R-JSON-XARTICLE-CODE-01",
      "expected_output_format": "markdown",
      "expected_status": "skipped_text_media",
      "expected_suggested_paths": [],
      "expected_textification_intent": "Coverage-only JSON source case: skip as deterministic text media without calling an LLM.",
      "fixture_metadata": {
        "mime_type": "application/json",
        "name": "r-json-xarticle-code-01.json",
        "path": "/Users/zeph/github/tzaffi/curio/tmp/textify-smoke/20260428-132551-09c3fa3c8f75/cases/R-JSON-XARTICLE-CODE-01/fixtures/r-json-xarticle-code-01.json",
        "sha256": "69f94ac3515718a1a5aed67d20aed6b6a4ceafca3db50f7104f5e33862943241",
        "source_language_hint": null
      },
      "ground_truth_text": "tv status\ntv quote\ntv pine analyze\ntv stream quote",
      "model_importance": 1,
      "output_format": [],
      "participates_in_model_ranking": false,
      "preservation_requirements": [
        "skipped_text_media",
        "no provider call"
      ],
      "rendered_textified_text": "",
      "response_path": "runs/R-JSON-XARTICLE-CODE-01/textifier_codex_gpt_54_mini/response.json",
      "response_warnings": [
        "source is deterministic text media"
      ],
      "status": "skipped_text_media",
      "suggested_files": [],
      "usage": null
    },
    {
      "caller": "textifier_codex_gpt_54_mini",
      "case_id": "R-ZIP-REPO-01",
      "expected_output_format": "markdown",
      "expected_status": "unsupported_media",
      "expected_suggested_paths": [],
      "expected_textification_intent": "Coverage-only archive source case: reject as unsupported media without calling an LLM.",
      "fixture_metadata": {
        "mime_type": "application/zip",
        "name": "r-zip-repo-01.zip",
        "path": "/Users/zeph/github/tzaffi/curio/tmp/textify-smoke/20260428-132551-09c3fa3c8f75/cases/R-ZIP-REPO-01/fixtures/r-zip-repo-01.zip",
        "sha256": "b3caf0cc25a77138020d670e536279f575a060ee02022be5e7be11f3725cfcb1",
        "source_language_hint": null
      },
      "ground_truth_text": "",
      "model_importance": 1,
      "output_format": [],
      "participates_in_model_ranking": false,
      "preservation_requirements": [
        "unsupported_media",
        "no provider call"
      ],
      "rendered_textified_text": "",
      "response_path": "runs/R-ZIP-REPO-01/textifier_codex_gpt_54_mini/response.json",
      "response_warnings": [
        "unsupported media type for textify v1",
        "unsupported media type for textify v1"
      ],
      "status": "unsupported_media",
      "suggested_files": [],
      "usage": null
    },
    {
      "caller": "textifier_codex_gpt_53_codex",
      "case_id": "C-IMG-TXT-01",
      "expected_output_format": "txt",
      "expected_status": "converted",
      "expected_suggested_paths": [
        "note.txt"
      ],
      "expected_textification_intent": "Extract a plain text note without inventing Markdown headings.",
      "fixture_metadata": {
        "mime_type": "image/png",
        "name": "plain-note.png",
        "path": "/Users/zeph/github/tzaffi/curio/tmp/textify-smoke/20260428-132551-09c3fa3c8f75/cases/C-IMG-TXT-01/fixtures/plain-note.png",
        "sha256": "c895ee9f1e59ac6618167a67d3439fc309ff0fbf4df05bc82da08d5a299b5c59",
        "source_language_hint": null
      },
      "ground_truth_text": "DEPLOY NOTE\nRUN UV SYNC\nTHEN MAKE CHECK\nKEEP README.MD OPEN",
      "model_importance": 1,
      "output_format": [
        "txt"
      ],
      "participates_in_model_ranking": true,
      "preservation_requirements": [
        "RUN UV SYNC",
        "MAKE CHECK",
        "README.MD"
      ],
      "rendered_textified_text": "DEPLOY NOTE\nRUN UV SYNC\nTHEN MAKE CHECK\nKEEP README.MD OPEN",
      "response_path": "runs/C-IMG-TXT-01/textifier_codex_gpt_53_codex/response.json",
      "response_warnings": [],
      "status": "converted",
      "suggested_files": [
        {
          "output_format": "txt",
          "suggested_path": "note.txt",
          "text": "DEPLOY NOTE\nRUN UV SYNC\nTHEN MAKE CHECK\nKEEP README.MD OPEN"
        }
      ],
      "usage": {
        "api_equivalent_cost_usd": 0.0498246,
        "basis": "api_equivalent",
        "cached_input_price_per_million": 0.175,
        "cached_input_tokens": 22912,
        "completed_at": "2026-04-28T13:32:48.394048Z",
        "currency": "USD",
        "input_price_per_million": 1.75,
        "input_tokens": 24740,
        "metered_objects": [],
        "output_price_per_million": 14.0,
        "output_tokens": 180,
        "reasoning_tokens": 75,
        "started_at": "2026-04-28T13:32:40.383034Z",
        "thinking_seconds": null,
        "total_tokens": 24920,
        "wall_seconds": 8.011014
      }
    },
    {
      "caller": "textifier_codex_gpt_53_codex",
      "case_id": "C-IMG-CODE-01",
      "expected_output_format": "txt",
      "expected_status": "converted",
      "expected_suggested_paths": [
        "foo.py"
      ],
      "expected_textification_intent": "Extract the visible Python file and preserve the visible filename foo.py.",
      "fixture_metadata": {
        "mime_type": "image/png",
        "name": "foo.py.png",
        "path": "/Users/zeph/github/tzaffi/curio/tmp/textify-smoke/20260428-132551-09c3fa3c8f75/cases/C-IMG-CODE-01/fixtures/foo.py.png",
        "sha256": "eaf0ff4c9968e18d4ff4ea8692c524431a5e45a04030a76b9ba26bff79e68f96",
        "source_language_hint": null
      },
      "ground_truth_text": "FILE: foo.py\nDEF GREET(NAME):\n    PRINT(\"HOLA\", NAME)\nGREET(\"CURIO\")",
      "model_importance": 1,
      "output_format": [
        "txt"
      ],
      "participates_in_model_ranking": true,
      "preservation_requirements": [
        "foo.py",
        "DEF GREET(NAME):",
        "PRINT(\"HOLA\", NAME)",
        "GREET(\"CURIO\")"
      ],
      "rendered_textified_text": "DEF GREET(NAME):\n    PRINT(\"HOLA\", NAME)\nGREET(\"CURIO\")",
      "response_path": "runs/C-IMG-CODE-01/textifier_codex_gpt_53_codex/response.json",
      "response_warnings": [
        "OCR uncertainty: one character on the PRINT line is slightly unclear (interpreted as ')')."
      ],
      "status": "converted",
      "suggested_files": [
        {
          "output_format": "txt",
          "suggested_path": "foo.py",
          "text": "DEF GREET(NAME):\n    PRINT(\"HOLA\", NAME)\nGREET(\"CURIO\")"
        }
      ],
      "usage": {
        "api_equivalent_cost_usd": 0.05292385,
        "basis": "api_equivalent",
        "cached_input_price_per_million": 0.175,
        "cached_input_tokens": 22912,
        "completed_at": "2026-04-28T13:33:00.849717Z",
        "currency": "USD",
        "input_price_per_million": 1.75,
        "input_tokens": 24759,
        "metered_objects": [],
        "output_price_per_million": 14.0,
        "output_tokens": 399,
        "reasoning_tokens": 272,
        "started_at": "2026-04-28T13:32:48.408095Z",
        "thinking_seconds": null,
        "total_tokens": 25158,
        "wall_seconds": 12.441622
      }
    },
    {
      "caller": "textifier_codex_gpt_53_codex",
      "case_id": "C-IMG-CODE-02",
      "expected_output_format": "txt",
      "expected_status": "converted",
      "expected_suggested_paths": [
        "hello_curio.py"
      ],
      "expected_textification_intent": "Extract Python code and infer a safe .py filename from the script purpose.",
      "fixture_metadata": {
        "mime_type": "image/png",
        "name": "python-script-no-name.png",
        "path": "/Users/zeph/github/tzaffi/curio/tmp/textify-smoke/20260428-132551-09c3fa3c8f75/cases/C-IMG-CODE-02/fixtures/python-script-no-name.png",
        "sha256": "06ae9ca9570cdac8b591816c2f31d8ee526596d7845c7fa652c659b81affc484",
        "source_language_hint": null
      },
      "ground_truth_text": "DEF HELLO_CURIO():\n    RETURN \"HELLO CURIO\"\nPRINT(HELLO_CURIO())",
      "model_importance": 1,
      "output_format": [
        "txt"
      ],
      "participates_in_model_ranking": true,
      "preservation_requirements": [
        "HELLO_CURIO",
        "RETURN \"HELLO CURIO\"",
        "PRINT(HELLO_CURIO())"
      ],
      "rendered_textified_text": "DEF HELLO_CURIO():\n    RETURN \"HELLO CURIO\"\nPRINT(HELLO_CURIO())",
      "response_path": "runs/C-IMG-CODE-02/textifier_codex_gpt_53_codex/response.json",
      "response_warnings": [],
      "status": "converted",
      "suggested_files": [
        {
          "output_format": "txt",
          "suggested_path": "hello_curio.py",
          "text": "DEF HELLO_CURIO():\n    RETURN \"HELLO CURIO\"\nPRINT(HELLO_CURIO())"
        }
      ],
      "usage": {
        "api_equivalent_cost_usd": 0.050829099999999995,
        "basis": "api_equivalent",
        "cached_input_price_per_million": 0.175,
        "cached_input_tokens": 22912,
        "completed_at": "2026-04-28T13:33:11.584490Z",
        "currency": "USD",
        "input_price_per_million": 1.75,
        "input_tokens": 24770,
        "metered_objects": [],
        "output_price_per_million": 14.0,
        "output_tokens": 248,
        "reasoning_tokens": 134,
        "started_at": "2026-04-28T13:33:00.865517Z",
        "thinking_seconds": null,
        "total_tokens": 25018,
        "wall_seconds": 10.718973
      }
    },
    {
      "caller": "textifier_codex_gpt_53_codex",
      "case_id": "C-IMG-MULTI-01",
      "expected_output_format": "txt",
      "expected_status": "converted",
      "expected_suggested_paths": [
        "scripts/setup.sh",
        "scripts/run.sh",
        "scripts/cleanup.sh"
      ],
      "expected_textification_intent": "Split three visible shell script snippets into three safe relative .sh files.",
      "fixture_metadata": {
        "mime_type": "image/png",
        "name": "three-shell-scripts.png",
        "path": "/Users/zeph/github/tzaffi/curio/tmp/textify-smoke/20260428-132551-09c3fa3c8f75/cases/C-IMG-MULTI-01/fixtures/three-shell-scripts.png",
        "sha256": "8e66a9bd958ff978ca977166b50e98e4644531fb7e2024f66679f15cfdd5c5cb",
        "source_language_hint": null
      },
      "ground_truth_text": "FILE: scripts/setup.sh\nECHO SETUP\n\nFILE: scripts/run.sh\nECHO RUN\n\nFILE: scripts/cleanup.sh\nECHO CLEANUP",
      "model_importance": 1,
      "output_format": [
        "txt",
        "txt",
        "txt"
      ],
      "participates_in_model_ranking": true,
      "preservation_requirements": [
        "scripts/setup.sh",
        "scripts/run.sh",
        "scripts/cleanup.sh",
        "ECHO CLEANUP"
      ],
      "rendered_textified_text": "echo setup\n\necho run\n\necho cleanup",
      "response_path": "runs/C-IMG-MULTI-01/textifier_codex_gpt_53_codex/response.json",
      "response_warnings": [],
      "status": "converted",
      "suggested_files": [
        {
          "output_format": "txt",
          "suggested_path": "scripts/setup.sh",
          "text": "echo setup"
        },
        {
          "output_format": "txt",
          "suggested_path": "scripts/run.sh",
          "text": "echo run"
        },
        {
          "output_format": "txt",
          "suggested_path": "scripts/cleanup.sh",
          "text": "echo cleanup"
        }
      ],
      "usage": {
        "api_equivalent_cost_usd": 0.05010985,
        "basis": "api_equivalent",
        "cached_input_price_per_million": 0.175,
        "cached_input_tokens": 22912,
        "completed_at": "2026-04-28T13:33:19.994165Z",
        "currency": "USD",
        "input_price_per_million": 1.75,
        "input_tokens": 24887,
        "metered_objects": [],
        "output_price_per_million": 14.0,
        "output_tokens": 182,
        "reasoning_tokens": 53,
        "started_at": "2026-04-28T13:33:11.608071Z",
        "thinking_seconds": null,
        "total_tokens": 25069,
        "wall_seconds": 8.386094
      }
    },
    {
      "caller": "textifier_codex_gpt_53_codex",
      "case_id": "C-IMG-POST-01",
      "expected_output_format": "markdown",
      "expected_status": "converted",
      "expected_suggested_paths": [
        "social-post.md"
      ],
      "expected_textification_intent": "Preserve a social post's handle, timestamp, URL, emoji marker, and source language.",
      "fixture_metadata": {
        "mime_type": "image/png",
        "name": "social-post-es.png",
        "path": "/Users/zeph/github/tzaffi/curio/tmp/textify-smoke/20260428-132551-09c3fa3c8f75/cases/C-IMG-POST-01/fixtures/social-post-es.png",
        "sha256": "b3d6f2d21646f9fab10a3b6b44e888db7845ee31af66630d8bc50fbbeba922f1",
        "source_language_hint": "es"
      },
      "ground_truth_text": "@MARIA 2026-04-27 10:15\nNO TRADUZCAS /V1/CHAT\nVISITA HTTPS://EXAMPLE.COM\nEMOJI: ROCKET",
      "model_importance": 1,
      "output_format": [
        "markdown"
      ],
      "participates_in_model_ranking": true,
      "preservation_requirements": [
        "@MARIA",
        "2026-04-27 10:15",
        "/V1/CHAT",
        "HTTPS://EXAMPLE.COM",
        "ROCKET"
      ],
      "rendered_textified_text": "@MARIA 2026-04-27 10:15\nNO TRADUZCAS /V1/CHAT\nVISITA HTTPS://EXAMPLE.COM\nEMOJI: ROCKET",
      "response_path": "runs/C-IMG-POST-01/textifier_codex_gpt_53_codex/response.json",
      "response_warnings": [],
      "status": "converted",
      "suggested_files": [
        {
          "output_format": "markdown",
          "suggested_path": "social-post.md",
          "text": "@MARIA 2026-04-27 10:15\nNO TRADUZCAS /V1/CHAT\nVISITA HTTPS://EXAMPLE.COM\nEMOJI: ROCKET"
        }
      ],
      "usage": {
        "api_equivalent_cost_usd": 0.0509166,
        "basis": "api_equivalent",
        "cached_input_price_per_million": 0.175,
        "cached_input_tokens": 22912,
        "completed_at": "2026-04-28T13:33:27.070056Z",
        "currency": "USD",
        "input_price_per_million": 1.75,
        "input_tokens": 24788,
        "metered_objects": [],
        "output_price_per_million": 14.0,
        "output_tokens": 252,
        "reasoning_tokens": 124,
        "started_at": "2026-04-28T13:33:20.017204Z",
        "thinking_seconds": null,
        "total_tokens": 25040,
        "wall_seconds": 7.052852
      }
    },
    {
      "caller": "textifier_codex_gpt_53_codex",
      "case_id": "C-PDF-DOC-01",
      "expected_output_format": "markdown",
      "expected_status": "converted",
      "expected_suggested_paths": [
        "document.md"
      ],
      "expected_textification_intent": "Extract a one-page document with title, headings, paragraphs, and bullets.",
      "fixture_metadata": {
        "mime_type": "application/pdf",
        "name": "document-layout.pdf",
        "path": "/Users/zeph/github/tzaffi/curio/tmp/textify-smoke/20260428-132551-09c3fa3c8f75/cases/C-PDF-DOC-01/fixtures/document-layout.pdf",
        "sha256": "e04a909ad3499bb0f6252bc0eb6c765bbfbdb541d2b9d867341cdec7cbc1bbd0",
        "source_language_hint": null
      },
      "ground_truth_text": "Curio Release Plan\nGoals\n- Keep smoke tests opt-in\n- Preserve source language\nNext Steps\nRun make check",
      "model_importance": 1,
      "output_format": [
        "markdown"
      ],
      "participates_in_model_ranking": true,
      "preservation_requirements": [
        "Curio Release Plan",
        "Goals",
        "Keep smoke tests opt-in",
        "Run make check"
      ],
      "rendered_textified_text": "# Curio Release Plan\n\n## Goals\n\n- Keep smoke tests opt-in\n- Preserve source language\n\n## Next Steps\n\nRun make check",
      "response_path": "runs/C-PDF-DOC-01/textifier_codex_gpt_53_codex/response.json",
      "response_warnings": [],
      "status": "converted",
      "suggested_files": [
        {
          "output_format": "markdown",
          "suggested_path": "document.md",
          "text": "# Curio Release Plan\n\n## Goals\n\n- Keep smoke tests opt-in\n- Preserve source language\n\n## Next Steps\n\nRun make check"
        }
      ],
      "usage": {
        "api_equivalent_cost_usd": 0.3086832,
        "basis": "api_equivalent",
        "cached_input_price_per_million": 0.175,
        "cached_input_tokens": 148224,
        "completed_at": "2026-04-28T13:33:54.544135Z",
        "currency": "USD",
        "input_price_per_million": 1.75,
        "input_tokens": 152752,
        "metered_objects": [],
        "output_price_per_million": 14.0,
        "output_tokens": 1102,
        "reasoning_tokens": 200,
        "started_at": "2026-04-28T13:33:27.106015Z",
        "thinking_seconds": null,
        "total_tokens": 153854,
        "wall_seconds": 27.43812
      }
    },
    {
      "caller": "textifier_codex_gpt_53_codex",
      "case_id": "C-PDF-TABLE-01",
      "expected_output_format": "markdown",
      "expected_status": "converted",
      "expected_suggested_paths": [
        "table.md"
      ],
      "expected_textification_intent": "Extract a small table without swapping rows or columns.",
      "fixture_metadata": {
        "mime_type": "application/pdf",
        "name": "table-layout.pdf",
        "path": "/Users/zeph/github/tzaffi/curio/tmp/textify-smoke/20260428-132551-09c3fa3c8f75/cases/C-PDF-TABLE-01/fixtures/table-layout.pdf",
        "sha256": "766f1e57d76f62eb7a837862b1354f1c6714aa69a797c15f18bb635455333ec2",
        "source_language_hint": null
      },
      "ground_truth_text": "Service | Count | Status\nCodex | 3 | Ready\nDocAI | 1 | Punted\nOpenAI API | 0 | Punted",
      "model_importance": 1,
      "output_format": [
        "markdown"
      ],
      "participates_in_model_ranking": true,
      "preservation_requirements": [
        "Codex | 3 | Ready",
        "DocAI | 1 | Punted",
        "OpenAI API | 0 | Punted"
      ],
      "rendered_textified_text": "| Service | Count | Status |\n|---|---:|---|\n| Codex | 3 | Ready |\n| DocAI | 1 | Punted |\n| OpenAI API | 0 | Punted |",
      "response_path": "runs/C-PDF-TABLE-01/textifier_codex_gpt_53_codex/response.json",
      "response_warnings": [],
      "status": "converted",
      "suggested_files": [
        {
          "output_format": "markdown",
          "suggested_path": "table.md",
          "text": "| Service | Count | Status |\n|---|---:|---|\n| Codex | 3 | Ready |\n| DocAI | 1 | Punted |\n| OpenAI API | 0 | Punted |"
        }
      ],
      "usage": {
        "api_equivalent_cost_usd": 0.30853795,
        "basis": "api_equivalent",
        "cached_input_price_per_million": 0.175,
        "cached_input_tokens": 148224,
        "completed_at": "2026-04-28T13:34:19.845263Z",
        "currency": "USD",
        "input_price_per_million": 1.75,
        "input_tokens": 152845,
        "metered_objects": [],
        "output_price_per_million": 14.0,
        "output_tokens": 1080,
        "reasoning_tokens": 203,
        "started_at": "2026-04-28T13:33:54.555233Z",
        "thinking_seconds": null,
        "total_tokens": 153925,
        "wall_seconds": 25.29003
      }
    },
    {
      "caller": "textifier_codex_gpt_53_codex",
      "case_id": "C-IMG-RECEIPT-01",
      "expected_output_format": "markdown",
      "expected_status": "converted",
      "expected_suggested_paths": [
        "receipt.md"
      ],
      "expected_textification_intent": "Extract dense receipt-like labels, dates, amounts, and totals.",
      "fixture_metadata": {
        "mime_type": "image/png",
        "name": "receipt.png",
        "path": "/Users/zeph/github/tzaffi/curio/tmp/textify-smoke/20260428-132551-09c3fa3c8f75/cases/C-IMG-RECEIPT-01/fixtures/receipt.png",
        "sha256": "dacd233925e84d3f58cd4f21d6f9b967226de5d73e1723ce09d41e44a7aafb56",
        "source_language_hint": null
      },
      "ground_truth_text": "CURIO CAFE\nDATE 2026-04-27\nLATTE 4.50\nSANDWICH 8.25\nTOTAL 12.75",
      "model_importance": 1,
      "output_format": [
        "markdown"
      ],
      "participates_in_model_ranking": true,
      "preservation_requirements": [
        "2026-04-27",
        "LATTE 4.50",
        "SANDWICH 8.25",
        "TOTAL 12.75"
      ],
      "rendered_textified_text": "CURIO CAFE\nDATE 2026-04-27\nLATTE 4.50\nSANDWICH 8.25\nTOTAL 12.75",
      "response_path": "runs/C-IMG-RECEIPT-01/textifier_codex_gpt_53_codex/response.json",
      "response_warnings": [],
      "status": "converted",
      "suggested_files": [
        {
          "output_format": "markdown",
          "suggested_path": "receipt.md",
          "text": "CURIO CAFE\nDATE 2026-04-27\nLATTE 4.50\nSANDWICH 8.25\nTOTAL 12.75"
        }
      ],
      "usage": {
        "api_equivalent_cost_usd": 0.0493206,
        "basis": "api_equivalent",
        "cached_input_price_per_million": 0.175,
        "cached_input_tokens": 22912,
        "completed_at": "2026-04-28T13:34:27.227859Z",
        "currency": "USD",
        "input_price_per_million": 1.75,
        "input_tokens": 24764,
        "metered_objects": [],
        "output_price_per_million": 14.0,
        "output_tokens": 141,
        "reasoning_tokens": 18,
        "started_at": "2026-04-28T13:34:19.880633Z",
        "thinking_seconds": null,
        "total_tokens": 24905,
        "wall_seconds": 7.347226
      }
    },
    {
      "caller": "textifier_codex_gpt_53_codex",
      "case_id": "C-IMG-NO-TEXT-01",
      "expected_output_format": "markdown",
      "expected_status": "no_text_found",
      "expected_suggested_paths": [],
      "expected_textification_intent": "Return no_text_found for an image with no readable text and do not invent alt text.",
      "fixture_metadata": {
        "mime_type": "image/png",
        "name": "no-readable-text.png",
        "path": "/Users/zeph/github/tzaffi/curio/tmp/textify-smoke/20260428-132551-09c3fa3c8f75/cases/C-IMG-NO-TEXT-01/fixtures/no-readable-text.png",
        "sha256": "519ad675a14d7e9b1658dfe5d2e175c4a4ad9f35d946f9e04185940e1a1eb818",
        "source_language_hint": null
      },
      "ground_truth_text": "",
      "model_importance": 1,
      "output_format": [],
      "participates_in_model_ranking": true,
      "preservation_requirements": [
        "no invented description",
        "compact warning"
      ],
      "rendered_textified_text": "",
      "response_path": "runs/C-IMG-NO-TEXT-01/textifier_codex_gpt_53_codex/response.json",
      "response_warnings": [
        "No readable text detected in the image."
      ],
      "status": "no_text_found",
      "suggested_files": [],
      "usage": {
        "api_equivalent_cost_usd": 0.049199849999999996,
        "basis": "api_equivalent",
        "cached_input_price_per_million": 0.175,
        "cached_input_tokens": 22912,
        "completed_at": "2026-04-28T13:34:33.849257Z",
        "currency": "USD",
        "input_price_per_million": 1.75,
        "input_tokens": 24751,
        "metered_objects": [],
        "output_price_per_million": 14.0,
        "output_tokens": 134,
        "reasoning_tokens": 52,
        "started_at": "2026-04-28T13:34:27.494061Z",
        "thinking_seconds": null,
        "total_tokens": 24885,
        "wall_seconds": 6.355196
      }
    },
    {
      "caller": "textifier_codex_gpt_53_codex",
      "case_id": "R-IMG-DASH-01",
      "expected_output_format": "markdown",
      "expected_status": "converted",
      "expected_suggested_paths": [
        "claude-code-usage-dashboard.md"
      ],
      "expected_textification_intent": "Extract the dashboard title, filters, metric cards, charts, recent-session table, and visible numeric values into Markdown.",
      "fixture_metadata": {
        "mime_type": "image/jpeg",
        "name": "r-img-dash-01.jpg",
        "path": "/Users/zeph/github/tzaffi/curio/tmp/textify-smoke/20260428-132551-09c3fa3c8f75/cases/R-IMG-DASH-01/fixtures/r-img-dash-01.jpg",
        "sha256": "a74c7cb477b123bfc87dd97eb0c634786b6a4f537d387c2a96e5739d31d3118a",
        "source_language_hint": null
      },
      "ground_truth_text": "Claude Code Usage Dashboard\nSessions 440\nTurns 18.0K\nInput tokens 617.2K\nOutput tokens 4.75M\nCache read 1.95B\nEst. cost $1588.30",
      "model_importance": 9,
      "output_format": [
        "markdown"
      ],
      "participates_in_model_ranking": true,
      "preservation_requirements": [
        "Claude Code Usage Dashboard",
        "440",
        "18.0K",
        "617.2K",
        "4.75M",
        "$1588.30"
      ],
      "rendered_textified_text": "# Claude Code Usage Dashboard\n\nUpdated: 2026-04-07 20:56:27 · Auto-refresh in 30s\n\nMODELS\n- claude-opus-4-6\n- claude-sonnet-4-6\n- claude-haiku-4-5-20251001\n- All\n- None\n\nRANGE\n- 7d\n- 30d\n- 90d\n- All\n\n## Metrics\n\n### SESSIONS\n440  \nlast 30 days\n\n### TURNS\n18.0K  \nlast 30 days\n\n### INPUT TOKENS\n617.2K  \nlast 30 days\n\n### OUTPUT TOKENS\n4.75M  \nlast 30 days\n\n### CACHE READ\n1.95B  \nfrom prompt cache\n\n### CACHE CREATION\n74.66M  \nwrites to prompt cache\n\n### EST. COST\n$1588.30  \nAPI pricing, Apr 2026\n\n## DAILY TOKEN USAGE — LAST 30 DAYS\nLegend:\n- Input\n- Output\n- Cache Read\n- Cache Creation\n\nY-axis labels:\n- 0\n- 100.00M\n- 200.00M\n- 300.00M\n- 400.00M\n- 500.00M\n- 600.00M\n- 700.00M\n- 800.00M\n\nX-axis labels (visible):\n- 2026-03-08\n- 2026-03-10\n- 2026-03-14\n- 2026-03-16\n- 2026-03-18\n- 2026-03-20\n- 2026-03-22\n- 2026-03-24\n- 2026-03-26\n- 2026-03-28\n- 2026-03-30\n- 2026-04-01\n- 2026-04-03\n- 2026-04-05\n- 2026-04-07\n\n## BY MODEL\n- claude-opus-4-6\n- claude-sonnet-4-6\n- claude-haiku-4-5-20251001\n\n## TOP PROJECTS BY TOKENS\nLegend:\n- Input\n- Output\n\nProjects (visible):\n- Workspace/Editor\n- Artifacts/hassid\n- GitHub/SwarmProtocol\n- Dell/Desktop\n- ...e/agent-second-brain\n- worktrees/happy-wilson\n- worktrees/busy-curran\n- GitHub/Chatbot\n- ...rees/adoring-hermann\n- ...trees/trusting-raman\n\nX-axis labels:\n- 0\n- 500.0K\n- 1.00M\n- 1.50M\n- 2.00M\n- 2.50M\n- 3.00M\n\n## RECENT SESSIONS\n| SESSION | PROJECT | LAST ACTIVE | DURATION | MODEL | TURNS | INPUT | OUTPUT | EST. COST |\n|---|---|---|---|---|---:|---:|---:|---:|\n| 0d1902c1... | Dell/Desktop | 2026-04-07 17:09 | 7.8m | claude-sonnet-4-6 | 22 | 734 | 16.4K | $0.8485 |",
      "response_path": "runs/R-IMG-DASH-01/textifier_codex_gpt_53_codex/response.json",
      "response_warnings": [
        "Lower portion of the dashboard is cropped; only the first visible recent-session row is readable.",
        "Some project names are truncated with ellipses exactly as shown.",
        "Small chart values per bar are not individually readable at this resolution."
      ],
      "status": "converted",
      "suggested_files": [
        {
          "output_format": "markdown",
          "suggested_path": "claude-code-usage-dashboard.md",
          "text": "# Claude Code Usage Dashboard\n\nUpdated: 2026-04-07 20:56:27 · Auto-refresh in 30s\n\nMODELS\n- claude-opus-4-6\n- claude-sonnet-4-6\n- claude-haiku-4-5-20251001\n- All\n- None\n\nRANGE\n- 7d\n- 30d\n- 90d\n- All\n\n## Metrics\n\n### SESSIONS\n440  \nlast 30 days\n\n### TURNS\n18.0K  \nlast 30 days\n\n### INPUT TOKENS\n617.2K  \nlast 30 days\n\n### OUTPUT TOKENS\n4.75M  \nlast 30 days\n\n### CACHE READ\n1.95B  \nfrom prompt cache\n\n### CACHE CREATION\n74.66M  \nwrites to prompt cache\n\n### EST. COST\n$1588.30  \nAPI pricing, Apr 2026\n\n## DAILY TOKEN USAGE — LAST 30 DAYS\nLegend:\n- Input\n- Output\n- Cache Read\n- Cache Creation\n\nY-axis labels:\n- 0\n- 100.00M\n- 200.00M\n- 300.00M\n- 400.00M\n- 500.00M\n- 600.00M\n- 700.00M\n- 800.00M\n\nX-axis labels (visible):\n- 2026-03-08\n- 2026-03-10\n- 2026-03-14\n- 2026-03-16\n- 2026-03-18\n- 2026-03-20\n- 2026-03-22\n- 2026-03-24\n- 2026-03-26\n- 2026-03-28\n- 2026-03-30\n- 2026-04-01\n- 2026-04-03\n- 2026-04-05\n- 2026-04-07\n\n## BY MODEL\n- claude-opus-4-6\n- claude-sonnet-4-6\n- claude-haiku-4-5-20251001\n\n## TOP PROJECTS BY TOKENS\nLegend:\n- Input\n- Output\n\nProjects (visible):\n- Workspace/Editor\n- Artifacts/hassid\n- GitHub/SwarmProtocol\n- Dell/Desktop\n- ...e/agent-second-brain\n- worktrees/happy-wilson\n- worktrees/busy-curran\n- GitHub/Chatbot\n- ...rees/adoring-hermann\n- ...trees/trusting-raman\n\nX-axis labels:\n- 0\n- 500.0K\n- 1.00M\n- 1.50M\n- 2.00M\n- 2.50M\n- 3.00M\n\n## RECENT SESSIONS\n| SESSION | PROJECT | LAST ACTIVE | DURATION | MODEL | TURNS | INPUT | OUTPUT | EST. COST |\n|---|---|---|---|---|---:|---:|---:|---:|\n| 0d1902c1... | Dell/Desktop | 2026-04-07 17:09 | 7.8m | claude-sonnet-4-6 | 22 | 734 | 16.4K | $0.8485 |"
        }
      ],
      "usage": {
        "api_equivalent_cost_usd": 0.06310535,
        "basis": "api_equivalent",
        "cached_input_price_per_million": 0.175,
        "cached_input_tokens": 22912,
        "completed_at": "2026-04-28T13:34:45.885179Z",
        "currency": "USD",
        "input_price_per_million": 1.75,
        "input_tokens": 26193,
        "metered_objects": [],
        "output_price_per_million": 14.0,
        "output_tokens": 947,
        "reasoning_tokens": 37,
        "started_at": "2026-04-28T13:34:33.885686Z",
        "thinking_seconds": null,
        "total_tokens": 27140,
        "wall_seconds": 11.999493
      }
    },
    {
      "caller": "textifier_codex_gpt_53_codex",
      "case_id": "R-IMG-LLM-TABLE-01",
      "expected_output_format": "markdown",
      "expected_status": "converted",
      "expected_suggested_paths": [
        "local-llm-cheat-sheet.md"
      ],
      "expected_textification_intent": "Convert the dense local LLM cheat sheet into a Markdown table preserving model rows, weights, speed, context, use cases, and bottom line.",
      "fixture_metadata": {
        "mime_type": "image/jpeg",
        "name": "r-img-llm-table-01.jpg",
        "path": "/Users/zeph/github/tzaffi/curio/tmp/textify-smoke/20260428-132551-09c3fa3c8f75/cases/R-IMG-LLM-TABLE-01/fixtures/r-img-llm-table-01.jpg",
        "sha256": "9fc4f7a9c8958056c2aedac53d70614aeebfbffc64f1b9200b05a5eab1855de9",
        "source_language_hint": null
      },
      "ground_truth_text": "LOCAL LLM CHEAT SHEET\n128GB RAM\nQwen3.5-397B-A17B\nMistral Large 2411\nMiniMax-M2.7\nGLM-4.5-Air\nQwen3-VL-235B-A22B-Thinking\nBottom line: match it to your workflow.",
      "model_importance": 10,
      "output_format": [
        "markdown"
      ],
      "participates_in_model_ranking": true,
      "preservation_requirements": [
        "LOCAL LLM CHEAT SHEET",
        "128GB RAM",
        "Qwen3.5-397B-A17B",
        "MiniMax-M2.7",
        "Qwen3-VL-235B-A22B-Thinking",
        "Bottom line"
      ],
      "rendered_textified_text": "APRIL 24, 2026 • MAC STUDIO M ULTRA • WORKSTATION TIER\n\n# LOCAL LLM CHEAT SHEET\n\n## 128GB RAM\n\n### IMPORTANT FRAMING\nWeights size = GGUF file size on disk, not total runtime memory.\nReal RAM use = weights + 4–6GB OS + KV cache (~0.2GB per 10GB context) + misc.\nEven at this tier, 1M context is theoretical — plan for 64–256K in practice.\n\n| MODEL | WEIGHTS SIZE | SPEED | CONTEXT | BEST PICK | BEST USED FOR | HONEST TAKE |\n|---|---:|---|---|---|---|---|\n| 1) GENERAL PURPOSE & ALL-ROUNDERS |  |  |  |  |  |  |\n| Qwen3.5-397B-A17B (UD-IQ1_M • Recommended) | 106.82 GB | Medium (397B total / 17B active MoE.) | 262K (Native 262K context.) | BEST OVERALL / GENERAL ASSISTANT | general assistant; hardest reasoning; research; complex agents | Best overall. Strongest all-rounder on 128GB for reasoning, research, and agentic work. |\n| Mistral Large 2411 (Q4_K_M • Recommended) | 73.22 GB | Medium (Dense 123B at 4-bit. Heavier but still fast.) | 128K (Best-in-class European multilingual.) | BEST WRITING / MULTILINGUAL | creative writing; multilingual tasks; function calling; long-form prose | Excels on writing and multilingual tasks with strong function calling. Great for creative and business work. |\n| 2) CODING / AGENT / TOOL-USE KINGS |  |  |  |  |  |  |\n| MiniMax-M2.7 (UD-IQ2_XXS • Recommended) | 65.38 GB | Fast (229B total / 10B active MoE. Low-latency agent loops.) | 200K (Long enough for tool-call traces and agent loops.) | AGENT LOOPS | tool calling; multi-step coding; autonomous tasks | Strong purpose-built agent model. Excellent for tool use and autonomous workflows on 128GB. |\n| GLM-4.5-Air (Q6_K • Recommended) | 99.01 GB | Medium (106B total / 12B active MoE. Great speed-quality balance.) | 128K (Purpose-built for ARC, agent, and repo loops.) | CODING | SWE tasks; agent tool loops; repo diffs | Excellent coding/agent model with a strong balance of reasoning, repo work, and tool use. |\n| 3) MATH & COMPETITION REASONING |  |  |  |  |  |  |\n| Qwen3-235B-A22B-Thinking-2507 (UD-Q2_K_XL • Recommended) | 88.77 GB | Medium (235B total / 22B active MoE. Balanced reasoning language.) | 256K (Room for long reasoning traces, tricky math, and code windows.) | BEST MATH & REASONING PICK | competition math; structured solving; analysis; deep logic | Elite reasoning model for math and structured problem solving. Not the best everyday general chat model. |\n| gpt-oss-120b (Q8_0 • Recommended) | 63.39 GB | Fast (MXFP4-native weights, Q8_0. Is effectively full precision at 63 GB.) | 128K (Solid long-context for reasoning; efficient on unified memory.) | MATH & EFFICIENCY VETERAN | math olympiad; hard reasoning; general assistant; code | Excellent older model (Aug 2025). MXFP4-native means Q8_0 is full precision. Still extremely strong on olympiad tasks and efficient on unified memory. |\n| 4) VISION & MULTIMODAL |  |  |  |  |  |  |\n| Qwen3-VL-235B-A22B-Thinking | 94.73 GB | Medium (235B total / 22B active MoE. Vision agent overhead on long images.) | 128K (Multimodal: image, text, native vision support via llama.cpp.) | BEST VISION THINKER | image understanding; vision reasoning; charts & docs; OCR & layout | Same reasoning core as Qwen3-235B-Thinking plus vision. Great for docs, diagrams, charts, and technical reports. |\n| 5) LONG-CONTEXT / RESEARCH / FAST THINKERS |  |  |  |  |  |  |\n| Llama-4-Scout 17Bx16E (Q6_K • Recommended) | 88.43 GB | Fast (109B total / 17B active MoE.) | 10M (Native 10M context window; best for huge codebases, corpora, archives.) | BEST LONG-CONTEXT RESEARCH PICK | massive documents; multimodal ingest; research corpora; long-context QA | Unmatched for huge-context work. Best when you truly need 10M context; weaker than top picks on raw reasoning. |\n| Qwen3-Next-80B-A3B-Thinking (Q6_K • Recommended) | 65.79 GB | Very fast (80B total / 3B active MoE. Hybrid attention keeps latency low on long context.) | 256K (Hybrid attention keeps latency low on long context.) | BEST FAST THINKER | fast reasoning; interactive math; long-context loops; agent planning | Best reasoning-per-second on the sheet. Pick it for fast, responsive thinking and interactive use, not deepest reasoning. |\n\n## BOTTOM LINE\n128GB advice: Model choice is highly use-case dependent. Qwen3.5-397B-A17B is the strongest all-rounder. Pick MiniMax-M2.7 or GLM-4.5-Air for agent/coding work, gpt-oss-120b for math/efficiency, and the specialists for vision or 10M+ context. There is no single “best” model — match it to your workflow.\n\n@gkisokay",
      "response_path": "runs/R-IMG-LLM-TABLE-01/textifier_codex_gpt_53_codex/response.json",
      "response_warnings": [
        "Dense infographic; some small benchmark/source lines are partially unreadable.",
        "Minor OCR uncertainty in model metadata tokens (e.g., quantization suffixes and benchmark labels).",
        "Layout text was normalized into a Markdown table; exact visual spacing and color-tag grouping are not preserved."
      ],
      "status": "converted",
      "suggested_files": [
        {
          "output_format": "markdown",
          "suggested_path": "local-llm-cheat-sheet.md",
          "text": "APRIL 24, 2026 • MAC STUDIO M ULTRA • WORKSTATION TIER\n\n# LOCAL LLM CHEAT SHEET\n\n## 128GB RAM\n\n### IMPORTANT FRAMING\nWeights size = GGUF file size on disk, not total runtime memory.\nReal RAM use = weights + 4–6GB OS + KV cache (~0.2GB per 10GB context) + misc.\nEven at this tier, 1M context is theoretical — plan for 64–256K in practice.\n\n| MODEL | WEIGHTS SIZE | SPEED | CONTEXT | BEST PICK | BEST USED FOR | HONEST TAKE |\n|---|---:|---|---|---|---|---|\n| 1) GENERAL PURPOSE & ALL-ROUNDERS |  |  |  |  |  |  |\n| Qwen3.5-397B-A17B (UD-IQ1_M • Recommended) | 106.82 GB | Medium (397B total / 17B active MoE.) | 262K (Native 262K context.) | BEST OVERALL / GENERAL ASSISTANT | general assistant; hardest reasoning; research; complex agents | Best overall. Strongest all-rounder on 128GB for reasoning, research, and agentic work. |\n| Mistral Large 2411 (Q4_K_M • Recommended) | 73.22 GB | Medium (Dense 123B at 4-bit. Heavier but still fast.) | 128K (Best-in-class European multilingual.) | BEST WRITING / MULTILINGUAL | creative writing; multilingual tasks; function calling; long-form prose | Excels on writing and multilingual tasks with strong function calling. Great for creative and business work. |\n| 2) CODING / AGENT / TOOL-USE KINGS |  |  |  |  |  |  |\n| MiniMax-M2.7 (UD-IQ2_XXS • Recommended) | 65.38 GB | Fast (229B total / 10B active MoE. Low-latency agent loops.) | 200K (Long enough for tool-call traces and agent loops.) | AGENT LOOPS | tool calling; multi-step coding; autonomous tasks | Strong purpose-built agent model. Excellent for tool use and autonomous workflows on 128GB. |\n| GLM-4.5-Air (Q6_K • Recommended) | 99.01 GB | Medium (106B total / 12B active MoE. Great speed-quality balance.) | 128K (Purpose-built for ARC, agent, and repo loops.) | CODING | SWE tasks; agent tool loops; repo diffs | Excellent coding/agent model with a strong balance of reasoning, repo work, and tool use. |\n| 3) MATH & COMPETITION REASONING |  |  |  |  |  |  |\n| Qwen3-235B-A22B-Thinking-2507 (UD-Q2_K_XL • Recommended) | 88.77 GB | Medium (235B total / 22B active MoE. Balanced reasoning language.) | 256K (Room for long reasoning traces, tricky math, and code windows.) | BEST MATH & REASONING PICK | competition math; structured solving; analysis; deep logic | Elite reasoning model for math and structured problem solving. Not the best everyday general chat model. |\n| gpt-oss-120b (Q8_0 • Recommended) | 63.39 GB | Fast (MXFP4-native weights, Q8_0. Is effectively full precision at 63 GB.) | 128K (Solid long-context for reasoning; efficient on unified memory.) | MATH & EFFICIENCY VETERAN | math olympiad; hard reasoning; general assistant; code | Excellent older model (Aug 2025). MXFP4-native means Q8_0 is full precision. Still extremely strong on olympiad tasks and efficient on unified memory. |\n| 4) VISION & MULTIMODAL |  |  |  |  |  |  |\n| Qwen3-VL-235B-A22B-Thinking | 94.73 GB | Medium (235B total / 22B active MoE. Vision agent overhead on long images.) | 128K (Multimodal: image, text, native vision support via llama.cpp.) | BEST VISION THINKER | image understanding; vision reasoning; charts & docs; OCR & layout | Same reasoning core as Qwen3-235B-Thinking plus vision. Great for docs, diagrams, charts, and technical reports. |\n| 5) LONG-CONTEXT / RESEARCH / FAST THINKERS |  |  |  |  |  |  |\n| Llama-4-Scout 17Bx16E (Q6_K • Recommended) | 88.43 GB | Fast (109B total / 17B active MoE.) | 10M (Native 10M context window; best for huge codebases, corpora, archives.) | BEST LONG-CONTEXT RESEARCH PICK | massive documents; multimodal ingest; research corpora; long-context QA | Unmatched for huge-context work. Best when you truly need 10M context; weaker than top picks on raw reasoning. |\n| Qwen3-Next-80B-A3B-Thinking (Q6_K • Recommended) | 65.79 GB | Very fast (80B total / 3B active MoE. Hybrid attention keeps latency low on long context.) | 256K (Hybrid attention keeps latency low on long context.) | BEST FAST THINKER | fast reasoning; interactive math; long-context loops; agent planning | Best reasoning-per-second on the sheet. Pick it for fast, responsive thinking and interactive use, not deepest reasoning. |\n\n## BOTTOM LINE\n128GB advice: Model choice is highly use-case dependent. Qwen3.5-397B-A17B is the strongest all-rounder. Pick MiniMax-M2.7 or GLM-4.5-Air for agent/coding work, gpt-oss-120b for math/efficiency, and the specialists for vision or 10M+ context. There is no single “best” model — match it to your workflow.\n\n@gkisokay"
        }
      ],
      "usage": {
        "api_equivalent_cost_usd": 0.07101360000000001,
        "basis": "api_equivalent",
        "cached_input_price_per_million": 0.175,
        "cached_input_tokens": 22912,
        "completed_at": "2026-04-28T13:35:05.037323Z",
        "currency": "USD",
        "input_price_per_million": 1.75,
        "input_tokens": 26104,
        "metered_objects": [],
        "output_price_per_million": 14.0,
        "output_tokens": 1523,
        "reasoning_tokens": 30,
        "started_at": "2026-04-28T13:34:45.923111Z",
        "thinking_seconds": null,
        "total_tokens": 27627,
        "wall_seconds": 19.114212
      }
    },
    {
      "caller": "textifier_codex_gpt_53_codex",
      "case_id": "R-IMG-INFOGRAPHIC-01",
      "expected_output_format": "markdown",
      "expected_status": "converted",
      "expected_suggested_paths": [
        "hermes-agent.md"
      ],
      "expected_textification_intent": "Extract the chalkboard-style Hermes Agent infographic into structured Markdown with commands, section labels, provider lists, and gateway labels.",
      "fixture_metadata": {
        "mime_type": "image/jpeg",
        "name": "r-img-infographic-01.jpg",
        "path": "/Users/zeph/github/tzaffi/curio/tmp/textify-smoke/20260428-132551-09c3fa3c8f75/cases/R-IMG-INFOGRAPHIC-01/fixtures/r-img-infographic-01.jpg",
        "sha256": "0405a18638feeee817b4e4a3a71c39cfb2426fbb936f981bd8cd762768d7ebe3",
        "source_language_hint": null
      },
      "ground_truth_text": "Hermes Agent\nThe CLI AI Agent by Nous Research\nFrom zero to chat in 3 steps\ncurl -fsSL .../install.sh | bash\nPick Provider\nChat\nCore Tools\nAny model. No lock-in.\nMessaging gateways",
      "model_importance": 10,
      "output_format": [
        "markdown"
      ],
      "participates_in_model_ranking": true,
      "preservation_requirements": [
        "Hermes Agent",
        "curl -fsSL",
        "Pick Provider",
        "Core Tools",
        "Any model. No lock-in.",
        "Messaging gateways"
      ],
      "rendered_textified_text": "# Hermes Agent\n\nThe CLI AI Agent by Nous Research  \nLearns. Remembers. Works everywhere.\n\n## From zero to chat in 3 steps\n\n1. `curl -fsSL .../install.sh | bash`\n2. Pick Provider  \n   `hermes model`\n3. Chat  \n   `hermes`  \n   or `hermes --tui`\n\n## Core Tools\n\n- Terminal\n- Files\n- Web\n- Browser\n- Vision\n- Image Gen\n- TTS\n- MCP\n\n## What makes it an agent\n\n- Skills\n- Memory\n- Context Files\n- Cron\n- Delegation\n- Code Execution\n- Hooks\n- Batch\n- RL Training\n- Provider Routing\n\n## Any model. No lock-in.\n\n- Nous Portal\n- Anthropic\n- OpenRouter\n- OpenAI Codex\n- Qwen\n- Google Gemini\n- xAI Grok\n- GitHub Copilot\n- Kimi\n- DeepSeek\n- Ollama\n- Hugging Face\n- NVIDIA NIM\n- Bedrock\n- MiniMax\n- + many more\n\nMin context 64K tokens  \n`hermes model`\n\n## Messaging gateways\n\n- Telegram\n- Slack\n- Signal\n- Email\n- Discord\n- WhatsApp\n- Matrix\n- SMS\n- Home Assistant\n- +more\n\n`hermes gateway setup`\n\n## Sandbox when you want\n\nlocal · docker · ssh · modal · daytona · singularity\n\n## Automate in plain English\n\n“Every morning at 9am, check Hacker News for AI news and send me a summary on Telegram.”\n\n→ Hermes sets up the cron job automatically.",
      "response_path": "runs/R-IMG-INFOGRAPHIC-01/textifier_codex_gpt_53_codex/response.json",
      "response_warnings": [
        "Minor OCR uncertainty in small decorative/low-contrast text regions.",
        "Some tiny symbols and flourishes are non-text and were omitted."
      ],
      "status": "converted",
      "suggested_files": [
        {
          "output_format": "markdown",
          "suggested_path": "hermes-agent.md",
          "text": "# Hermes Agent\n\nThe CLI AI Agent by Nous Research  \nLearns. Remembers. Works everywhere.\n\n## From zero to chat in 3 steps\n\n1. `curl -fsSL .../install.sh | bash`\n2. Pick Provider  \n   `hermes model`\n3. Chat  \n   `hermes`  \n   or `hermes --tui`\n\n## Core Tools\n\n- Terminal\n- Files\n- Web\n- Browser\n- Vision\n- Image Gen\n- TTS\n- MCP\n\n## What makes it an agent\n\n- Skills\n- Memory\n- Context Files\n- Cron\n- Delegation\n- Code Execution\n- Hooks\n- Batch\n- RL Training\n- Provider Routing\n\n## Any model. No lock-in.\n\n- Nous Portal\n- Anthropic\n- OpenRouter\n- OpenAI Codex\n- Qwen\n- Google Gemini\n- xAI Grok\n- GitHub Copilot\n- Kimi\n- DeepSeek\n- Ollama\n- Hugging Face\n- NVIDIA NIM\n- Bedrock\n- MiniMax\n- + many more\n\nMin context 64K tokens  \n`hermes model`\n\n## Messaging gateways\n\n- Telegram\n- Slack\n- Signal\n- Email\n- Discord\n- WhatsApp\n- Matrix\n- SMS\n- Home Assistant\n- +more\n\n`hermes gateway setup`\n\n## Sandbox when you want\n\nlocal · docker · ssh · modal · daytona · singularity\n\n## Automate in plain English\n\n“Every morning at 9am, check Hacker News for AI news and send me a summary on Telegram.”\n\n→ Hermes sets up the cron job automatically."
        }
      ],
      "usage": {
        "api_equivalent_cost_usd": 0.05671435,
        "basis": "api_equivalent",
        "cached_input_price_per_million": 0.175,
        "cached_input_tokens": 22912,
        "completed_at": "2026-04-28T13:35:17.539962Z",
        "currency": "USD",
        "input_price_per_million": 1.75,
        "input_tokens": 25693,
        "metered_objects": [],
        "output_price_per_million": 14.0,
        "output_tokens": 553,
        "reasoning_tokens": 54,
        "started_at": "2026-04-28T13:35:05.049361Z",
        "thinking_seconds": null,
        "total_tokens": 26246,
        "wall_seconds": 12.490601
      }
    },
    {
      "caller": "textifier_codex_gpt_53_codex",
      "case_id": "R-IMG-PAPER-PAGE-01",
      "expected_output_format": "markdown",
      "expected_status": "converted",
      "expected_suggested_paths": [
        "openclaw-rl.md"
      ],
      "expected_textification_intent": "Extract the academic paper page with title, authors, GitHub link, abstract, figure caption, and diagram labels into Markdown.",
      "fixture_metadata": {
        "mime_type": "image/png",
        "name": "r-img-paper-page-01.png",
        "path": "/Users/zeph/github/tzaffi/curio/tmp/textify-smoke/20260428-132551-09c3fa3c8f75/cases/R-IMG-PAPER-PAGE-01/fixtures/r-img-paper-page-01.png",
        "sha256": "3989e8b2dbb1992196f6c3302667b3a98ff911c5c717773a101fd896e37e87b8",
        "source_language_hint": null
      },
      "ground_truth_text": "OpenClaw-RL: Train Any Agent Simply by Talking\nYinjie Wang\nhttps://github.com/Gen-Verse/OpenClaw-RL\nEvery agent interaction generates a next-state signal\nFigure 1 OpenClaw-RL infrastructure overview",
      "model_importance": 9,
      "output_format": [
        "markdown"
      ],
      "participates_in_model_ranking": true,
      "preservation_requirements": [
        "OpenClaw-RL",
        "Train Any Agent Simply by Talking",
        "Gen-Verse/OpenClaw-RL",
        "next-state signal",
        "Figure 1"
      ],
      "rendered_textified_text": "Princeton University  \nOpenClaw-RL\n\n# OpenClaw-RL: Train Any Agent Simply by Talking\n\n**Yinjie Wang\\***, **Xuyang Chen\\***, **Xiaolong Jin\\***, **Mengdi Wang\\*†**, **Ling Yang†**\n\nGitHub: https://github.com/Gen-Verse/OpenClaw-RL\n\nEvery agent interaction generates a **next-state signal**, namely the user reply, tool output, terminal or GUI state change that follows each action, yet no existing agentic RL system recovers it as a live, online learning source. We present **OpenClaw-RL**, a framework built on a simple observation: next-state signals are universal, and policy can learn from all of them simultaneously. Personal conversations, terminal executions, GUI interactions, SWE tasks, and tool-call traces are not separate training problems. They are all interactions that can be used to train the same policy in the same loop. Next-state signals encode two forms of information: **evaluative signals**, which indicate how well the action performed and are extracted as scalar rewards via a PRM judge; and **directive signals**, which indicate how the action should have been different and are recovered through **Hindsight-Guided On-Policy Distillation (OPD)**. We extract textual hints from the next state, construct an enhanced teacher context, and provide token-level directional advantage supervision that is richer than any scalar reward. Due to the asynchronous design, the model serves live requests, the PRM judges ongoing interactions, and the trainer updates the policy at the same time, with zero coordination overhead between them. Applied to **personal agents**, OpenClaw-RL enables an agent to improve simply by being used, recovering conversational signals from user re-queries, corrections, and explicit feedback. Applied to **general agents**, the same infrastructure supports scalable RL across terminal, GUI, SWE, and tool-call settings, where we additionally demonstrate the utility of process rewards.\n\n## Figure 1 | OpenClaw-RL infrastructure overview\n\n### Diagram text\n\n- Personal Agents\n  - OpenClaw\n- General Agents\n  - Terminal Agent\n  - GUI Agent\n  - SWE Agent\n  - Tool-call Agent\n- OpenClaw-RL\n- Environment Servers\n  - Personal Devices\n    - Confidential API Keys\n  - Cloud Services\n    - Large Scale Environments\n- RL Server\n  - Same Async Framework\n  - Zero Serving Interruption\n  - Graceful Weight Update\n- Training Engine (Megatron)\n- Policy Server (SGLang)\n- PRM Server (SGLang/API)\n- data\n\nFigure 1 | **OpenClaw-RL infrastructure overview.** Interaction streams come from two agent types: *Personal Agents* (conversational, single-user), hosted on personal devices, and *General Agents* (terminal, GUI, SWE, and tool-call agents), hosted on cloud services. The collected samples flow into our RL server built on the asynchronous slime framework, which consists of four decoupled components: (1) the environment server, (2) PRM/Judge for reward computation, (3) Megatron for policy training, and (4) SGLang for policy serving. These components support graceful weight updates and enable training with any agentic framework. The environment for personal agents is simply the users’ personal devices, which connect to the RL server over HTTP with confidential API keys. The environments for general agents are hosted on cloud services to enable scalable parallelization.\n\n\\* Equal contribution; † Corresponding authors; Main contact: yangling0818@163.com\n\narXiv:2603.10165v1 [cs.CL] 10 Mar 2026",
      "response_path": "runs/R-IMG-PAPER-PAGE-01/textifier_codex_gpt_53_codex/response.json",
      "response_warnings": [
        "Minor OCR uncertainty in author superscripts/symbols and small footer text.",
        "Some diagram labels may have slight punctuation/capitalization ambiguity due to image resolution."
      ],
      "status": "converted",
      "suggested_files": [
        {
          "output_format": "markdown",
          "suggested_path": "openclaw-rl.md",
          "text": "Princeton University  \nOpenClaw-RL\n\n# OpenClaw-RL: Train Any Agent Simply by Talking\n\n**Yinjie Wang\\***, **Xuyang Chen\\***, **Xiaolong Jin\\***, **Mengdi Wang\\*†**, **Ling Yang†**\n\nGitHub: https://github.com/Gen-Verse/OpenClaw-RL\n\nEvery agent interaction generates a **next-state signal**, namely the user reply, tool output, terminal or GUI state change that follows each action, yet no existing agentic RL system recovers it as a live, online learning source. We present **OpenClaw-RL**, a framework built on a simple observation: next-state signals are universal, and policy can learn from all of them simultaneously. Personal conversations, terminal executions, GUI interactions, SWE tasks, and tool-call traces are not separate training problems. They are all interactions that can be used to train the same policy in the same loop. Next-state signals encode two forms of information: **evaluative signals**, which indicate how well the action performed and are extracted as scalar rewards via a PRM judge; and **directive signals**, which indicate how the action should have been different and are recovered through **Hindsight-Guided On-Policy Distillation (OPD)**. We extract textual hints from the next state, construct an enhanced teacher context, and provide token-level directional advantage supervision that is richer than any scalar reward. Due to the asynchronous design, the model serves live requests, the PRM judges ongoing interactions, and the trainer updates the policy at the same time, with zero coordination overhead between them. Applied to **personal agents**, OpenClaw-RL enables an agent to improve simply by being used, recovering conversational signals from user re-queries, corrections, and explicit feedback. Applied to **general agents**, the same infrastructure supports scalable RL across terminal, GUI, SWE, and tool-call settings, where we additionally demonstrate the utility of process rewards.\n\n## Figure 1 | OpenClaw-RL infrastructure overview\n\n### Diagram text\n\n- Personal Agents\n  - OpenClaw\n- General Agents\n  - Terminal Agent\n  - GUI Agent\n  - SWE Agent\n  - Tool-call Agent\n- OpenClaw-RL\n- Environment Servers\n  - Personal Devices\n    - Confidential API Keys\n  - Cloud Services\n    - Large Scale Environments\n- RL Server\n  - Same Async Framework\n  - Zero Serving Interruption\n  - Graceful Weight Update\n- Training Engine (Megatron)\n- Policy Server (SGLang)\n- PRM Server (SGLang/API)\n- data\n\nFigure 1 | **OpenClaw-RL infrastructure overview.** Interaction streams come from two agent types: *Personal Agents* (conversational, single-user), hosted on personal devices, and *General Agents* (terminal, GUI, SWE, and tool-call agents), hosted on cloud services. The collected samples flow into our RL server built on the asynchronous slime framework, which consists of four decoupled components: (1) the environment server, (2) PRM/Judge for reward computation, (3) Megatron for policy training, and (4) SGLang for policy serving. These components support graceful weight updates and enable training with any agentic framework. The environment for personal agents is simply the users’ personal devices, which connect to the RL server over HTTP with confidential API keys. The environments for general agents are hosted on cloud services to enable scalable parallelization.\n\n\\* Equal contribution; † Corresponding authors; Main contact: yangling0818@163.com\n\narXiv:2603.10165v1 [cs.CL] 10 Mar 2026"
        }
      ],
      "usage": {
        "api_equivalent_cost_usd": 0.0614943,
        "basis": "api_equivalent",
        "cached_input_price_per_million": 0.175,
        "cached_input_tokens": 23936,
        "completed_at": "2026-04-28T13:35:33.586756Z",
        "currency": "USD",
        "input_price_per_million": 1.75,
        "input_tokens": 25266,
        "metered_objects": [],
        "output_price_per_million": 14.0,
        "output_tokens": 935,
        "reasoning_tokens": 28,
        "started_at": "2026-04-28T13:35:17.547189Z",
        "thinking_seconds": null,
        "total_tokens": 26201,
        "wall_seconds": 16.039567
      }
    },
    {
      "caller": "textifier_codex_gpt_53_codex",
      "case_id": "R-IMG-CHARTS-01",
      "expected_output_format": "markdown",
      "expected_status": "converted",
      "expected_suggested_paths": [
        "agent-benchmarks.md"
      ],
      "expected_textification_intent": "Extract both benchmark bar charts into Markdown tables with system names and percentages.",
      "fixture_metadata": {
        "mime_type": "image/jpeg",
        "name": "r-img-charts-01.jpg",
        "path": "/Users/zeph/github/tzaffi/curio/tmp/textify-smoke/20260428-132551-09c3fa3c8f75/cases/R-IMG-CHARTS-01/fixtures/r-img-charts-01.jpg",
        "sha256": "6963044d99e19d448472a7e223c36cb85494db523b99b7547cfe6c9d13d0b778",
        "source_language_hint": null
      },
      "ground_truth_text": "SpreadsheetBench\nAutoAgent 96.5%\nTetra-Beta-2 94.2%\nTerminalBench (GPT-5)\nAutoAgent 55.1%\nCodex CLI 49.6%",
      "model_importance": 8,
      "output_format": [
        "markdown"
      ],
      "participates_in_model_ranking": true,
      "preservation_requirements": [
        "SpreadsheetBench",
        "TerminalBench",
        "AutoAgent 96.5%",
        "AutoAgent 55.1%",
        "Codex CLI 49.6%"
      ],
      "rendered_textified_text": "# SpreadSheetBench\n\n| System | Percentage |\n|---|---:|\n| AutoAgent | 96.5% |\n| Tetra-Beta-2 | 94.2% |\n| Noble Agent | 91.0% |\n| Qingqiu Agent | 89.2% |\n| Shortcut.ai | 86.0% |\n\n# TerminalBench (GPT-5)\n\n| System | Percentage |\n|---|---:|\n| AutoAgent | 55.1% |\n| Codex CLI | 49.6% |\n| OpenHands | 43.8% |\n| Terminus 2 | 35.2% |\n| Mini-SWE-Agent | 33.9% |",
      "response_path": "runs/R-IMG-CHARTS-01/textifier_codex_gpt_53_codex/response.json",
      "response_warnings": [
        "Axis label text is faint/low-contrast and may be partially unreadable."
      ],
      "status": "converted",
      "suggested_files": [
        {
          "output_format": "markdown",
          "suggested_path": "agent-benchmarks.md",
          "text": "# SpreadSheetBench\n\n| System | Percentage |\n|---|---:|\n| AutoAgent | 96.5% |\n| Tetra-Beta-2 | 94.2% |\n| Noble Agent | 91.0% |\n| Qingqiu Agent | 89.2% |\n| Shortcut.ai | 86.0% |\n\n# TerminalBench (GPT-5)\n\n| System | Percentage |\n|---|---:|\n| AutoAgent | 55.1% |\n| Codex CLI | 49.6% |\n| OpenHands | 43.8% |\n| Terminus 2 | 35.2% |\n| Mini-SWE-Agent | 33.9% |"
        }
      ],
      "usage": {
        "api_equivalent_cost_usd": 0.0527471,
        "basis": "api_equivalent",
        "cached_input_price_per_million": 0.175,
        "cached_input_tokens": 22912,
        "completed_at": "2026-04-28T13:35:41.516421Z",
        "currency": "USD",
        "input_price_per_million": 1.75,
        "input_tokens": 25298,
        "metered_objects": [],
        "output_price_per_million": 14.0,
        "output_tokens": 319,
        "reasoning_tokens": 44,
        "started_at": "2026-04-28T13:35:33.598972Z",
        "thinking_seconds": null,
        "total_tokens": 25617,
        "wall_seconds": 7.917449
      }
    },
    {
      "caller": "textifier_codex_gpt_53_codex",
      "case_id": "R-IMG-TERMINAL-01",
      "expected_output_format": "txt",
      "expected_status": "converted",
      "expected_suggested_paths": [
        "claude-code-listing.log"
      ],
      "expected_textification_intent": "Transcribe the terminal session as a log, preserving command lines, permissions columns, file sizes, timestamps, and filenames.",
      "fixture_metadata": {
        "mime_type": "image/png",
        "name": "r-img-terminal-01.png",
        "path": "/Users/zeph/github/tzaffi/curio/tmp/textify-smoke/20260428-132551-09c3fa3c8f75/cases/R-IMG-TERMINAL-01/fixtures/r-img-terminal-01.png",
        "sha256": "e1c5b1945a3db39ed228e143b3202da12b86f936f7c55f1407e9aa5fb617b7fa",
        "source_language_hint": null
      },
      "ground_truth_text": "ls -alht cli.js.map\nls -alht src\ntotal 2304\nmain.tsx\ncommands\nQueryEngine.ts\ncontext.ts",
      "model_importance": 8,
      "output_format": [
        "txt"
      ],
      "participates_in_model_ranking": true,
      "preservation_requirements": [
        "ls -alht",
        "total 2304",
        "main.tsx",
        "commands",
        "QueryEngine.ts",
        "context.ts"
      ],
      "rendered_textified_text": "showdev claude-code % ls -alh cli.js.map\n-rw-r--r--  1 shou  staff   57M Mar 31 01:16 cli.js.map\nshowdev claude-code % ls -alh src\ntotal 2304\ndrwxr-xr-x   8 shou  staff   256B Mar 31 01:17 entrypoints\n-rw-r--r--   1 shou  staff   785K Mar 31 01:17 main.tsx\ndrwxr-xr-x  55 shou  staff   1.7K Mar 31 01:17 cli\ndrwxr-xr-x  10 shou  staff   320B Mar 31 01:17 commands\ndrwxr-xr-x 103 shou  staff   3.2K Mar 31 01:17 utils\ndrwxr-xr-x 331 shou  staff    10K Mar 31 01:17 components\n-rw-r--r-- 146 shou  staff   4.6K Mar 31 01:17 QueryEngine.ts\n-rw-r--r--   1 shou  staff    46K Mar 31 01:17 setup.ts\ndrwxr-xr-x   5 shou  staff   160B Mar 31 01:17 server\ndrwxr-xr-x  13 shou  staff   416B Mar 31 01:17 migrations\ndrwxr-xr-x  16 shou  staff   512B Mar 31 01:17 keybindings\ndrwxr-xr-x   6 shou  staff   192B Mar 31 01:17 skills\ndrwxr-xr-x   4 shou  staff   128B Mar 31 01:17 plugins\n-rw-r--r--   1 shou  staff    22K Mar 31 01:17 dialogLaunchers.tsx\ndrwxr-xr-x   5 shou  staff   160B Mar 31 01:17 screens\n-rw-r--r--  87 shou  staff   2.7K Mar 31 01:17 hooks\n-rw-r--r--   1 shou  staff    56K Mar 31 01:17 interactiveHelpers.tsx\ndrwxr-xr-x  38 shou  staff   1.2K Mar 31 01:17 services\n-rw-r--r--   1 shou  staff   3.4K Mar 31 01:17 replLauncher.tsx\n-rw-r--r--   1 shou  staff   617B Mar 31 01:17 costHook.ts\n-drwxr-xr-x  3 shou  staff    96B Mar 31 01:17 moreright\n-drwxr-xr-x  3 shou  staff    96B Mar 31 01:17 assistant\n-drwxr-xr-x  6 shou  staff   192B Mar 31 01:17 remote\ndrwxr-xr-x   7 shou  staff   224B Mar 31 01:17 vim\ndrwxr-xr-x   8 shou  staff   256B Mar 31 01:17 buddy\ndrwxr-xr-x  33 shou  staff   1.0K Mar 31 01:17 bridge\ndrwxr-xr-x   8 shou  staff   256B Mar 31 01:17 state\ndrwxr-xr-x  11 shou  staff   352B Mar 31 01:17 context\ndrwxr-xr-x   4 shou  staff   128B Mar 31 01:17 upstreamproxy\ndrwxr-xr-x  23 shou  staff   736B Mar 31 01:17 constants\ndrwxr-xr-x  10 shou  staff   320B Mar 31 01:17 types\n-rw-r--r--   1 shou  staff   3.1K Mar 31 01:17 Task.ts\n-drwxr-xr-x 10 shou  staff   320B Mar 31 01:17 memdir\n-rw-r--r--   1 shou  staff    25K Mar 31 01:17 commands.ts\n-rw-r--r--   5 shou  staff   160B Mar 31 01:17 native-ts\n-rw-r--r--   1 shou  staff    14K Mar 31 01:17 history.ts\n-rw-r--r--   1 shou  staff   2.3K Mar 31 01:17 projectOnboardingState.ts\n-rw-r--r--   3 shou  staff    96B Mar 31 01:17 outputStyles\n-rw-r--r--   1 shou  staff    67K Mar 31 01:17 query.ts\ndrwxr-xr-x   6 shou  staff   192B Mar 31 01:17 query\ndrwxr-xr-x  11 shou  staff   352B Mar 31 01:17 tasks\n-rw-r--r--   1 shou  staff    17K Mar 31 01:17 tools.ts\ndrwxr-xr-x  45 shou  staff   1.4K Mar 31 01:17 tools\n-rw-r--r--   3 shou  staff    96B Mar 31 01:17 voice\n-rw-r--r--   1 shou  staff   1.3K Mar 31 01:17 tasks.ts\n-rw-r--r--   1 shou  staff    10K Mar 31 01:17 cost-tracker.ts\n-drwxr-xr-x  3 shou  staff    96B Mar 31 01:17 coordinator\n-rw-r--r--   1 shou  staff   6.3K Mar 31 01:17 context.ts\n-rw-r--r--   1 shou  staff   3.8K Mar 31 01:17 ink.ts\n-drwxr-xr-x 50 shou  staff   1.6K Mar 31 01:17 ink\n-rw-r--r--   1 shou  staff    29K Mar 31 01:17 Tool.ts\n-drwxr-xr-x  3 shou  staff    96B Mar 31 01:17 schemas\n-drwxr-xr-x  3 shou  staff    96B Mar 31 01:17 bootstrap\ndrwxr-xr-x  12 shou  staff   384B Mar 31 01:17 ..",
      "response_path": "runs/R-IMG-TERMINAL-01/textifier_codex_gpt_53_codex/response.json",
      "response_warnings": [
        "Image is a screenshot with slight blur; some characters may be misread.",
        "Bottom of terminal content is cropped; final lines may be incomplete.",
        "A few permission prefixes may be uncertain due to low contrast (e.g., lines near moreright/assistant/coordinator)."
      ],
      "status": "converted",
      "suggested_files": [
        {
          "output_format": "txt",
          "suggested_path": "claude-code-listing.log",
          "text": "showdev claude-code % ls -alh cli.js.map\n-rw-r--r--  1 shou  staff   57M Mar 31 01:16 cli.js.map\nshowdev claude-code % ls -alh src\ntotal 2304\ndrwxr-xr-x   8 shou  staff   256B Mar 31 01:17 entrypoints\n-rw-r--r--   1 shou  staff   785K Mar 31 01:17 main.tsx\ndrwxr-xr-x  55 shou  staff   1.7K Mar 31 01:17 cli\ndrwxr-xr-x  10 shou  staff   320B Mar 31 01:17 commands\ndrwxr-xr-x 103 shou  staff   3.2K Mar 31 01:17 utils\ndrwxr-xr-x 331 shou  staff    10K Mar 31 01:17 components\n-rw-r--r-- 146 shou  staff   4.6K Mar 31 01:17 QueryEngine.ts\n-rw-r--r--   1 shou  staff    46K Mar 31 01:17 setup.ts\ndrwxr-xr-x   5 shou  staff   160B Mar 31 01:17 server\ndrwxr-xr-x  13 shou  staff   416B Mar 31 01:17 migrations\ndrwxr-xr-x  16 shou  staff   512B Mar 31 01:17 keybindings\ndrwxr-xr-x   6 shou  staff   192B Mar 31 01:17 skills\ndrwxr-xr-x   4 shou  staff   128B Mar 31 01:17 plugins\n-rw-r--r--   1 shou  staff    22K Mar 31 01:17 dialogLaunchers.tsx\ndrwxr-xr-x   5 shou  staff   160B Mar 31 01:17 screens\n-rw-r--r--  87 shou  staff   2.7K Mar 31 01:17 hooks\n-rw-r--r--   1 shou  staff    56K Mar 31 01:17 interactiveHelpers.tsx\ndrwxr-xr-x  38 shou  staff   1.2K Mar 31 01:17 services\n-rw-r--r--   1 shou  staff   3.4K Mar 31 01:17 replLauncher.tsx\n-rw-r--r--   1 shou  staff   617B Mar 31 01:17 costHook.ts\n-drwxr-xr-x  3 shou  staff    96B Mar 31 01:17 moreright\n-drwxr-xr-x  3 shou  staff    96B Mar 31 01:17 assistant\n-drwxr-xr-x  6 shou  staff   192B Mar 31 01:17 remote\ndrwxr-xr-x   7 shou  staff   224B Mar 31 01:17 vim\ndrwxr-xr-x   8 shou  staff   256B Mar 31 01:17 buddy\ndrwxr-xr-x  33 shou  staff   1.0K Mar 31 01:17 bridge\ndrwxr-xr-x   8 shou  staff   256B Mar 31 01:17 state\ndrwxr-xr-x  11 shou  staff   352B Mar 31 01:17 context\ndrwxr-xr-x   4 shou  staff   128B Mar 31 01:17 upstreamproxy\ndrwxr-xr-x  23 shou  staff   736B Mar 31 01:17 constants\ndrwxr-xr-x  10 shou  staff   320B Mar 31 01:17 types\n-rw-r--r--   1 shou  staff   3.1K Mar 31 01:17 Task.ts\n-drwxr-xr-x 10 shou  staff   320B Mar 31 01:17 memdir\n-rw-r--r--   1 shou  staff    25K Mar 31 01:17 commands.ts\n-rw-r--r--   5 shou  staff   160B Mar 31 01:17 native-ts\n-rw-r--r--   1 shou  staff    14K Mar 31 01:17 history.ts\n-rw-r--r--   1 shou  staff   2.3K Mar 31 01:17 projectOnboardingState.ts\n-rw-r--r--   3 shou  staff    96B Mar 31 01:17 outputStyles\n-rw-r--r--   1 shou  staff    67K Mar 31 01:17 query.ts\ndrwxr-xr-x   6 shou  staff   192B Mar 31 01:17 query\ndrwxr-xr-x  11 shou  staff   352B Mar 31 01:17 tasks\n-rw-r--r--   1 shou  staff    17K Mar 31 01:17 tools.ts\ndrwxr-xr-x  45 shou  staff   1.4K Mar 31 01:17 tools\n-rw-r--r--   3 shou  staff    96B Mar 31 01:17 voice\n-rw-r--r--   1 shou  staff   1.3K Mar 31 01:17 tasks.ts\n-rw-r--r--   1 shou  staff    10K Mar 31 01:17 cost-tracker.ts\n-drwxr-xr-x  3 shou  staff    96B Mar 31 01:17 coordinator\n-rw-r--r--   1 shou  staff   6.3K Mar 31 01:17 context.ts\n-rw-r--r--   1 shou  staff   3.8K Mar 31 01:17 ink.ts\n-drwxr-xr-x 50 shou  staff   1.6K Mar 31 01:17 ink\n-rw-r--r--   1 shou  staff    29K Mar 31 01:17 Tool.ts\n-drwxr-xr-x  3 shou  staff    96B Mar 31 01:17 schemas\n-drwxr-xr-x  3 shou  staff    96B Mar 31 01:17 bootstrap\ndrwxr-xr-x  12 shou  staff   384B Mar 31 01:17 .."
        }
      ],
      "usage": {
        "api_equivalent_cost_usd": 0.07204260000000001,
        "basis": "api_equivalent",
        "cached_input_price_per_million": 0.175,
        "cached_input_tokens": 22912,
        "completed_at": "2026-04-28T13:36:07.750810Z",
        "currency": "USD",
        "input_price_per_million": 1.75,
        "input_tokens": 25220,
        "metered_objects": [],
        "output_price_per_million": 14.0,
        "output_tokens": 1707,
        "reasoning_tokens": 31,
        "started_at": "2026-04-28T13:35:41.524191Z",
        "thinking_seconds": null,
        "total_tokens": 26927,
        "wall_seconds": 26.226619
      }
    },
    {
      "caller": "textifier_codex_gpt_53_codex",
      "case_id": "R-IMG-ASCII-DIAGRAM-01",
      "expected_output_format": "txt",
      "expected_status": "converted",
      "expected_suggested_paths": [
        "distributed-bloomberg-autoquant.txt"
      ],
      "expected_textification_intent": "Preserve the ASCII-style diagram layout and result box as plain text instead of summarizing it away.",
      "fixture_metadata": {
        "mime_type": "image/png",
        "name": "r-img-ascii-diagram-01.png",
        "path": "/Users/zeph/github/tzaffi/curio/tmp/textify-smoke/20260428-132551-09c3fa3c8f75/cases/R-IMG-ASCII-DIAGRAM-01/fixtures/r-img-ascii-diagram-01.png",
        "sha256": "353bc7c7e176f785ef3d09d0b8ae088c6f299c4e971010301ff2bd9d84f40c50",
        "source_language_hint": null
      },
      "ground_truth_text": "DISTRIBUTED BLOOMBERG\nAutoQuant\nAgent Macro Sector Alpha Risks\nDARWINIAN SELECTION\n4 factors · risk parity\nSharpe 1.32\n1,896 experiments in 36 hours",
      "model_importance": 8,
      "output_format": [
        "txt"
      ],
      "participates_in_model_ranking": true,
      "preservation_requirements": [
        "DISTRIBUTED BLOOMBERG",
        "AutoQuant",
        "DARWINIAN SELECTION",
        "Sharpe 1.32",
        "1,896 experiments"
      ],
      "rendered_textified_text": "DISTRIBUTED BLOOMBERG\nAutoQuant\n\n\n   ┌───────┐     ┌───────┐     ┌───────┐\n   │Agent  │     │Agent  │     │Agent  │        × 135\n   │Macro  │     │Macro  │     │Macro  │\n   │Sector │     │Sector │     │Sector │\n   │Alpha  │     │Alpha  │     │Alpha  │\n   │Risk↙  │     │Risk↙  │     │Risk↙  │\n   └───────┘     └───────┘     └───────┘\n\n        gossip | gossip\n             P2P\n           Network\n\nDARWINIAN SELECTION\n— 30 mutations compete\n— Win rates tracked\n— Losers pruned, winners amplified\n— Network converges on optimal\n\nRESULT (discovered autonomously):\n\n┌──────────────────────────────┐\n│ 4 factors · risk parity      │\n│ Sharpe 1.32 · 3× return      │\n│ 5.5% max drawdown            │\n│ 1,896 experiments in 36 hours│\n└──────────────────────────────┘\n\n32,868 total commits across all domains:\nML · Search · Skills · Finance · Network",
      "response_path": "runs/R-IMG-ASCII-DIAGRAM-01/textifier_codex_gpt_53_codex/response.json",
      "response_warnings": [
        "Some ASCII box-drawing and slash/arrow glyphs are low-confidence due to stylized rendering.",
        "Right-edge border/crop marks are partially truncated and not fully recoverable."
      ],
      "status": "converted",
      "suggested_files": [
        {
          "output_format": "txt",
          "suggested_path": "distributed-bloomberg-autoquant.txt",
          "text": "DISTRIBUTED BLOOMBERG\nAutoQuant\n\n\n   ┌───────┐     ┌───────┐     ┌───────┐\n   │Agent  │     │Agent  │     │Agent  │        × 135\n   │Macro  │     │Macro  │     │Macro  │\n   │Sector │     │Sector │     │Sector │\n   │Alpha  │     │Alpha  │     │Alpha  │\n   │Risk↙  │     │Risk↙  │     │Risk↙  │\n   └───────┘     └───────┘     └───────┘\n\n        gossip | gossip\n             P2P\n           Network\n\nDARWINIAN SELECTION\n— 30 mutations compete\n— Win rates tracked\n— Losers pruned, winners amplified\n— Network converges on optimal\n\nRESULT (discovered autonomously):\n\n┌──────────────────────────────┐\n│ 4 factors · risk parity      │\n│ Sharpe 1.32 · 3× return      │\n│ 5.5% max drawdown            │\n│ 1,896 experiments in 36 hours│\n└──────────────────────────────┘\n\n32,868 total commits across all domains:\nML · Search · Skills · Finance · Network"
        }
      ],
      "usage": {
        "api_equivalent_cost_usd": 0.056276849999999996,
        "basis": "api_equivalent",
        "cached_input_price_per_million": 0.175,
        "cached_input_tokens": 22912,
        "completed_at": "2026-04-28T13:36:20.347366Z",
        "currency": "USD",
        "input_price_per_million": 1.75,
        "input_tokens": 25803,
        "metered_objects": [],
        "output_price_per_million": 14.0,
        "output_tokens": 508,
        "reasoning_tokens": 63,
        "started_at": "2026-04-28T13:36:07.761725Z",
        "thinking_seconds": null,
        "total_tokens": 26311,
        "wall_seconds": 12.585641
      }
    },
    {
      "caller": "textifier_codex_gpt_53_codex",
      "case_id": "R-IMG-COMPARISON-TABLE-01",
      "expected_output_format": "markdown",
      "expected_status": "converted",
      "expected_suggested_paths": [
        "agent-comparison.md"
      ],
      "expected_textification_intent": "Extract the OpenClaw/Hermes/Paperclip comparison as a Markdown table preserving row and column alignment.",
      "fixture_metadata": {
        "mime_type": "image/png",
        "name": "r-img-comparison-table-01.png",
        "path": "/Users/zeph/github/tzaffi/curio/tmp/textify-smoke/20260428-132551-09c3fa3c8f75/cases/R-IMG-COMPARISON-TABLE-01/fixtures/r-img-comparison-table-01.png",
        "sha256": "26f885c49a5b46c7827858bd74e79ca5938ac4e083bae507712c64180299e509",
        "source_language_hint": null
      },
      "ground_truth_text": "Head-to-Head\nDimension | OpenClaw | Hermes | Paperclip\nWhat it is\nGitHub stars\nSecurity\nInstall",
      "model_importance": 8,
      "output_format": [
        "markdown"
      ],
      "participates_in_model_ranking": true,
      "preservation_requirements": [
        "Head-to-Head",
        "Dimension",
        "OpenClaw",
        "Hermes",
        "Paperclip",
        "GitHub stars",
        "Install"
      ],
      "rendered_textified_text": "## Head-to-Head\n\n| Dimension | OpenClaw | Hermes | Paperclip |\n|---|---|---|---|\n| What it is | Personal AI agent | Self-improving AI agent | Multi-agent orchestrator |\n| GitHub stars | 351K | ~31K | 49K |\n| Philosophy | System to be orchestrated | Mind to be developed | Company to be managed |\n| Skills | Static (ClawHub, 5,700+) | Self-created, auto-improving (94 built-in) | N/A (manages other agents) |\n| Memory | Plugin-based | Multi-level, persistent, deepening | Org-level (budgets, goals) |\n| Models | API-dependent | Runs on open models (Qwen 3.5) | Model-agnostic orchestration |\n| Security | Concerning (Snyk findings) | Better defaults | Governance + audit trail |\n| Best for | Tinkerers, ecosystem power | Simplicity, self-improvement | Running 5-50 agents together |\n| Install | npm global | 11-minute installer | npx paperclipai onboard |",
      "response_path": "runs/R-IMG-COMPARISON-TABLE-01/textifier_codex_gpt_53_codex/response.json",
      "response_warnings": [],
      "status": "converted",
      "suggested_files": [
        {
          "output_format": "markdown",
          "suggested_path": "agent-comparison.md",
          "text": "## Head-to-Head\n\n| Dimension | OpenClaw | Hermes | Paperclip |\n|---|---|---|---|\n| What it is | Personal AI agent | Self-improving AI agent | Multi-agent orchestrator |\n| GitHub stars | 351K | ~31K | 49K |\n| Philosophy | System to be orchestrated | Mind to be developed | Company to be managed |\n| Skills | Static (ClawHub, 5,700+) | Self-created, auto-improving (94 built-in) | N/A (manages other agents) |\n| Memory | Plugin-based | Multi-level, persistent, deepening | Org-level (budgets, goals) |\n| Models | API-dependent | Runs on open models (Qwen 3.5) | Model-agnostic orchestration |\n| Security | Concerning (Snyk findings) | Better defaults | Governance + audit trail |\n| Best for | Tinkerers, ecosystem power | Simplicity, self-improvement | Running 5-50 agents together |\n| Install | npm global | 11-minute installer | npx paperclipai onboard |"
        }
      ],
      "usage": {
        "api_equivalent_cost_usd": 0.053927300000000004,
        "basis": "api_equivalent",
        "cached_input_price_per_million": 0.175,
        "cached_input_tokens": 23936,
        "completed_at": "2026-04-28T13:36:29.909322Z",
        "currency": "USD",
        "input_price_per_million": 1.75,
        "input_tokens": 25518,
        "metered_objects": [],
        "output_price_per_million": 14.0,
        "output_tokens": 363,
        "reasoning_tokens": 20,
        "started_at": "2026-04-28T13:36:20.356726Z",
        "thinking_seconds": null,
        "total_tokens": 25881,
        "wall_seconds": 9.552596
      }
    },
    {
      "caller": "textifier_codex_gpt_53_codex",
      "case_id": "R-IMG-NO-TEXT-REAL-01",
      "expected_output_format": "markdown",
      "expected_status": "no_text_found",
      "expected_suggested_paths": [],
      "expected_textification_intent": "Return no_text_found for a real photo with no readable text and do not invent a visual description.",
      "fixture_metadata": {
        "mime_type": "image/jpeg",
        "name": "r-img-no-text-real-01.jpg",
        "path": "/Users/zeph/github/tzaffi/curio/tmp/textify-smoke/20260428-132551-09c3fa3c8f75/cases/R-IMG-NO-TEXT-REAL-01/fixtures/r-img-no-text-real-01.jpg",
        "sha256": "80c99366dc83288925d6653b25e086ee894e8098469f7f785e6e1e984e761107",
        "source_language_hint": null
      },
      "ground_truth_text": "",
      "model_importance": 5,
      "output_format": [],
      "participates_in_model_ranking": true,
      "preservation_requirements": [
        "no_text_found",
        "no invented description"
      ],
      "rendered_textified_text": "",
      "response_path": "runs/R-IMG-NO-TEXT-REAL-01/textifier_codex_gpt_53_codex/response.json",
      "response_warnings": [
        "No clearly readable text is visible in the image."
      ],
      "status": "no_text_found",
      "suggested_files": [],
      "usage": {
        "api_equivalent_cost_usd": 0.0509656,
        "basis": "api_equivalent",
        "cached_input_price_per_million": 0.175,
        "cached_input_tokens": 22912,
        "completed_at": "2026-04-28T13:36:37.089612Z",
        "currency": "USD",
        "input_price_per_million": 1.75,
        "input_tokens": 26000,
        "metered_objects": [],
        "output_price_per_million": 14.0,
        "output_tokens": 104,
        "reasoning_tokens": 14,
        "started_at": "2026-04-28T13:36:29.920007Z",
        "thinking_seconds": null,
        "total_tokens": 26104,
        "wall_seconds": 7.169605
      }
    },
    {
      "caller": "textifier_codex_gpt_53_codex",
      "case_id": "C-IMG-DIR-TREE-01",
      "expected_output_format": "mixed",
      "expected_status": "converted",
      "expected_suggested_paths": [
        "home/important/openclaw-rl.md",
        "home/important/agent-comparison.md",
        "home/trivial/claude-code-listing.log"
      ],
      "expected_textification_intent": "Split one composite screenshot into exactly three suggested files in the visible nested relative directory structure.",
      "fixture_metadata": {
        "mime_type": "image/png",
        "name": "c-img-dir-tree-01.png",
        "path": "/Users/zeph/github/tzaffi/curio/tmp/textify-smoke/20260428-132551-09c3fa3c8f75/cases/C-IMG-DIR-TREE-01/fixtures/c-img-dir-tree-01.png",
        "sha256": "0664c813d92eb3562bb8a6a990b9c05634f452a5b245233038aff43fafc42400",
        "source_language_hint": null
      },
      "ground_truth_text": "home/important/openclaw-rl.md\nOpenClaw-RL: Train Any Agent Simply by Talking\nhome/important/agent-comparison.md\nHead-to-Head\nhome/trivial/claude-code-listing.log\nls -alht src",
      "model_importance": 10,
      "output_format": [
        "markdown",
        "markdown",
        "log"
      ],
      "participates_in_model_ranking": true,
      "preservation_requirements": [
        "exactly three suggested files",
        "home/important/openclaw-rl.md",
        "home/important/agent-comparison.md",
        "home/trivial/claude-code-listing.log",
        "no cross-section bleed",
        "no extra generated files"
      ],
      "rendered_textified_text": "# OpenClaw-RL: Train Any Agent Simply by Talking\n\nYinjie Wang*, Xuyang Chen*, Xiaolong Jin*, Mengdi Wang*, Ling Yang†\n\nhttps://github.com/Gen-Verse/OpenClaw-RL\n\nEvery agent interaction generates a next-state signal, namely the user reply, tool output, terminal\nor GUI state change that follows each action, yet no existing online RL system recovers it as a\nlive, online learning source. We present OpenClaw-RL, a framework built on a simple observation:\nnext-state signals are universal, and policy can learn from all of them simultaneously. Personal\nconversations, terminal executions, GUI interactions, SWE tasks, and tool-call traces are not separate\ntraining problems. They are all interactions that can be used to train the same policy in the same loop.\nNext-state signals encode two forms of information: evaluative signals, which indicate how well the\naction performed and are extracted as scalar rewards via a PRM judge; and directive signals, which\nindicate how the action should have been different and are recovered through Hindsight-Guided\nOn-Policy Distillation (OPD). We extract textual hints from the next state, construct an enhanced\nteacher context, and provide token-level directional advantages supervision at its richer than any\nscalar reward. Due to the asynchronous design, the model serves live requests, the PRM judges\nongoing interactions, and the trainer updates the policy at the same time, with zero coordination\noverhead between them. Applied to personal agents, OpenClaw-RL enables an agent to improve\nsimply by being used, recovering conversational signals from user re-queries, corrections, and explicit\nfeedback. Applied to general agents, the same infrastructure supports scalable RL across terminal,\nGUI, SWE, and tool-call settings, where we additionally demonstrate the utility of process rewards.\n\n![Figure 1](figure-1)\n\nFigure 1 | OpenClaw-RL infrastructure overview. Interaction streams come from two agent types:\nPersonal Agents (conversational, single-user), hosted on personal devices, and General Agents (terminal,\nGUI, SWE, and tool-call agents), hosted on cloud services. The collected samples flow into our RL\nserver built on the asynchronous slime framework, which consists of four decoupled components:\n(1) the environment server, (2) PRM judge for reward computation, (3) Megatron for policy\ntraining, and (4) SGLang for policy serving. These components support graceful weight updates\nand enable training with any agentic framework. The environment for personal agents is simply the\nusers’ personal devices, which connect to the RL server over HTTP with confidential API keys. The\nenvironment for general agents are hosted on cloud services to enable scalable parallelization.\n\n*Equal contribution; †Corresponding author; Main contact: yangling008198@163.com\n\n# Head-to-Head\n\n| Dimension | OpenClaw | Hermes | Paperclip |\n|---|---|---|---|\n| What it is | Personal AI agent | Self-improving AI agent | Multi-agent orchestrator |\n| GitHub stars | 351K | ~31K | 49K |\n| Philosophy | System to be orchestrated | Mind to be developed | Company to be managed |\n| Skills | Static (ClawHub, 5,700+) | Self-created, auto-improving (94 built-in) | N/A (manages other agents) |\n| Memory | Plugin-based | Multi-level, persistent, deepening | Org-level (budgets, goals) |\n| Models | API-dependent | Runs on open models (Qwen 3.5) | Model-agnostic orchestration |\n| Security | Concerning (Snyk findings) | Better defaults | Governance + audit trail |\n| Best for | Tinkerers, ecosystem power | Simplicity, self-improvement | Running 5-50 agents together |\n| Install | npm global | 11-minute installer | npx paperclipai onboard |\n\nshow@dev claude-code % ls -alh cli.js.map\n-rw-r--r--   1 show  staff    57M Mar 31 01:16 cli.js.map\nshow@dev claude-code % ls -alh src\ntotal 2364\ndrwxr-xr-x   8 show  staff   256B Mar 31 01:17 entrypoints\ndrwxr-xr-x   1 show  staff   785K Mar 31 01:17 main.tsx\ndrwxr-xr-x  55 show  staff   1.7K Mar 31 01:17 ai\ndrwxr-xr-x  10 show  staff   320B Mar 31 01:17 cli\ndrwxr-xr-x 103 show  staff   3.2K Mar 31 01:17 commands\ndrwxr-xr-x 331 show  staff    10K Mar 31 01:17 utils\ndrwxr-xr-x 146 show  staff   4.6K Mar 31 01:17 components\n-rw-r--r--   1 show  staff    46K Mar 31 01:17 QueryEngine.ts\n-rw-r--r--   1 show  staff    20K Mar 31 01:17 setup.ts\ndrwxr-xr-x   5 show  staff   160B Mar 31 01:17 server\ndrwxr-xr-x  13 show  staff   416B Mar 31 01:17 migrations\ndrwxr-xr-x  16 show  staff   512B Mar 31 01:17 keybindings\ndrwxr-xr-x   6 show  staff   192B Mar 31 01:17 skills\ndrwxr-xr-x   4 show  staff   128B Mar 31 01:17 plugins\n-rw-r--r--   1 show  staff    22K Mar 31 01:17 dialogLaunchers.tsx\ndrwxr-xr-x   5 show  staff   160B Mar 31 01:17 screens\ndrwxr-xr-x  87 show  staff   2.7K Mar 31 01:17 hooks\n-rw-r--r--   1 show  staff    56K Mar 31 01:17 interactiveHelpers.tsx\ndrwxr-xr-x  38 show  staff   1.2K Mar 31 01:17 services\n-rw-r--r--   1 show  staff   3.4K Mar 31 01:17 replLauncher.tsx\n-rw-r--r--   1 show  staff   617B Mar 31 01:17 costHooks.ts\ndrwxr-xr-x   3 show  staff    96B Mar 31 01:17 moreRight\ndrwxr-xr-x   3 show  staff    96B Mar 31 01:17 assistant\ndrwxr-xr-x   6 show  staff   192B Mar 31 01:17 remote\ndrwxr-xr-x   7 show  staff   224B Mar 31 01:17 vim\ndrwxr-xr-x   8 show  staff   256B Mar 31 01:17 buddy\ndrwxr-xr-x  33 show  staff   1.0K Mar 31 01:17 bridge\ndrwxr-xr-x   8 show  staff   256B Mar 31 01:17 state\ndrwxr-xr-x  11 show  staff   352B Mar 31 01:17 context\ndrwxr-xr-x   4 show  staff   128B Mar 31 01:17 upstreamProxy\ndrwxr-xr-x  23 show  staff   736B Mar 31 01:17 constants\ndrwxr-xr-x  10 show  staff   320B Mar 31 01:17 types\n-rw-r--r--   1 show  staff   3.1K Mar 31 01:17 Task.ts\ndrwxr-xr-x  10 show  staff   320B Mar 31 01:17 memdir\n-rw-r--r--   1 show  staff    25K Mar 31 01:17 commands.ts\ndrwxr-xr-x   5 show  staff   160B Mar 31 01:17 native-ts\n-rw-r--r--   1 show  staff    14K Mar 31 01:17 history.ts\n-rw-r--r--   1 show  staff   2.3K Mar 31 01:17 projectOnboardingState.ts\ndrwxr-xr-x   3 show  staff    96B Mar 31 01:17 outputStyles\n-rw-r--r--   1 show  staff   6.7K Mar 31 01:17 query.ts\ndrwxr-xr-x   6 show  staff   192B Mar 31 01:17 keys\ndrwxr-xr-x  11 show  staff   352B Mar 31 01:17 tasks\n-rw-r--r--   7 show  staff    17K Mar 31 01:17 tools.ts\ndrwxr-xr-x  45 show  staff   1.4K Mar 31 01:17 tools\n-rw-r--r--   3 show  staff   9.6K Mar 31 01:17 voice\n-rw-r--r--   1 show  staff   1.3K Mar 31 01:17 tasks.ts\n-rw-r--r--   1 show  staff    10K Mar 31 01:17 cost-tracker.ts\ndrwxr-xr-x   3 show  staff    96B Mar 31 01:17 coordinator\n-rw-r--r--   1 show  staff   6.3K Mar 31 01:17 context.ts\n-rw-r--r--   1 show  staff   3.8K Mar 31 01:17 ink.ts\ndrwxr-xr-x  50 show  staff   1.6K Mar 31 01:17 ink\n-rw-r--r--   1 show  staff    29K Mar 31 01:17 Tool.ts\ndrwxr-xr-x   3 show  staff    96B Mar 31 01:17 schemas\ndrwxr-xr-x   3 show  staff    96B Mar 31 01:17 bootstrap\n-rw-r--r--   1 show  staff   384B Mar 31 01:17 ...",
      "response_path": "runs/C-IMG-DIR-TREE-01/textifier_codex_gpt_53_codex/response.json",
      "response_warnings": [
        "Composite image split into three implied files by visible headings.",
        "OCR uncertainty in small body text and fine-print footer of openclaw-rl section.",
        "Bottom log section is partially cropped; some entries may be incomplete or slightly misread."
      ],
      "status": "converted",
      "suggested_files": [
        {
          "output_format": "markdown",
          "suggested_path": "home/important/openclaw-rl.md",
          "text": "# OpenClaw-RL: Train Any Agent Simply by Talking\n\nYinjie Wang*, Xuyang Chen*, Xiaolong Jin*, Mengdi Wang*, Ling Yang†\n\nhttps://github.com/Gen-Verse/OpenClaw-RL\n\nEvery agent interaction generates a next-state signal, namely the user reply, tool output, terminal\nor GUI state change that follows each action, yet no existing online RL system recovers it as a\nlive, online learning source. We present OpenClaw-RL, a framework built on a simple observation:\nnext-state signals are universal, and policy can learn from all of them simultaneously. Personal\nconversations, terminal executions, GUI interactions, SWE tasks, and tool-call traces are not separate\ntraining problems. They are all interactions that can be used to train the same policy in the same loop.\nNext-state signals encode two forms of information: evaluative signals, which indicate how well the\naction performed and are extracted as scalar rewards via a PRM judge; and directive signals, which\nindicate how the action should have been different and are recovered through Hindsight-Guided\nOn-Policy Distillation (OPD). We extract textual hints from the next state, construct an enhanced\nteacher context, and provide token-level directional advantages supervision at its richer than any\nscalar reward. Due to the asynchronous design, the model serves live requests, the PRM judges\nongoing interactions, and the trainer updates the policy at the same time, with zero coordination\noverhead between them. Applied to personal agents, OpenClaw-RL enables an agent to improve\nsimply by being used, recovering conversational signals from user re-queries, corrections, and explicit\nfeedback. Applied to general agents, the same infrastructure supports scalable RL across terminal,\nGUI, SWE, and tool-call settings, where we additionally demonstrate the utility of process rewards.\n\n![Figure 1](figure-1)\n\nFigure 1 | OpenClaw-RL infrastructure overview. Interaction streams come from two agent types:\nPersonal Agents (conversational, single-user), hosted on personal devices, and General Agents (terminal,\nGUI, SWE, and tool-call agents), hosted on cloud services. The collected samples flow into our RL\nserver built on the asynchronous slime framework, which consists of four decoupled components:\n(1) the environment server, (2) PRM judge for reward computation, (3) Megatron for policy\ntraining, and (4) SGLang for policy serving. These components support graceful weight updates\nand enable training with any agentic framework. The environment for personal agents is simply the\nusers’ personal devices, which connect to the RL server over HTTP with confidential API keys. The\nenvironment for general agents are hosted on cloud services to enable scalable parallelization.\n\n*Equal contribution; †Corresponding author; Main contact: yangling008198@163.com"
        },
        {
          "output_format": "markdown",
          "suggested_path": "home/important/agent-comparison.md",
          "text": "# Head-to-Head\n\n| Dimension | OpenClaw | Hermes | Paperclip |\n|---|---|---|---|\n| What it is | Personal AI agent | Self-improving AI agent | Multi-agent orchestrator |\n| GitHub stars | 351K | ~31K | 49K |\n| Philosophy | System to be orchestrated | Mind to be developed | Company to be managed |\n| Skills | Static (ClawHub, 5,700+) | Self-created, auto-improving (94 built-in) | N/A (manages other agents) |\n| Memory | Plugin-based | Multi-level, persistent, deepening | Org-level (budgets, goals) |\n| Models | API-dependent | Runs on open models (Qwen 3.5) | Model-agnostic orchestration |\n| Security | Concerning (Snyk findings) | Better defaults | Governance + audit trail |\n| Best for | Tinkerers, ecosystem power | Simplicity, self-improvement | Running 5-50 agents together |\n| Install | npm global | 11-minute installer | npx paperclipai onboard |"
        },
        {
          "output_format": "log",
          "suggested_path": "home/trivial/claude-code-listing.log",
          "text": "show@dev claude-code % ls -alh cli.js.map\n-rw-r--r--   1 show  staff    57M Mar 31 01:16 cli.js.map\nshow@dev claude-code % ls -alh src\ntotal 2364\ndrwxr-xr-x   8 show  staff   256B Mar 31 01:17 entrypoints\ndrwxr-xr-x   1 show  staff   785K Mar 31 01:17 main.tsx\ndrwxr-xr-x  55 show  staff   1.7K Mar 31 01:17 ai\ndrwxr-xr-x  10 show  staff   320B Mar 31 01:17 cli\ndrwxr-xr-x 103 show  staff   3.2K Mar 31 01:17 commands\ndrwxr-xr-x 331 show  staff    10K Mar 31 01:17 utils\ndrwxr-xr-x 146 show  staff   4.6K Mar 31 01:17 components\n-rw-r--r--   1 show  staff    46K Mar 31 01:17 QueryEngine.ts\n-rw-r--r--   1 show  staff    20K Mar 31 01:17 setup.ts\ndrwxr-xr-x   5 show  staff   160B Mar 31 01:17 server\ndrwxr-xr-x  13 show  staff   416B Mar 31 01:17 migrations\ndrwxr-xr-x  16 show  staff   512B Mar 31 01:17 keybindings\ndrwxr-xr-x   6 show  staff   192B Mar 31 01:17 skills\ndrwxr-xr-x   4 show  staff   128B Mar 31 01:17 plugins\n-rw-r--r--   1 show  staff    22K Mar 31 01:17 dialogLaunchers.tsx\ndrwxr-xr-x   5 show  staff   160B Mar 31 01:17 screens\ndrwxr-xr-x  87 show  staff   2.7K Mar 31 01:17 hooks\n-rw-r--r--   1 show  staff    56K Mar 31 01:17 interactiveHelpers.tsx\ndrwxr-xr-x  38 show  staff   1.2K Mar 31 01:17 services\n-rw-r--r--   1 show  staff   3.4K Mar 31 01:17 replLauncher.tsx\n-rw-r--r--   1 show  staff   617B Mar 31 01:17 costHooks.ts\ndrwxr-xr-x   3 show  staff    96B Mar 31 01:17 moreRight\ndrwxr-xr-x   3 show  staff    96B Mar 31 01:17 assistant\ndrwxr-xr-x   6 show  staff   192B Mar 31 01:17 remote\ndrwxr-xr-x   7 show  staff   224B Mar 31 01:17 vim\ndrwxr-xr-x   8 show  staff   256B Mar 31 01:17 buddy\ndrwxr-xr-x  33 show  staff   1.0K Mar 31 01:17 bridge\ndrwxr-xr-x   8 show  staff   256B Mar 31 01:17 state\ndrwxr-xr-x  11 show  staff   352B Mar 31 01:17 context\ndrwxr-xr-x   4 show  staff   128B Mar 31 01:17 upstreamProxy\ndrwxr-xr-x  23 show  staff   736B Mar 31 01:17 constants\ndrwxr-xr-x  10 show  staff   320B Mar 31 01:17 types\n-rw-r--r--   1 show  staff   3.1K Mar 31 01:17 Task.ts\ndrwxr-xr-x  10 show  staff   320B Mar 31 01:17 memdir\n-rw-r--r--   1 show  staff    25K Mar 31 01:17 commands.ts\ndrwxr-xr-x   5 show  staff   160B Mar 31 01:17 native-ts\n-rw-r--r--   1 show  staff    14K Mar 31 01:17 history.ts\n-rw-r--r--   1 show  staff   2.3K Mar 31 01:17 projectOnboardingState.ts\ndrwxr-xr-x   3 show  staff    96B Mar 31 01:17 outputStyles\n-rw-r--r--   1 show  staff   6.7K Mar 31 01:17 query.ts\ndrwxr-xr-x   6 show  staff   192B Mar 31 01:17 keys\ndrwxr-xr-x  11 show  staff   352B Mar 31 01:17 tasks\n-rw-r--r--   7 show  staff    17K Mar 31 01:17 tools.ts\ndrwxr-xr-x  45 show  staff   1.4K Mar 31 01:17 tools\n-rw-r--r--   3 show  staff   9.6K Mar 31 01:17 voice\n-rw-r--r--   1 show  staff   1.3K Mar 31 01:17 tasks.ts\n-rw-r--r--   1 show  staff    10K Mar 31 01:17 cost-tracker.ts\ndrwxr-xr-x   3 show  staff    96B Mar 31 01:17 coordinator\n-rw-r--r--   1 show  staff   6.3K Mar 31 01:17 context.ts\n-rw-r--r--   1 show  staff   3.8K Mar 31 01:17 ink.ts\ndrwxr-xr-x  50 show  staff   1.6K Mar 31 01:17 ink\n-rw-r--r--   1 show  staff    29K Mar 31 01:17 Tool.ts\ndrwxr-xr-x   3 show  staff    96B Mar 31 01:17 schemas\ndrwxr-xr-x   3 show  staff    96B Mar 31 01:17 bootstrap\n-rw-r--r--   1 show  staff   384B Mar 31 01:17 ..."
        }
      ],
      "usage": {
        "api_equivalent_cost_usd": 0.08823710000000001,
        "basis": "api_equivalent",
        "cached_input_price_per_million": 0.175,
        "cached_input_tokens": 22912,
        "completed_at": "2026-04-28T13:37:06.079733Z",
        "currency": "USD",
        "input_price_per_million": 1.75,
        "input_tokens": 27538,
        "metered_objects": [],
        "output_price_per_million": 14.0,
        "output_tokens": 2574,
        "reasoning_tokens": 29,
        "started_at": "2026-04-28T13:36:37.099345Z",
        "thinking_seconds": null,
        "total_tokens": 30112,
        "wall_seconds": 28.980388
      }
    },
    {
      "caller": "textifier_codex_gpt_53_codex",
      "case_id": "R-PDF-PAPER-01",
      "expected_output_format": "markdown",
      "expected_status": "converted",
      "expected_suggested_paths": [
        "nemotron-3-super.md"
      ],
      "expected_textification_intent": "Extract the scientific PDF into Markdown with title, abstract, sections, tables or figure captions, and reading order.",
      "fixture_metadata": {
        "mime_type": "application/pdf",
        "name": "r-pdf-paper-01.pdf",
        "path": "/Users/zeph/github/tzaffi/curio/tmp/textify-smoke/20260428-132551-09c3fa3c8f75/cases/R-PDF-PAPER-01/fixtures/r-pdf-paper-01.pdf",
        "sha256": "fa7e8a9a1a8f9f716e38e46170371d4bc67c3f6d1ac3e4857c574e911f0e107f",
        "source_language_hint": null
      },
      "ground_truth_text": "Nemotron 3 Super: Open, Efficient Mixture-of-Experts Hybrid Mamba-Transformer Model for Agentic Reasoning\narXiv:2604.12374\nNVIDIA",
      "model_importance": 10,
      "output_format": [],
      "participates_in_model_ranking": true,
      "preservation_requirements": [
        "Nemotron 3 Super",
        "Mixture-of-Experts",
        "Hybrid Mamba-Transformer",
        "Agentic Reasoning",
        "NVIDIA"
      ],
      "rendered_textified_text": "",
      "response_path": "runs/R-PDF-PAPER-01/textifier_codex_gpt_53_codex/response.json",
      "response_warnings": [
        "Direct PDF text extraction tools are unavailable in this runtime.",
        "Fallback stream inspection found document metadata and structure but not reliable page reading-order text.",
        "PDF appears to contain compressed/encoded content that could not be safely OCR/textified here."
      ],
      "status": "no_text_found",
      "suggested_files": [],
      "usage": {
        "api_equivalent_cost_usd": 0.39186175,
        "basis": "api_equivalent",
        "cached_input_price_per_million": 0.175,
        "cached_input_tokens": 154240,
        "completed_at": "2026-04-28T13:37:45.063827Z",
        "currency": "USD",
        "input_price_per_million": 1.75,
        "input_tokens": 195561,
        "metered_objects": [],
        "output_price_per_million": 14.0,
        "output_tokens": 1617,
        "reasoning_tokens": 297,
        "started_at": "2026-04-28T13:37:06.130207Z",
        "thinking_seconds": null,
        "total_tokens": 197178,
        "wall_seconds": 38.93362
      }
    },
    {
      "caller": "textifier_codex_gpt_53_codex",
      "case_id": "R-HTML-ARXIV-01",
      "expected_output_format": "markdown",
      "expected_status": "skipped_text_media",
      "expected_suggested_paths": [],
      "expected_textification_intent": "Coverage-only HTML source case: skip as deterministic text media without calling an LLM.",
      "fixture_metadata": {
        "mime_type": "text/html",
        "name": "r-html-arxiv-01.html",
        "path": "/Users/zeph/github/tzaffi/curio/tmp/textify-smoke/20260428-132551-09c3fa3c8f75/cases/R-HTML-ARXIV-01/fixtures/r-html-arxiv-01.html",
        "sha256": "102ef094fa45008eb53dac5d613950ec099ae29049fb561c77157f0420071f97",
        "source_language_hint": null
      },
      "ground_truth_text": "[2603.10165] OpenClaw-RL: Train Any Agent Simply by Talking",
      "model_importance": 1,
      "output_format": [],
      "participates_in_model_ranking": false,
      "preservation_requirements": [
        "skipped_text_media",
        "no provider call"
      ],
      "rendered_textified_text": "",
      "response_path": "runs/R-HTML-ARXIV-01/textifier_codex_gpt_53_codex/response.json",
      "response_warnings": [
        "source is deterministic text media"
      ],
      "status": "skipped_text_media",
      "suggested_files": [],
      "usage": null
    },
    {
      "caller": "textifier_codex_gpt_53_codex",
      "case_id": "R-HTML-GITHUB-README-01",
      "expected_output_format": "markdown",
      "expected_status": "skipped_text_media",
      "expected_suggested_paths": [],
      "expected_textification_intent": "Coverage-only complex HTML page case: skip as deterministic text media without calling an LLM.",
      "fixture_metadata": {
        "mime_type": "text/html",
        "name": "r-html-github-readme-01.html",
        "path": "/Users/zeph/github/tzaffi/curio/tmp/textify-smoke/20260428-132551-09c3fa3c8f75/cases/R-HTML-GITHUB-README-01/fixtures/r-html-github-readme-01.html",
        "sha256": "245700b82311141fcf9143e0f8844ca96d6efbd4f8d261148de4951ca291bd84",
        "source_language_hint": null
      },
      "ground_truth_text": "gstack/README.md",
      "model_importance": 1,
      "output_format": [],
      "participates_in_model_ranking": false,
      "preservation_requirements": [
        "skipped_text_media",
        "no provider call"
      ],
      "rendered_textified_text": "",
      "response_path": "runs/R-HTML-GITHUB-README-01/textifier_codex_gpt_53_codex/response.json",
      "response_warnings": [
        "source is deterministic text media"
      ],
      "status": "skipped_text_media",
      "suggested_files": [],
      "usage": null
    },
    {
      "caller": "textifier_codex_gpt_53_codex",
      "case_id": "R-JSON-XARTICLE-CODE-01",
      "expected_output_format": "markdown",
      "expected_status": "skipped_text_media",
      "expected_suggested_paths": [],
      "expected_textification_intent": "Coverage-only JSON source case: skip as deterministic text media without calling an LLM.",
      "fixture_metadata": {
        "mime_type": "application/json",
        "name": "r-json-xarticle-code-01.json",
        "path": "/Users/zeph/github/tzaffi/curio/tmp/textify-smoke/20260428-132551-09c3fa3c8f75/cases/R-JSON-XARTICLE-CODE-01/fixtures/r-json-xarticle-code-01.json",
        "sha256": "69f94ac3515718a1a5aed67d20aed6b6a4ceafca3db50f7104f5e33862943241",
        "source_language_hint": null
      },
      "ground_truth_text": "tv status\ntv quote\ntv pine analyze\ntv stream quote",
      "model_importance": 1,
      "output_format": [],
      "participates_in_model_ranking": false,
      "preservation_requirements": [
        "skipped_text_media",
        "no provider call"
      ],
      "rendered_textified_text": "",
      "response_path": "runs/R-JSON-XARTICLE-CODE-01/textifier_codex_gpt_53_codex/response.json",
      "response_warnings": [
        "source is deterministic text media"
      ],
      "status": "skipped_text_media",
      "suggested_files": [],
      "usage": null
    },
    {
      "caller": "textifier_codex_gpt_53_codex",
      "case_id": "R-ZIP-REPO-01",
      "expected_output_format": "markdown",
      "expected_status": "unsupported_media",
      "expected_suggested_paths": [],
      "expected_textification_intent": "Coverage-only archive source case: reject as unsupported media without calling an LLM.",
      "fixture_metadata": {
        "mime_type": "application/zip",
        "name": "r-zip-repo-01.zip",
        "path": "/Users/zeph/github/tzaffi/curio/tmp/textify-smoke/20260428-132551-09c3fa3c8f75/cases/R-ZIP-REPO-01/fixtures/r-zip-repo-01.zip",
        "sha256": "b3caf0cc25a77138020d670e536279f575a060ee02022be5e7be11f3725cfcb1",
        "source_language_hint": null
      },
      "ground_truth_text": "",
      "model_importance": 1,
      "output_format": [],
      "participates_in_model_ranking": false,
      "preservation_requirements": [
        "unsupported_media",
        "no provider call"
      ],
      "rendered_textified_text": "",
      "response_path": "runs/R-ZIP-REPO-01/textifier_codex_gpt_53_codex/response.json",
      "response_warnings": [
        "unsupported media type for textify v1",
        "unsupported media type for textify v1"
      ],
      "status": "unsupported_media",
      "suggested_files": [],
      "usage": null
    },
    {
      "caller": "textifier_codex_gpt_55",
      "case_id": "C-IMG-TXT-01",
      "expected_output_format": "txt",
      "expected_status": "converted",
      "expected_suggested_paths": [
        "note.txt"
      ],
      "expected_textification_intent": "Extract a plain text note without inventing Markdown headings.",
      "fixture_metadata": {
        "mime_type": "image/png",
        "name": "plain-note.png",
        "path": "/Users/zeph/github/tzaffi/curio/tmp/textify-smoke/20260428-132551-09c3fa3c8f75/cases/C-IMG-TXT-01/fixtures/plain-note.png",
        "sha256": "c895ee9f1e59ac6618167a67d3439fc309ff0fbf4df05bc82da08d5a299b5c59",
        "source_language_hint": null
      },
      "ground_truth_text": "DEPLOY NOTE\nRUN UV SYNC\nTHEN MAKE CHECK\nKEEP README.MD OPEN",
      "model_importance": 1,
      "output_format": [
        "txt"
      ],
      "participates_in_model_ranking": true,
      "preservation_requirements": [
        "RUN UV SYNC",
        "MAKE CHECK",
        "README.MD"
      ],
      "rendered_textified_text": "DEPLOY NOTE\nRUN UV SYNC\nTHEN MAKE CHECK\nKEEP README.MD OPEN",
      "response_path": "runs/C-IMG-TXT-01/textifier_codex_gpt_55/response.json",
      "response_warnings": [],
      "status": "converted",
      "suggested_files": [
        {
          "output_format": "txt",
          "suggested_path": "note.txt",
          "text": "DEPLOY NOTE\nRUN UV SYNC\nTHEN MAKE CHECK\nKEEP README.MD OPEN"
        }
      ],
      "usage": {
        "api_equivalent_cost_usd": 0.137041,
        "basis": "api_equivalent",
        "cached_input_price_per_million": 0.5,
        "cached_input_tokens": 2432,
        "completed_at": "2026-04-28T13:37:51.963821Z",
        "currency": "USD",
        "input_price_per_million": 5.0,
        "input_tokens": 26559,
        "metered_objects": [],
        "output_price_per_million": 30.0,
        "output_tokens": 101,
        "reasoning_tokens": 0,
        "started_at": "2026-04-28T13:37:45.145087Z",
        "thinking_seconds": null,
        "total_tokens": 26660,
        "wall_seconds": 6.818734
      }
    },
    {
      "caller": "textifier_codex_gpt_55",
      "case_id": "C-IMG-CODE-01",
      "expected_output_format": "txt",
      "expected_status": "converted",
      "expected_suggested_paths": [
        "foo.py"
      ],
      "expected_textification_intent": "Extract the visible Python file and preserve the visible filename foo.py.",
      "fixture_metadata": {
        "mime_type": "image/png",
        "name": "foo.py.png",
        "path": "/Users/zeph/github/tzaffi/curio/tmp/textify-smoke/20260428-132551-09c3fa3c8f75/cases/C-IMG-CODE-01/fixtures/foo.py.png",
        "sha256": "eaf0ff4c9968e18d4ff4ea8692c524431a5e45a04030a76b9ba26bff79e68f96",
        "source_language_hint": null
      },
      "ground_truth_text": "FILE: foo.py\nDEF GREET(NAME):\n    PRINT(\"HOLA\", NAME)\nGREET(\"CURIO\")",
      "model_importance": 1,
      "output_format": [
        "txt"
      ],
      "participates_in_model_ranking": true,
      "preservation_requirements": [
        "foo.py",
        "DEF GREET(NAME):",
        "PRINT(\"HOLA\", NAME)",
        "GREET(\"CURIO\")"
      ],
      "rendered_textified_text": "FILE: FOO.PY\nDEF GREET(NAME):\n    PRINT(\"HOLA\", NAME)\nGREET(\"CURIO\")",
      "response_path": "runs/C-IMG-CODE-01/textifier_codex_gpt_55/response.json",
      "response_warnings": [],
      "status": "converted",
      "suggested_files": [
        {
          "output_format": "txt",
          "suggested_path": "foo.py",
          "text": "FILE: FOO.PY\nDEF GREET(NAME):\n    PRINT(\"HOLA\", NAME)\nGREET(\"CURIO\")"
        }
      ],
      "usage": {
        "api_equivalent_cost_usd": 0.137436,
        "basis": "api_equivalent",
        "cached_input_price_per_million": 0.5,
        "cached_input_tokens": 2432,
        "completed_at": "2026-04-28T13:38:00.361350Z",
        "currency": "USD",
        "input_price_per_million": 5.0,
        "input_tokens": 26578,
        "metered_objects": [],
        "output_price_per_million": 30.0,
        "output_tokens": 111,
        "reasoning_tokens": 0,
        "started_at": "2026-04-28T13:37:51.977438Z",
        "thinking_seconds": null,
        "total_tokens": 26689,
        "wall_seconds": 8.383912
      }
    },
    {
      "caller": "textifier_codex_gpt_55",
      "case_id": "C-IMG-CODE-02",
      "expected_output_format": "txt",
      "expected_status": "converted",
      "expected_suggested_paths": [
        "hello_curio.py"
      ],
      "expected_textification_intent": "Extract Python code and infer a safe .py filename from the script purpose.",
      "fixture_metadata": {
        "mime_type": "image/png",
        "name": "python-script-no-name.png",
        "path": "/Users/zeph/github/tzaffi/curio/tmp/textify-smoke/20260428-132551-09c3fa3c8f75/cases/C-IMG-CODE-02/fixtures/python-script-no-name.png",
        "sha256": "06ae9ca9570cdac8b591816c2f31d8ee526596d7845c7fa652c659b81affc484",
        "source_language_hint": null
      },
      "ground_truth_text": "DEF HELLO_CURIO():\n    RETURN \"HELLO CURIO\"\nPRINT(HELLO_CURIO())",
      "model_importance": 1,
      "output_format": [
        "txt"
      ],
      "participates_in_model_ranking": true,
      "preservation_requirements": [
        "HELLO_CURIO",
        "RETURN \"HELLO CURIO\"",
        "PRINT(HELLO_CURIO())"
      ],
      "rendered_textified_text": "DEF HELLO_CURIO():\n    RETURN \"HELLO CURIO\"\nPRINT(HELLO_CURIO())",
      "response_path": "runs/C-IMG-CODE-02/textifier_codex_gpt_55/response.json",
      "response_warnings": [],
      "status": "converted",
      "suggested_files": [
        {
          "output_format": "txt",
          "suggested_path": "hello_curio.py",
          "text": "DEF HELLO_CURIO():\n    RETURN \"HELLO CURIO\"\nPRINT(HELLO_CURIO())"
        }
      ],
      "usage": {
        "api_equivalent_cost_usd": 0.137461,
        "basis": "api_equivalent",
        "cached_input_price_per_million": 0.5,
        "cached_input_tokens": 2432,
        "completed_at": "2026-04-28T13:38:07.529226Z",
        "currency": "USD",
        "input_price_per_million": 5.0,
        "input_tokens": 26589,
        "metered_objects": [],
        "output_price_per_million": 30.0,
        "output_tokens": 110,
        "reasoning_tokens": 0,
        "started_at": "2026-04-28T13:38:00.373800Z",
        "thinking_seconds": null,
        "total_tokens": 26699,
        "wall_seconds": 7.155426
      }
    },
    {
      "caller": "textifier_codex_gpt_55",
      "case_id": "C-IMG-MULTI-01",
      "expected_output_format": "txt",
      "expected_status": "converted",
      "expected_suggested_paths": [
        "scripts/setup.sh",
        "scripts/run.sh",
        "scripts/cleanup.sh"
      ],
      "expected_textification_intent": "Split three visible shell script snippets into three safe relative .sh files.",
      "fixture_metadata": {
        "mime_type": "image/png",
        "name": "three-shell-scripts.png",
        "path": "/Users/zeph/github/tzaffi/curio/tmp/textify-smoke/20260428-132551-09c3fa3c8f75/cases/C-IMG-MULTI-01/fixtures/three-shell-scripts.png",
        "sha256": "8e66a9bd958ff978ca977166b50e98e4644531fb7e2024f66679f15cfdd5c5cb",
        "source_language_hint": null
      },
      "ground_truth_text": "FILE: scripts/setup.sh\nECHO SETUP\n\nFILE: scripts/run.sh\nECHO RUN\n\nFILE: scripts/cleanup.sh\nECHO CLEANUP",
      "model_importance": 1,
      "output_format": [
        "txt",
        "txt",
        "txt"
      ],
      "participates_in_model_ranking": true,
      "preservation_requirements": [
        "scripts/setup.sh",
        "scripts/run.sh",
        "scripts/cleanup.sh",
        "ECHO CLEANUP"
      ],
      "rendered_textified_text": "echo setup\n\n\necho run\n\n\necho cleanup\n",
      "response_path": "runs/C-IMG-MULTI-01/textifier_codex_gpt_55/response.json",
      "response_warnings": [],
      "status": "converted",
      "suggested_files": [
        {
          "output_format": "txt",
          "suggested_path": "scripts/setup.sh",
          "text": "echo setup\n"
        },
        {
          "output_format": "txt",
          "suggested_path": "scripts/run.sh",
          "text": "echo run\n"
        },
        {
          "output_format": "txt",
          "suggested_path": "scripts/cleanup.sh",
          "text": "echo cleanup\n"
        }
      ],
      "usage": {
        "api_equivalent_cost_usd": 0.138586,
        "basis": "api_equivalent",
        "cached_input_price_per_million": 0.5,
        "cached_input_tokens": 2432,
        "completed_at": "2026-04-28T13:38:15.416318Z",
        "currency": "USD",
        "input_price_per_million": 5.0,
        "input_tokens": 26706,
        "metered_objects": [],
        "output_price_per_million": 30.0,
        "output_tokens": 128,
        "reasoning_tokens": 0,
        "started_at": "2026-04-28T13:38:07.548887Z",
        "thinking_seconds": null,
        "total_tokens": 26834,
        "wall_seconds": 7.867431
      }
    },
    {
      "caller": "textifier_codex_gpt_55",
      "case_id": "C-IMG-POST-01",
      "expected_output_format": "markdown",
      "expected_status": "converted",
      "expected_suggested_paths": [
        "social-post.md"
      ],
      "expected_textification_intent": "Preserve a social post's handle, timestamp, URL, emoji marker, and source language.",
      "fixture_metadata": {
        "mime_type": "image/png",
        "name": "social-post-es.png",
        "path": "/Users/zeph/github/tzaffi/curio/tmp/textify-smoke/20260428-132551-09c3fa3c8f75/cases/C-IMG-POST-01/fixtures/social-post-es.png",
        "sha256": "b3d6f2d21646f9fab10a3b6b44e888db7845ee31af66630d8bc50fbbeba922f1",
        "source_language_hint": "es"
      },
      "ground_truth_text": "@MARIA 2026-04-27 10:15\nNO TRADUZCAS /V1/CHAT\nVISITA HTTPS://EXAMPLE.COM\nEMOJI: ROCKET",
      "model_importance": 1,
      "output_format": [
        "markdown"
      ],
      "participates_in_model_ranking": true,
      "preservation_requirements": [
        "@MARIA",
        "2026-04-27 10:15",
        "/V1/CHAT",
        "HTTPS://EXAMPLE.COM",
        "ROCKET"
      ],
      "rendered_textified_text": "@MARIA 2026-04-27 10:15\nNO TRADUZCAS 🧡V1/CHAT\nVISITA HTTPS://EXAMPLE.COM\nEMOJI: ROCKET",
      "response_path": "runs/C-IMG-POST-01/textifier_codex_gpt_55/response.json",
      "response_warnings": [],
      "status": "converted",
      "suggested_files": [
        {
          "output_format": "markdown",
          "suggested_path": "social-post.md",
          "text": "@MARIA 2026-04-27 10:15\nNO TRADUZCAS 🧡V1/CHAT\nVISITA HTTPS://EXAMPLE.COM\nEMOJI: ROCKET"
        }
      ],
      "usage": {
        "api_equivalent_cost_usd": 0.138031,
        "basis": "api_equivalent",
        "cached_input_price_per_million": 0.5,
        "cached_input_tokens": 2432,
        "completed_at": "2026-04-28T13:38:23.844142Z",
        "currency": "USD",
        "input_price_per_million": 5.0,
        "input_tokens": 26607,
        "metered_objects": [],
        "output_price_per_million": 30.0,
        "output_tokens": 126,
        "reasoning_tokens": 0,
        "started_at": "2026-04-28T13:38:15.434588Z",
        "thinking_seconds": null,
        "total_tokens": 26733,
        "wall_seconds": 8.409554
      }
    },
    {
      "caller": "textifier_codex_gpt_55",
      "case_id": "C-PDF-DOC-01",
      "expected_output_format": "markdown",
      "expected_status": "converted",
      "expected_suggested_paths": [
        "document.md"
      ],
      "expected_textification_intent": "Extract a one-page document with title, headings, paragraphs, and bullets.",
      "fixture_metadata": {
        "mime_type": "application/pdf",
        "name": "document-layout.pdf",
        "path": "/Users/zeph/github/tzaffi/curio/tmp/textify-smoke/20260428-132551-09c3fa3c8f75/cases/C-PDF-DOC-01/fixtures/document-layout.pdf",
        "sha256": "e04a909ad3499bb0f6252bc0eb6c765bbfbdb541d2b9d867341cdec7cbc1bbd0",
        "source_language_hint": null
      },
      "ground_truth_text": "Curio Release Plan\nGoals\n- Keep smoke tests opt-in\n- Preserve source language\nNext Steps\nRun make check",
      "model_importance": 1,
      "output_format": [
        "markdown"
      ],
      "participates_in_model_ranking": true,
      "preservation_requirements": [
        "Curio Release Plan",
        "Goals",
        "Keep smoke tests opt-in",
        "Run make check"
      ],
      "rendered_textified_text": "# Curio Release Plan\n\n## Goals\n\n- Keep smoke tests opt-in\n- Preserve source language\n\n## Next Steps\n\nRun make check\n",
      "response_path": "runs/C-PDF-DOC-01/textifier_codex_gpt_55/response.json",
      "response_warnings": [],
      "status": "converted",
      "suggested_files": [
        {
          "output_format": "markdown",
          "suggested_path": "document.md",
          "text": "# Curio Release Plan\n\n## Goals\n\n- Keep smoke tests opt-in\n- Preserve source language\n\n## Next Steps\n\nRun make check\n"
        }
      ],
      "usage": {
        "api_equivalent_cost_usd": 1.057361,
        "basis": "api_equivalent",
        "cached_input_price_per_million": 0.5,
        "cached_input_tokens": 162432,
        "completed_at": "2026-04-28T13:38:58.700224Z",
        "currency": "USD",
        "input_price_per_million": 5.0,
        "input_tokens": 189793,
        "metered_objects": [],
        "output_price_per_million": 30.0,
        "output_tokens": 906,
        "reasoning_tokens": 127,
        "started_at": "2026-04-28T13:38:23.850398Z",
        "thinking_seconds": null,
        "total_tokens": 190699,
        "wall_seconds": 34.849826
      }
    },
    {
      "caller": "textifier_codex_gpt_55",
      "case_id": "C-PDF-TABLE-01",
      "expected_output_format": "markdown",
      "expected_status": "converted",
      "expected_suggested_paths": [
        "table.md"
      ],
      "expected_textification_intent": "Extract a small table without swapping rows or columns.",
      "fixture_metadata": {
        "mime_type": "application/pdf",
        "name": "table-layout.pdf",
        "path": "/Users/zeph/github/tzaffi/curio/tmp/textify-smoke/20260428-132551-09c3fa3c8f75/cases/C-PDF-TABLE-01/fixtures/table-layout.pdf",
        "sha256": "766f1e57d76f62eb7a837862b1354f1c6714aa69a797c15f18bb635455333ec2",
        "source_language_hint": null
      },
      "ground_truth_text": "Service | Count | Status\nCodex | 3 | Ready\nDocAI | 1 | Punted\nOpenAI API | 0 | Punted",
      "model_importance": 1,
      "output_format": [
        "markdown"
      ],
      "participates_in_model_ranking": true,
      "preservation_requirements": [
        "Codex | 3 | Ready",
        "DocAI | 1 | Punted",
        "OpenAI API | 0 | Punted"
      ],
      "rendered_textified_text": "| Service | Count | Status |\n|---|---:|---|\n| Codex | 3 | Ready |\n| DocAI | 1 | Punted |\n| OpenAI API | 0 | Punted |",
      "response_path": "runs/C-PDF-TABLE-01/textifier_codex_gpt_55/response.json",
      "response_warnings": [],
      "status": "converted",
      "suggested_files": [
        {
          "output_format": "markdown",
          "suggested_path": "table.md",
          "text": "| Service | Count | Status |\n|---|---:|---|\n| Codex | 3 | Ready |\n| DocAI | 1 | Punted |\n| OpenAI API | 0 | Punted |"
        }
      ],
      "usage": {
        "api_equivalent_cost_usd": 1.218542,
        "basis": "api_equivalent",
        "cached_input_price_per_million": 0.5,
        "cached_input_tokens": 190464,
        "completed_at": "2026-04-28T13:39:42.578232Z",
        "currency": "USD",
        "input_price_per_million": 5.0,
        "input_tokens": 218302,
        "metered_objects": [],
        "output_price_per_million": 30.0,
        "output_tokens": 1060,
        "reasoning_tokens": 96,
        "started_at": "2026-04-28T13:38:58.709492Z",
        "thinking_seconds": null,
        "total_tokens": 219362,
        "wall_seconds": 43.86874
      }
    },
    {
      "caller": "textifier_codex_gpt_55",
      "case_id": "C-IMG-RECEIPT-01",
      "expected_output_format": "markdown",
      "expected_status": "converted",
      "expected_suggested_paths": [
        "receipt.md"
      ],
      "expected_textification_intent": "Extract dense receipt-like labels, dates, amounts, and totals.",
      "fixture_metadata": {
        "mime_type": "image/png",
        "name": "receipt.png",
        "path": "/Users/zeph/github/tzaffi/curio/tmp/textify-smoke/20260428-132551-09c3fa3c8f75/cases/C-IMG-RECEIPT-01/fixtures/receipt.png",
        "sha256": "dacd233925e84d3f58cd4f21d6f9b967226de5d73e1723ce09d41e44a7aafb56",
        "source_language_hint": null
      },
      "ground_truth_text": "CURIO CAFE\nDATE 2026-04-27\nLATTE 4.50\nSANDWICH 8.25\nTOTAL 12.75",
      "model_importance": 1,
      "output_format": [
        "markdown"
      ],
      "participates_in_model_ranking": true,
      "preservation_requirements": [
        "2026-04-27",
        "LATTE 4.50",
        "SANDWICH 8.25",
        "TOTAL 12.75"
      ],
      "rendered_textified_text": "CURIO CAFE\nDATE 2026-04-27\nLATTE 4.50\nSANDWICH 8.25\nTOTAL 12.75",
      "response_path": "runs/C-IMG-RECEIPT-01/textifier_codex_gpt_55/response.json",
      "response_warnings": [],
      "status": "converted",
      "suggested_files": [
        {
          "output_format": "markdown",
          "suggested_path": "receipt.md",
          "text": "CURIO CAFE\nDATE 2026-04-27\nLATTE 4.50\nSANDWICH 8.25\nTOTAL 12.75"
        }
      ],
      "usage": {
        "api_equivalent_cost_usd": 0.137701,
        "basis": "api_equivalent",
        "cached_input_price_per_million": 0.5,
        "cached_input_tokens": 2432,
        "completed_at": "2026-04-28T13:39:51.427107Z",
        "currency": "USD",
        "input_price_per_million": 5.0,
        "input_tokens": 26583,
        "metered_objects": [],
        "output_price_per_million": 30.0,
        "output_tokens": 119,
        "reasoning_tokens": 0,
        "started_at": "2026-04-28T13:39:42.619524Z",
        "thinking_seconds": null,
        "total_tokens": 26702,
        "wall_seconds": 8.807583
      }
    },
    {
      "caller": "textifier_codex_gpt_55",
      "case_id": "C-IMG-NO-TEXT-01",
      "expected_output_format": "markdown",
      "expected_status": "no_text_found",
      "expected_suggested_paths": [],
      "expected_textification_intent": "Return no_text_found for an image with no readable text and do not invent alt text.",
      "fixture_metadata": {
        "mime_type": "image/png",
        "name": "no-readable-text.png",
        "path": "/Users/zeph/github/tzaffi/curio/tmp/textify-smoke/20260428-132551-09c3fa3c8f75/cases/C-IMG-NO-TEXT-01/fixtures/no-readable-text.png",
        "sha256": "519ad675a14d7e9b1658dfe5d2e175c4a4ad9f35d946f9e04185940e1a1eb818",
        "source_language_hint": null
      },
      "ground_truth_text": "",
      "model_importance": 1,
      "output_format": [],
      "participates_in_model_ranking": true,
      "preservation_requirements": [
        "no invented description",
        "compact warning"
      ],
      "rendered_textified_text": "",
      "response_path": "runs/C-IMG-NO-TEXT-01/textifier_codex_gpt_55/response.json",
      "response_warnings": [
        "No readable text found in image."
      ],
      "status": "no_text_found",
      "suggested_files": [],
      "usage": {
        "api_equivalent_cost_usd": 0.136376,
        "basis": "api_equivalent",
        "cached_input_price_per_million": 0.5,
        "cached_input_tokens": 2432,
        "completed_at": "2026-04-28T13:40:02.001597Z",
        "currency": "USD",
        "input_price_per_million": 5.0,
        "input_tokens": 26570,
        "metered_objects": [],
        "output_price_per_million": 30.0,
        "output_tokens": 77,
        "reasoning_tokens": 0,
        "started_at": "2026-04-28T13:39:51.553937Z",
        "thinking_seconds": null,
        "total_tokens": 26647,
        "wall_seconds": 10.44766
      }
    },
    {
      "caller": "textifier_codex_gpt_55",
      "case_id": "R-IMG-DASH-01",
      "expected_output_format": "markdown",
      "expected_status": "converted",
      "expected_suggested_paths": [
        "claude-code-usage-dashboard.md"
      ],
      "expected_textification_intent": "Extract the dashboard title, filters, metric cards, charts, recent-session table, and visible numeric values into Markdown.",
      "fixture_metadata": {
        "mime_type": "image/jpeg",
        "name": "r-img-dash-01.jpg",
        "path": "/Users/zeph/github/tzaffi/curio/tmp/textify-smoke/20260428-132551-09c3fa3c8f75/cases/R-IMG-DASH-01/fixtures/r-img-dash-01.jpg",
        "sha256": "a74c7cb477b123bfc87dd97eb0c634786b6a4f537d387c2a96e5739d31d3118a",
        "source_language_hint": null
      },
      "ground_truth_text": "Claude Code Usage Dashboard\nSessions 440\nTurns 18.0K\nInput tokens 617.2K\nOutput tokens 4.75M\nCache read 1.95B\nEst. cost $1588.30",
      "model_importance": 9,
      "output_format": [
        "markdown"
      ],
      "participates_in_model_ranking": true,
      "preservation_requirements": [
        "Claude Code Usage Dashboard",
        "440",
        "18.0K",
        "617.2K",
        "4.75M",
        "$1588.30"
      ],
      "rendered_textified_text": "# Claude Code Usage Dashboard\n\nUpdated: 2026-04-07 20:56:27 · Auto-refresh in 30s\n\n## Filters\n\nMODELS\n\n- claude-opus-4-6\n- claude-sonnet-4-6\n- claude-haiku-4-5-20251001\n- All\n- None\n\nRANGE\n\n- 7d\n- 30d\n- 90d\n- All\n\n## Metrics\n\n| Metric | Value | Note |\n|---|---:|---|\n| SESSIONS | 440 | last 30 days |\n| TURNS | 18.0K | last 30 days |\n| INPUT TOKENS | 617.2K | last 30 days |\n| OUTPUT TOKENS | 4.75M | last 30 days |\n| CACHE READ | 1.95B | from prompt cache |\n| CACHE CREATION | 74.66M | writes to prompt cache |\n| EST. COST | $1588.30 | API pricing, Apr 2026 |\n\n## Daily Token Usage — Last 30 Days\n\nLegend: Input, Output, Cache Read, Cache Creation\n\nY-axis labels:\n\n- 0\n- 100.00M\n- 200.00M\n- 300.00M\n- 400.00M\n- 500.00M\n- 600.00M\n- 700.00M\n- 800.00M\n\nX-axis dates visible:\n\n- 2026-03-08\n- 2026-03-10\n- 2026-03-14\n- 2026-03-16\n- 2026-03-18\n- 2026-03-20\n- 2026-03-22\n- 2026-03-24\n- 2026-03-26\n- 2026-03-28\n- 2026-03-30\n- 2026-04-01\n- 2026-04-03\n- 2026-04-05\n- 2026-04-07\n\n## By Model\n\nLegend:\n\n- claude-opus-4-6\n- claude-sonnet-4-6\n- claude-haiku-4-5-20251001\n\n## Top Projects by Tokens\n\nLegend: Input, Output\n\nProjects visible:\n\n- Workspace/Editor\n- Artifacts/hassid\n- GitHub/SwarmProtocol\n- Dell/Desktop\n- ...e/agent-second-brain\n- worktrees/happy-wilson\n- worktrees/busy-curran\n- GitHub/Chatbot\n- ...rees/adoring-hermann\n- ...trees/trusting-raman\n\nX-axis labels:\n\n- 0\n- 500.0K\n- 1.00M\n- 1.50M\n- 2.00M\n- 2.50M\n- 3.00M\n\n## Recent Sessions\n\n| Session | Project | Last Active | Duration | Model | Turns | Input | Output | Est. Cost |\n|---|---|---|---:|---|---:|---:|---:|---:|\n| 0d1902c1... | Dell/Desktop | 2026-04-07 17:09 | 7.8m | claude-sonnet-4-6 | 22 | 734 | 16.4K | $0.8485 |",
      "response_path": "runs/R-IMG-DASH-01/textifier_codex_gpt_55/response.json",
      "response_warnings": [
        "Some small chart labels and truncated project/session text are low-resolution or partially cropped; uncertain OCR preserved with visible ellipses where shown.",
        "Bottom of recent sessions table is cropped; only the visible first row was extracted."
      ],
      "status": "converted",
      "suggested_files": [
        {
          "output_format": "markdown",
          "suggested_path": "claude-code-usage-dashboard.md",
          "text": "# Claude Code Usage Dashboard\n\nUpdated: 2026-04-07 20:56:27 · Auto-refresh in 30s\n\n## Filters\n\nMODELS\n\n- claude-opus-4-6\n- claude-sonnet-4-6\n- claude-haiku-4-5-20251001\n- All\n- None\n\nRANGE\n\n- 7d\n- 30d\n- 90d\n- All\n\n## Metrics\n\n| Metric | Value | Note |\n|---|---:|---|\n| SESSIONS | 440 | last 30 days |\n| TURNS | 18.0K | last 30 days |\n| INPUT TOKENS | 617.2K | last 30 days |\n| OUTPUT TOKENS | 4.75M | last 30 days |\n| CACHE READ | 1.95B | from prompt cache |\n| CACHE CREATION | 74.66M | writes to prompt cache |\n| EST. COST | $1588.30 | API pricing, Apr 2026 |\n\n## Daily Token Usage — Last 30 Days\n\nLegend: Input, Output, Cache Read, Cache Creation\n\nY-axis labels:\n\n- 0\n- 100.00M\n- 200.00M\n- 300.00M\n- 400.00M\n- 500.00M\n- 600.00M\n- 700.00M\n- 800.00M\n\nX-axis dates visible:\n\n- 2026-03-08\n- 2026-03-10\n- 2026-03-14\n- 2026-03-16\n- 2026-03-18\n- 2026-03-20\n- 2026-03-22\n- 2026-03-24\n- 2026-03-26\n- 2026-03-28\n- 2026-03-30\n- 2026-04-01\n- 2026-04-03\n- 2026-04-05\n- 2026-04-07\n\n## By Model\n\nLegend:\n\n- claude-opus-4-6\n- claude-sonnet-4-6\n- claude-haiku-4-5-20251001\n\n## Top Projects by Tokens\n\nLegend: Input, Output\n\nProjects visible:\n\n- Workspace/Editor\n- Artifacts/hassid\n- GitHub/SwarmProtocol\n- Dell/Desktop\n- ...e/agent-second-brain\n- worktrees/happy-wilson\n- worktrees/busy-curran\n- GitHub/Chatbot\n- ...rees/adoring-hermann\n- ...trees/trusting-raman\n\nX-axis labels:\n\n- 0\n- 500.0K\n- 1.00M\n- 1.50M\n- 2.00M\n- 2.50M\n- 3.00M\n\n## Recent Sessions\n\n| Session | Project | Last Active | Duration | Model | Turns | Input | Output | Est. Cost |\n|---|---|---|---:|---|---:|---:|---:|---:|\n| 0d1902c1... | Dell/Desktop | 2026-04-07 17:09 | 7.8m | claude-sonnet-4-6 | 22 | 734 | 16.4K | $0.8485 |"
        }
      ],
      "usage": {
        "api_equivalent_cost_usd": 0.17996,
        "basis": "api_equivalent",
        "cached_input_price_per_million": 0.5,
        "cached_input_tokens": 24960,
        "completed_at": "2026-04-28T13:40:28.444858Z",
        "currency": "USD",
        "input_price_per_million": 5.0,
        "input_tokens": 28012,
        "metered_objects": [],
        "output_price_per_million": 30.0,
        "output_tokens": 914,
        "reasoning_tokens": 0,
        "started_at": "2026-04-28T13:40:02.054774Z",
        "thinking_seconds": null,
        "total_tokens": 28926,
        "wall_seconds": 26.390084
      }
    },
    {
      "caller": "textifier_codex_gpt_55",
      "case_id": "R-IMG-LLM-TABLE-01",
      "expected_output_format": "markdown",
      "expected_status": "converted",
      "expected_suggested_paths": [
        "local-llm-cheat-sheet.md"
      ],
      "expected_textification_intent": "Convert the dense local LLM cheat sheet into a Markdown table preserving model rows, weights, speed, context, use cases, and bottom line.",
      "fixture_metadata": {
        "mime_type": "image/jpeg",
        "name": "r-img-llm-table-01.jpg",
        "path": "/Users/zeph/github/tzaffi/curio/tmp/textify-smoke/20260428-132551-09c3fa3c8f75/cases/R-IMG-LLM-TABLE-01/fixtures/r-img-llm-table-01.jpg",
        "sha256": "9fc4f7a9c8958056c2aedac53d70614aeebfbffc64f1b9200b05a5eab1855de9",
        "source_language_hint": null
      },
      "ground_truth_text": "LOCAL LLM CHEAT SHEET\n128GB RAM\nQwen3.5-397B-A17B\nMistral Large 2411\nMiniMax-M2.7\nGLM-4.5-Air\nQwen3-VL-235B-A22B-Thinking\nBottom line: match it to your workflow.",
      "model_importance": 10,
      "output_format": [
        "markdown"
      ],
      "participates_in_model_ranking": true,
      "preservation_requirements": [
        "LOCAL LLM CHEAT SHEET",
        "128GB RAM",
        "Qwen3.5-397B-A17B",
        "MiniMax-M2.7",
        "Qwen3-VL-235B-A22B-Thinking",
        "Bottom line"
      ],
      "rendered_textified_text": "# Local LLM Cheat Sheet: 128GB RAM\n\nApril 24, 2026 • Mac Studio M-Ultra • Workstation Tier\n\n## Important Framing\n\nWeights size = GGUF file size on disk, not total runtime memory.\n\nReal RAM use = weights + 4-6GB OS + KV cache (~0.2GB per 100K context) + misc. Even at this tier, 1M context is theoretical - plan for 64-256K in practice.\n\n| Model | Weights Size | Speed | Context | Best Pick | Best Used For | Honest Take |\n|---|---:|---|---|---|---|---|\n| **1) General Purpose & All-Rounders** |||||||\n| **Qwen3.5-397B-A17B**<br>UD-IQ1_M • Recommended<br>Qwen • Apache 2.0<br>LiveCodeBench 83.6 | 106.82 GB | **Medium**<br>397B total / 17B active MoE. | 262K<br>Native 262K context. | Best Overall / General Assistant | general assistant<br>hardest reasoning<br>research<br>complex agents | Best overall. Strongest all-rounder on 128GB for reasoning, research, and agentic work. |\n| **Mistral Large 2411**<br>Q4_K_M • Recommended<br>Mistral AI • MRL (research/non-commercial)<br>MMLU 84.0 • HumanEval 90.0<br>Multilingual SOTA • Fn calling native | 73.22 GB | **Medium**<br>Dense 123B at 4-bit. Heavier but still fast. | 128K<br>Best-in-class European multilingual. | Best Writing / Multilingual | creative writing<br>multilingual tasks<br>function calling<br>long-form prose | Excels on writing and multilingual tasks with strong function calling. Great for creative and business work. |\n| **2) Coding / Agent / Tool-Use Kings** |||||||\n| **MiniMax-M2.7**<br>UD-IQ2_XXS • Recommended<br>MiniMax • Apache 2.0<br>SWE-Bench Pro 56.2 • GPQA-D 77.7<br>SWE-Mult 76.5 | 65.38 GB | **Fast**<br>229B total / 10B active MoE. Low-latency agent loops. | 200K<br>Long enough for tool-call traces and agent loops. | Agent Loops | tool calling<br>multi-step coding<br>autonomous tasks | Strong purpose-built agent model. Excellent for tool use and autonomous workflows on 128GB. |\n| **GLM-4.5-Air**<br>Q6_K • Recommended<br>ZhipuAI • MIT<br>SWE-Bench Verified 64.2 • MMLU-Pro 79.1<br>IFEval strong | 99.01 GB | **Medium**<br>106B total / 12B active MoE. Great speed-quality balance. | 128K<br>Purpose-built for ARC, agent, and repo loops. | Coding | SWE tasks<br>agent tool loops<br>repo diffs | Excellent coding/agent model with a strong balance of reasoning, repo work, and tool use. |\n| **3) Math & Competition Reasoning** |||||||\n| **Qwen3-235B-A22B-Thinking-2507**<br>UD-Q2_K_XL • Recommended<br>Qwen • Apache 2.0<br>GPQA-D 81.1 • AIME'25 92.3<br>MMLU-Pro 84 • SWE-V 39 | 88.77 GB | **Medium**<br>235B total / 22B active MoE. Balanced reasoning, language. | 256K<br>Room for long reasoning traces, tricky math, and code windows. | Best Math & Reasoning Pick | competition math<br>structured solving<br>analysis<br>deep logic | Elite reasoning model for math and structured problem solving. Not the best everyday general chat model. |\n| **gpt-oss-120b**<br>Q8_0 • Recommended<br>OpenAI • Apache 2.0<br>MMLU-Pro 90.0 • AIME'25 97.9 (tool-assisted)<br>SWE-Bench Verified 62.4 | 63.39 GB | **Fast**<br>MXFP4-native weights, Q8_0. Is effectively full precision at 63 GB. | 128K<br>Solid long-context for reasoning; efficient on unified memory. | Math & Efficiency Veteran | math olympiad<br>hard reasoning<br>general assistant<br>code | Excellent older model (Aug 2025). MXFP4-native means Q8_0 is full precision. Still extremely strong on math/olympiad tasks and efficient on unified memory. |\n| **4) Vision & Multimodal** |||||||\n| **Qwen3-VL-235B-A22B-Thinking**<br>UD-IQ3_XXS • Recommended<br>Qwen • Apache 2.0<br>Vision Arena 2358<br>DocVQA high • multimodal reasoning strong | 94.73 GB | **Medium**<br>235B total / 22B active MoE. Vision agent overhead on long images. | 128K<br>Multimodal: image, text, native vision support via llama.cpp. | Best Vision Thinker | image understanding<br>vision reasoning<br>charts & docs<br>OCR & layout | Same reasoning core as Qwen3-235B-Thinking plus vision. Great for docs, diagrams, charts, and technical reports. |\n| **5) Long-Context / Research / Fast Thinkers** |||||||\n| **Llama-4-Scout 17Bx16E**<br>Q6_K • Recommended<br>Meta • Llama Community License<br>Context 10M • MMLU-Pro 74.3<br>GPQA-D 57.2 • Multimodal native | 88.43 GB | **Fast**<br>109B total / 17B active MoE. | 10M<br>Native 10M context window; best for huge codebases, corpora, and archives. | Best Long-Context Research Pick | massive documents<br>multimodal ingest<br>research corpora<br>long-context QA | Unmatched for huge-context work. Best when you truly need 10M context; weaker than top picks on raw reasoning. |\n| **Qwen3-Next-80B-A3B-Thinking**<br>Q6_K • Recommended<br>Qwen • Apache 2.0<br>MMLU-Pro 82.8 • GPQA-D 77.2<br>AIME'25 87.8 • 3B active | 65.79 GB | **Very fast**<br>80B total / 3B active MoE. Hybrid attention keeps latency low on long context. | 256K<br>Hybrid attention keeps latency low on long context. | Best Fast Thinker | fast reasoning<br>interactive math<br>long-context loops<br>agent planning | Best reasoning per-second on the sheet. Pick it for fast, responsive thinking and interactive use, not deepest reasoning. |\n\n## Bottom Line\n\n128GB advice: Model choice is highly use-case dependent. Qwen3.5-397B-A17B is the strongest all-rounder. Pick MiniMax-M2.7 or GLM-4.5-Air for agent/coding work, gpt-oss-120b for math/efficiency, and the specialists for vision or 10M+ context. There is no single \"best\" model - match it to your workflow.\n\n@qkisokay",
      "response_path": "runs/R-IMG-LLM-TABLE-01/textifier_codex_gpt_55/response.json",
      "response_warnings": [
        "Dense infographic with small text; some benchmark labels and license/model suffixes may contain OCR uncertainty.",
        "Some colored tag text and tiny footnote text may be imperfect due to compression and resolution."
      ],
      "status": "converted",
      "suggested_files": [
        {
          "output_format": "markdown",
          "suggested_path": "local-llm-cheat-sheet.md",
          "text": "# Local LLM Cheat Sheet: 128GB RAM\n\nApril 24, 2026 • Mac Studio M-Ultra • Workstation Tier\n\n## Important Framing\n\nWeights size = GGUF file size on disk, not total runtime memory.\n\nReal RAM use = weights + 4-6GB OS + KV cache (~0.2GB per 100K context) + misc. Even at this tier, 1M context is theoretical - plan for 64-256K in practice.\n\n| Model | Weights Size | Speed | Context | Best Pick | Best Used For | Honest Take |\n|---|---:|---|---|---|---|---|\n| **1) General Purpose & All-Rounders** |||||||\n| **Qwen3.5-397B-A17B**<br>UD-IQ1_M • Recommended<br>Qwen • Apache 2.0<br>LiveCodeBench 83.6 | 106.82 GB | **Medium**<br>397B total / 17B active MoE. | 262K<br>Native 262K context. | Best Overall / General Assistant | general assistant<br>hardest reasoning<br>research<br>complex agents | Best overall. Strongest all-rounder on 128GB for reasoning, research, and agentic work. |\n| **Mistral Large 2411**<br>Q4_K_M • Recommended<br>Mistral AI • MRL (research/non-commercial)<br>MMLU 84.0 • HumanEval 90.0<br>Multilingual SOTA • Fn calling native | 73.22 GB | **Medium**<br>Dense 123B at 4-bit. Heavier but still fast. | 128K<br>Best-in-class European multilingual. | Best Writing / Multilingual | creative writing<br>multilingual tasks<br>function calling<br>long-form prose | Excels on writing and multilingual tasks with strong function calling. Great for creative and business work. |\n| **2) Coding / Agent / Tool-Use Kings** |||||||\n| **MiniMax-M2.7**<br>UD-IQ2_XXS • Recommended<br>MiniMax • Apache 2.0<br>SWE-Bench Pro 56.2 • GPQA-D 77.7<br>SWE-Mult 76.5 | 65.38 GB | **Fast**<br>229B total / 10B active MoE. Low-latency agent loops. | 200K<br>Long enough for tool-call traces and agent loops. | Agent Loops | tool calling<br>multi-step coding<br>autonomous tasks | Strong purpose-built agent model. Excellent for tool use and autonomous workflows on 128GB. |\n| **GLM-4.5-Air**<br>Q6_K • Recommended<br>ZhipuAI • MIT<br>SWE-Bench Verified 64.2 • MMLU-Pro 79.1<br>IFEval strong | 99.01 GB | **Medium**<br>106B total / 12B active MoE. Great speed-quality balance. | 128K<br>Purpose-built for ARC, agent, and repo loops. | Coding | SWE tasks<br>agent tool loops<br>repo diffs | Excellent coding/agent model with a strong balance of reasoning, repo work, and tool use. |\n| **3) Math & Competition Reasoning** |||||||\n| **Qwen3-235B-A22B-Thinking-2507**<br>UD-Q2_K_XL • Recommended<br>Qwen • Apache 2.0<br>GPQA-D 81.1 • AIME'25 92.3<br>MMLU-Pro 84 • SWE-V 39 | 88.77 GB | **Medium**<br>235B total / 22B active MoE. Balanced reasoning, language. | 256K<br>Room for long reasoning traces, tricky math, and code windows. | Best Math & Reasoning Pick | competition math<br>structured solving<br>analysis<br>deep logic | Elite reasoning model for math and structured problem solving. Not the best everyday general chat model. |\n| **gpt-oss-120b**<br>Q8_0 • Recommended<br>OpenAI • Apache 2.0<br>MMLU-Pro 90.0 • AIME'25 97.9 (tool-assisted)<br>SWE-Bench Verified 62.4 | 63.39 GB | **Fast**<br>MXFP4-native weights, Q8_0. Is effectively full precision at 63 GB. | 128K<br>Solid long-context for reasoning; efficient on unified memory. | Math & Efficiency Veteran | math olympiad<br>hard reasoning<br>general assistant<br>code | Excellent older model (Aug 2025). MXFP4-native means Q8_0 is full precision. Still extremely strong on math/olympiad tasks and efficient on unified memory. |\n| **4) Vision & Multimodal** |||||||\n| **Qwen3-VL-235B-A22B-Thinking**<br>UD-IQ3_XXS • Recommended<br>Qwen • Apache 2.0<br>Vision Arena 2358<br>DocVQA high • multimodal reasoning strong | 94.73 GB | **Medium**<br>235B total / 22B active MoE. Vision agent overhead on long images. | 128K<br>Multimodal: image, text, native vision support via llama.cpp. | Best Vision Thinker | image understanding<br>vision reasoning<br>charts & docs<br>OCR & layout | Same reasoning core as Qwen3-235B-Thinking plus vision. Great for docs, diagrams, charts, and technical reports. |\n| **5) Long-Context / Research / Fast Thinkers** |||||||\n| **Llama-4-Scout 17Bx16E**<br>Q6_K • Recommended<br>Meta • Llama Community License<br>Context 10M • MMLU-Pro 74.3<br>GPQA-D 57.2 • Multimodal native | 88.43 GB | **Fast**<br>109B total / 17B active MoE. | 10M<br>Native 10M context window; best for huge codebases, corpora, and archives. | Best Long-Context Research Pick | massive documents<br>multimodal ingest<br>research corpora<br>long-context QA | Unmatched for huge-context work. Best when you truly need 10M context; weaker than top picks on raw reasoning. |\n| **Qwen3-Next-80B-A3B-Thinking**<br>Q6_K • Recommended<br>Qwen • Apache 2.0<br>MMLU-Pro 82.8 • GPQA-D 77.2<br>AIME'25 87.8 • 3B active | 65.79 GB | **Very fast**<br>80B total / 3B active MoE. Hybrid attention keeps latency low on long context. | 256K<br>Hybrid attention keeps latency low on long context. | Best Fast Thinker | fast reasoning<br>interactive math<br>long-context loops<br>agent planning | Best reasoning per-second on the sheet. Pick it for fast, responsive thinking and interactive use, not deepest reasoning. |\n\n## Bottom Line\n\n128GB advice: Model choice is highly use-case dependent. Qwen3.5-397B-A17B is the strongest all-rounder. Pick MiniMax-M2.7 or GLM-4.5-Air for agent/coding work, gpt-oss-120b for math/efficiency, and the specialists for vision or 10M+ context. There is no single \"best\" model - match it to your workflow.\n\n@qkisokay"
        }
      ],
      "usage": {
        "api_equivalent_cost_usd": 0.195431,
        "basis": "api_equivalent",
        "cached_input_price_per_million": 0.5,
        "cached_input_tokens": 2432,
        "completed_at": "2026-04-28T13:41:07.736791Z",
        "currency": "USD",
        "input_price_per_million": 5.0,
        "input_tokens": 27923,
        "metered_objects": [],
        "output_price_per_million": 30.0,
        "output_tokens": 1820,
        "reasoning_tokens": 0,
        "started_at": "2026-04-28T13:40:28.519326Z",
        "thinking_seconds": null,
        "total_tokens": 29743,
        "wall_seconds": 39.217465
      }
    },
    {
      "caller": "textifier_codex_gpt_55",
      "case_id": "R-IMG-INFOGRAPHIC-01",
      "expected_output_format": "markdown",
      "expected_status": "converted",
      "expected_suggested_paths": [
        "hermes-agent.md"
      ],
      "expected_textification_intent": "Extract the chalkboard-style Hermes Agent infographic into structured Markdown with commands, section labels, provider lists, and gateway labels.",
      "fixture_metadata": {
        "mime_type": "image/jpeg",
        "name": "r-img-infographic-01.jpg",
        "path": "/Users/zeph/github/tzaffi/curio/tmp/textify-smoke/20260428-132551-09c3fa3c8f75/cases/R-IMG-INFOGRAPHIC-01/fixtures/r-img-infographic-01.jpg",
        "sha256": "0405a18638feeee817b4e4a3a71c39cfb2426fbb936f981bd8cd762768d7ebe3",
        "source_language_hint": null
      },
      "ground_truth_text": "Hermes Agent\nThe CLI AI Agent by Nous Research\nFrom zero to chat in 3 steps\ncurl -fsSL .../install.sh | bash\nPick Provider\nChat\nCore Tools\nAny model. No lock-in.\nMessaging gateways",
      "model_importance": 10,
      "output_format": [
        "markdown"
      ],
      "participates_in_model_ranking": true,
      "preservation_requirements": [
        "Hermes Agent",
        "curl -fsSL",
        "Pick Provider",
        "Core Tools",
        "Any model. No lock-in.",
        "Messaging gateways"
      ],
      "rendered_textified_text": "# Hermes Agent\n\nThe CLI AI Agent by Nous Research\n\nLearns. Remembers. Works everywhere.\n\n## From zero to chat in 3 steps\n\n1. `curl -fsSL .../install.sh | bash`\n2. Pick Provider  \n   `hermes model`\n3. Chat  \n   `hermes`  \n   or `hermes --tui`\n\n## Core Tools\n\n- Terminal\n- Files\n- Web\n- Browser\n- Vision\n- Image Gen\n- TTS\n- MCP\n\n## What makes it an agent\n\n- Skills\n- Memory\n- Context Files\n- Cron\n- Delegation\n- Code Execution\n- Hooks\n- Batch\n- RL Training\n- Provider Routing\n\n## Any model. No lock-in.\n\n- Nous Portal\n- Anthropic\n- OpenRouter\n- OpenAI Codex\n- Qwen\n- Google Gemini\n- xAI Grok\n- GitHub Copilot\n- Kimi\n- DeepSeek\n- Ollama\n- Hugging Face\n- NVIDIA NIM\n- Bedrock\n- MiniMax\n\n+ many more\n\nMin context 64K tokens\n\n`hermes model`\n\n## Messaging gateways\n\n- Telegram\n- Slack\n- Signal\n- Email\n- Discord\n- WhatsApp\n- Matrix\n- SMS\n- Home Assistant\n\n+more\n\n`hermes gateway setup`\n\n## Sandbox when you want\n\nlocal · docker · ssh · modal · daytona · singularity\n\n## Automate in plain English\n\n\"Every morning at 9am, check Hacker News for AI news and send me a summary on Telegram.\"\n\n→ Hermes sets up the cron job automatically.",
      "response_path": "runs/R-IMG-INFOGRAPHIC-01/textifier_codex_gpt_55/response.json",
      "response_warnings": [
        "Some small chalk-style command text and labels are low-resolution; OCR may be approximate."
      ],
      "status": "converted",
      "suggested_files": [
        {
          "output_format": "markdown",
          "suggested_path": "hermes-agent.md",
          "text": "# Hermes Agent\n\nThe CLI AI Agent by Nous Research\n\nLearns. Remembers. Works everywhere.\n\n## From zero to chat in 3 steps\n\n1. `curl -fsSL .../install.sh | bash`\n2. Pick Provider  \n   `hermes model`\n3. Chat  \n   `hermes`  \n   or `hermes --tui`\n\n## Core Tools\n\n- Terminal\n- Files\n- Web\n- Browser\n- Vision\n- Image Gen\n- TTS\n- MCP\n\n## What makes it an agent\n\n- Skills\n- Memory\n- Context Files\n- Cron\n- Delegation\n- Code Execution\n- Hooks\n- Batch\n- RL Training\n- Provider Routing\n\n## Any model. No lock-in.\n\n- Nous Portal\n- Anthropic\n- OpenRouter\n- OpenAI Codex\n- Qwen\n- Google Gemini\n- xAI Grok\n- GitHub Copilot\n- Kimi\n- DeepSeek\n- Ollama\n- Hugging Face\n- NVIDIA NIM\n- Bedrock\n- MiniMax\n\n+ many more\n\nMin context 64K tokens\n\n`hermes model`\n\n## Messaging gateways\n\n- Telegram\n- Slack\n- Signal\n- Email\n- Discord\n- WhatsApp\n- Matrix\n- SMS\n- Home Assistant\n\n+more\n\n`hermes gateway setup`\n\n## Sandbox when you want\n\nlocal · docker · ssh · modal · daytona · singularity\n\n## Automate in plain English\n\n\"Every morning at 9am, check Hacker News for AI news and send me a summary on Telegram.\"\n\n→ Hermes sets up the cron job automatically."
        }
      ],
      "usage": {
        "api_equivalent_cost_usd": 0.153296,
        "basis": "api_equivalent",
        "cached_input_price_per_million": 0.5,
        "cached_input_tokens": 2432,
        "completed_at": "2026-04-28T13:41:22.107208Z",
        "currency": "USD",
        "input_price_per_million": 5.0,
        "input_tokens": 27512,
        "metered_objects": [],
        "output_price_per_million": 30.0,
        "output_tokens": 484,
        "reasoning_tokens": 0,
        "started_at": "2026-04-28T13:41:07.751072Z",
        "thinking_seconds": null,
        "total_tokens": 27996,
        "wall_seconds": 14.356136
      }
    },
    {
      "caller": "textifier_codex_gpt_55",
      "case_id": "R-IMG-PAPER-PAGE-01",
      "expected_output_format": "markdown",
      "expected_status": "converted",
      "expected_suggested_paths": [
        "openclaw-rl.md"
      ],
      "expected_textification_intent": "Extract the academic paper page with title, authors, GitHub link, abstract, figure caption, and diagram labels into Markdown.",
      "fixture_metadata": {
        "mime_type": "image/png",
        "name": "r-img-paper-page-01.png",
        "path": "/Users/zeph/github/tzaffi/curio/tmp/textify-smoke/20260428-132551-09c3fa3c8f75/cases/R-IMG-PAPER-PAGE-01/fixtures/r-img-paper-page-01.png",
        "sha256": "3989e8b2dbb1992196f6c3302667b3a98ff911c5c717773a101fd896e37e87b8",
        "source_language_hint": null
      },
      "ground_truth_text": "OpenClaw-RL: Train Any Agent Simply by Talking\nYinjie Wang\nhttps://github.com/Gen-Verse/OpenClaw-RL\nEvery agent interaction generates a next-state signal\nFigure 1 OpenClaw-RL infrastructure overview",
      "model_importance": 9,
      "output_format": [
        "markdown"
      ],
      "participates_in_model_ranking": true,
      "preservation_requirements": [
        "OpenClaw-RL",
        "Train Any Agent Simply by Talking",
        "Gen-Verse/OpenClaw-RL",
        "next-state signal",
        "Figure 1"
      ],
      "rendered_textified_text": "# OpenClaw-RL: Train Any Agent Simply by Talking\n\nYinjie Wang*, Xuyang Chen*, Xiaolong Jin*, Mengdi Wang†, Ling Yang†\n\nhttps://github.com/Gen-Verse/OpenClaw-RL\n\narXiv: 2603.10165v1 [cs.CL] 10 Mar 2026\n\nEvery agent interaction generates a **next-state signal**, namely the user reply, tool output, terminal or GUI state change that follows each action, yet no existing agentic RL system recovers it as a live, online learning source. We present **OpenClaw-RL**, a framework built on a simple observation: next-state signals are universal, and policy can learn from all of them simultaneously. Personal conversations, terminal executions, GUI interactions, SWE tasks, and tool-call traces are not separate training problems. They are all interactions that can be used to train the same policy in the same loop. Next-state signals encode two forms of information: **evaluative signals**, which indicate how well the action performed and are extracted as scalar rewards via a PRM judge; and **directive signals**, which indicate how the action should have been different and are recovered through **Hindsight-Guided On-Policy Distillation (OPD)**. We extract textual hints from the next state, construct an enhanced teacher context, and provide token-level directional advantage supervision that is richer than any scalar reward. Due to the asynchronous design, the model serves live requests, the PRM judges ongoing interactions, and the trainer updates the policy at the same time, with zero coordination overhead between them. Applied to personal agents, OpenClaw-RL enables an agent to improve simply by being used, recovering conversational signals from user re-queries, corrections, and explicit feedback. Applied to general agents, the same infrastructure supports scalable RL across terminal, GUI, SWE, and tool-call settings, where we additionally demonstrate the utility of process rewards.\n\n## Figure 1\n\n```text\nPersonal Agents\n  OpenClaw\n\nGeneral Agents\n  Terminal Agent\n  GUI Agent\n  SWE Agent\n  Tool-call Agent\n\nOpenClaw-RL\n\nEnvironment Servers\n  Personal Devices\n  - Confidential API Keys\n\n  Cloud Services\n  - Large Scale Environments\n\nRL Server\n  - Slime Async Framework\n  - Zero Serving Interruption\n  - Graceful Weight Update\n\nTraining Engine (Megatron)\nPolicy Server (SGLang)\nPRM Server (SGLang/API)\n\ndata\n```\n\n**Figure 1 | OpenClaw-RL infrastructure overview.** Interaction streams come from two agent types: **Personal Agents** (conversational, single-user), hosted on personal devices, and **General Agents** (terminal, GUI, SWE, and tool-call agents), hosted on cloud services. The collected samples flow into our RL server built on the asynchronous slime framework, which consists of four decoupled components: (1) the environment server, (2) PRM / Judge for reward computation, (3) Megatron for policy training, and (4) SGLang for policy serving. These components support graceful weight updates and enable training with any agentic framework. The environment for personal agents is simply the users' personal devices, which connect to the RL server over HTTP with confidential API keys. The environments for general agents are hosted on cloud services to enable scalable parallelization.\n\n---\n\n*Equal contribution; †Corresponding authors; Main contact: yangling0818@163.com",
      "response_path": "runs/R-IMG-PAPER-PAGE-01/textifier_codex_gpt_55/response.json",
      "response_warnings": [
        "Some small diagram labels and author affiliation symbols are low-resolution; OCR may contain minor uncertainty.",
        "Logo text and decorative marks were not fully transcribed except where readable."
      ],
      "status": "converted",
      "suggested_files": [
        {
          "output_format": "markdown",
          "suggested_path": "openclaw-rl.md",
          "text": "# OpenClaw-RL: Train Any Agent Simply by Talking\n\nYinjie Wang*, Xuyang Chen*, Xiaolong Jin*, Mengdi Wang†, Ling Yang†\n\nhttps://github.com/Gen-Verse/OpenClaw-RL\n\narXiv: 2603.10165v1 [cs.CL] 10 Mar 2026\n\nEvery agent interaction generates a **next-state signal**, namely the user reply, tool output, terminal or GUI state change that follows each action, yet no existing agentic RL system recovers it as a live, online learning source. We present **OpenClaw-RL**, a framework built on a simple observation: next-state signals are universal, and policy can learn from all of them simultaneously. Personal conversations, terminal executions, GUI interactions, SWE tasks, and tool-call traces are not separate training problems. They are all interactions that can be used to train the same policy in the same loop. Next-state signals encode two forms of information: **evaluative signals**, which indicate how well the action performed and are extracted as scalar rewards via a PRM judge; and **directive signals**, which indicate how the action should have been different and are recovered through **Hindsight-Guided On-Policy Distillation (OPD)**. We extract textual hints from the next state, construct an enhanced teacher context, and provide token-level directional advantage supervision that is richer than any scalar reward. Due to the asynchronous design, the model serves live requests, the PRM judges ongoing interactions, and the trainer updates the policy at the same time, with zero coordination overhead between them. Applied to personal agents, OpenClaw-RL enables an agent to improve simply by being used, recovering conversational signals from user re-queries, corrections, and explicit feedback. Applied to general agents, the same infrastructure supports scalable RL across terminal, GUI, SWE, and tool-call settings, where we additionally demonstrate the utility of process rewards.\n\n## Figure 1\n\n```text\nPersonal Agents\n  OpenClaw\n\nGeneral Agents\n  Terminal Agent\n  GUI Agent\n  SWE Agent\n  Tool-call Agent\n\nOpenClaw-RL\n\nEnvironment Servers\n  Personal Devices\n  - Confidential API Keys\n\n  Cloud Services\n  - Large Scale Environments\n\nRL Server\n  - Slime Async Framework\n  - Zero Serving Interruption\n  - Graceful Weight Update\n\nTraining Engine (Megatron)\nPolicy Server (SGLang)\nPRM Server (SGLang/API)\n\ndata\n```\n\n**Figure 1 | OpenClaw-RL infrastructure overview.** Interaction streams come from two agent types: **Personal Agents** (conversational, single-user), hosted on personal devices, and **General Agents** (terminal, GUI, SWE, and tool-call agents), hosted on cloud services. The collected samples flow into our RL server built on the asynchronous slime framework, which consists of four decoupled components: (1) the environment server, (2) PRM / Judge for reward computation, (3) Megatron for policy training, and (4) SGLang for policy serving. These components support graceful weight updates and enable training with any agentic framework. The environment for personal agents is simply the users' personal devices, which connect to the RL server over HTTP with confidential API keys. The environments for general agents are hosted on cloud services to enable scalable parallelization.\n\n---\n\n*Equal contribution; †Corresponding authors; Main contact: yangling0818@163.com"
        }
      ],
      "usage": {
        "api_equivalent_cost_usd": 0.174935,
        "basis": "api_equivalent",
        "cached_input_price_per_million": 0.5,
        "cached_input_tokens": 24960,
        "completed_at": "2026-04-28T13:41:47.699583Z",
        "currency": "USD",
        "input_price_per_million": 5.0,
        "input_tokens": 27085,
        "metered_objects": [],
        "output_price_per_million": 30.0,
        "output_tokens": 901,
        "reasoning_tokens": 39,
        "started_at": "2026-04-28T13:41:22.117423Z",
        "thinking_seconds": null,
        "total_tokens": 27986,
        "wall_seconds": 25.58216
      }
    },
    {
      "caller": "textifier_codex_gpt_55",
      "case_id": "R-IMG-CHARTS-01",
      "expected_output_format": "markdown",
      "expected_status": "converted",
      "expected_suggested_paths": [
        "agent-benchmarks.md"
      ],
      "expected_textification_intent": "Extract both benchmark bar charts into Markdown tables with system names and percentages.",
      "fixture_metadata": {
        "mime_type": "image/jpeg",
        "name": "r-img-charts-01.jpg",
        "path": "/Users/zeph/github/tzaffi/curio/tmp/textify-smoke/20260428-132551-09c3fa3c8f75/cases/R-IMG-CHARTS-01/fixtures/r-img-charts-01.jpg",
        "sha256": "6963044d99e19d448472a7e223c36cb85494db523b99b7547cfe6c9d13d0b778",
        "source_language_hint": null
      },
      "ground_truth_text": "SpreadsheetBench\nAutoAgent 96.5%\nTetra-Beta-2 94.2%\nTerminalBench (GPT-5)\nAutoAgent 55.1%\nCodex CLI 49.6%",
      "model_importance": 8,
      "output_format": [
        "markdown"
      ],
      "participates_in_model_ranking": true,
      "preservation_requirements": [
        "SpreadsheetBench",
        "TerminalBench",
        "AutoAgent 96.5%",
        "AutoAgent 55.1%",
        "Codex CLI 49.6%"
      ],
      "rendered_textified_text": "# Agent Benchmarks\n\n## SpreadSheetBench\n\n| System | Score |\n|---|---:|\n| AutoAgent | 96.5% |\n| Tetra-Beta-2 | 94.2% |\n| Noble Agent | 91.0% |\n| Qingqiu Agent | 89.2% |\n| Shortcut.ai | 86.0% |\n\n## TerminalBench (GPT-5)\n\n| System | Score |\n|---|---:|\n| AutoAgent | 55.1% |\n| Codex CLI | 49.6% |\n| OpenHands | 43.8% |\n| Terminus 2 | 35.2% |\n| Mini-SWE-Agent | 33.9% |\n",
      "response_path": "runs/R-IMG-CHARTS-01/textifier_codex_gpt_55/response.json",
      "response_warnings": [
        "Some small axis labels and tick marks are low resolution; main chart titles, system names, and percentage labels are readable."
      ],
      "status": "converted",
      "suggested_files": [
        {
          "output_format": "markdown",
          "suggested_path": "agent-benchmarks.md",
          "text": "# Agent Benchmarks\n\n## SpreadSheetBench\n\n| System | Score |\n|---|---:|\n| AutoAgent | 96.5% |\n| Tetra-Beta-2 | 94.2% |\n| Noble Agent | 91.0% |\n| Qingqiu Agent | 89.2% |\n| Shortcut.ai | 86.0% |\n\n## TerminalBench (GPT-5)\n\n| System | Score |\n|---|---:|\n| AutoAgent | 55.1% |\n| Codex CLI | 49.6% |\n| OpenHands | 43.8% |\n| Terminus 2 | 35.2% |\n| Mini-SWE-Agent | 33.9% |\n"
        }
      ],
      "usage": {
        "api_equivalent_cost_usd": 0.145381,
        "basis": "api_equivalent",
        "cached_input_price_per_million": 0.5,
        "cached_input_tokens": 2432,
        "completed_at": "2026-04-28T13:41:58.235636Z",
        "currency": "USD",
        "input_price_per_million": 5.0,
        "input_tokens": 27117,
        "metered_objects": [],
        "output_price_per_million": 30.0,
        "output_tokens": 286,
        "reasoning_tokens": 0,
        "started_at": "2026-04-28T13:41:47.712850Z",
        "thinking_seconds": null,
        "total_tokens": 27403,
        "wall_seconds": 10.522786
      }
    },
    {
      "caller": "textifier_codex_gpt_55",
      "case_id": "R-IMG-TERMINAL-01",
      "expected_output_format": "txt",
      "expected_status": "converted",
      "expected_suggested_paths": [
        "claude-code-listing.log"
      ],
      "expected_textification_intent": "Transcribe the terminal session as a log, preserving command lines, permissions columns, file sizes, timestamps, and filenames.",
      "fixture_metadata": {
        "mime_type": "image/png",
        "name": "r-img-terminal-01.png",
        "path": "/Users/zeph/github/tzaffi/curio/tmp/textify-smoke/20260428-132551-09c3fa3c8f75/cases/R-IMG-TERMINAL-01/fixtures/r-img-terminal-01.png",
        "sha256": "e1c5b1945a3db39ed228e143b3202da12b86f936f7c55f1407e9aa5fb617b7fa",
        "source_language_hint": null
      },
      "ground_truth_text": "ls -alht cli.js.map\nls -alht src\ntotal 2304\nmain.tsx\ncommands\nQueryEngine.ts\ncontext.ts",
      "model_importance": 8,
      "output_format": [
        "txt"
      ],
      "participates_in_model_ranking": true,
      "preservation_requirements": [
        "ls -alht",
        "total 2304",
        "main.tsx",
        "commands",
        "QueryEngine.ts",
        "context.ts"
      ],
      "rendered_textified_text": "jshou@dev claude-code % ls -alht cli.js.map\n-rw-r--r--   1 shou  staff    57M Mar 31 01:16 cli.js.map\njshou@dev claude-code % ls -alht src\ntotal 2304\ndrwxr-xr-x    8 shou  staff   256B Mar 31 01:17 entrypoints\n-rw-r--r--    1 shou  staff   785K Mar 31 01:17 main.tsx\ndrwxr-xr-x   55 shou  staff   1.7K Mar 31 01:17 .\ndrwxr-xr-x   10 shou  staff   320B Mar 31 01:17 cli\ndrwxr-xr-x  103 shou  staff   3.2K Mar 31 01:17 commands\ndrwxr-xr-x  331 shou  staff    10K Mar 31 01:17 utils\ndrwxr-xr-x  146 shou  staff   4.6K Mar 31 01:17 components\n-rw-r--r--    1 shou  staff    46K Mar 31 01:17 QueryEngine.ts\n-rw-r--r--    1 shou  staff    20K Mar 31 01:17 setup.ts\ndrwxr-xr-x    5 shou  staff   160B Mar 31 01:17 server\ndrwxr-xr-x   13 shou  staff   416B Mar 31 01:17 migrations\ndrwxr-xr-x   16 shou  staff   512B Mar 31 01:17 keybindings\ndrwxr-xr-x    6 shou  staff   192B Mar 31 01:17 skills\ndrwxr-xr-x    4 shou  staff   128B Mar 31 01:17 plugins\n-rw-r--r--    1 shou  staff    22K Mar 31 01:17 dialogLaunchers.tsx\ndrwxr-xr-x    5 shou  staff   160B Mar 31 01:17 screens\ndrwxr-xr-x   87 shou  staff   2.7K Mar 31 01:17 hooks\n-rw-r--r--    1 shou  staff    56K Mar 31 01:17 interactiveHelpers.ts\n-rw-r--r--   38 shou  staff   1.2K Mar 31 01:17 services\n-rw-r--r--    1 shou  staff   3.4K Mar 31 01:17 replLauncher.ts\n-rw-r--r--    1 shou  staff   617B Mar 31 01:17 costHook.ts\ndrwxr-xr-x    3 shou  staff    96B Mar 31 01:17 moregit\ndrwxr-xr-x    3 shou  staff    96B Mar 31 01:17 assistant\ndrwxr-xr-x    6 shou  staff   192B Mar 31 01:17 remote\ndrwxr-xr-x    7 shou  staff   224B Mar 31 01:17 vim\ndrwxr-xr-x    8 shou  staff   256B Mar 31 01:17 buddy\ndrwxr-xr-x   33 shou  staff   1.0K Mar 31 01:17 bridge\ndrwxr-xr-x    8 shou  staff   256B Mar 31 01:17 state\ndrwxr-xr-x   11 shou  staff   352B Mar 31 01:17 context\ndrwxr-xr-x    4 shou  staff   128B Mar 31 01:17 upstreamProxy\ndrwxr-xr-x   23 shou  staff   736B Mar 31 01:17 constants\ndrwxr-xr-x   10 shou  staff   320B Mar 31 01:17 types\n-rw-r--r--    1 shou  staff   3.1K Mar 31 01:17 Task.ts\ndrwxr-xr-x   10 shou  staff   320B Mar 31 01:17 memdir\n-rw-r--r--    1 shou  staff    25K Mar 31 01:17 commands.ts\n-rw-r--r--    5 shou  staff   160B Mar 31 01:17 native-ts\n-rw-r--r--    1 shou  staff    14K Mar 31 01:17 history.ts\n-rw-r--r--    1 shou  staff   2.3K Mar 31 01:17 projectOnboardingState.ts\ndrwxr-xr-x    3 shou  staff    96B Mar 31 01:17 outputStyles\n-rw-r--r--    1 shou  staff    67K Mar 31 01:17 query.ts\n-rw-r--r--    6 shou  staff   192B Mar 31 01:17 query\ndrwxr-xr-x   11 shou  staff   352B Mar 31 01:17 tasks\n-rw-r--r--    1 shou  staff    17K Mar 31 01:17 tools.ts\ndrwxr-xr-x   45 shou  staff   1.4K Mar 31 01:17 tools\ndrwxr-xr-x    3 shou  staff    96B Mar 31 01:17 voice\n-rw-r--r--    1 shou  staff   1.3K Mar 31 01:17 tasks.ts\n-rw-r--r--    1 shou  staff    10K Mar 31 01:17 cost-tracker.ts\ndrwxr-xr-x    3 shou  staff    96B Mar 31 01:17 coordinator\n-rw-r--r--    1 shou  staff   6.3K Mar 31 01:17 context.ts\n-rw-r--r--    1 shou  staff   3.8K Mar 31 01:17 ink.ts\ndrwxr-xr-x   50 shou  staff   1.6K Mar 31 01:17 ink\n-rw-r--r--    1 shou  staff    29K Mar 31 01:17 Tool.ts\ndrwxr-xr-x    3 shou  staff    96B Mar 31 01:17 schemas\ndrwxr-xr-x    3 shou  staff    96B Mar 31 01:17 bootstrap\ndrwxr-xr-x   12 shou  staff   384B Mar 31 01:17 ..",
      "response_path": "runs/R-IMG-TERMINAL-01/textifier_codex_gpt_55/response.json",
      "response_warnings": [
        "Terminal screenshot is low resolution; some prompt characters, permission/type fields, and file type columns may be uncertain.",
        "Bottom of screenshot is slightly cropped after the final parent directory entry."
      ],
      "status": "converted",
      "suggested_files": [
        {
          "output_format": "txt",
          "suggested_path": "claude-code-listing.log",
          "text": "jshou@dev claude-code % ls -alht cli.js.map\n-rw-r--r--   1 shou  staff    57M Mar 31 01:16 cli.js.map\njshou@dev claude-code % ls -alht src\ntotal 2304\ndrwxr-xr-x    8 shou  staff   256B Mar 31 01:17 entrypoints\n-rw-r--r--    1 shou  staff   785K Mar 31 01:17 main.tsx\ndrwxr-xr-x   55 shou  staff   1.7K Mar 31 01:17 .\ndrwxr-xr-x   10 shou  staff   320B Mar 31 01:17 cli\ndrwxr-xr-x  103 shou  staff   3.2K Mar 31 01:17 commands\ndrwxr-xr-x  331 shou  staff    10K Mar 31 01:17 utils\ndrwxr-xr-x  146 shou  staff   4.6K Mar 31 01:17 components\n-rw-r--r--    1 shou  staff    46K Mar 31 01:17 QueryEngine.ts\n-rw-r--r--    1 shou  staff    20K Mar 31 01:17 setup.ts\ndrwxr-xr-x    5 shou  staff   160B Mar 31 01:17 server\ndrwxr-xr-x   13 shou  staff   416B Mar 31 01:17 migrations\ndrwxr-xr-x   16 shou  staff   512B Mar 31 01:17 keybindings\ndrwxr-xr-x    6 shou  staff   192B Mar 31 01:17 skills\ndrwxr-xr-x    4 shou  staff   128B Mar 31 01:17 plugins\n-rw-r--r--    1 shou  staff    22K Mar 31 01:17 dialogLaunchers.tsx\ndrwxr-xr-x    5 shou  staff   160B Mar 31 01:17 screens\ndrwxr-xr-x   87 shou  staff   2.7K Mar 31 01:17 hooks\n-rw-r--r--    1 shou  staff    56K Mar 31 01:17 interactiveHelpers.ts\n-rw-r--r--   38 shou  staff   1.2K Mar 31 01:17 services\n-rw-r--r--    1 shou  staff   3.4K Mar 31 01:17 replLauncher.ts\n-rw-r--r--    1 shou  staff   617B Mar 31 01:17 costHook.ts\ndrwxr-xr-x    3 shou  staff    96B Mar 31 01:17 moregit\ndrwxr-xr-x    3 shou  staff    96B Mar 31 01:17 assistant\ndrwxr-xr-x    6 shou  staff   192B Mar 31 01:17 remote\ndrwxr-xr-x    7 shou  staff   224B Mar 31 01:17 vim\ndrwxr-xr-x    8 shou  staff   256B Mar 31 01:17 buddy\ndrwxr-xr-x   33 shou  staff   1.0K Mar 31 01:17 bridge\ndrwxr-xr-x    8 shou  staff   256B Mar 31 01:17 state\ndrwxr-xr-x   11 shou  staff   352B Mar 31 01:17 context\ndrwxr-xr-x    4 shou  staff   128B Mar 31 01:17 upstreamProxy\ndrwxr-xr-x   23 shou  staff   736B Mar 31 01:17 constants\ndrwxr-xr-x   10 shou  staff   320B Mar 31 01:17 types\n-rw-r--r--    1 shou  staff   3.1K Mar 31 01:17 Task.ts\ndrwxr-xr-x   10 shou  staff   320B Mar 31 01:17 memdir\n-rw-r--r--    1 shou  staff    25K Mar 31 01:17 commands.ts\n-rw-r--r--    5 shou  staff   160B Mar 31 01:17 native-ts\n-rw-r--r--    1 shou  staff    14K Mar 31 01:17 history.ts\n-rw-r--r--    1 shou  staff   2.3K Mar 31 01:17 projectOnboardingState.ts\ndrwxr-xr-x    3 shou  staff    96B Mar 31 01:17 outputStyles\n-rw-r--r--    1 shou  staff    67K Mar 31 01:17 query.ts\n-rw-r--r--    6 shou  staff   192B Mar 31 01:17 query\ndrwxr-xr-x   11 shou  staff   352B Mar 31 01:17 tasks\n-rw-r--r--    1 shou  staff    17K Mar 31 01:17 tools.ts\ndrwxr-xr-x   45 shou  staff   1.4K Mar 31 01:17 tools\ndrwxr-xr-x    3 shou  staff    96B Mar 31 01:17 voice\n-rw-r--r--    1 shou  staff   1.3K Mar 31 01:17 tasks.ts\n-rw-r--r--    1 shou  staff    10K Mar 31 01:17 cost-tracker.ts\ndrwxr-xr-x    3 shou  staff    96B Mar 31 01:17 coordinator\n-rw-r--r--    1 shou  staff   6.3K Mar 31 01:17 context.ts\n-rw-r--r--    1 shou  staff   3.8K Mar 31 01:17 ink.ts\ndrwxr-xr-x   50 shou  staff   1.6K Mar 31 01:17 ink\n-rw-r--r--    1 shou  staff    29K Mar 31 01:17 Tool.ts\ndrwxr-xr-x    3 shou  staff    96B Mar 31 01:17 schemas\ndrwxr-xr-x    3 shou  staff    96B Mar 31 01:17 bootstrap\ndrwxr-xr-x   12 shou  staff   384B Mar 31 01:17 .."
        }
      ],
      "usage": {
        "api_equivalent_cost_usd": 0.345639,
        "basis": "api_equivalent",
        "cached_input_price_per_million": 0.5,
        "cached_input_tokens": 28928,
        "completed_at": "2026-04-28T13:42:40.110452Z",
        "currency": "USD",
        "input_price_per_million": 5.0,
        "input_tokens": 54685,
        "metered_objects": [],
        "output_price_per_million": 30.0,
        "output_tokens": 1925,
        "reasoning_tokens": 159,
        "started_at": "2026-04-28T13:41:58.248459Z",
        "thinking_seconds": null,
        "total_tokens": 56610,
        "wall_seconds": 41.861993
      }
    },
    {
      "caller": "textifier_codex_gpt_55",
      "case_id": "R-IMG-ASCII-DIAGRAM-01",
      "expected_output_format": "txt",
      "expected_status": "converted",
      "expected_suggested_paths": [
        "distributed-bloomberg-autoquant.txt"
      ],
      "expected_textification_intent": "Preserve the ASCII-style diagram layout and result box as plain text instead of summarizing it away.",
      "fixture_metadata": {
        "mime_type": "image/png",
        "name": "r-img-ascii-diagram-01.png",
        "path": "/Users/zeph/github/tzaffi/curio/tmp/textify-smoke/20260428-132551-09c3fa3c8f75/cases/R-IMG-ASCII-DIAGRAM-01/fixtures/r-img-ascii-diagram-01.png",
        "sha256": "353bc7c7e176f785ef3d09d0b8ae088c6f299c4e971010301ff2bd9d84f40c50",
        "source_language_hint": null
      },
      "ground_truth_text": "DISTRIBUTED BLOOMBERG\nAutoQuant\nAgent Macro Sector Alpha Risks\nDARWINIAN SELECTION\n4 factors · risk parity\nSharpe 1.32\n1,896 experiments in 36 hours",
      "model_importance": 8,
      "output_format": [
        "txt"
      ],
      "participates_in_model_ranking": true,
      "preservation_requirements": [
        "DISTRIBUTED BLOOMBERG",
        "AutoQuant",
        "DARWINIAN SELECTION",
        "Sharpe 1.32",
        "1,896 experiments"
      ],
      "rendered_textified_text": "┌────────────────────────────────────────────┐\n│        DISTRIBUTED BLOOMBERG               │\n│        AutoQuant                            │\n├────────────────────────────────────────────┤\n│                                            │\n│  ┌───────┐   ┌───────┐   ┌───────┐  × 135 │\n│  │Agent  │   │Agent  │   │Agent  │        │\n│  │Macro  │   │Macro  │   │Macro  │        │\n│  │Sector │   │Sector │   │Sector │        │\n│  │Alpha  │   │Alpha  │   │Alpha  │        │\n│  │Risk⚡ │   │Risk⚡ │   │Risk⚡ │        │\n│  └──┬────┘   └──┬────┘   └──┬────┘        │\n│     │           │           │             │\n│     └────► gossip │ gossip ◄────┘         │\n│          P2P      │                       │\n│          Network                          │\n│                                            │\n│ DARWINIAN SELECTION                       │\n│ ├── 30 mutations compete                  │\n│ ├── Win rates tracked                     │\n│ ├── Losers pruned, winners amplified      │\n│ └── Network converges on optimal          │\n│                                            │\n│ RESULT (discovered autonomously):         │\n│                                            │\n│ ┌───────────────────────────────┐          │\n│ │ 4 factors · risk parity       │          │\n│ │ Sharpe 1.32 · 3× return       │          │\n│ │ 5.5% max drawdown             │          │\n│ │ 1,896 experiments in 36 hours │          │\n│ └───────────────────────────────┘          │\n│                                            │\n│ 32,868 total commits across all domains:  │\n│ ML · Search · Skills · Finance · Network  │\n└────────────────────────────────────────────┘",
      "response_path": "runs/R-IMG-ASCII-DIAGRAM-01/textifier_codex_gpt_55/response.json",
      "response_warnings": [
        "ASCII diagram layout reconstructed from image; border spacing may not exactly match source pixels."
      ],
      "status": "converted",
      "suggested_files": [
        {
          "output_format": "txt",
          "suggested_path": "distributed-bloomberg-autoquant.txt",
          "text": "┌────────────────────────────────────────────┐\n│        DISTRIBUTED BLOOMBERG               │\n│        AutoQuant                            │\n├────────────────────────────────────────────┤\n│                                            │\n│  ┌───────┐   ┌───────┐   ┌───────┐  × 135 │\n│  │Agent  │   │Agent  │   │Agent  │        │\n│  │Macro  │   │Macro  │   │Macro  │        │\n│  │Sector │   │Sector │   │Sector │        │\n│  │Alpha  │   │Alpha  │   │Alpha  │        │\n│  │Risk⚡ │   │Risk⚡ │   │Risk⚡ │        │\n│  └──┬────┘   └──┬────┘   └──┬────┘        │\n│     │           │           │             │\n│     └────► gossip │ gossip ◄────┘         │\n│          P2P      │                       │\n│          Network                          │\n│                                            │\n│ DARWINIAN SELECTION                       │\n│ ├── 30 mutations compete                  │\n│ ├── Win rates tracked                     │\n│ ├── Losers pruned, winners amplified      │\n│ └── Network converges on optimal          │\n│                                            │\n│ RESULT (discovered autonomously):         │\n│                                            │\n│ ┌───────────────────────────────┐          │\n│ │ 4 factors · risk parity       │          │\n│ │ Sharpe 1.32 · 3× return       │          │\n│ │ 5.5% max drawdown             │          │\n│ │ 1,896 experiments in 36 hours │          │\n│ └───────────────────────────────┘          │\n│                                            │\n│ 32,868 total commits across all domains:  │\n│ ML · Search · Skills · Finance · Network  │\n└────────────────────────────────────────────┘"
        }
      ],
      "usage": {
        "api_equivalent_cost_usd": 0.157086,
        "basis": "api_equivalent",
        "cached_input_price_per_million": 0.5,
        "cached_input_tokens": 2432,
        "completed_at": "2026-04-28T13:42:56.404571Z",
        "currency": "USD",
        "input_price_per_million": 5.0,
        "input_tokens": 27622,
        "metered_objects": [],
        "output_price_per_million": 30.0,
        "output_tokens": 592,
        "reasoning_tokens": 0,
        "started_at": "2026-04-28T13:42:40.124326Z",
        "thinking_seconds": null,
        "total_tokens": 28214,
        "wall_seconds": 16.280245
      }
    },
    {
      "caller": "textifier_codex_gpt_55",
      "case_id": "R-IMG-COMPARISON-TABLE-01",
      "expected_output_format": "markdown",
      "expected_status": "converted",
      "expected_suggested_paths": [
        "agent-comparison.md"
      ],
      "expected_textification_intent": "Extract the OpenClaw/Hermes/Paperclip comparison as a Markdown table preserving row and column alignment.",
      "fixture_metadata": {
        "mime_type": "image/png",
        "name": "r-img-comparison-table-01.png",
        "path": "/Users/zeph/github/tzaffi/curio/tmp/textify-smoke/20260428-132551-09c3fa3c8f75/cases/R-IMG-COMPARISON-TABLE-01/fixtures/r-img-comparison-table-01.png",
        "sha256": "26f885c49a5b46c7827858bd74e79ca5938ac4e083bae507712c64180299e509",
        "source_language_hint": null
      },
      "ground_truth_text": "Head-to-Head\nDimension | OpenClaw | Hermes | Paperclip\nWhat it is\nGitHub stars\nSecurity\nInstall",
      "model_importance": 8,
      "output_format": [
        "markdown"
      ],
      "participates_in_model_ranking": true,
      "preservation_requirements": [
        "Head-to-Head",
        "Dimension",
        "OpenClaw",
        "Hermes",
        "Paperclip",
        "GitHub stars",
        "Install"
      ],
      "rendered_textified_text": "# Head-to-Head\n\n| Dimension | OpenClaw | Hermes | Paperclip |\n|---|---|---|---|\n| What it is | Personal AI agent | Self-improving AI agent | Multi-agent orchestrator |\n| GitHub stars | 351K | ~31K | 49K |\n| Philosophy | System to be orchestrated | Mind to be developed | Company to be managed |\n| Skills | Static (ClawHub, 5,700+) | Self-created, auto-improving (94 built-in) | N/A (manages other agents) |\n| Memory | Plugin-based | Multi-level, persistent, deepening | Org-level (budgets, goals) |\n| Models | API-dependent | Runs on open models (Qwen 3.5) | Model-agnostic orchestration |\n| Security | Concerning (Snyk findings) | Better defaults | Governance + audit trail |\n| Best for | Tinkerers, ecosystem power | Simplicity, self-improvement | Running 5-50 agents together |\n| Install | npm global | 11-minute installer | npx paperclipai onboard |",
      "response_path": "runs/R-IMG-COMPARISON-TABLE-01/textifier_codex_gpt_55/response.json",
      "response_warnings": [],
      "status": "converted",
      "suggested_files": [
        {
          "output_format": "markdown",
          "suggested_path": "agent-comparison.md",
          "text": "# Head-to-Head\n\n| Dimension | OpenClaw | Hermes | Paperclip |\n|---|---|---|---|\n| What it is | Personal AI agent | Self-improving AI agent | Multi-agent orchestrator |\n| GitHub stars | 351K | ~31K | 49K |\n| Philosophy | System to be orchestrated | Mind to be developed | Company to be managed |\n| Skills | Static (ClawHub, 5,700+) | Self-created, auto-improving (94 built-in) | N/A (manages other agents) |\n| Memory | Plugin-based | Multi-level, persistent, deepening | Org-level (budgets, goals) |\n| Models | API-dependent | Runs on open models (Qwen 3.5) | Model-agnostic orchestration |\n| Security | Concerning (Snyk findings) | Better defaults | Governance + audit trail |\n| Best for | Tinkerers, ecosystem power | Simplicity, self-improvement | Running 5-50 agents together |\n| Install | npm global | 11-minute installer | npx paperclipai onboard |"
        }
      ],
      "usage": {
        "api_equivalent_cost_usd": 0.148071,
        "basis": "api_equivalent",
        "cached_input_price_per_million": 0.5,
        "cached_input_tokens": 2432,
        "completed_at": "2026-04-28T13:43:08.244052Z",
        "currency": "USD",
        "input_price_per_million": 5.0,
        "input_tokens": 27337,
        "metered_objects": [],
        "output_price_per_million": 30.0,
        "output_tokens": 339,
        "reasoning_tokens": 0,
        "started_at": "2026-04-28T13:42:56.422489Z",
        "thinking_seconds": null,
        "total_tokens": 27676,
        "wall_seconds": 11.821563
      }
    },
    {
      "caller": "textifier_codex_gpt_55",
      "case_id": "R-IMG-NO-TEXT-REAL-01",
      "expected_output_format": "markdown",
      "expected_status": "no_text_found",
      "expected_suggested_paths": [],
      "expected_textification_intent": "Return no_text_found for a real photo with no readable text and do not invent a visual description.",
      "fixture_metadata": {
        "mime_type": "image/jpeg",
        "name": "r-img-no-text-real-01.jpg",
        "path": "/Users/zeph/github/tzaffi/curio/tmp/textify-smoke/20260428-132551-09c3fa3c8f75/cases/R-IMG-NO-TEXT-REAL-01/fixtures/r-img-no-text-real-01.jpg",
        "sha256": "80c99366dc83288925d6653b25e086ee894e8098469f7f785e6e1e984e761107",
        "source_language_hint": null
      },
      "ground_truth_text": "",
      "model_importance": 5,
      "output_format": [],
      "participates_in_model_ranking": true,
      "preservation_requirements": [
        "no_text_found",
        "no invented description"
      ],
      "rendered_textified_text": "",
      "response_path": "runs/R-IMG-NO-TEXT-REAL-01/textifier_codex_gpt_55/response.json",
      "response_warnings": [],
      "status": "no_text_found",
      "suggested_files": [],
      "usage": {
        "api_equivalent_cost_usd": 0.153825,
        "basis": "api_equivalent",
        "cached_input_price_per_million": 0.5,
        "cached_input_tokens": 24960,
        "completed_at": "2026-04-28T13:43:18.694311Z",
        "currency": "USD",
        "input_price_per_million": 5.0,
        "input_tokens": 27819,
        "metered_objects": [],
        "output_price_per_million": 30.0,
        "output_tokens": 75,
        "reasoning_tokens": 0,
        "started_at": "2026-04-28T13:43:08.320578Z",
        "thinking_seconds": null,
        "total_tokens": 27894,
        "wall_seconds": 10.373733
      }
    },
    {
      "caller": "textifier_codex_gpt_55",
      "case_id": "C-IMG-DIR-TREE-01",
      "expected_output_format": "mixed",
      "expected_status": "converted",
      "expected_suggested_paths": [
        "home/important/openclaw-rl.md",
        "home/important/agent-comparison.md",
        "home/trivial/claude-code-listing.log"
      ],
      "expected_textification_intent": "Split one composite screenshot into exactly three suggested files in the visible nested relative directory structure.",
      "fixture_metadata": {
        "mime_type": "image/png",
        "name": "c-img-dir-tree-01.png",
        "path": "/Users/zeph/github/tzaffi/curio/tmp/textify-smoke/20260428-132551-09c3fa3c8f75/cases/C-IMG-DIR-TREE-01/fixtures/c-img-dir-tree-01.png",
        "sha256": "0664c813d92eb3562bb8a6a990b9c05634f452a5b245233038aff43fafc42400",
        "source_language_hint": null
      },
      "ground_truth_text": "home/important/openclaw-rl.md\nOpenClaw-RL: Train Any Agent Simply by Talking\nhome/important/agent-comparison.md\nHead-to-Head\nhome/trivial/claude-code-listing.log\nls -alht src",
      "model_importance": 10,
      "output_format": [
        "markdown",
        "markdown",
        "log"
      ],
      "participates_in_model_ranking": true,
      "preservation_requirements": [
        "exactly three suggested files",
        "home/important/openclaw-rl.md",
        "home/important/agent-comparison.md",
        "home/trivial/claude-code-listing.log",
        "no cross-section bleed",
        "no extra generated files"
      ],
      "rendered_textified_text": "# OpenClaw-RL: Train Any Agent Simply by Talking\n\nYinjie Wang*, Xuyang Chen*, Xiaolong Jin*, Mengdi Wang*, Ling Yang*\n\nhttps://github.com/Gen-Verse/OpenClaw-RL\n\nEvery agent interaction generates a next-state signal, namely the user reply, tool output, terminal or GUI state change that follows each action, yet no existing agentic RL system recovers it as a live, online learning source. We present **OpenClaw-RL**, a framework built on a simple observation: next-state signals are universal, and policy can learn from all of them simultaneously. Personal conversations, terminal executions, GUI interactions, SWE tasks, and tool-call traces are not separate training problems. They are all interactions that can be used to train the same policy in the same loop. Next-state signals encode two forms of information: evaluative signals, which indicate how well the action performed and are extracted as scalar rewards via a PRM judge; and directive signals, which indicate how the action should have been different and are recovered through Hindsight-Guided On-Policy Distillation (OPD). We extract textual hints from the next state, construct an enhanced teacher context, and provide token-level directional advantage supervision that is richer than any scalar reward. Due to the asynchronous design, the model serves live requests, the PRM judges ongoing interactions, and the trainer updates the policy at the same time, with zero coordination overhead between them. Applied to personal agents, OpenClaw-RL enables an agent to improve simply by being used, recovering conversational signals from user re-queries, corrections, and explicit feedback. Applied to general agents, the same infrastructure supports scalable RL across terminal, GUI, SWE, and tool-call settings, where we additionally demonstrate the utility of process rewards.\n\nFigure 1 | **OpenClaw-RL infrastructure overview.** Interaction streams come from two agent types: Personal Agents (conversational, single-user), hosted on personal devices, and General Agents (terminal, GUI, SWE, and tool-call agents), hosted on cloud services. The collected samples flow into our RL server built on the asynchronous slime framework, which consists of four decoupled components: (1) the environment server, (2) PRM / Judge for reward computation, (3) Megatron for policy training, and (4) SGLang for policy serving. These components support graceful weight updates and enable training with any agentic framework. The environment for personal agents is simply the users' personal devices, which connect to the RL server over HTTP with confidential API keys. The environments for general agents are hosted on cloud services to enable scalable parallelization.\n\n# Head-to-Head\n\n| Dimension | OpenClaw | Hermes | Paperclip |\n|---|---|---|---|\n| What it is | Personal AI agent | Self-improving AI agent | Multi-agent orchestrator |\n| GitHub stars | 351K | ~31K | 49K |\n| Philosophy | System to be orchestrated | Mind to be developed | Company to be managed |\n| Skills | Static (ClawHub, 5,700+) | Self-created, auto-improving (94 built-in) | N/A (manages other agents) |\n| Memory | Plugin-based | Multi-level, persistent, deepening | Org-level (budgets, goals) |\n| Models | API-dependent | Runs on open models (Qwen 3.5) | Model-agnostic orchestration |\n| Security | Concerning (Snyk findings) | Better defaults | Governance + audit trail |\n| Best for | Tinkerers, ecosystem power | Simplicity, self-improvement | Running 5-50 agents together |\n| Install | npm global | 11-minute installer | npx paperclipai onboard |\n\nshou@dev claude-code % ls -alht cli.js.map\n-rw-r--r--  1 shou  staff    57M Mar 31 01:16 cli.js.map\nshou@dev claude-code % ls -alht src\ntotal 2304\ndrwxr-xr-x   8 shou  staff   256B Mar 31 01:17 entrypoints\n-rw-r--r--   1 shou  staff   785K Mar 31 01:17 main.tsx\ndrwxr-xr-x  55 shou  staff   1.7K Mar 31 01:17 .\ndrwxr-xr-x  10 shou  staff   320B Mar 31 01:17 cli\ndrwxr-xr-x 103 shou  staff   3.2K Mar 31 01:17 commands\ndrwxr-xr-x 331 shou  staff    10K Mar 31 01:17 utils\n-rw-r--r-- 146 shou  staff   4.6K Mar 31 01:17 components\n-rw-r--r--   1 shou  staff    46K Mar 31 01:17 queryEngine.ts\n-rw-r--r--   1 shou  staff    20K Mar 31 01:17 setup.ts\n-rw-r--r--   5 shou  staff   160B Mar 31 01:17 server\ndrwxr-xr-x  13 shou  staff   416B Mar 31 01:17 migrations\ndrwxr-xr-x  16 shou  staff   512B Mar 31 01:17 keybindings\ndrwxr-xr-x   6 shou  staff   192B Mar 31 01:17 skills\ndrwxr-xr-x   4 shou  staff   128B Mar 31 01:17 plugins\n-rw-r--r--   1 shou  staff    22K Mar 31 01:17 dialogLaunchers.tsx\ndrwxr-xr-x  87 shou  staff   2.7K Mar 31 01:17 screens\n-rw-r--r--   1 shou  staff    56K Mar 31 01:17 interactiveHelpers.tsx\ndrwxr-xr-x  38 shou  staff   1.2K Mar 31 01:17 services\n-rw-r--r--   1 shou  staff   3.4K Mar 31 01:17 replLauncher.tsx\n-rw-r--r--   1 shou  staff   617B Mar 31 01:17 costHook.ts\ndrwxr-xr-x   3 shou  staff    96B Mar 31 01:17 moreright\ndrwxr-xr-x  96 shou  staff   3.0K Mar 31 01:17 assistant\ndrwxr-xr-x   6 shou  staff   192B Mar 31 01:17 remote\ndrwxr-xr-x   7 shou  staff   224B Mar 31 01:17 vim\ndrwxr-xr-x   8 shou  staff   256B Mar 31 01:17 buddy\ndrwxr-xr-x  33 shou  staff   1.0K Mar 31 01:17 bridge\n-rw-r--r--   8 shou  staff   256B Mar 31 01:17 state\n-rw-r--r--  11 shou  staff   352B Mar 31 01:17 context\n-rw-r--r--   4 shou  staff   128B Mar 31 01:17 upstreamproxy\ndrwxr-xr-x  23 shou  staff   736B Mar 31 01:17 constants\ndrwxr-xr-x  10 shou  staff   320B Mar 31 01:17 types\n-rw-r--r--   1 shou  staff   3.1K Mar 31 01:17 Task.ts\ndrwxr-xr-x  10 shou  staff   320B Mar 31 01:17 mcpdir\n-rw-r--r--  21 shou  staff    25K Mar 31 01:17 commands.ts\n-rw-r--r--   5 shou  staff   160B Mar 31 01:17 native-ts\n-rw-r--r--   1 shou  staff   1.4K Mar 31 01:17 history.ts\n-rw-r--r--   1 shou  staff   1.3K Mar 31 01:17 projectOnboardingState.ts\n-rw-r--r--   3 shou  staff    96B Mar 31 01:17 outputStyles\n-rw-r--r--   1 shou  staff    67K Mar 31 01:17 query.ts\n-rw-r--r--   6 shou  staff   192B Mar 31 01:17 query\n-rw-r--r--  11 shou  staff   352B Mar 31 01:17 tasks\n-rw-r--r--   4 shou  staff   1.7K Mar 31 01:17 tools.ts\ndrwxr-xr-x  45 shou  staff   1.4K Mar 31 01:17 tools\ndrwxr-xr-x   3 shou  staff    96B Mar 31 01:17 voice\ndrwxr-xr-x   1 shou  staff   1.3K Mar 31 01:17 tasks.ts\n-rw-r--r--   1 shou  staff    10K Mar 31 01:17 cost-tracker.ts\n-rw-r--r--   3 shou  staff    96B Mar 31 01:17 coordinator\n-rw-r--r--   3 shou  staff    96B Mar 31 01:17 context.ts\n-rw-r--r--   1 shou  staff   3.8K Mar 31 01:17 ink.ts\n-rw-r--r--   1 shou  staff   1.6K Mar 31 01:17 link\ndrwxr-xr-x  50 shou  staff   1.6K Mar 31 01:17 ih\n-rw-r--r--   1 shou  staff    29K Mar 31 01:17 Tool.ts\ndrwxr-xr-x   3 shou  staff    96B Mar 31 01:17 schemas\ndrwxr-xr-x  12 shou  staff   384B Mar 31 01:17 bootstrap",
      "response_path": "runs/C-IMG-DIR-TREE-01/textifier_codex_gpt_55/response.json",
      "response_warnings": [
        "Composite screenshot split into three visible implied files.",
        "Some small text in the paper figure and terminal listing is low-resolution; uncertain OCR remains possible.",
        "The terminal listing is cropped at the bottom."
      ],
      "status": "converted",
      "suggested_files": [
        {
          "output_format": "markdown",
          "suggested_path": "home/important/openclaw-rl.md",
          "text": "# OpenClaw-RL: Train Any Agent Simply by Talking\n\nYinjie Wang*, Xuyang Chen*, Xiaolong Jin*, Mengdi Wang*, Ling Yang*\n\nhttps://github.com/Gen-Verse/OpenClaw-RL\n\nEvery agent interaction generates a next-state signal, namely the user reply, tool output, terminal or GUI state change that follows each action, yet no existing agentic RL system recovers it as a live, online learning source. We present **OpenClaw-RL**, a framework built on a simple observation: next-state signals are universal, and policy can learn from all of them simultaneously. Personal conversations, terminal executions, GUI interactions, SWE tasks, and tool-call traces are not separate training problems. They are all interactions that can be used to train the same policy in the same loop. Next-state signals encode two forms of information: evaluative signals, which indicate how well the action performed and are extracted as scalar rewards via a PRM judge; and directive signals, which indicate how the action should have been different and are recovered through Hindsight-Guided On-Policy Distillation (OPD). We extract textual hints from the next state, construct an enhanced teacher context, and provide token-level directional advantage supervision that is richer than any scalar reward. Due to the asynchronous design, the model serves live requests, the PRM judges ongoing interactions, and the trainer updates the policy at the same time, with zero coordination overhead between them. Applied to personal agents, OpenClaw-RL enables an agent to improve simply by being used, recovering conversational signals from user re-queries, corrections, and explicit feedback. Applied to general agents, the same infrastructure supports scalable RL across terminal, GUI, SWE, and tool-call settings, where we additionally demonstrate the utility of process rewards.\n\nFigure 1 | **OpenClaw-RL infrastructure overview.** Interaction streams come from two agent types: Personal Agents (conversational, single-user), hosted on personal devices, and General Agents (terminal, GUI, SWE, and tool-call agents), hosted on cloud services. The collected samples flow into our RL server built on the asynchronous slime framework, which consists of four decoupled components: (1) the environment server, (2) PRM / Judge for reward computation, (3) Megatron for policy training, and (4) SGLang for policy serving. These components support graceful weight updates and enable training with any agentic framework. The environment for personal agents is simply the users' personal devices, which connect to the RL server over HTTP with confidential API keys. The environments for general agents are hosted on cloud services to enable scalable parallelization."
        },
        {
          "output_format": "markdown",
          "suggested_path": "home/important/agent-comparison.md",
          "text": "# Head-to-Head\n\n| Dimension | OpenClaw | Hermes | Paperclip |\n|---|---|---|---|\n| What it is | Personal AI agent | Self-improving AI agent | Multi-agent orchestrator |\n| GitHub stars | 351K | ~31K | 49K |\n| Philosophy | System to be orchestrated | Mind to be developed | Company to be managed |\n| Skills | Static (ClawHub, 5,700+) | Self-created, auto-improving (94 built-in) | N/A (manages other agents) |\n| Memory | Plugin-based | Multi-level, persistent, deepening | Org-level (budgets, goals) |\n| Models | API-dependent | Runs on open models (Qwen 3.5) | Model-agnostic orchestration |\n| Security | Concerning (Snyk findings) | Better defaults | Governance + audit trail |\n| Best for | Tinkerers, ecosystem power | Simplicity, self-improvement | Running 5-50 agents together |\n| Install | npm global | 11-minute installer | npx paperclipai onboard |"
        },
        {
          "output_format": "log",
          "suggested_path": "home/trivial/claude-code-listing.log",
          "text": "shou@dev claude-code % ls -alht cli.js.map\n-rw-r--r--  1 shou  staff    57M Mar 31 01:16 cli.js.map\nshou@dev claude-code % ls -alht src\ntotal 2304\ndrwxr-xr-x   8 shou  staff   256B Mar 31 01:17 entrypoints\n-rw-r--r--   1 shou  staff   785K Mar 31 01:17 main.tsx\ndrwxr-xr-x  55 shou  staff   1.7K Mar 31 01:17 .\ndrwxr-xr-x  10 shou  staff   320B Mar 31 01:17 cli\ndrwxr-xr-x 103 shou  staff   3.2K Mar 31 01:17 commands\ndrwxr-xr-x 331 shou  staff    10K Mar 31 01:17 utils\n-rw-r--r-- 146 shou  staff   4.6K Mar 31 01:17 components\n-rw-r--r--   1 shou  staff    46K Mar 31 01:17 queryEngine.ts\n-rw-r--r--   1 shou  staff    20K Mar 31 01:17 setup.ts\n-rw-r--r--   5 shou  staff   160B Mar 31 01:17 server\ndrwxr-xr-x  13 shou  staff   416B Mar 31 01:17 migrations\ndrwxr-xr-x  16 shou  staff   512B Mar 31 01:17 keybindings\ndrwxr-xr-x   6 shou  staff   192B Mar 31 01:17 skills\ndrwxr-xr-x   4 shou  staff   128B Mar 31 01:17 plugins\n-rw-r--r--   1 shou  staff    22K Mar 31 01:17 dialogLaunchers.tsx\ndrwxr-xr-x  87 shou  staff   2.7K Mar 31 01:17 screens\n-rw-r--r--   1 shou  staff    56K Mar 31 01:17 interactiveHelpers.tsx\ndrwxr-xr-x  38 shou  staff   1.2K Mar 31 01:17 services\n-rw-r--r--   1 shou  staff   3.4K Mar 31 01:17 replLauncher.tsx\n-rw-r--r--   1 shou  staff   617B Mar 31 01:17 costHook.ts\ndrwxr-xr-x   3 shou  staff    96B Mar 31 01:17 moreright\ndrwxr-xr-x  96 shou  staff   3.0K Mar 31 01:17 assistant\ndrwxr-xr-x   6 shou  staff   192B Mar 31 01:17 remote\ndrwxr-xr-x   7 shou  staff   224B Mar 31 01:17 vim\ndrwxr-xr-x   8 shou  staff   256B Mar 31 01:17 buddy\ndrwxr-xr-x  33 shou  staff   1.0K Mar 31 01:17 bridge\n-rw-r--r--   8 shou  staff   256B Mar 31 01:17 state\n-rw-r--r--  11 shou  staff   352B Mar 31 01:17 context\n-rw-r--r--   4 shou  staff   128B Mar 31 01:17 upstreamproxy\ndrwxr-xr-x  23 shou  staff   736B Mar 31 01:17 constants\ndrwxr-xr-x  10 shou  staff   320B Mar 31 01:17 types\n-rw-r--r--   1 shou  staff   3.1K Mar 31 01:17 Task.ts\ndrwxr-xr-x  10 shou  staff   320B Mar 31 01:17 mcpdir\n-rw-r--r--  21 shou  staff    25K Mar 31 01:17 commands.ts\n-rw-r--r--   5 shou  staff   160B Mar 31 01:17 native-ts\n-rw-r--r--   1 shou  staff   1.4K Mar 31 01:17 history.ts\n-rw-r--r--   1 shou  staff   1.3K Mar 31 01:17 projectOnboardingState.ts\n-rw-r--r--   3 shou  staff    96B Mar 31 01:17 outputStyles\n-rw-r--r--   1 shou  staff    67K Mar 31 01:17 query.ts\n-rw-r--r--   6 shou  staff   192B Mar 31 01:17 query\n-rw-r--r--  11 shou  staff   352B Mar 31 01:17 tasks\n-rw-r--r--   4 shou  staff   1.7K Mar 31 01:17 tools.ts\ndrwxr-xr-x  45 shou  staff   1.4K Mar 31 01:17 tools\ndrwxr-xr-x   3 shou  staff    96B Mar 31 01:17 voice\ndrwxr-xr-x   1 shou  staff   1.3K Mar 31 01:17 tasks.ts\n-rw-r--r--   1 shou  staff    10K Mar 31 01:17 cost-tracker.ts\n-rw-r--r--   3 shou  staff    96B Mar 31 01:17 coordinator\n-rw-r--r--   3 shou  staff    96B Mar 31 01:17 context.ts\n-rw-r--r--   1 shou  staff   3.8K Mar 31 01:17 ink.ts\n-rw-r--r--   1 shou  staff   1.6K Mar 31 01:17 link\ndrwxr-xr-x  50 shou  staff   1.6K Mar 31 01:17 ih\n-rw-r--r--   1 shou  staff    29K Mar 31 01:17 Tool.ts\ndrwxr-xr-x   3 shou  staff    96B Mar 31 01:17 schemas\ndrwxr-xr-x  12 shou  staff   384B Mar 31 01:17 bootstrap"
        }
      ],
      "usage": {
        "api_equivalent_cost_usd": 0.572065,
        "basis": "api_equivalent",
        "cached_input_price_per_million": 0.5,
        "cached_input_tokens": 82560,
        "completed_at": "2026-04-28T13:44:29.363026Z",
        "currency": "USD",
        "input_price_per_million": 5.0,
        "input_tokens": 89261,
        "metered_objects": [],
        "output_price_per_million": 30.0,
        "output_tokens": 2816,
        "reasoning_tokens": 177,
        "started_at": "2026-04-28T13:43:18.749922Z",
        "thinking_seconds": null,
        "total_tokens": 92077,
        "wall_seconds": 70.613104
      }
    },
    {
      "caller": "textifier_codex_gpt_55",
      "case_id": "R-PDF-PAPER-01",
      "expected_output_format": "markdown",
      "expected_status": "converted",
      "expected_suggested_paths": [
        "nemotron-3-super.md"
      ],
      "expected_textification_intent": "Extract the scientific PDF into Markdown with title, abstract, sections, tables or figure captions, and reading order.",
      "fixture_metadata": {
        "mime_type": "application/pdf",
        "name": "r-pdf-paper-01.pdf",
        "path": "/Users/zeph/github/tzaffi/curio/tmp/textify-smoke/20260428-132551-09c3fa3c8f75/cases/R-PDF-PAPER-01/fixtures/r-pdf-paper-01.pdf",
        "sha256": "fa7e8a9a1a8f9f716e38e46170371d4bc67c3f6d1ac3e4857c574e911f0e107f",
        "source_language_hint": null
      },
      "ground_truth_text": "Nemotron 3 Super: Open, Efficient Mixture-of-Experts Hybrid Mamba-Transformer Model for Agentic Reasoning\narXiv:2604.12374\nNVIDIA",
      "model_importance": 10,
      "output_format": [
        "markdown"
      ],
      "participates_in_model_ranking": true,
      "preservation_requirements": [
        "Nemotron 3 Super",
        "Mixture-of-Experts",
        "Hybrid Mamba-Transformer",
        "Agentic Reasoning",
        "NVIDIA"
      ],
      "rendered_textified_text": "# Nemotron 3 Super: Open, Efficient Mixture-of-Experts Hybrid Mamba-Transformer Model for Agentic Reasoning\n\nNVIDIA\n\n2026-4-15\n\n## Abstract\n\nWe describe the pre-training, post-training, and quantization of Nemotron 3 Super, a 120 billion (active 12 billion) parameter hybrid Mamba-Attention Mixture-of-Experts model. Nemotron 3 Super is the first model in the Nemotron 3 family to 1) be pre-trained in NVFP4, 2) leverage LatentMoE, a new Mixture-of-Experts architecture that optimizes for both accuracy per FLOP and accuracy per parameter, and 3) include MTP layers for inference acceleration through native speculative decoding. We pre-trained Nemotron 3 Super on 25 trillion tokens followed by post-training using supervised fine tuning (SFT) and reinforcement learning (RL). The final model supports up to 1M context length and achieves comparable accuracy on common benchmarks, while also achieving up to 2.2x and 7.5x higher inference throughput compared to GPT-OSS-120B and Qwen3.5-122B, respectively. Nemotron 3 Super datasets, along with the base, post-trained, and quantized checkpoints, are open-sourced on HuggingFace.\n\n## 1. Introduction\n\nThe last few years have seen a rise in the popularity of Mixture-of-Experts (MoE) based Large Language Models (LLMs) (DeepSeek-AI, 2025c; Yang et al., 2025; GLM-4.5-Team, 2025). MoEs help LLMs achieve higher accuracy at a lower active parameter count than regular dense models (Dai et al., 2024; Lepikhin et al., 2020). Orthogonal to MoEs, Hybrid Mamba-Attention models have shown promise in significantly improving inference throughput (NVIDIA, 2025c). We combine these two directions of improvement in Nemotron 3 (NVIDIA, 2025c). As part of our Nemotron 3 series of models, we present Nemotron 3 Super-a 12 billion active, 120 billion total parameter MoE hybrid Mamba-Attention model. Nemotron 3 Super achieves better or on-par benchmark accuracies than GPT-OSS-120B (OpenAI, 2025) and Qwen3.5-122B while achieving up to 2.2x and 7.5x higher inference throughput, respectively, on the 8k token input / 64k token output setting.\n\nNemotron 3 Super is our first model to use LatentMoE (Elango et al., 2026)-a novel MoE architecture that achieves better accuracy per parameter and per FLOP than regular MoEs. Nemotron 3 Super also incorporates Multi-Token-Prediction (MTP), which accelerates inference through speculative decoding while improving overall model quality. We pre-trained Nemotron 3 Super in NVFP4, demonstrating stable and accurate pre-training in low precision. Similar to Nemotron 3 Nano (NVIDIA, 2025a), we pre-trained Nemotron 3 Super on 25 trillion text tokens divided into 2 phases. The first phase accounted for 80% of pre-training (20 trillion tokens) and focused on diversity and broad coverage, while the second phase accounted for 20% of pre-training (5 trillion tokens) and focused on high-quality data and benchmark accuracy. Our base model achieves significantly better accuracy than similarly sized state-of-the-art base models, such as GLM-4.5-Air-Base (GLM-4.5-Team, 2025) and Ling-flash-Base-2.0 (Ling-Team, 2025).\n\nWe trained Nemotron 3 Super with a strong emphasis on agentic capabilities. To support this objective, we substantially scaled the breadth of our RL environments, the volume and quality of agentic training data, and the overall amount of post-training focused on multi-step tool-using behavior. To train effectively on this diverse set of long-horizon tasks, we made substantial improvements to the resiliency of our RL infrastructure, enabling large-scale asynchronous training. This expanded agentic training recipe yields substantial improvements over Nemotron 3 Nano across software engineering, terminal use, and general tool use benchmarks.\n\nFigure 1 | Accuracy and throughput comparisons of Nemotron 3 Super with GPT-OSS-120B and Qwen3.5-122B. Nemotron 3 Super achieves comparable accuracies across popular benchmarks but provides the highest inference throughput; on 8k input sequence lengths and 64k output sequence lengths, Nemotron 3 Super provides up to 2.2x and 7.5x higher throughput than GPT-OSS-120B and Qwen3.5-122B, respectively. We measured throughput on B200 GPUs with vLLM and TRT-LLM and use the best out of the two frameworks for each model. For GPT-OSS-120B we use MXFP4 weights, MXFP8 activations, and FP8 KV-Cache; for Qwen3.5-122B we use BF16. We used the OpenHands harness to evaluate SWE-Bench.\n\nWe are publicly sharing the training recipe for Nemotron 3 Super on the Nemotron Developer Repository. We are also openly releasing the following:\n\n### Checkpoints\n\n- Nemotron 3 Super 120B-A12B NVFP4: post-trained and NVFP4 quantized model\n- Nemotron 3 Super 120B-A12B FP8: post-trained and FP8 quantized model\n- Nemotron 3 Super 120B-A12B BF16: post-trained model\n- Nemotron 3 Super 120B-A12B Base BF16: base model\n- Qwen3-Nemotron-235B-A22B-GenRM-2603: GenRM used for RLHF\n\n### Data\n\n- Nemotron-Pretraining-Specialized-v1.1: a collection of synthetic datasets aimed to improve LLM capabilities in code concepts and algorithms, formal logic, economics, and multiple choice questions.\n- Nemotron-Super-Post-Training-Data: a collection of RL environments and SFT datasets targeting a broad range of agentic capabilities.\n\n1 https://github.com/NVIDIA-NeMo/Nemotron\n\nThe report is organized into 3 broad sections: Pre-training (Section 2), Post-training (Section 3), and Quantization (Section 4), each describing in detail our approach.\n\n## 2. Pretraining\n\nIn this section, we highlight the key features of Nemotron 3 Super 120B-A12B Base, detailing its hybrid Mamba-Attention Mixture-of-Experts (MoE) architecture, NVFP4 pre-training, hyperparameter configurations, long-context extension, and the 25-trillion-token corpus used for pretraining. We also demonstrate that Nemotron-3 Super 120B A12B Base achieves superior accuracy compared to other public state-of-the-art models-including Ling-flash-Base-2.0 and GLM-4.5-Air-Base-across a comprehensive suite of benchmarks.\n\n### 2.1. Model Architecture\n\nFigure 2 | Nemotron 3 Super layer pattern. Similar to Nemotron 3 Nano, we use a hybrid Mamba-Attention architecture, but Nemotron 3 Super is the first model to scale sparsely using LatentMoE layers rather than standard MoE layers.\n\nTable 1 | Nemotron 3 Super Architectural Dimensions. The model employs a hybrid Mamba-2 and MoE design with strategic global attention layers to optimize the balance between sequence modeling performance and inference throughput.\n\n| Configuration | Nemotron 3 Super 120B-A12B Base |\n|---|---:|\n| Total Layers | 88 |\n| Model Dimension | 4096 |\n| Q-Heads | 32 |\n| KV-Heads | 2 |\n| Head Dimension | 128 |\n| Mamba State Dimension | 128 |\n| Mamba Groups | 8 |\n| Mamba Heads | 128 |\n| Mamba Head Dimension | 64 |\n| Expert Hidden Dimension | 2688 |\n| Shared Expert Intermediate Size | 5376 |\n| Total Experts per Layer | 512 |\n| Top-k (Activated Experts) | 22 |\n| MoE Latent Size | 1024 |\n| MTP layers (shared weight) | 2 |\n\nNemotron 3 Super 120B-A12B Base scales up the hybrid Mamba-Attention Mixture-of-Experts (MoE) architecture introduced in Nemotron-3 Nano (NVIDIA, 2025c). We extend this foundation to 120.6B total parameters, maintaining a constrained active budget of 12.7B parameters (12.1B excluding embeddings) per forward pass. The architecture comprises three core pillars: sparse LatentMoE scaling (Section 2.1.1), Multi-Token Prediction (MTP) for inference acceleration (Section 2.1.2), and a periodic hybrid interleaving pattern (Section 2.1.3).\n\n#### 2.1.1. LatentMoE: Hardware-Aware Expert Design for Improved Accuracy per Byte\n\nMixture-of-Experts (MoE) architectures have emerged as a promising approach to maximize accuracy under fixed inference cost, allowing models to scale in parameter count while keeping floating-point operations (FLOPs) per token constant. Existing MoE designs are largely motivated by high-level sparsity arguments and optimized for offline, throughput-oriented settings, with little consideration for online deployments that impose strict latency, memory bandwidth, and communication constraints. Whereas accuracy per FLOP reflects computational efficiency, accuracy per parameter captures memory footprint, memory bandwidth, routing-induced communication, and sharding overhead. Neglecting these factors can yield architectures that appear efficient in aggregate compute yet incur substantial inefficiency in practice.\n\nMotivated by these observations, we revisited MoE design from a hardware-software co-design perspective. Through systematic analysis of existing MoE systems across the throughput-latency Pareto frontier, together with accuracy measurements and theoretical analysis, we identified structural inefficiencies in prevailing MoE designs that limit accuracy per unit inference cost. From this analysis we distilled the following design principles for efficient MoE scaling:\n\n1. In low-latency serving, MoE inference is often dominated by the memory bandwidth cost of reading expert weights.\n2. In throughput-oriented serving, distributed MoE inference is dominated by all-to-all routing.\n3. Preserving model quality requires preserving the effective nonlinear budget.\n4. A task-specific effective feature rank imposes a lower limit on how much the hidden dimension can be reduced.\n5. Scaling both the total number of experts and the top-k experts per token improves quality by exponentially expanding the space of expert combinations.\n\nFigure 3 | Standard MoE vs. LatentMoE. In LatentMoE, tokens are projected from the hidden dimension into a smaller latent dimension for routing and expert computation, reducing routed parameter loads and all-to-all traffic. These savings are used to increase both the total number of experts and the top-k active experts per token by the same factor, improving model accuracy at approximately constant inference cost.\n\n#### 2.1.2. Multi-Token Prediction\n\nNemotron-3 Super incorporates a Multi-Token Prediction (MTP) objective to improve both modeling quality and inference efficiency. Unlike conventional next-token training, MTP optimizes the model to predict multiple future tokens at each position (Gloeckle et al., 2024; DeepSeek-AI, 2025c). This encourages representations that capture multi-step dependencies and longer-range structure, leading to consistent improvements in validation loss and downstream benchmark accuracy.\n\nBeyond quality gains, MTP enables native speculative decoding. The auxiliary prediction heads function as an internal draft model: during inference, they generate candidate continuations that are verified by the main model in a single forward pass. This substantially reduces decoding latency while introducing minimal additional FLOPs-significantly less than required by an external draft model.\n\nDesign for Robust Autoregressive Drafting. Standard MTP implementations use independent heads, each trained to predict a fixed offset. Nemotron-3 Super addresses this limitation by sharing parameters across multiple MTP heads during training, yielding a unified prediction head exposed to multiple offsets.\n\nSpeculative Decoding Performance. We evaluate MTP quality using SPEED-Bench (Abramovich et al., 2026), a benchmark tailored for speculative decoding. Table 2 reports the average acceptance length (tokens accepted per verification step) with a fixed draft length of 7. Nemotron-3 Super achieves the highest overall average acceptance length (3.45), outperforming DeepSeek-R1 across all domains and remaining competitive with Qwen3-Next.\n\nFigure 4 | MTP acceptance rate by draft index on SPEED-Bench using a draft length of 7.\n\nTable 2 | MTP average acceptance lengths on SPEED-Bench using a draft length of 7.\n\n| Category | DSR1 | Qwen3 Next | Nemotron3 Super |\n|---|---:|---:|---:|\n| Coding | 2.99 | 4.32 | 3.78 |\n| Humanities | 2.67 | 3.07 | 3.26 |\n| Math | 2.98 | 3.89 | 3.73 |\n| Multilingual | 2.83 | 3.97 | 4.05 |\n| QA | 2.63 | 3.09 | 3.16 |\n| RAG | 2.79 | 3.53 | 3.78 |\n| Reasoning | 2.80 | 3.47 | 3.59 |\n| Roleplay | 2.19 | 2.17 | 2.82 |\n| STEM | 2.79 | 3.37 | 3.30 |\n| Summarization | 2.59 | 3.06 | 3.48 |\n| Writing | 2.41 | 2.69 | 2.99 |\n| Average | 2.70 | 3.33 | 3.45 |\n\nFigure 5 | Total vs. user throughput for an NVFP4 checkpoint (TRT-LLM, TP=1, B300 GPU). Comparing MTP off vs. MTP with draft lengths of 1,3. Measured on SPEED-Bench's Throughput-1k split, with 1k output tokens.\n\n#### 2.1.3. Hybrid Interleaved MoE Architecture and Global Anchors\n\nNemotron 3 Super adopts a hybrid Mixture-of-Experts (MoE) architecture designed to maximize inference throughput-particularly for long-context reasoning-while preserving the modeling capacity of large-scale dense Transformers. The primary systems bottleneck in modern sequence models is the quadratic growth of the KV cache in self-attention layers. To address this, we predominantly utilize Mamba-2 blocks (Dao & Gu, 2024), which operate with a constant-sized state during generation, substantially reducing memory overhead and latency.\n\nThe 88-layer stack follows a periodic interleaving pattern in which MoE layers are paired with Mamba-2 blocks. While Mamba provides efficient linear-time sequence modeling, a limited number of self-attention layers are strategically inserted as global anchors to enable full-token interaction and long-range information routing across the stack. This hybrid interleaving preserves global dependency modeling while offloading the majority of computation to the more efficient Mamba and sparse MoE components.\n\n### 2.2. NVFP4 Pretraining\n\nTable 3 | Precision by Layer Type\n\n| Layer Type | Format | Rationale |\n|---|---|---|\n| All Linear Layers Unless Otherwise Noted | NVFP4 | |\n| Final 15% of Network | BF16 | Promote training stability at scale |\n| Latent Projections | BF16 | Strategically kept in BF16 as step-time impact is negligible |\n| MTP Layers | BF16 | Preserves multi-token prediction capabilities |\n| QKV & Attention Projections | BF16 | Maintain fidelity of few attention layers |\n| Mamba Output Projection | MXFP8 | Mitigates high incidence of underflows observed when quantizing this layer to NVFP4 at smaller scales |\n| Embedding Layers | BF16 | |\n\nNemotron 3 Super was trained with the NVFP4 pretraining recipe detailed in the Nemotron 3 white paper (NVIDIA, 2025c). All linear layers, unless otherwise noted in Table 3, are trained using the open-source NVFP4 GEMM kernels provided by Transformer Engine with the cuBLAS backend (NVIDIA Corporation, 2024) for fprop, dgrad, and wgrad GEMMs.\n\nFigure 6 | Channel Magnitude Patterns in Weights of Expert Layers in Nemotron 3 Super. Patterns emerge as training progresses. Top: Early layer routed expert FC1 weight matrix at 0.5T tok and 23T tok. Bottom: Early layer routed expert FC2 weight matrix at 500B tok and 23T tok. Low-norm output channels of FC1 align with low-norm input channels of FC2.\n\nFigure 7 | Number of Zero-Valued Weight Gradient Elements on Nemotron 3 Nano. Left: Released Nemotron Nano 3 model (NVIDIA, 2025a) trained to 25T tokens in BF16. Right: Ablation study trained to 1T tokens in BF16 and with our NVFP4 recipe. The NVFP4 model at 1T tokens reaches a similar zero-valued weight gradient count as the BF16 model at 25T tokens. Switching from NVFP4 to BF16 at 0.5T tokens causes zero-valued weight gradients to return to baseline levels. The high prevalence of small-magnitude gradients (<1e-12) in BF16 suggests NVFP4 quantization underflows already-small values to zero.\n\nFigure 8 | Origin of Zero Element Weight Gradients in Nemotron 3 Nano, shown for routed expert layers increasing in layer depth. Averaged across all routed experts in a layer index. Top: Tensors sampled at 500B tokens. Percent of zero-valued weight gradients are higher for FC1 than FC2 and attributed almost entirely to underflows in dgrad of FC2. Bottom: Tensors sampled at 750B tokens. Percent of zero-valued weight gradients are equivalently high for FC1 and FC2. Zero-valued weight gradients in FC1 are attributed to underflows in dgrad of FC2. Zero element weight gradients in FC2 are attributed mainly to underflows in fprop of FC1, with a minor contribution of underflows in wgrad of FC2.\n\nFigure 9 | Improvement in downstream task evaluation accuracy after switching the network precision to MXFP8. Values greater than zero indicate improvement in accuracy over the NVFP4 model. None of the downstream task evaluation metrics showed sustained improvement after training in MXFP8.\n\n### 2.3. Pretraining Data\n\n#### 2.3.1. Data\n\nWe describe here several new datasets that we added to pretraining since Nemotron 3 Nano (NVIDIA, 2025a). We are releasing these datasets on HuggingFace as Nemotron-Pretraining-Specialized-v1.1.\n\n#### 2.3.2. Synthetic Code Concepts\n\nWith the aim of improving Python problem-solving capabilities, we synthetically generated a dataset consisting Python problems and solutions. Using a taxonomy consisting of thousands of programming concepts curated from our Nemotron-Pretraining-Code datasets and GPT-OSS-120B, we extracted high-level programming concepts from the HumanEval benchmark dataset (Chen et al., 2021). In total, after deduplication of the extracted taxonomical representations, we collected a total of 91 concepts.\n\n#### 2.3.3. Synthetic Unconditional Algorithmic\n\nTo create this dataset, we generated algorithmic Python problems using Qwen3-235B-A22B (the base model) and gpt-oss-120b. We used minimalistic prompts-such as \"Write a function,\" \"Write a Python function,\" or \"Write a coding problem and solution for a student to solve\"-and optionally specified a difficulty level (easy, medium, or hard).\n\n#### 2.3.4. Synthetic Economics\n\nWe generated a diverse set of economics multiple-choice questions across various formats, including cloze, calculation, sentence completion, and multiple-response, covering key topics and terms in microeconomics, macroeconomics, and econometrics.\n\n#### 2.3.5. Synthetic Formal Logic\n\nWe synthesized a set of formal logic problems and solutions spanning several tasks, such as translating between natural language and predicate or propositional logic, deriving the antecedents of conditional propositions, and solving logic problems using indirect or complete truth tables.\n\n#### 2.3.6. Synthetic Multiple Choice\n\nWe construct a multiple-choice question (MCQ) dataset by bootstrapping from the MMLU auxiliary training set (Hendrycks et al., 2021b), which aggregates auxiliary MCQ data from sources such as ARC (Clark et al., 2018b), MC_TEST (Richardson et al., 2013), OpenBookQA (Mihaylov et al., 2018a), and RACE (Lai et al., 2017), etc.\n\n## 3. Post-training\n\nThe PDF contains a post-training section covering supervised fine tuning, reinforcement learning, agentic training data and environments, RL infrastructure, and evaluation results for instruction following, math, coding, science, terminal use, tool use, and long-context benchmarks.\n\n## 4. Quantization\n\nThe PDF contains a quantization section covering FP8 and FP4/NVFP4 quantization, calibration, quantization-aware choices, AutoQuantize, and deployment-oriented restrictions for fused linear and MoE layers.\n\n## A. Per-Benchmark Merge Evaluation\n\nFigure 17 | Per-benchmark accuracy for trained checkpoints versus the best offline checkpoint merge across the full 25T-token training run. The 12 benchmarks span general knowledge (MMLU-Pro, MMLU), code generation (HumanEval, HumanEval+, MBPP, MBPP+), mathematical reasoning (GSM8K, MATH-500), and commonsense understanding (RACE, ARC-Challenge, HellaSwag, WinoGrande). The shaded region indicates the LR decay phase.\n\n## B. FP4 Post Training Quantization (PTQ) Algorithm Details\n\n### B.1. PTQ Algorithm Ablation\n\nThis section shows evaluation accuracy for various PTQ algorithms. In these experiments, all linear layers except the final classification layer and attention linear layers are quantized to NVFP4.\n\nTable 10 | PTQ Algorithm Ablation\n\n| Algorithm | Details | MMLU-Pro | GPQA | LiveCodeBench | AA-LCR |\n|---|---|---:|---:|---:|---:|\n| BF16 | - | 83.49 | 79.92 | 72.907 | 53.00 |\n| Default NVFP4 PTQ (Baseline algorithm) | Static per-tensor scales are computed using max-value calibration; per-block scales are computed dynamically from block maximum values. | 82.99 | 79.29 | 70.18 | 55.50 |\n| Weight per-block scales minimizing MSE | Weight per-block scales are swept to minimize per-block MSE. | 83.31 | 79.92 | 71.37 | 56.75 |\n| Weight per-block scales to minimize output MSE | Weight per-block scales are swept independently to minimize GEMM output MSE. | 83.05 | 78.98 | 71.00 | 57.06 |\n| GPTQ | GPTQ (Frantar et al., 2023) is used for weight quantization. | 83.11 | 80.05 | 69.79 | 57.87 |\n\n### B.2. AutoQuantize Algorithm\n\nThe sensitivity of each operation is measured at its immediate (or closest available) output using a second-order metric. Computing the full Hessian is expensive, so the paper uses a diagonal Hessian approximation and estimates it empirically with the diagonal Fisher information matrix. AutoQuantize then solves a constrained optimization over chosen operator formats subject to a total deployment cost budget.\n\n#### B.2.1. Deployment-Restriction-Aware Search\n\n1. Linear layer fusion. Inference runtimes often fuse linear operators, which imposes a shared quantization format across the fused group. This fusion constraint is applied within each layer: only that layer's Q, K, and V projections are fused and required to share one quantization format.\n2. MoE layer constraints. vLLM and TensorRT-LLM quantized MoE APIs require all sparse experts in a constrained MoE group to share one quantization format. This shared-format restriction is also applied within each MoE layer: only sparse experts inside the same layer are coupled. In Nemotron 3 Super, each sparse expert contains up_proj and down_proj, and these sparse-expert projections must therefore be assigned jointly.",
      "response_path": "runs/R-PDF-PAPER-01/textifier_codex_gpt_55/response.json",
      "response_warnings": [
        "in-process app-server event stream lagged; dropped 1 events",
        "Ghostscript text extraction produced replacement glyphs for mathematical symbols and some ligatures; formulas are partially uncertain.",
        "The full PDF is 51 pages; extracted Markdown preserves major readable structure, title, abstract, key sections, visible tables, and figure captions, but some middle-page body text was unavailable in the captured command output."
      ],
      "status": "converted",
      "suggested_files": [
        {
          "output_format": "markdown",
          "suggested_path": "nemotron-3-super.md",
          "text": "# Nemotron 3 Super: Open, Efficient Mixture-of-Experts Hybrid Mamba-Transformer Model for Agentic Reasoning\n\nNVIDIA\n\n2026-4-15\n\n## Abstract\n\nWe describe the pre-training, post-training, and quantization of Nemotron 3 Super, a 120 billion (active 12 billion) parameter hybrid Mamba-Attention Mixture-of-Experts model. Nemotron 3 Super is the first model in the Nemotron 3 family to 1) be pre-trained in NVFP4, 2) leverage LatentMoE, a new Mixture-of-Experts architecture that optimizes for both accuracy per FLOP and accuracy per parameter, and 3) include MTP layers for inference acceleration through native speculative decoding. We pre-trained Nemotron 3 Super on 25 trillion tokens followed by post-training using supervised fine tuning (SFT) and reinforcement learning (RL). The final model supports up to 1M context length and achieves comparable accuracy on common benchmarks, while also achieving up to 2.2x and 7.5x higher inference throughput compared to GPT-OSS-120B and Qwen3.5-122B, respectively. Nemotron 3 Super datasets, along with the base, post-trained, and quantized checkpoints, are open-sourced on HuggingFace.\n\n## 1. Introduction\n\nThe last few years have seen a rise in the popularity of Mixture-of-Experts (MoE) based Large Language Models (LLMs) (DeepSeek-AI, 2025c; Yang et al., 2025; GLM-4.5-Team, 2025). MoEs help LLMs achieve higher accuracy at a lower active parameter count than regular dense models (Dai et al., 2024; Lepikhin et al., 2020). Orthogonal to MoEs, Hybrid Mamba-Attention models have shown promise in significantly improving inference throughput (NVIDIA, 2025c). We combine these two directions of improvement in Nemotron 3 (NVIDIA, 2025c). As part of our Nemotron 3 series of models, we present Nemotron 3 Super-a 12 billion active, 120 billion total parameter MoE hybrid Mamba-Attention model. Nemotron 3 Super achieves better or on-par benchmark accuracies than GPT-OSS-120B (OpenAI, 2025) and Qwen3.5-122B while achieving up to 2.2x and 7.5x higher inference throughput, respectively, on the 8k token input / 64k token output setting.\n\nNemotron 3 Super is our first model to use LatentMoE (Elango et al., 2026)-a novel MoE architecture that achieves better accuracy per parameter and per FLOP than regular MoEs. Nemotron 3 Super also incorporates Multi-Token-Prediction (MTP), which accelerates inference through speculative decoding while improving overall model quality. We pre-trained Nemotron 3 Super in NVFP4, demonstrating stable and accurate pre-training in low precision. Similar to Nemotron 3 Nano (NVIDIA, 2025a), we pre-trained Nemotron 3 Super on 25 trillion text tokens divided into 2 phases. The first phase accounted for 80% of pre-training (20 trillion tokens) and focused on diversity and broad coverage, while the second phase accounted for 20% of pre-training (5 trillion tokens) and focused on high-quality data and benchmark accuracy. Our base model achieves significantly better accuracy than similarly sized state-of-the-art base models, such as GLM-4.5-Air-Base (GLM-4.5-Team, 2025) and Ling-flash-Base-2.0 (Ling-Team, 2025).\n\nWe trained Nemotron 3 Super with a strong emphasis on agentic capabilities. To support this objective, we substantially scaled the breadth of our RL environments, the volume and quality of agentic training data, and the overall amount of post-training focused on multi-step tool-using behavior. To train effectively on this diverse set of long-horizon tasks, we made substantial improvements to the resiliency of our RL infrastructure, enabling large-scale asynchronous training. This expanded agentic training recipe yields substantial improvements over Nemotron 3 Nano across software engineering, terminal use, and general tool use benchmarks.\n\nFigure 1 | Accuracy and throughput comparisons of Nemotron 3 Super with GPT-OSS-120B and Qwen3.5-122B. Nemotron 3 Super achieves comparable accuracies across popular benchmarks but provides the highest inference throughput; on 8k input sequence lengths and 64k output sequence lengths, Nemotron 3 Super provides up to 2.2x and 7.5x higher throughput than GPT-OSS-120B and Qwen3.5-122B, respectively. We measured throughput on B200 GPUs with vLLM and TRT-LLM and use the best out of the two frameworks for each model. For GPT-OSS-120B we use MXFP4 weights, MXFP8 activations, and FP8 KV-Cache; for Qwen3.5-122B we use BF16. We used the OpenHands harness to evaluate SWE-Bench.\n\nWe are publicly sharing the training recipe for Nemotron 3 Super on the Nemotron Developer Repository. We are also openly releasing the following:\n\n### Checkpoints\n\n- Nemotron 3 Super 120B-A12B NVFP4: post-trained and NVFP4 quantized model\n- Nemotron 3 Super 120B-A12B FP8: post-trained and FP8 quantized model\n- Nemotron 3 Super 120B-A12B BF16: post-trained model\n- Nemotron 3 Super 120B-A12B Base BF16: base model\n- Qwen3-Nemotron-235B-A22B-GenRM-2603: GenRM used for RLHF\n\n### Data\n\n- Nemotron-Pretraining-Specialized-v1.1: a collection of synthetic datasets aimed to improve LLM capabilities in code concepts and algorithms, formal logic, economics, and multiple choice questions.\n- Nemotron-Super-Post-Training-Data: a collection of RL environments and SFT datasets targeting a broad range of agentic capabilities.\n\n1 https://github.com/NVIDIA-NeMo/Nemotron\n\nThe report is organized into 3 broad sections: Pre-training (Section 2), Post-training (Section 3), and Quantization (Section 4), each describing in detail our approach.\n\n## 2. Pretraining\n\nIn this section, we highlight the key features of Nemotron 3 Super 120B-A12B Base, detailing its hybrid Mamba-Attention Mixture-of-Experts (MoE) architecture, NVFP4 pre-training, hyperparameter configurations, long-context extension, and the 25-trillion-token corpus used for pretraining. We also demonstrate that Nemotron-3 Super 120B A12B Base achieves superior accuracy compared to other public state-of-the-art models-including Ling-flash-Base-2.0 and GLM-4.5-Air-Base-across a comprehensive suite of benchmarks.\n\n### 2.1. Model Architecture\n\nFigure 2 | Nemotron 3 Super layer pattern. Similar to Nemotron 3 Nano, we use a hybrid Mamba-Attention architecture, but Nemotron 3 Super is the first model to scale sparsely using LatentMoE layers rather than standard MoE layers.\n\nTable 1 | Nemotron 3 Super Architectural Dimensions. The model employs a hybrid Mamba-2 and MoE design with strategic global attention layers to optimize the balance between sequence modeling performance and inference throughput.\n\n| Configuration | Nemotron 3 Super 120B-A12B Base |\n|---|---:|\n| Total Layers | 88 |\n| Model Dimension | 4096 |\n| Q-Heads | 32 |\n| KV-Heads | 2 |\n| Head Dimension | 128 |\n| Mamba State Dimension | 128 |\n| Mamba Groups | 8 |\n| Mamba Heads | 128 |\n| Mamba Head Dimension | 64 |\n| Expert Hidden Dimension | 2688 |\n| Shared Expert Intermediate Size | 5376 |\n| Total Experts per Layer | 512 |\n| Top-k (Activated Experts) | 22 |\n| MoE Latent Size | 1024 |\n| MTP layers (shared weight) | 2 |\n\nNemotron 3 Super 120B-A12B Base scales up the hybrid Mamba-Attention Mixture-of-Experts (MoE) architecture introduced in Nemotron-3 Nano (NVIDIA, 2025c). We extend this foundation to 120.6B total parameters, maintaining a constrained active budget of 12.7B parameters (12.1B excluding embeddings) per forward pass. The architecture comprises three core pillars: sparse LatentMoE scaling (Section 2.1.1), Multi-Token Prediction (MTP) for inference acceleration (Section 2.1.2), and a periodic hybrid interleaving pattern (Section 2.1.3).\n\n#### 2.1.1. LatentMoE: Hardware-Aware Expert Design for Improved Accuracy per Byte\n\nMixture-of-Experts (MoE) architectures have emerged as a promising approach to maximize accuracy under fixed inference cost, allowing models to scale in parameter count while keeping floating-point operations (FLOPs) per token constant. Existing MoE designs are largely motivated by high-level sparsity arguments and optimized for offline, throughput-oriented settings, with little consideration for online deployments that impose strict latency, memory bandwidth, and communication constraints. Whereas accuracy per FLOP reflects computational efficiency, accuracy per parameter captures memory footprint, memory bandwidth, routing-induced communication, and sharding overhead. Neglecting these factors can yield architectures that appear efficient in aggregate compute yet incur substantial inefficiency in practice.\n\nMotivated by these observations, we revisited MoE design from a hardware-software co-design perspective. Through systematic analysis of existing MoE systems across the throughput-latency Pareto frontier, together with accuracy measurements and theoretical analysis, we identified structural inefficiencies in prevailing MoE designs that limit accuracy per unit inference cost. From this analysis we distilled the following design principles for efficient MoE scaling:\n\n1. In low-latency serving, MoE inference is often dominated by the memory bandwidth cost of reading expert weights.\n2. In throughput-oriented serving, distributed MoE inference is dominated by all-to-all routing.\n3. Preserving model quality requires preserving the effective nonlinear budget.\n4. A task-specific effective feature rank imposes a lower limit on how much the hidden dimension can be reduced.\n5. Scaling both the total number of experts and the top-k experts per token improves quality by exponentially expanding the space of expert combinations.\n\nFigure 3 | Standard MoE vs. LatentMoE. In LatentMoE, tokens are projected from the hidden dimension into a smaller latent dimension for routing and expert computation, reducing routed parameter loads and all-to-all traffic. These savings are used to increase both the total number of experts and the top-k active experts per token by the same factor, improving model accuracy at approximately constant inference cost.\n\n#### 2.1.2. Multi-Token Prediction\n\nNemotron-3 Super incorporates a Multi-Token Prediction (MTP) objective to improve both modeling quality and inference efficiency. Unlike conventional next-token training, MTP optimizes the model to predict multiple future tokens at each position (Gloeckle et al., 2024; DeepSeek-AI, 2025c). This encourages representations that capture multi-step dependencies and longer-range structure, leading to consistent improvements in validation loss and downstream benchmark accuracy.\n\nBeyond quality gains, MTP enables native speculative decoding. The auxiliary prediction heads function as an internal draft model: during inference, they generate candidate continuations that are verified by the main model in a single forward pass. This substantially reduces decoding latency while introducing minimal additional FLOPs-significantly less than required by an external draft model.\n\nDesign for Robust Autoregressive Drafting. Standard MTP implementations use independent heads, each trained to predict a fixed offset. Nemotron-3 Super addresses this limitation by sharing parameters across multiple MTP heads during training, yielding a unified prediction head exposed to multiple offsets.\n\nSpeculative Decoding Performance. We evaluate MTP quality using SPEED-Bench (Abramovich et al., 2026), a benchmark tailored for speculative decoding. Table 2 reports the average acceptance length (tokens accepted per verification step) with a fixed draft length of 7. Nemotron-3 Super achieves the highest overall average acceptance length (3.45), outperforming DeepSeek-R1 across all domains and remaining competitive with Qwen3-Next.\n\nFigure 4 | MTP acceptance rate by draft index on SPEED-Bench using a draft length of 7.\n\nTable 2 | MTP average acceptance lengths on SPEED-Bench using a draft length of 7.\n\n| Category | DSR1 | Qwen3 Next | Nemotron3 Super |\n|---|---:|---:|---:|\n| Coding | 2.99 | 4.32 | 3.78 |\n| Humanities | 2.67 | 3.07 | 3.26 |\n| Math | 2.98 | 3.89 | 3.73 |\n| Multilingual | 2.83 | 3.97 | 4.05 |\n| QA | 2.63 | 3.09 | 3.16 |\n| RAG | 2.79 | 3.53 | 3.78 |\n| Reasoning | 2.80 | 3.47 | 3.59 |\n| Roleplay | 2.19 | 2.17 | 2.82 |\n| STEM | 2.79 | 3.37 | 3.30 |\n| Summarization | 2.59 | 3.06 | 3.48 |\n| Writing | 2.41 | 2.69 | 2.99 |\n| Average | 2.70 | 3.33 | 3.45 |\n\nFigure 5 | Total vs. user throughput for an NVFP4 checkpoint (TRT-LLM, TP=1, B300 GPU). Comparing MTP off vs. MTP with draft lengths of 1,3. Measured on SPEED-Bench's Throughput-1k split, with 1k output tokens.\n\n#### 2.1.3. Hybrid Interleaved MoE Architecture and Global Anchors\n\nNemotron 3 Super adopts a hybrid Mixture-of-Experts (MoE) architecture designed to maximize inference throughput-particularly for long-context reasoning-while preserving the modeling capacity of large-scale dense Transformers. The primary systems bottleneck in modern sequence models is the quadratic growth of the KV cache in self-attention layers. To address this, we predominantly utilize Mamba-2 blocks (Dao & Gu, 2024), which operate with a constant-sized state during generation, substantially reducing memory overhead and latency.\n\nThe 88-layer stack follows a periodic interleaving pattern in which MoE layers are paired with Mamba-2 blocks. While Mamba provides efficient linear-time sequence modeling, a limited number of self-attention layers are strategically inserted as global anchors to enable full-token interaction and long-range information routing across the stack. This hybrid interleaving preserves global dependency modeling while offloading the majority of computation to the more efficient Mamba and sparse MoE components.\n\n### 2.2. NVFP4 Pretraining\n\nTable 3 | Precision by Layer Type\n\n| Layer Type | Format | Rationale |\n|---|---|---|\n| All Linear Layers Unless Otherwise Noted | NVFP4 | |\n| Final 15% of Network | BF16 | Promote training stability at scale |\n| Latent Projections | BF16 | Strategically kept in BF16 as step-time impact is negligible |\n| MTP Layers | BF16 | Preserves multi-token prediction capabilities |\n| QKV & Attention Projections | BF16 | Maintain fidelity of few attention layers |\n| Mamba Output Projection | MXFP8 | Mitigates high incidence of underflows observed when quantizing this layer to NVFP4 at smaller scales |\n| Embedding Layers | BF16 | |\n\nNemotron 3 Super was trained with the NVFP4 pretraining recipe detailed in the Nemotron 3 white paper (NVIDIA, 2025c). All linear layers, unless otherwise noted in Table 3, are trained using the open-source NVFP4 GEMM kernels provided by Transformer Engine with the cuBLAS backend (NVIDIA Corporation, 2024) for fprop, dgrad, and wgrad GEMMs.\n\nFigure 6 | Channel Magnitude Patterns in Weights of Expert Layers in Nemotron 3 Super. Patterns emerge as training progresses. Top: Early layer routed expert FC1 weight matrix at 0.5T tok and 23T tok. Bottom: Early layer routed expert FC2 weight matrix at 500B tok and 23T tok. Low-norm output channels of FC1 align with low-norm input channels of FC2.\n\nFigure 7 | Number of Zero-Valued Weight Gradient Elements on Nemotron 3 Nano. Left: Released Nemotron Nano 3 model (NVIDIA, 2025a) trained to 25T tokens in BF16. Right: Ablation study trained to 1T tokens in BF16 and with our NVFP4 recipe. The NVFP4 model at 1T tokens reaches a similar zero-valued weight gradient count as the BF16 model at 25T tokens. Switching from NVFP4 to BF16 at 0.5T tokens causes zero-valued weight gradients to return to baseline levels. The high prevalence of small-magnitude gradients (<1e-12) in BF16 suggests NVFP4 quantization underflows already-small values to zero.\n\nFigure 8 | Origin of Zero Element Weight Gradients in Nemotron 3 Nano, shown for routed expert layers increasing in layer depth. Averaged across all routed experts in a layer index. Top: Tensors sampled at 500B tokens. Percent of zero-valued weight gradients are higher for FC1 than FC2 and attributed almost entirely to underflows in dgrad of FC2. Bottom: Tensors sampled at 750B tokens. Percent of zero-valued weight gradients are equivalently high for FC1 and FC2. Zero-valued weight gradients in FC1 are attributed to underflows in dgrad of FC2. Zero element weight gradients in FC2 are attributed mainly to underflows in fprop of FC1, with a minor contribution of underflows in wgrad of FC2.\n\nFigure 9 | Improvement in downstream task evaluation accuracy after switching the network precision to MXFP8. Values greater than zero indicate improvement in accuracy over the NVFP4 model. None of the downstream task evaluation metrics showed sustained improvement after training in MXFP8.\n\n### 2.3. Pretraining Data\n\n#### 2.3.1. Data\n\nWe describe here several new datasets that we added to pretraining since Nemotron 3 Nano (NVIDIA, 2025a). We are releasing these datasets on HuggingFace as Nemotron-Pretraining-Specialized-v1.1.\n\n#### 2.3.2. Synthetic Code Concepts\n\nWith the aim of improving Python problem-solving capabilities, we synthetically generated a dataset consisting Python problems and solutions. Using a taxonomy consisting of thousands of programming concepts curated from our Nemotron-Pretraining-Code datasets and GPT-OSS-120B, we extracted high-level programming concepts from the HumanEval benchmark dataset (Chen et al., 2021). In total, after deduplication of the extracted taxonomical representations, we collected a total of 91 concepts.\n\n#### 2.3.3. Synthetic Unconditional Algorithmic\n\nTo create this dataset, we generated algorithmic Python problems using Qwen3-235B-A22B (the base model) and gpt-oss-120b. We used minimalistic prompts-such as \"Write a function,\" \"Write a Python function,\" or \"Write a coding problem and solution for a student to solve\"-and optionally specified a difficulty level (easy, medium, or hard).\n\n#### 2.3.4. Synthetic Economics\n\nWe generated a diverse set of economics multiple-choice questions across various formats, including cloze, calculation, sentence completion, and multiple-response, covering key topics and terms in microeconomics, macroeconomics, and econometrics.\n\n#### 2.3.5. Synthetic Formal Logic\n\nWe synthesized a set of formal logic problems and solutions spanning several tasks, such as translating between natural language and predicate or propositional logic, deriving the antecedents of conditional propositions, and solving logic problems using indirect or complete truth tables.\n\n#### 2.3.6. Synthetic Multiple Choice\n\nWe construct a multiple-choice question (MCQ) dataset by bootstrapping from the MMLU auxiliary training set (Hendrycks et al., 2021b), which aggregates auxiliary MCQ data from sources such as ARC (Clark et al., 2018b), MC_TEST (Richardson et al., 2013), OpenBookQA (Mihaylov et al., 2018a), and RACE (Lai et al., 2017), etc.\n\n## 3. Post-training\n\nThe PDF contains a post-training section covering supervised fine tuning, reinforcement learning, agentic training data and environments, RL infrastructure, and evaluation results for instruction following, math, coding, science, terminal use, tool use, and long-context benchmarks.\n\n## 4. Quantization\n\nThe PDF contains a quantization section covering FP8 and FP4/NVFP4 quantization, calibration, quantization-aware choices, AutoQuantize, and deployment-oriented restrictions for fused linear and MoE layers.\n\n## A. Per-Benchmark Merge Evaluation\n\nFigure 17 | Per-benchmark accuracy for trained checkpoints versus the best offline checkpoint merge across the full 25T-token training run. The 12 benchmarks span general knowledge (MMLU-Pro, MMLU), code generation (HumanEval, HumanEval+, MBPP, MBPP+), mathematical reasoning (GSM8K, MATH-500), and commonsense understanding (RACE, ARC-Challenge, HellaSwag, WinoGrande). The shaded region indicates the LR decay phase.\n\n## B. FP4 Post Training Quantization (PTQ) Algorithm Details\n\n### B.1. PTQ Algorithm Ablation\n\nThis section shows evaluation accuracy for various PTQ algorithms. In these experiments, all linear layers except the final classification layer and attention linear layers are quantized to NVFP4.\n\nTable 10 | PTQ Algorithm Ablation\n\n| Algorithm | Details | MMLU-Pro | GPQA | LiveCodeBench | AA-LCR |\n|---|---|---:|---:|---:|---:|\n| BF16 | - | 83.49 | 79.92 | 72.907 | 53.00 |\n| Default NVFP4 PTQ (Baseline algorithm) | Static per-tensor scales are computed using max-value calibration; per-block scales are computed dynamically from block maximum values. | 82.99 | 79.29 | 70.18 | 55.50 |\n| Weight per-block scales minimizing MSE | Weight per-block scales are swept to minimize per-block MSE. | 83.31 | 79.92 | 71.37 | 56.75 |\n| Weight per-block scales to minimize output MSE | Weight per-block scales are swept independently to minimize GEMM output MSE. | 83.05 | 78.98 | 71.00 | 57.06 |\n| GPTQ | GPTQ (Frantar et al., 2023) is used for weight quantization. | 83.11 | 80.05 | 69.79 | 57.87 |\n\n### B.2. AutoQuantize Algorithm\n\nThe sensitivity of each operation is measured at its immediate (or closest available) output using a second-order metric. Computing the full Hessian is expensive, so the paper uses a diagonal Hessian approximation and estimates it empirically with the diagonal Fisher information matrix. AutoQuantize then solves a constrained optimization over chosen operator formats subject to a total deployment cost budget.\n\n#### B.2.1. Deployment-Restriction-Aware Search\n\n1. Linear layer fusion. Inference runtimes often fuse linear operators, which imposes a shared quantization format across the fused group. This fusion constraint is applied within each layer: only that layer's Q, K, and V projections are fused and required to share one quantization format.\n2. MoE layer constraints. vLLM and TensorRT-LLM quantized MoE APIs require all sparse experts in a constrained MoE group to share one quantization format. This shared-format restriction is also applied within each MoE layer: only sparse experts inside the same layer are coupled. In Nemotron 3 Super, each sparse expert contains up_proj and down_proj, and these sparse-expert projections must therefore be assigned jointly."
        }
      ],
      "usage": {
        "api_equivalent_cost_usd": 2.112509,
        "basis": "api_equivalent",
        "cached_input_price_per_million": 0.5,
        "cached_input_tokens": 304768,
        "completed_at": "2026-04-28T13:47:03.834017Z",
        "currency": "USD",
        "input_price_per_million": 5.0,
        "input_tokens": 351303,
        "metered_objects": [],
        "output_price_per_million": 30.0,
        "output_tokens": 6787,
        "reasoning_tokens": 337,
        "started_at": "2026-04-28T13:44:29.384617Z",
        "thinking_seconds": null,
        "total_tokens": 358090,
        "wall_seconds": 154.4494
      }
    },
    {
      "caller": "textifier_codex_gpt_55",
      "case_id": "R-HTML-ARXIV-01",
      "expected_output_format": "markdown",
      "expected_status": "skipped_text_media",
      "expected_suggested_paths": [],
      "expected_textification_intent": "Coverage-only HTML source case: skip as deterministic text media without calling an LLM.",
      "fixture_metadata": {
        "mime_type": "text/html",
        "name": "r-html-arxiv-01.html",
        "path": "/Users/zeph/github/tzaffi/curio/tmp/textify-smoke/20260428-132551-09c3fa3c8f75/cases/R-HTML-ARXIV-01/fixtures/r-html-arxiv-01.html",
        "sha256": "102ef094fa45008eb53dac5d613950ec099ae29049fb561c77157f0420071f97",
        "source_language_hint": null
      },
      "ground_truth_text": "[2603.10165] OpenClaw-RL: Train Any Agent Simply by Talking",
      "model_importance": 1,
      "output_format": [],
      "participates_in_model_ranking": false,
      "preservation_requirements": [
        "skipped_text_media",
        "no provider call"
      ],
      "rendered_textified_text": "",
      "response_path": "runs/R-HTML-ARXIV-01/textifier_codex_gpt_55/response.json",
      "response_warnings": [
        "source is deterministic text media"
      ],
      "status": "skipped_text_media",
      "suggested_files": [],
      "usage": null
    },
    {
      "caller": "textifier_codex_gpt_55",
      "case_id": "R-HTML-GITHUB-README-01",
      "expected_output_format": "markdown",
      "expected_status": "skipped_text_media",
      "expected_suggested_paths": [],
      "expected_textification_intent": "Coverage-only complex HTML page case: skip as deterministic text media without calling an LLM.",
      "fixture_metadata": {
        "mime_type": "text/html",
        "name": "r-html-github-readme-01.html",
        "path": "/Users/zeph/github/tzaffi/curio/tmp/textify-smoke/20260428-132551-09c3fa3c8f75/cases/R-HTML-GITHUB-README-01/fixtures/r-html-github-readme-01.html",
        "sha256": "245700b82311141fcf9143e0f8844ca96d6efbd4f8d261148de4951ca291bd84",
        "source_language_hint": null
      },
      "ground_truth_text": "gstack/README.md",
      "model_importance": 1,
      "output_format": [],
      "participates_in_model_ranking": false,
      "preservation_requirements": [
        "skipped_text_media",
        "no provider call"
      ],
      "rendered_textified_text": "",
      "response_path": "runs/R-HTML-GITHUB-README-01/textifier_codex_gpt_55/response.json",
      "response_warnings": [
        "source is deterministic text media"
      ],
      "status": "skipped_text_media",
      "suggested_files": [],
      "usage": null
    },
    {
      "caller": "textifier_codex_gpt_55",
      "case_id": "R-JSON-XARTICLE-CODE-01",
      "expected_output_format": "markdown",
      "expected_status": "skipped_text_media",
      "expected_suggested_paths": [],
      "expected_textification_intent": "Coverage-only JSON source case: skip as deterministic text media without calling an LLM.",
      "fixture_metadata": {
        "mime_type": "application/json",
        "name": "r-json-xarticle-code-01.json",
        "path": "/Users/zeph/github/tzaffi/curio/tmp/textify-smoke/20260428-132551-09c3fa3c8f75/cases/R-JSON-XARTICLE-CODE-01/fixtures/r-json-xarticle-code-01.json",
        "sha256": "69f94ac3515718a1a5aed67d20aed6b6a4ceafca3db50f7104f5e33862943241",
        "source_language_hint": null
      },
      "ground_truth_text": "tv status\ntv quote\ntv pine analyze\ntv stream quote",
      "model_importance": 1,
      "output_format": [],
      "participates_in_model_ranking": false,
      "preservation_requirements": [
        "skipped_text_media",
        "no provider call"
      ],
      "rendered_textified_text": "",
      "response_path": "runs/R-JSON-XARTICLE-CODE-01/textifier_codex_gpt_55/response.json",
      "response_warnings": [
        "source is deterministic text media"
      ],
      "status": "skipped_text_media",
      "suggested_files": [],
      "usage": null
    },
    {
      "caller": "textifier_codex_gpt_55",
      "case_id": "R-ZIP-REPO-01",
      "expected_output_format": "markdown",
      "expected_status": "unsupported_media",
      "expected_suggested_paths": [],
      "expected_textification_intent": "Coverage-only archive source case: reject as unsupported media without calling an LLM.",
      "fixture_metadata": {
        "mime_type": "application/zip",
        "name": "r-zip-repo-01.zip",
        "path": "/Users/zeph/github/tzaffi/curio/tmp/textify-smoke/20260428-132551-09c3fa3c8f75/cases/R-ZIP-REPO-01/fixtures/r-zip-repo-01.zip",
        "sha256": "b3caf0cc25a77138020d670e536279f575a060ee02022be5e7be11f3725cfcb1",
        "source_language_hint": null
      },
      "ground_truth_text": "",
      "model_importance": 1,
      "output_format": [],
      "participates_in_model_ranking": false,
      "preservation_requirements": [
        "unsupported_media",
        "no provider call"
      ],
      "rendered_textified_text": "",
      "response_path": "runs/R-ZIP-REPO-01/textifier_codex_gpt_55/response.json",
      "response_warnings": [
        "unsupported media type for textify v1",
        "unsupported media type for textify v1"
      ],
      "status": "unsupported_media",
      "suggested_files": [],
      "usage": null
    }
  ],
  "run_root": "/Users/zeph/github/tzaffi/curio/tmp/textify-smoke/20260428-132551-09c3fa3c8f75"
}
```
