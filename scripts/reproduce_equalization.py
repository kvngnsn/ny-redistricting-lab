"""Replay a retained search stage using its saved inputs and exact schedule."""
import argparse,json,shutil,subprocess,sys
from common import ROOT,CACHE
folder=ROOT/'research/equalization'
choices=sorted(p.name.removesuffix('-config.json') for p in folder.glob('*-config.json'))
p=argparse.ArgumentParser();p.add_argument('--stage',choices=choices,required=True);args=p.parse_args()
config=json.loads((folder/f'{args.stage}-config.json').read_text())
subprocess.run([sys.executable,str(ROOT/'scripts/replay.py')],check=True)
for name in ['fine.npz','fine-graph.npz',config['init']]:shutil.copyfile(folder/name,CACHE/name)
config['name']='reproduced-'+args.stage
report=json.loads((folder/'result.json').read_text());stage=next(r for r in report['retained_runs'] if r['name']==args.stage)
config['stop_after']=stage['completed_rounds']
command=[sys.executable,str(ROOT/'scripts/equalize.py')]
for key,value in config.items():
    if value is None or value is False:continue
    command.append('--'+key.replace('_','-'))
    if value is not True:command.append(str(value))
print('Running:', ' '.join(command),flush=True)
subprocess.run(command,check=True)
