from __future__ import annotations

import json

from typer.testing import CliRunner

from jsonibase.cli.main import app

runner = CliRunner()


def _payload(result):
    return json.loads(result.stdout)


def test_cli_guide_returns_json_envelope_without_vcs_commands() -> None:
    result = runner.invoke(app, ["guide"])

    assert result.exit_code == 0
    payload = _payload(result)
    assert payload["ok"] is True
    assert payload["command"] == "guide"
    commands = payload["data"]["commands"]
    assert {
        "init",
        "status",
        "validate",
        "build",
        "search",
        "get",
        "list",
        "plan",
        "apply",
    }.issubset(commands)
    assert "git" not in commands
    assert "github" not in commands


def test_cli_init_validate_build_status_get_list_and_search(tmp_path) -> None:
    root = str(tmp_path)
    common = [
        "--root",
        root,
        "--collection",
        "standards",
        "--path",
        "data/standards.jsonl",
        "--fts",
        "title",
        "--fts",
        "body",
        "--embedding",
        "title",
        "--embedding",
        "body",
        "--filter",
        "status",
    ]

    init = runner.invoke(app, ["init", *common])
    assert init.exit_code == 0
    assert _payload(init)["ok"] is True

    source = tmp_path / "data" / "standards.jsonl"
    source.write_text(
        '{"body":"Prefer managed services.","id":"std_001",'
        '"status":"active","title":"Managed services"}\n',
        encoding="utf-8",
    )

    validate = runner.invoke(app, ["validate", *common])
    build = runner.invoke(app, ["build", *common])
    status = runner.invoke(app, ["status", *common])
    get = runner.invoke(app, ["get", *common, "--id", "std_001"])
    listed = runner.invoke(app, ["list", *common, "--filter-eq", "status=active"])
    search = runner.invoke(app, ["search", *common, "--query", "managed services"])

    assert _payload(validate)["ok"] is True
    assert _payload(build)["ok"] is True
    assert _payload(status)["data"]["reason"] == "fresh"
    assert _payload(get)["data"]["record"]["id"] == "std_001"
    assert _payload(listed)["data"]["records"][0]["id"] == "std_001"
    assert _payload(search)["data"]["results"][0]["record_id"] == "std_001"


def test_cli_plan_and_apply_return_json_envelopes(tmp_path) -> None:
    root = str(tmp_path)
    common = [
        "--root",
        root,
        "--collection",
        "standards",
        "--path",
        "data/standards.jsonl",
        "--fts",
        "title",
    ]
    runner.invoke(app, ["init", *common])

    record = '{"id":"std_001","title":"One"}'
    plan = runner.invoke(app, ["plan", *common, "--op", "add", "--record", record])
    apply = runner.invoke(app, ["apply", *common, "--op", "add", "--record", record])

    assert _payload(plan)["data"]["operations"][0]["record_id"] == "std_001"
    assert _payload(apply)["data"]["changed_files"]
