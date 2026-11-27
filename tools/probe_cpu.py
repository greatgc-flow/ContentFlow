"""Render or recheck a private synthetic fixture on the pinned Linux CPU toolchain."""
import argparse
from array import array
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from contentflow.brief import processing_time_brief  # noqa: E402

FFMPEG = "/usr/bin/ffmpeg"
FFPROBE = "/usr/bin/ffprobe"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
TOOLS = {
    FFMPEG: "e8a8d46f5225f3062cec7c07fb145d58ae73c603cb740dcd5bad34bfb54e455a",
    FFPROBE: "cefc5f81c0b18429cdbf8fa5a89e1e9c759235e10f93f9b329ff1b2fdff26f46",
    FONT: "57f73e11f51999432bf7ab22ce55b6f945d5eca1bf824404cfa9ec2e3718c84e",
}
SOURCE_HASH = "8a458535a74a1631a13c2de8bb62d24574c1234e1f467679aab877f595d5ca45"
MEDIA = {"preview.mp4", "thumbnail.png"}
LIMIT = 16 * 1024 * 1024


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def encoded(obj):
    return (json.dumps(obj, sort_keys=True, indent=2) + "\n").encode()


def inputs():
    raw = (ROOT / "contentflow/fixtures/processing-times.csv").read_bytes()
    require(sha(raw) == SOURCE_HASH, "authored CSV does not match the fixture lock")
    brief = processing_time_brief(raw)
    baseline, optimized = brief["baseline_ms"], brief["optimized_ms"]
    percent = brief["relative_decrease_percent"]
    scenes = {"test_only": True, "width": 1080, "height": 1920, "fps": 30, "frames": 450,
              "source_sha256": brief["source_sha256"], "audio": "synthetic 440 Hz tone",
              "captions": [[0, 7500, f"TEST_ONLY: {baseline} ms baseline, {optimized} ms optimized."],
                           [7500, 15000, f"{percent}% relative decrease in this synthetic example."]]}
    captions = ("1\n00:00:00,000 --> 00:00:07,500\n" + scenes["captions"][0][2]
                + "\n\n2\n00:00:07,500 --> 00:00:15,000\n" + scenes["captions"][1][2] + "\n")
    width = 840 * optimized // baseline
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1920">\n'
           '<rect width="1080" height="1920" fill="#102130"/>\n'
           '<rect x="120" y="730" width="840" height="110" fill="#75b7c3"/>\n'
           f'<rect x="120" y="1050" width="{width}" height="110" fill="#e9ad68"/>\n</svg>\n')
    article = (f"# Synthetic processing time comparison\n\n{brief['disclosure']}\n\n"
               f"The fixture falls from {baseline} ms to {optimized} ms. Dividing the difference "
               f"by the baseline gives a {percent}% relative decrease. "
               f"The observations are CSV records 2-3. Source SHA-256: {SOURCE_HASH}.\n")
    return {"source.csv": raw, "brief.json": encoded(brief), "article.md": article.encode(),
            "scenes.json": encoded(scenes), "captions.srt": captions.encode(), "chart.svg": svg.encode()}


def run(root, tool, *args):
    proc = subprocess.run([tool, "-v", "error", *args], cwd=root, stdin=subprocess.DEVNULL,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=75)
    if proc.returncode:
        raise ValueError(proc.stderr[-2048:].decode(errors="replace") or f"{tool} failed")
    return proc.stdout


def draw(root, brief):
    labels = [(240, 52, "SYNTHETIC DATA"), (405, 62, "Processing time"),
              (645, 40, f"Baseline     {brief['baseline_ms']} ms"),
              (965, 40, f"Optimized   {brief['optimized_ms']} ms"),
              (1335, 54, f"{brief['relative_decrease_percent']}% relative decrease"),
              (1660, 38, "TEST_ONLY   /   Private preview")]
    filters = ",".join(f"drawtext=fontfile={FONT}:fontsize={size}:fontcolor=white:x=120:y={y}"
                       f":expansion=none:text='{label}'" for y, size, label in labels)
    run(root, FFMPEG, "-nostdin", "-protocol_whitelist", "file,pipe", "-i", "chart.svg",
        "-filter_threads", "1", "-vf", filters, "-frames:v", "1", "-threads", "1", "thumbnail.png")
    run(root, FFMPEG, "-nostdin", "-protocol_whitelist", "file,pipe", "-framerate", "30",
        "-loop", "1", "-i", "thumbnail.png", "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000",
        "-t", "15", "-map_metadata", "-1", "-filter_threads", "1", "-c:v", "libx264",
        "-threads:v", "2", "-preset", "ultrafast", "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-threads:a", "1", "-b:a", "96k", "-movflags", "+faststart", "preview.mp4")


def qc(root):
    common = ("-protocol_whitelist", "file,pipe", "-f", "mov", "-i", "preview.mp4")
    info = json.loads(run(root, FFPROBE, *common, "-show_streams", "-of", "json"))
    streams = {s["codec_type"]: s for s in info["streams"]}
    require(len(info["streams"]) == 2 and streams.keys() == {"audio", "video"}, "unexpected streams")
    video, audio = streams["video"], streams["audio"]
    require((video["codec_name"], video["width"], video["height"], video["avg_frame_rate"])
            == ("h264", 1080, 1920, "30/1"), "unexpected video format")
    require(audio["codec_name"] == "aac" and float(audio["duration"]) == 15
            and float(video["duration"]) == 15, "unexpected duration or audio codec")
    frames = run(root, FFMPEG, "-xerror", *common, "-map", "0:v:0", "-threads", "1",
                 "-f", "framemd5", "-").splitlines()
    count = sum(line.startswith(b"0,") for line in frames)
    require(count == 450, "full decode did not yield 450 frames")
    pcm = run(root, FFMPEG, "-xerror", *common, "-map", "0:a:0", "-ac", "1", "-ar", "8000",
              "-t", "15", "-f", "s16le", "-")
    samples = array("h")
    samples.frombytes(pcm)
    if sys.byteorder != "little":
        samples.byteswap()
    require(len(samples) == 120000, "incomplete decoded audio")
    peak = max(abs(x) for x in samples)
    require(peak > 100, "unexpected silent tone")
    cues = json.loads(run(root, FFPROBE, "-protocol_whitelist", "file,pipe", "-f", "srt",
                          "-i", "captions.srt", "-show_packets", "-of", "json"))["packets"]
    require([(float(c["pts_time"]), float(c["duration_time"])) for c in cues]
            == [(0, 7.5), (7.5, 7.5)], "caption bounds disagree with scene timeline")
    return {"decoded_frames": count, "captions": len(cues), "audio_peak": peak,
            "decoded_samples_at_8000_hz": len(samples)}


def manifest(root, authored):
    hashes = {}
    for name in sorted(set(authored) | MEDIA):
        path = root / name
        require(not path.is_symlink() and path.is_file() and 0 < path.stat().st_size <= LIMIT,
                "missing or oversized fixture artifact: " + name)
        data = path.read_bytes()
        if name in authored:
            require(data == authored[name], "fixture lineage mismatch: " + name)
        hashes[name] = sha(data)
    return {"fixture_version": 1, "test_only": True, "publication": "PROHIBITED",
            "tools": TOOLS, "files": hashes, "qc": qc(root)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("render", "verify"))
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    root = args.directory
    try:
        for tool, expected in TOOLS.items():
            require(sha(Path(tool).read_bytes()) == expected, "local toolchain pin mismatch: " + tool)
        authored = inputs()
        if args.action == "render":
            root.mkdir(exist_ok=False)
            for name, data in authored.items():
                (root / name).write_bytes(data)
            draw(root, json.loads(authored["brief.json"]))
            result = manifest(root, authored)
            with (root / "manifest.json").open("xb") as marker:
                marker.write(encoded(result))
        else:
            require(not root.is_symlink() and root.is_dir(), "expected a local fixture directory")
            marker = root / "manifest.json"
            require(not marker.is_symlink() and marker.is_file() and marker.stat().st_size < 16384,
                    "incomplete fixture")
            result = manifest(root, authored)
            require(marker.read_bytes() == encoded(result), "manifest disagrees with decoded fixture")
        print(json.dumps(result["qc"], sort_keys=True))
    except (KeyError, OSError, ValueError, subprocess.TimeoutExpired) as exc:
        parser.exit(1, f"Fixture qualification failed: {exc}\n")


if __name__ == "__main__":
    main()
