"""Generate a UV-textured reconstruction candidate with the official Hunyuan3D space.

This is an offline asset-authoring tool. It is never imported by the game runtime.
Outputs stay in ``art-source/characters/work/v5`` until they pass visual and GLB
validation; the script refuses to overwrite an existing candidate.
"""

from __future__ import annotations

import argparse
import json
import shutil
import time
import uuid
from pathlib import Path
from urllib.parse import quote

import requests


BASE_URL = "https://tencent-hunyuan3d-2mv.hf.space"
PROJECT = Path("/mnt/c/Users/t_maruyama/Documents/gameapp")
INPUT_ROOT = PROJECT / "docs/character-concepts/reconstruction-inputs"
OUTPUT_ROOT = PROJECT / "art-source/characters/work/v5/hunyuan-textured"
CACHE_ROOT = Path("/home/t_maruyama/.cache/gameapp-tools/hunyuan-textured-downloads")


def log(label: str, value: object) -> None:
    print(f"{label} {json.dumps(value, ensure_ascii=False, default=str)}", flush=True)


def upload(session: requests.Session, path: Path) -> dict[str, str]:
    started = time.monotonic()
    with path.open("rb") as stream:
        response = session.post(
            f"{BASE_URL}/upload",
            files={"files": (path.name, stream, "image/png")},
            timeout=(30, 120),
        )
    response.raise_for_status()
    uploaded = response.json()
    if not isinstance(uploaded, list) or len(uploaded) != 1:
        raise ValueError(f"Unexpected upload response for {path}: {uploaded!r}")
    log(
        "UPLOAD",
        {
            "file": str(path),
            "remote_path": uploaded[0],
            "seconds": round(time.monotonic() - started, 2),
        },
    )
    return {"path": uploaded[0], "orig_name": path.name}


def endpoint_index(config: dict, api_name: str) -> int:
    for index, dependency in enumerate(config.get("dependencies", [])):
        if dependency.get("api_name") == api_name:
            return index
    raise RuntimeError(f"Live endpoint is unavailable: {api_name}")


def run_job(
    session: requests.Session, data: list[object], session_hash: str, fn_index: int
) -> dict:
    joined_response = session.post(
        f"{BASE_URL}/queue/join",
        json={"data": data, "fn_index": fn_index, "session_hash": session_hash},
        timeout=(30, 120),
    )
    if joined_response.status_code == 503:
        raise RuntimeError(f"Space queue is full: {joined_response.text}")
    joined_response.raise_for_status()
    event_id = joined_response.json().get("event_id")
    if not event_id:
        raise ValueError(f"Missing event_id: {joined_response.text}")
    log("QUEUE_JOINED", {"event_id": event_id, "session_hash": session_hash})

    last_status = None
    with session.get(
        f"{BASE_URL}/queue/data",
        params={"session_hash": session_hash},
        stream=True,
        timeout=(30, 3600),
    ) as response:
        response.raise_for_status()
        for raw_line in response.iter_lines(decode_unicode=True):
            if not raw_line or not raw_line.startswith("data:"):
                continue
            message = json.loads(raw_line[5:])
            if message.get("msg") == "heartbeat":
                continue
            if message.get("event_id") not in (None, event_id):
                continue
            status = {
                key: message.get(key)
                for key in ("msg", "rank", "queue_size", "rank_eta", "success")
                if key in message
            }
            if status != last_status:
                log("QUEUE_STATUS", status)
                last_status = status
            if message.get("msg") == "queue_full":
                raise RuntimeError("Space queue reported queue_full")
            if message.get("msg") == "process_completed":
                output = message.get("output")
                if not isinstance(output, dict):
                    raise ValueError(f"Unexpected completion payload: {message!r}")
                if output.get("error"):
                    raise RuntimeError(f"Space generation failed: {output['error']}")
                return output
            if message.get("msg") in ("server_stopped", "unexpected_error"):
                raise RuntimeError(f"Space stopped: {message!r}")
    raise RuntimeError("SSE stream ended before process_completed")


def unwrap_file_value(file_value: object) -> object:
    while (
        isinstance(file_value, dict)
        and file_value.get("__type__") == "update"
        and "value" in file_value
    ):
        file_value = file_value["value"]
    return file_value


def download_glb(
    session: requests.Session, file_value: object, destination: Path
) -> int:
    file_value = unwrap_file_value(file_value)
    if isinstance(file_value, str):
        remote_path = file_value
        url = f"{BASE_URL}/file={quote(remote_path, safe='/')}"
    elif isinstance(file_value, dict):
        remote_path = file_value.get("path")
        url = file_value.get("url") or (
            f"{BASE_URL}/file={quote(remote_path, safe='/')}" if remote_path else None
        )
    else:
        remote_path = None
        url = None
    if not isinstance(url, str):
        raise TypeError(f"Unrecognized GLB output: {file_value!r}")

    CACHE_ROOT.mkdir(parents=True, exist_ok=True)
    temporary = CACHE_ROOT / f"{uuid.uuid4().hex}.glb"
    with session.get(url, stream=True, timeout=(30, 300)) as response:
        response.raise_for_status()
        with temporary.open("wb") as stream:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    stream.write(chunk)
    if temporary.read_bytes()[:4] != b"glTF":
        raise ValueError(f"Downloaded output is not a GLB: {remote_path!r}")
    shutil.copy2(temporary, destination)
    return destination.stat().st_size


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sex", choices=("male", "female"), required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--steps", type=int, default=30)
    parser.add_argument("--octree", type=int, default=380)
    parser.add_argument("--chunks", type=int, default=20000)
    args = parser.parse_args()

    input_dir = INPUT_ROOT / args.sex
    paths = {name: input_dir / f"{name}.png" for name in ("front", "right", "back")}
    for path in paths.values():
        if not path.is_file():
            raise FileNotFoundError(path)

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    stem = f"{args.sex}-seed-{args.seed}"
    shape_path = OUTPUT_ROOT / f"{stem}-shape.glb"
    textured_path = OUTPUT_ROOT / f"{stem}-textured.glb"
    metadata_path = OUTPUT_ROOT / f"{stem}.json"
    for path in (shape_path, textured_path, metadata_path):
        if path.exists():
            raise FileExistsError(f"Refusing to overwrite existing candidate: {path}")

    session = requests.Session()
    session.headers.update({"User-Agent": "gameapp-offline-asset-authoring/1.0"})
    config_response = session.get(f"{BASE_URL}/config", timeout=(30, 60))
    config_response.raise_for_status()
    config = config_response.json()
    fn_index = endpoint_index(config, "generation_all")
    uploaded = {name: upload(session, path) for name, path in paths.items()}
    request_record = {
        "space": BASE_URL,
        "endpoint": "generation_all",
        "sex": args.sex,
        "seed": args.seed,
        "steps": args.steps,
        "guidance_scale": 5.0,
        "octree_resolution": args.octree,
        "num_chunks": args.chunks,
        "remove_background": True,
        "left_view": None,
    }
    log("REQUEST", request_record)
    data = [
        None,
        None,
        uploaded["front"],
        uploaded["back"],
        None,
        uploaded["right"],
        args.steps,
        5.0,
        args.seed,
        args.octree,
        True,
        args.chunks,
        False,
    ]
    output = run_job(session, data, uuid.uuid4().hex, fn_index)
    result_data = output.get("data")
    if not isinstance(result_data, list) or len(result_data) < 5:
        raise ValueError(f"Unexpected Space output: {output!r}")
    shape_bytes = download_glb(session, result_data[0], shape_path)
    textured_bytes = download_glb(session, result_data[1], textured_path)
    record = {
        **request_record,
        "shape": {"path": str(shape_path), "bytes": shape_bytes},
        "textured": {"path": str(textured_path), "bytes": textured_bytes},
        "mesh_stats": result_data[3],
        "returned_seed": result_data[4],
        "status": "diagnostic",
    }
    metadata_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    log("RESULT", record)


if __name__ == "__main__":
    main()
