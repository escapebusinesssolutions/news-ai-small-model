from __future__ import annotations
import argparse,json,subprocess,re
from pathlib import Path

def run(cmd):
    r=subprocess.run(cmd,capture_output=True,text=True)
    if r.returncode: raise RuntimeError(r.stderr[-1600:])
    return (r.stdout + "\n" + r.stderr).strip()

def duration(p): return float(run(["ffprobe","-v","error","-show_entries","format=duration","-of","default=nw=1:nk=1",str(p)]))

def narrative_arc_check(m):
    required=["hook","context","what_happened","why_it_matters","whats_next"]
    arcs=m.get("narrative_arc") or [b.get("arc") for b in m.get("story_beats",[])]
    return {"required":required,"present":arcs,"pass":all(x in arcs for x in required)}

def segment_relevance_check(slots):
    failures=[]
    for i,s in enumerate(slots):
        if not s.get("beat_id") or not s.get("arc") or not str(s.get("script_line") or "").strip():
            failures.append({"slot":i,"reason":"missing beat_id, arc, or exact script_line"})
        if s.get("asset_type")=="original_graphic" and not str(s.get("graphic_text") or "").strip():
            failures.append({"slot":i,"reason":"story-specific graphic has no exact script-line text"})
    return {"pass":not failures,"failures":failures}

def voice_quality_check(video,m):
    audio=run(["ffprobe","-v","error","-select_streams","a:0","-show_entries","stream=codec_name,sample_rate,channels,bit_rate","-of","json",str(video)])
    data=json.loads(audio); stream=(data.get("streams") or [{}])[0]
    vd=run(["ffmpeg","-hide_banner","-i",str(video),"-af","volumedetect","-f","null","NUL"])
    max_db=re.findall(r"max_volume:\s*([-+0-9.]+) dB",vd)
    mean_db=re.findall(r"mean_volume:\s*([-+0-9.]+) dB",vd)
    max_v=float(max_db[-1]) if max_db else -999
    mean_v=float(mean_db[-1]) if mean_db else -999
    video_duration=duration(video); script_words=sum(len(re.findall(r"\b[\w''-]+\b",str(s.get("script_line") or ""))) for s in m.get("slots",[]))
    return {"pass":bool(stream.get("codec_name") and stream.get("sample_rate") and stream.get("channels") and max_v < -0.1 and mean_v > -45 and video_duration > 0),"audio_stream":stream,"max_volume_db":max_v,"mean_volume_db":mean_v,"manual_listen_through":"required for final acceptance","script_line_word_total":script_words}

def static_hold_check(video):
    out=run(["ffmpeg","-hide_banner","-i",str(video),"-vf","freezedetect=n=-60dB:d=4","-an","-f","null","NUL"])
    starts=[x for x in out.splitlines() if "freeze_start:" in x]
    return {"pass":not starts,"freeze_events":starts}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--manifest",required=True); ap.add_argument("--video",required=True); ap.add_argument("--output",required=True); ap.add_argument("--min-sources",type=int,default=8); ap.add_argument("--min-changes",type=int,default=10); a=ap.parse_args()
    m=json.loads(Path(a.manifest).read_text(encoding="utf-8-sig")); v=Path(a.video); slots=m.get("slots",[])
    visual_keys=[]; rights_missing=[]; repeats=[]
    for s in slots:
        key=("graphic:"+str(s.get("graphic_kind",s.get("beat_id",len(visual_keys))))) if s.get("asset_type")=="original_graphic" else ("asset:"+str(s.get("asset_id")) if s.get("asset_id") else (s.get("local_path") or s.get("source_url")))
        if key: visual_keys.append(key)
        if s.get("asset_type") not in {"original_graphic"} and s.get("rights_status") not in {"EDITORIAL_ALLOWED","LOCAL_TEST_ONLY","REPOSITORY_ASSET","CC_BY_3.0","CC_BY_4.0","PUBLIC_DOMAIN"}: rights_missing.append(s.get("beat"))
        if key in visual_keys[:-1] and not s.get("repeat_reason"): repeats.append({"asset":key,"beat":s.get("beat")})
    black=run(["ffmpeg","-hide_banner","-i",str(v),"-vf","blackdetect=d=0.10:pix_th=0.02","-an","-f","null","NUL"]) if v.exists() else ""
    black_intervals=[x for x in black.splitlines() if "black_start:" in x]
    narrative=narrative_arc_check(m); relevance=segment_relevance_check(slots); voice=voice_quality_check(v,m); motion=static_hold_check(v)
    checks={"video_exists":v.is_file(),"source_count":len(set(visual_keys)),"source_density_pass":len(set(visual_keys))>=a.min_sources,"visual_change_count":len(slots),"density_pass":len(slots)>=a.min_changes,"rights_metadata_pass":not rights_missing,"repeat_pass":not repeats,"black_interval_pass":not black_intervals,"narrative_arc_pass":narrative["pass"],"segment_relevance_pass":relevance["pass"],"voice_quality_preflight_pass":voice["pass"],"static_hold_pass":motion["pass"],"duration_seconds":duration(v) if v.exists() else 0.0}
    checks["overall_pass"]=all(checks[k] for k in ["video_exists","source_density_pass","density_pass","rights_metadata_pass","repeat_pass","black_interval_pass","narrative_arc_pass","segment_relevance_pass","voice_quality_preflight_pass","static_hold_pass"])
    out={"status":"PASS" if checks["overall_pass"] else "REJECT","checks":checks,"new_m46_gates":{"narrative_arc":narrative,"segment_relevance":relevance,"voice_quality":voice,"static_hold":motion},"rights_missing":rights_missing,"repeats":repeats,"black_detect_output":black[:4000]}
    p=Path(a.output); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(out,indent=2,ensure_ascii=False),encoding="utf-8"); print(json.dumps(out,indent=2)); raise SystemExit(0 if checks["overall_pass"] else 2)
if __name__=="__main__": main()
