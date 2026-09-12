import argparse,json,re
from pathlib import Path
from datetime import datetime,timezone
BEATS=["hook","primary_visual","technical_explanation","evidence","context","why_it_matters","what_next"]
KEYWORDS={"hook":["new","launch","announce","breakthrough"],"primary_visual":["exoskeleton","robot","system","device","product"],"technical_explanation":["ai","compute","chip","processor","sensor","control","technology"],"evidence":["test","research","clinical","demo","result"],"context":["industry","healthcare","market","facility","partner"],"why_it_matters":["impact","benefit","performance","scale","capacity"],"what_next":["future","next","plan","will","build"]}
THEME=["exoskeleton","robot","robotics","rehab","rehabilitation","medical","healthcare","human","wearable"]
GRAPHICS=["hook","headline","fact","mechanism","component","evidence","metric","impact","context","comparison","next_step","source"]

def _contains_term(text, needle):
 return re.search(r'\b' + re.escape(str(needle)) + r'\b', text) is not None

def story_subject_tags(story):
 text=" ".join(str(story.get(k,"")) for k in ("title","summary","description","script","domain","topic","subjects","subject_tags")).lower()
 rules={"exoskeleton":("exoskeleton","rehabilitation","rehab","wearable robot","medical robot"),"robotics":("robotics","robot","humanoid","robotic"),"healthcare":("healthcare","medical","clinical","patient","hospital"),"chips":("chip","processor","semiconductor","silicon","accelerator","gpu","npu","cpu"),"networking":("network","networking","ethernet","switch","router","connectivity","optical"),"cloud":("cloud","sovereign cloud","cloud infrastructure","data center","datacenter"),"cybersecurity":("security","cybersecurity","identity","authentication","authorization","iam"),"ai-agents":("ai agent","ai agents","agentic ai","autonomous agent","autonomous ai"),"generative-ai":("generative ai","genai","llm","large language model"),"quantum":("quantum","qubit"),"storage":("storage","ssd","memory","dram","nand"),"data-centers":("data center","datacenter","server","servers")}
 return {tag for tag,needles in rules.items() if any(_contains_term(text, n) for n in needles)}

def asset_subject_tags(asset):
 tags={str(x).lower() for x in asset.get("subject_tags",[]) if str(x).strip()}
 if tags: return tags
 text=" ".join(str(asset.get(k,"")) for k in ("asset_id","description","attribution","usage_basis","source_url")).lower()
 if any(_contains_term(text, x) for x in ("exoskeleton","rehab","robot","robotics","medical")): tags.update({"exoskeleton","robotics","healthcare"})
 return tags

def semantic_relevance(story,asset):
 st=story_subject_tags(story); at=asset_subject_tags(asset)
 if not st: return False,"no explicit story subject identified; reusable subject-specific asset is blocked"
 exclusive={"exoskeleton","quantum","chips","networking","cloud","cybersecurity","storage"}
 blocked=[tag for tag in exclusive if tag in at and tag not in st]
 if blocked: return False,f"exclusive subject mismatch: required={blocked} story={sorted(st)} asset={sorted(at)}"
 overlap=sorted(st & at)
 return (True,f"subject match: {overlap}") if overlap else (False,f"subject mismatch: story={sorted(st)} asset={sorted(at)}")

def score(a,beat,title):
 d=(a.get("description","")+" "+a.get("asset_id","")+" "+a.get("attribution","")).lower(); priority=int(a.get("production_priority", 100 if a.get("asset_type")=="subject_footage" else 0)); quality=int(a.get("source_window_quality_score", 0)); return priority+2*quality+sum(k in d for k in KEYWORDS[beat])+3*(a.get("editorial_beat")==beat)
def _split_script_sentences(text):
 text=re.sub(r"\s+"," ",str(text or "")).strip()
 if not text: return []
 parts=re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(])",text)
 return [p.strip() for p in parts if p.strip()]

def extract_story_beats(story):
 labels=(("hook","hook"),("context","context"),("what_happened","what_happened"),("why_it_matters","why_it_matters"),("whats_next","whats_next"))
 beats=[]
 for key,arc in labels:
  value=story.get(key)
  if isinstance(value,str) and value.strip():
   beats.append({"beat_id":f"beat-{len(beats)+1:02d}","arc":arc,"text":value.strip(),"source":key})
 if len(beats)==5: return beats
 raw=story.get("script") or story.get("summary") or story.get("description") or story.get("title") or "Technology story"
 parts=_split_script_sentences(raw) or [str(story.get("title") or "Technology story")]
 arc_names=["hook","context","what_happened","why_it_matters","whats_next"]
 if len(parts)>=5:
  selected=parts[:4]+[" ".join(parts[4:])]
 else:
  selected=parts
  arc_names=arc_names[:len(selected)]
 return [{"beat_id":f"beat-{i+1:02d}","arc":arc_names[i],"text":text,"source":"script"} for i,text in enumerate(selected)]

def story_sentences(story):
 raw=str(story.get("script") or story.get("summary") or story.get("description") or story.get("title") or "")
 return _split_script_sentences(raw) or [str(story.get("title") or "Technology story")]

def graphic_detail(story,beat,index):
 title=str(story.get("title") or "Technology story")
 sentences=story_sentences(story); sentence=sentences[index % len(sentences)]
 labels={"hook":"Story focus","primary_visual":"What the story is about","technical_explanation":"How the technology works","evidence":"Reported evidence","context":"Business context","why_it_matters":"Why it matters","what_next":"What happens next"}
 return f"{labels.get(beat,beat)}: {sentence}. Subject: {title}"
def main():
 ap=argparse.ArgumentParser(); ap.add_argument("--package",required=True); ap.add_argument("--library",required=True); ap.add_argument("--output",required=True); a=ap.parse_args(); p=json.loads(Path(a.package).read_text(encoding="utf-8-sig")); lib=json.loads(Path(a.library).read_text(encoding="utf-8-sig")); story=dict(p.get("story",{})); story["script"]=p.get("script") or story.get("script") or story.get("summary") or story.get("description") or ""
 candidates=[x for x in lib.get("assets",[]) if x.get("rights_checked") and x.get("rights_status") in {"EDITORIAL_ALLOWED","LOCAL_TEST_ONLY","REPOSITORY_ASSET","CC_BY_3.0","CC_BY_4.0","PUBLIC_DOMAIN"} and x.get("local_path") and x.get("source_url") and x.get("usage_basis")]
 relevant=[]; rejected=[]
 for x in candidates:
  ok,reason=semantic_relevance(story,x); (relevant if ok else rejected).append(x if ok else {"asset_id":x.get("asset_id"),"reason":reason})
 used=set(); slots=[]; graphic_index=0
 story_beats=extract_story_beats(story)
 for beat_index,beat in enumerate(BEATS):
  beat_record=story_beats[beat_index % len(story_beats)]
  ranked=sorted(((score(x,beat,story.get("title","")),x) for x in relevant if x["asset_id"] not in used),reverse=True,key=lambda z:(z[0],z[1].get("asset_id","")))
  if ranked:
   s,x=ranked[0]; used.add(x["asset_id"]); slots.append({"beat":beat,"beat_id":beat_record["beat_id"],"arc":beat_record["arc"],"script_line":beat_record["text"],"asset_type":"library_asset","asset_id":x["asset_id"],"local_path":x["local_path"],"source_url":x["source_url"],"rights_status":x["rights_status"],"rights_checked":True,"usage_basis":x["usage_basis"],"attribution":x.get("attribution",""),"asset_url":x.get("asset_url"),"attribution_required":x.get("attribution_required",True),"sha256":x.get("sha256"),"match_score":s,"subject_match":True,"match_reason":semantic_relevance(story,x)[1],"source_start":x.get("source_start",0),"source_window_quality":x.get("source_window_quality","UNREVIEWED"),"source_window_quality_score":x.get("source_window_quality_score",0),"source_window_duration_seconds":x.get("source_window_duration_seconds")})
  else:
   kind=GRAPHICS[graphic_index]; slots.append({"beat":beat,"beat_id":beat_record["beat_id"],"arc":beat_record["arc"],"script_line":beat_record["text"],"asset_type":"original_graphic","graphic_kind":kind,"graphic_text":beat_record["text"],"asset_id":None,"rights_status":"N/A","subject_match":True,"match_reason":"exact script-line visualization; no semantically relevant reusable asset"}); graphic_index+=1
 while len(slots)<12:
  idx=len(slots); beat=BEATS[idx%len(BEATS)]; beat_record=story_beats[idx%len(story_beats)]
  ranked=sorted(((score(x,beat,story.get("title","")),x) for x in relevant if x["asset_id"] not in used),reverse=True,key=lambda z:(z[0],z[1].get("asset_id","")))
  if ranked:
   s,x=ranked[0]; used.add(x["asset_id"]); slots.append({"beat":beat,"beat_id":beat_record["beat_id"],"arc":beat_record["arc"],"script_line":beat_record["text"],"asset_type":"library_asset","asset_id":x["asset_id"],"local_path":x["local_path"],"source_url":x["source_url"],"rights_status":x["rights_status"],"rights_checked":True,"usage_basis":x["usage_basis"],"attribution":x.get("attribution",""),"asset_url":x.get("asset_url"),"attribution_required":x.get("attribution_required",True),"sha256":x.get("sha256"),"match_score":s,"subject_match":True,"match_reason":semantic_relevance(story,x)[1],"source_start":x.get("source_start",0),"source_window_quality":x.get("source_window_quality","UNREVIEWED"),"source_window_quality_score":x.get("source_window_quality_score",0),"source_window_duration_seconds":x.get("source_window_duration_seconds")})
  else:
   kind=GRAPHICS[graphic_index]; slots.append({"beat":beat,"beat_id":beat_record["beat_id"],"arc":beat_record["arc"],"script_line":beat_record["text"],"asset_type":"original_graphic","graphic_kind":kind,"graphic_text":beat_record["text"],"asset_id":None,"rights_status":"N/A","subject_match":True,"match_reason":"exact script-line visualization; no qualifying subject footage remaining"}); graphic_index+=1
 out={"status":"SUCCESS","stage":"M4.5-V15-REUSABLE-LIBRARY-SELECTOR-V05-STORY-SPECIFIC-GRAPHICS","created_at_utc":datetime.now(timezone.utc).isoformat(),"story":story,"slots":slots,"library_candidates":len(candidates),"library_selected":sum(s["asset_type"]=="library_asset" for s in slots),"original_graphics":sum(s["asset_type"]=="original_graphic" for s in slots),"coverage_count":len(slots),"required_count":len(slots),"rights_review_required":False,"story_subject_tags":sorted(story_subject_tags(story)),"library_subject_rejected":rejected,"semantic_asset_gate":"HARD_REJECT_ON_SUBJECT_MISMATCH","story_specific_graphics":True,"narrative_arc":[b["arc"] for b in story_beats],"story_beats":story_beats}; q=Path(a.output); q.parent.mkdir(parents=True,exist_ok=True); q.write_text(json.dumps(out,indent=2,ensure_ascii=False),encoding="utf-8"); print(json.dumps({k:out[k] for k in ["status","library_candidates","library_selected","original_graphics","coverage_count","story_specific_graphics"]},indent=2))
if __name__=="__main__": main()

