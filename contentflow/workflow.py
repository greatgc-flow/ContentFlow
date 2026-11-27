"""Validate and order the CPU-only local subset of the v1 workflow contract."""
from graphlib import CycleError, TopologicalSorter
import re

from contentflow.domain import MAX_INT

_ID = re.compile(r"[a-zA-Z][a-zA-Z0-9_.-]{0,95}")
_LOCAL = {"IMPORT", "VERIFY", "BRIEF", "SCRIPT", "ASSET_PLAN", "ASSET_CREATE",
          "ALIGN", "RENDER", "QC", "REVIEW", "EXPORT", "REPORT"}
_FIELDS = {"key", "kind", "depends_on", "inputs", "outputs", "optional", "provider_id",
           "max_attempts", "timeout_seconds", "effect", "gpu_slots"}


def _id(value):
    return isinstance(value, str) and _ID.fullmatch(value)


def _integer(value, low, high):
    return type(value) is int and low <= value <= high


def _names(values):
    return (type(values) is list and len(values) <= 100 and all(_id(v) for v in values)
            and len(set(values)) == len(values))


def _step(step):
    if type(step) is not dict or step.keys() != _FIELDS or not _id(step["key"]):
        raise ValueError("invalid step fields or key")
    if not all(_names(step[k]) for k in ("depends_on", "inputs", "outputs")):
        raise ValueError("invalid dependency or artifact names")
    kind = step["kind"]
    if not _id(kind) or kind not in _LOCAL or step["effect"] not in ("PURE", "LOCAL_WRITE"):
        raise ValueError("step is outside the offline profile")
    permitted = ("fixture.local", None, "local.ffmpeg") if kind == "RENDER" else ("fixture.local", None)
    if step["provider_id"] not in permitted or not _integer(step["gpu_slots"], 0, 0):
        raise ValueError("provider requires an unavailable capability")
    if (type(step["optional"]) is not bool or not _integer(step["max_attempts"], 1, 5)
            or not _integer(step["timeout_seconds"], 1, 86400)):
        raise ValueError("invalid step bounds")


def plan(document):
    if (type(document) is not dict
            or document.keys() != {"schema_version", "workflow_id", "revision", "offline", "steps"}
            or document["schema_version"] != "1.0" or document["offline"] is not True
            or not _id(document["workflow_id"]) or not _integer(document["revision"], 1, MAX_INT)):
        raise ValueError("expected a versioned offline workflow")
    steps = document["steps"]
    if type(steps) is not list or not 1 <= len(steps) <= 1000:
        raise ValueError("invalid step count")
    by_key, producers = {}, {}
    for step in steps:
        _step(step)
        key = step["key"]
        if key in by_key or producers.keys() & step["outputs"]:
            raise ValueError("duplicate step or output")
        by_key[key] = step
        producers.update(dict.fromkeys(step["outputs"], key))
    graph = {k: set(s["depends_on"]) for k, s in by_key.items()}
    for parents in graph.values():
        if not parents <= by_key.keys():
            raise ValueError("missing dependency")
    sorter = TopologicalSorter(graph)
    try:
        sorter.prepare()
    except CycleError as exc:
        raise ValueError("cyclic dependencies") from exc
    order, ancestors = [], {}
    while sorter.is_active():
        ready = sorted(sorter.get_ready())
        for key in ready:
            parents = graph[key]
            reachable = parents.union(*(ancestors[p] for p in parents))
            for name in by_key[key]["inputs"]:
                owner = producers.get(name)
                if owner not in reachable or (by_key[owner]["optional"] and not by_key[key]["optional"]):
                    raise ValueError("input has no guaranteed upstream producer")
            ancestors[key] = reachable
        order.extend(ready)
        sorter.done(*ready)
    return order
