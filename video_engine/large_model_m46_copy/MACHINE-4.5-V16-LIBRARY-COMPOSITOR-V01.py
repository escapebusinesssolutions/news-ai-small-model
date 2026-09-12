import argparse,json,subprocess,tempfile,re,unicodedata
from pathlib import Path
W,H=1080,1920; FONT='/Windows/Fonts/AGENCYB.TTF'; FONT2='/Windows/Fonts/AGENCYR.TTF'

def run(c): subprocess.run([str(x) for x in c],check=True)
def dur(p): return float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1',str(p)],text=True))
def esc(s):
 s=unicodedata.normalize('NFKD',str(s or '')).encode('ascii','ignore').decode('ascii')
 s=s.replace('\\','/').replace("'",'').replace(':',' - ').replace(',',' - ').replace('%','%%')
 return s.replace('[','(').replace(']',')').replace(';',' - ').replace('\n',' ').replace('=',' - ').replace('#',' - ')
def text(s,width=24):
 s=esc(str(s or '')); words=s.split(); lines=[]; line=''
 for word in words:
  if line and len(line)+1+len(word)>width: lines.append(line); line=word
  else: line=(line+' '+word).strip()
 if line: lines.append(line)
 return '\n'.join(lines)

def fit_text(s,width_chars,height_px,base_size,min_size=16,spacing=10):
 for size in range(base_size,min_size-1,-1):
  chars=max(8,int(width_chars*base_size/size))
  wrapped=text(s,chars)
  lines=wrapped.count('\n')+1 if wrapped else 1
  line_h=int(size*1.2)+spacing
  if lines*line_h <= height_px:
   return wrapped,size,spacing
 return text(s,max(8,int(width_chars*base_size/min_size))),min_size,spacing

def overlay(title,beat):
 beat_t,beat_sz,_=fit_text(beat.upper(),18,32,25,18,4)
 title_t,title_sz,title_sp=fit_text(title,24,112,30,18,4)
 return f"drawbox=x=38:y=38:w=1004:h=235:color=0x07111e@0.72:t=fill,drawtext=fontfile={FONT}:text='{beat_t}':fontcolor=0x55d8ff:fontsize={beat_sz}:x=66:y=58,drawtext=fontfile={FONT}:text='{title_t}':fontcolor=white:fontsize={title_sz}:x=66:y=92:line_spacing={title_sp},drawtext=fontfile={FONT2}:text='EVOLUTION TECHNOLOGY':fontcolor=0x8aa8bd:fontsize=22:x=60:y=1840"

GRAPHIC_KINDS=['hook','headline','fact','mechanism','component','evidence','metric','impact','context','comparison','next_step','source']

def graphic(title,beat,kind,detail):
 t,tfs,tsp=fit_text(title,24,430,44,18,6)
 d,d_fs,d_sp=fit_text(detail,22,220,31,16,8)
 label=text(kind.replace('_',' ').upper(),28)
 common=f"color=c=0x081522:s={W}x{H}:r=25,{overlay(title,beat)}"
 layouts={
 'hook':f"drawbox=x=90:y=430:w=900:h=820:color=0x10283a:t=fill,drawtext=fontfile={FONT}:text='{label}':fontcolor=0x55d8ff:fontsize=30:x=145:y=505,drawtext=fontfile={FONT2}:text='{d}':fontcolor=white:fontsize={d_fs}:x=145:y=610:line_spacing={d_sp}",
 'headline':f"drawbox=x=80:y=470:w=920:h=700:color=0x10283a:t=fill,drawtext=fontfile={FONT}:text='WHAT CHANGED':fontcolor=0xffad55:fontsize=34:x=125:y=540,drawtext=fontfile={FONT2}:text='{d}':fontcolor=white:fontsize={d_fs}:x=125:y=640:line_spacing={d_sp}",
 'fact':f"drawbox=x=180:y=520:w=720:h=760:color=0x10283a:t=fill,drawtext=fontfile={FONT}:text='FACT':fontcolor=0x55d8ff:fontsize=52:x=430:y=600,drawtext=fontfile={FONT2}:text='{d}':fontcolor=white:fontsize={d_fs}:x=240:y=730:line_spacing={d_sp}",
 'mechanism':f"drawbox=x=100:y=480:w=880:h=210:color=0x10283a:t=fill,drawbox=x=100:y=820:w=250:h=210:color=0x10283a:t=fill,drawbox=x=415:y=820:w=250:h=210:color=0x10283a:t=fill,drawbox=x=730:y=820:w=250:h=210:color=0x10283a:t=fill,drawtext=fontfile={FONT}:text='INPUT':fontcolor=white:fontsize=34:x=170:y=900,drawtext=fontfile={FONT}:text='CONTROL':fontcolor=white:fontsize=34:x=455:y=900,drawtext=fontfile={FONT}:text='OUTCOME':fontcolor=white:fontsize=31:x=755:y=900,drawtext=fontfile={FONT2}:text='{d}':fontcolor=white:fontsize={d_fs}:x=125:y=1080:line_spacing={d_sp}",
 'component':f"drawbox=x=140:y=500:w=800:h=800:color=0x10283a:t=fill,drawbox=x=210:y=590:w=220:h=160:color=0x55d8ff:t=fill,drawbox=x=430:y=590:w=220:h=160:color=0xffad55:t=fill,drawbox=x=650:y=590:w=220:h=160:color=0x8aa8bd:t=fill,drawtext=fontfile={FONT}:text='1':fontcolor=0x081522:fontsize=70:x=290:y=625,drawtext=fontfile={FONT}:text='2':fontcolor=0x081522:fontsize=70:x=510:y=625,drawtext=fontfile={FONT}:text='3':fontcolor=0x081522:fontsize=70:x=730:y=625,drawtext=fontfile={FONT2}:text='{d}':fontcolor=white:fontsize={d_fs}:x=190:y=820:line_spacing={d_sp}",
 'evidence':f"drawbox=x=120:y=470:w=840:h=940:color=0x10283a:t=fill,drawbox=x=180:y=560:w=720:h=16:color=0x55d8ff:t=fill,drawtext=fontfile={FONT}:text='EVIDENCE':fontcolor=white:fontsize=50:x=180:y=520,drawtext=fontfile={FONT2}:text='{d}':fontcolor=white:fontsize={d_fs}:x=180:y=680:line_spacing={d_sp}",
 'metric':f"drawtext=fontfile={FONT}:text='MEASURE':fontcolor=0x55d8ff:fontsize=34:x=120:y=500,drawtext=fontfile={FONT}:text='{d}':fontcolor=white:fontsize={min(d_fs+12,58)}:x=120:y=610:line_spacing={d_sp},drawbox=x=120:y=1050:w=800:h=30:color=0x10283a:t=fill,drawbox=x=120:y=1050:w=560:h=30:color=0x55d8ff:t=fill",
 'impact':f"drawbox=x=120:y=480:w=840:h=820:color=0x10283a:t=fill,drawbox=x=250:y=650:w=580:h=420:color=0x55d8ff:t=fill,drawbox=x=330:y=730:w=420:h=260:color=0x081522:t=fill,drawtext=fontfile={FONT}:text='IMPACT':fontcolor=white:fontsize=52:x=405:y=780,drawtext=fontfile={FONT2}:text='{d}':fontcolor=white:fontsize={d_fs}:x=150:y=1110:line_spacing={d_sp}",
 'context':f"drawbox=x=90:y=480:w=900:h=180:color=0x10283a:t=fill,drawbox=x=90:y=720:w=280:h=520:color=0x10283a:t=fill,drawbox=x=400:y=720:w=280:h=520:color=0x10283a:t=fill,drawbox=x=710:y=720:w=280:h=520:color=0x10283a:t=fill,drawtext=fontfile={FONT}:text='WHY':fontcolor=0x55d8ff:fontsize=34:x=130:y=535,drawtext=fontfile={FONT}:text='NOW':fontcolor=0xffad55:fontsize=34:x=450:y=535,drawtext=fontfile={FONT}:text='NEXT':fontcolor=white:fontsize=34:x=760:y=535,drawtext=fontfile={FONT2}:text='{d}':fontcolor=white:fontsize={d_fs}:x=125:y=800:line_spacing={d_sp}",
 'comparison':f"drawbox=x=100:y=500:w=390:h=720:color=0x10283a:t=fill,drawbox=x=590:y=500:w=390:h=720:color=0x10283a:t=fill,drawtext=fontfile={FONT}:text='BEFORE':fontcolor=0x8aa8bd:fontsize=38:x=160:y=570,drawtext=fontfile={FONT}:text='NOW':fontcolor=0x55d8ff:fontsize=38:x=700:y=570,drawtext=fontfile={FONT2}:text='{d}':fontcolor=white:fontsize={max(16,d_fs-2)}:x=125:y=690:line_spacing={d_sp},drawtext=fontfile={FONT}:text='Enterprise planning':fontcolor=white:fontsize=28:x=625:y=700,drawtext=fontfile={FONT2}:text='Quantum risk is entering planning workflows.':fontcolor=white:fontsize=20:x=625:y=770:line_spacing=5",
 'next_step':f"drawbox=x=140:y=480:w=800:h=900:color=0x10283a:t=fill,drawbox=x=210:y=600:w=160:h=160:color=0x55d8ff:t=fill,drawbox=x=460:y=800:w=160:h=160:color=0xffad55:t=fill,drawbox=x=710:y=1000:w=160:h=160:color=0x8aa8bd:t=fill,drawbox=x=370:y=675:w=100:h=8:color=white:t=fill,drawbox=x=620:y=875:w=100:h=8:color=white:t=fill,drawtext=fontfile={FONT}:text='1':fontcolor=0x081522:fontsize=70:x=265:y=625,drawtext=fontfile={FONT}:text='2':fontcolor=0x081522:fontsize=70:x=515:y=825,drawtext=fontfile={FONT}:text='3':fontcolor=0x081522:fontsize=70:x=765:y=1025,drawtext=fontfile={FONT2}:text='{d}':fontcolor=white:fontsize={d_fs}:x=170:y=1170:line_spacing={d_sp}",
 'source':f"drawbox=x=100:y=500:w=880:h=900:color=0x10283a:t=fill,drawtext=fontfile={FONT}:text='SOURCE':fontcolor=0x55d8ff:fontsize=50:x=150:y=590,drawtext=fontfile={FONT2}:text='{d}':fontcolor=white:fontsize={d_fs}:x=150:y=760:line_spacing={d_sp}"
 }
 return common+','+layouts[kind]

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--manifest',required=True); ap.add_argument('--voice',required=True); ap.add_argument('--output',required=True); a=ap.parse_args(); m=json.loads(Path(a.manifest).read_text(encoding='utf-8')); voice=Path(a.voice); out=Path(a.output); out.parent.mkdir(parents=True,exist_ok=True); total=dur(voice); slots=m['slots']; sd=total/len(slots)
 with tempfile.TemporaryDirectory(prefix='m45-v16-') as td:
  td=Path(td); segs=[]
  for i,s in enumerate(slots):
   seg=td/f'seg-{i:02}.mp4'; typ=s.get('asset_type'); title=s.get('title') or m.get('story',{}).get('title','Technology story'); beat=s.get('beat','technology')
   if typ=='original_graphic':
    kind=s.get('graphic_kind','hook'); detail=s.get('graphic_text') or s.get('reason','Story-specific explanatory visual'); vf=graphic(title,beat,kind,detail)
    run(['ffmpeg','-y','-f','lavfi','-i',vf,'-vf',f"zoompan=z='1+0.045*sin(on*PI/250)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={W}x{H}:fps=25",'-t',f'{sd:.3f}','-an','-c:v','libx264','-preset','veryfast','-crf','19','-pix_fmt','yuv420p',seg])
   else:
    src=Path(s['local_path']); src=src if src.is_absolute() else Path(__file__).resolve().parent/src; start=float(s.get('source_start',0)); inp=['-loop','1','-framerate','25'] if src.suffix.lower() in {'.jpg','.jpeg','.png','.webp'} else ['-ss',str(start),'-stream_loop','-1']; vf=f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,eq=contrast=1.04:saturation=1.06,{overlay(title,beat)}"; run(['ffmpeg','-y']+inp+['-i',str(src),'-vf',vf,'-t',f'{sd:.3f}','-an','-r','25','-c:v','libx264','-preset','veryfast','-crf','19','-pix_fmt','yuv420p',seg])
   segs.append(seg)
  concat=td/'concat.txt'; concat.write_text('\n'.join("file '%s'"%p.as_posix() for p in segs)); silent=td/'silent.mp4'; run(['ffmpeg','-y','-f','concat','-safe','0','-i',concat,'-c','copy',silent]); run(['ffmpeg','-y','-i',silent,'-i',voice,'-t',f'{total:.3f}','-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','96k','-movflags','+faststart',out])
 print(json.dumps({'status':'SUCCESS','stage':'M4.5-V16-STORY-SPECIFIC-COMPOSITOR','duration_seconds':round(total,3),'segments':len(slots),'output':str(out)},indent=2))
if __name__=='__main__': main()
