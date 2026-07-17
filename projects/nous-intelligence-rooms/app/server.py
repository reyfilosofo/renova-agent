#!/usr/bin/env python3
"""NOUS Intelligence Rooms - dependency-free demo and OpenAI Responses API backend."""
from __future__ import annotations
import base64, json, mimetypes, os, pathlib, re, sys, urllib.error, urllib.request
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parent
STATIC = ROOT / "static"
MODEL = os.environ.get("OPENAI_MODEL", "gpt-5.6-terra")
API_KEY = os.environ.get("OPENAI_API_KEY", "").strip()
PORT = int(os.environ.get("PORT", "8000"))

DEMO_PATH = ROOT / "demo_analysis.json"

SCHEMA: dict[str, Any] = {
  "type":"object","additionalProperties":False,
  "required":["meta","organization","sector","decision","thesis","summary","decision_enabled","overall_score","score_interpretation","metrics","top_opportunity","top_risk","signals","decisions","roadmap","evidence"],
  "properties":{
    "meta":{"type":"object","additionalProperties":False,"required":["mode","model","confidence","generated_at"],"properties":{"mode":{"type":"string"},"model":{"type":"string"},"confidence":{"type":"integer","minimum":0,"maximum":100},"generated_at":{"type":"string"}}},
    "organization":{"type":"string"},"sector":{"type":"string"},"decision":{"type":"string"},"thesis":{"type":"string"},"summary":{"type":"string"},"decision_enabled":{"type":"string"},
    "overall_score":{"type":"integer","minimum":0,"maximum":100},"score_interpretation":{"type":"string"},
    "metrics":{"type":"array","minItems":5,"maxItems":5,"items":{"type":"object","additionalProperties":False,"required":["name","score"],"properties":{"name":{"type":"string"},"score":{"type":"integer","minimum":0,"maximum":100}}}},
    "top_opportunity":{"$ref":"#/$defs/titlewhy"},"top_risk":{"$ref":"#/$defs/titlewhy"},
    "signals":{"type":"array","minItems":5,"maxItems":8,"items":{"type":"object","additionalProperties":False,"required":["type","tone","title","body","confidence","source"],"properties":{"type":{"type":"string"},"tone":{"type":"string","enum":["opportunity","risk","neutral"]},"title":{"type":"string"},"body":{"type":"string"},"confidence":{"type":"integer","minimum":0,"maximum":100},"source":{"type":"string"}}}},
    "decisions":{"type":"array","minItems":5,"maxItems":8,"items":{"type":"object","additionalProperties":False,"required":["rank","title","detail","impact","effort","urgency","quadrant"],"properties":{"rank":{"type":"integer"},"title":{"type":"string"},"detail":{"type":"string"},"impact":{"type":"string"},"effort":{"type":"string"},"urgency":{"type":"string"},"quadrant":{"type":"string"}}}},
    "roadmap":{"type":"object","additionalProperties":False,"required":["0–30 days","31–60 days","61–90 days"],"properties":{"0–30 days":{"$ref":"#/$defs/roaditems"},"31–60 days":{"$ref":"#/$defs/roaditems"},"61–90 days":{"$ref":"#/$defs/roaditems"}}},
    "evidence":{"type":"array","minItems":4,"maxItems":10,"items":{"type":"object","additionalProperties":False,"required":["id","observation","source","confidence","implication"],"properties":{"id":{"type":"string"},"observation":{"type":"string"},"source":{"type":"string"},"confidence":{"type":"integer","minimum":0,"maximum":100},"implication":{"type":"string"}}}}
  },
  "$defs":{
    "titlewhy":{"type":"object","additionalProperties":False,"required":["title","why"],"properties":{"title":{"type":"string"},"why":{"type":"string"}}},
    "roaditems":{"type":"array","minItems":3,"maxItems":5,"items":{"type":"object","additionalProperties":False,"required":["title","detail"],"properties":{"title":{"type":"string"},"detail":{"type":"string"}}}}
  }
}

DEVELOPER_PROMPT = """You are NOUS, a strategic-intelligence analyst. Transform organizational evidence into a traceable decision architecture. Be rigorous, specific, economical and non-theatrical. Distinguish observations from inferences. Do not claim facts that are not supported by the submitted material. Scores must be internally coherent. Recommendations must be prioritized by impact, urgency, effort and reversibility. Preserve human judgment: your output structures the decision; it does not make binding legal, medical, financial or employment decisions. Return only the requested structured JSON."""

def load_demo() -> dict[str, Any]:
    return json.loads(DEMO_PATH.read_text(encoding="utf-8"))

def extract_output_text(response: dict[str, Any]) -> str:
    for item in response.get("output", []):
        if item.get("type") == "message":
            for content in item.get("content", []):
                if content.get("type") in ("output_text", "text") and content.get("text"):
                    return content["text"]
    if isinstance(response.get("output_text"), str):
        return response["output_text"]
    raise ValueError("No text output returned by the model")

def build_live_analysis(payload: dict[str, Any]) -> dict[str, Any]:
    if not API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not configured")
    org = str(payload.get("organization", "")).strip()[:200]
    sector = str(payload.get("sector", "")).strip()[:200]
    goal = str(payload.get("goal", "")).strip()[:500]
    website = str(payload.get("website", "")).strip()[:500]
    context = str(payload.get("context", "")).strip()[:15000]
    user_text = f"Organization: {org}\nSector: {sector}\nDecision to enable: {goal}\nPublic URL supplied by user: {website or 'None'}\nStrategic context:\n{context}\n\nAnalyze only the supplied material. Cite uploaded filenames in evidence.source where relevant."
    content: list[dict[str, Any]] = [{"type":"input_text","text":user_text}]
    for f in payload.get("files", [])[:3]:
        name = re.sub(r"[^A-Za-z0-9._ -]", "_", str(f.get("name", "evidence")))[:140]
        mime = str(f.get("type") or mimetypes.guess_type(name)[0] or "application/octet-stream")
        data = str(f.get("data", ""))
        if not data or len(data) > 12_000_000:
            continue
        if mime.startswith("image/"):
            content.append({"type":"input_image","image_url":f"data:{mime};base64,{data}","detail":"high"})
        else:
            content.append({"type":"input_file","file_data":data,"filename":name})
    body = {
      "model": MODEL,
      "store": False,
      "reasoning": {"effort":"medium"},
      "instructions": DEVELOPER_PROMPT,
      "input": [{"role":"user","content":content}],
      "text": {"format":{"type":"json_schema","name":"nous_intelligence_room","description":"Evidence-backed strategic diagnosis and 90-day decision roadmap.","strict":True,"schema":SCHEMA},"verbosity":"medium"}
    }
    req = urllib.request.Request("https://api.openai.com/v1/responses", data=json.dumps(body).encode("utf-8"), headers={"Authorization":f"Bearer {API_KEY}","Content-Type":"application/json","User-Agent":"NOUS-Intelligence-Rooms/1.0"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            response = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")[:2000]
        raise RuntimeError(f"OpenAI API error {e.code}: {detail}") from e
    analysis = json.loads(extract_output_text(response))
    analysis.setdefault("meta", {})["mode"] = "live"
    analysis["meta"]["model"] = MODEL
    return analysis

class Handler(SimpleHTTPRequestHandler):
    def translate_path(self, path: str) -> str:
        clean = path.split("?",1)[0].split("#",1)[0]
        if clean == "/": clean = "/index.html"
        if clean.startswith("/static/"):
            return str(STATIC / clean.removeprefix("/static/"))
        return str(STATIC / clean.lstrip("/"))
    def send_json(self, data: Any, status: int=200) -> None:
        raw = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status);self.send_header("Content-Type","application/json; charset=utf-8");self.send_header("Content-Length",str(len(raw)));self.send_header("Cache-Control","no-store");self.end_headers();self.wfile.write(raw)
    def do_GET(self) -> None:
        if self.path.startswith("/api/health"):
            self.send_json({"ok":True,"live_available":bool(API_KEY),"model":MODEL,"privacy":"Responses API store=false"});return
        super().do_GET()
    def do_POST(self) -> None:
        if self.path != "/api/analyze": self.send_json({"error":"Not found"},404);return
        try:
            length = int(self.headers.get("Content-Length","0"))
            if length > 30_000_000: raise ValueError("Request too large")
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            use_live = bool(payload.get("use_live")) and bool(API_KEY)
            if use_live:
                try:
                    analysis = build_live_analysis(payload);mode="live"
                except Exception as live_error:
                    analysis = load_demo();analysis["organization"] = payload.get("organization") or analysis["organization"];analysis["sector"] = payload.get("sector") or analysis["sector"];analysis["decision"] = payload.get("goal") or analysis["decision"];analysis["meta"]["fallback_reason"] = str(live_error);mode="demo-fallback"
            else:
                analysis=load_demo();analysis["organization"] = payload.get("organization") or analysis["organization"];analysis["sector"] = payload.get("sector") or analysis["sector"];analysis["decision"] = payload.get("goal") or analysis["decision"];mode="demo"
            self.send_json({"analysis":analysis,"mode":mode})
        except Exception as e:
            self.send_json({"error":str(e)},400)
    def log_message(self, fmt: str, *args: Any) -> None:
        sys.stdout.write("[NOUS] "+fmt%args+"\n")

if __name__ == "__main__":
    os.chdir(STATIC)
    print(f"NOUS Intelligence Rooms running at http://127.0.0.1:{PORT}")
    print(f"Mode: {'live-capable' if API_KEY else 'demo'} | Model: {MODEL}")
    ThreadingHTTPServer(("0.0.0.0",PORT),Handler).serve_forever()
