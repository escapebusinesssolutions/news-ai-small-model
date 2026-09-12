from pathlib import Path
import argparse,json,subprocess,sys
ROOT=Path(__file__).resolve().parent
SELECTOR=ROOT/'MACHINE-4.5-V15-REUSABLE-LIBRARY-SELECTOR-V01.py'
ACQUIRE=ROOT/'MACHINE-4.5-RIGHTS-AWARE-ASSET-ACQUISITION-V01.py'
COMPOSITOR=ROOT/'MACHINE-4.5-V16-LIBRARY-COMPOSITOR-V01.py'
QC=ROOT/'MACHINE-4.5-V11-VISUAL-QC-GATES-V01.py'

def stage(name,cmd,record):
 p=subprocess.run([str(x) for x in cmd],cwd=ROOT,capture_output=True,text=True)
 record.append({'stage':name,'exit_code':p.returncode,'stdout':p.stdout[-3000:],'stderr':p.stderr[-3000:]})
 if p.returncode: raise RuntimeError(f'{name}:{p.returncode}')

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--package',required=True); ap.add_argument('--voice',required=True); ap.add_argument('--output',required=True); ap.add_argument('--run-dir',required=True); ap.add_argument('--library',default=str(ROOT/'M4.5-V14-REUSABLE-MEDIA-LIBRARY.json')); a=ap.parse_args()
 rd=Path(a.run_dir); rd.mkdir(parents=True,exist_ok=True); stages=[]
 try:
  selected=rd/'selector.json'; stage('V15-REUSABLE-SELECTOR',[sys.executable,SELECTOR,'--package',a.package,'--library',a.library,'--output',selected],stages)
  acquired_dir=rd/'acquired'; acquired=rd/'acquired-manifest.json'; stage('V08-RIGHTS-AWARE-ASSET-ACQUISITION',[sys.executable,ACQUIRE,'--manifest',selected,'--output-dir',acquired_dir,'--output-manifest',acquired],stages)
  stage('V16-LIBRARY-COMPOSITOR',[sys.executable,COMPOSITOR,'--manifest',acquired,'--voice',a.voice,'--output',a.output],stages)
  qc=rd/'visual-qc.json'; stage('V11-VISUAL-QC',[sys.executable,QC,'--manifest',acquired,'--video',a.output,'--output',qc],stages)
  q=json.loads(qc.read_text(encoding='utf-8-sig'))
  if q.get('status')!='PASS': raise RuntimeError('V11-VISUAL-QC:REJECT')
  result={'status':'PASS','failure_code':None,'stages':stages,'output':str(Path(a.output).resolve()),'visual_qc':q,'portable_media':True}
 except Exception as e:
  result={'status':'FAIL','failure_code':str(e),'stages':stages}
 (rd/'run-record.json').write_text(json.dumps(result,indent=2),encoding='utf-8'); print(json.dumps(result,indent=2)); return 0 if result['status']=='PASS' else 2
if __name__=='__main__': raise SystemExit(main())