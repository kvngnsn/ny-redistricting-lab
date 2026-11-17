"""Validate and package a selected, exactly balanced statewide-margin result."""
import argparse,csv,gzip,json,shutil
import numpy as np
from scipy.sparse import load_npz
from scipy.optimize import linear_sum_assignment
from common import CACHE,ROOT,write_json
from validate import validate,ISLAND_EXCEPTIONS
from equalize import metrics

def main():
    p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--before',required=True);p.add_argument('--runs',nargs='+',required=True);args=p.parse_args()
    b=np.load(CACHE/'blocks.npz');v=np.load(CACHE/'votes.npy');g=load_npz(CACHE/'graph.npz');a=np.load(CACHE/f'{args.input}.npy');original=np.load(CACHE/args.before)
    overlap=np.zeros((26,26),np.int64);np.add.at(overlap,(a,b['baseline']),b['pop']);old,new=linear_sum_assignment(-overlap);mapping=np.empty(26,np.int16);mapping[old]=new
    a=mapping[a];islands=np.isin(b['ids'],ISLAND_EXCEPTIONS);a[islands]=b['baseline'][islands]
    audit=validate(a,b,v,g);assert audit['constraints_pass'];assert audit['democratic_leads_by_election'][-1]==26
    fit=metrics(a,b['pop'],v[:,-1,0],v[:,-1,1]);np.save(CACHE/'statewide.npy',a)
    np.save(ROOT/'research/checkpoints/statewide-before-balance.npy',original)
    with gzip.open(ROOT/'research/checkpoints/statewide-finish.csv.gz','wt',newline='') as f:
        w=csv.writer(f);w.writerow(['block_index','district_zero_based']);w.writerows((int(i),int(a[i])) for i in np.flatnonzero(a!=original))
    folder=ROOT/'research/equalization';folder.mkdir(exist_ok=True)
    runs=[]
    for name in args.runs:
        prefix='equalize-' if (CACHE/f'equalize-{name}-log.json').exists() else ''
        logpath=CACHE/f'{prefix}{name}-log.json';configpath=CACHE/f'{prefix}{name}-config.json'
        log=json.loads(logpath.read_text());config=json.loads(configpath.read_text())
        # Preserve the exact numerical start of every retained stage.
        init=config['init'];shutil.copyfile(CACHE/init,folder/f'{name}-start.npy')
        config['init']=f'{name}-start.npy'
        config.setdefault('slack',.02);config.setdefault('end_slack',.01);config.setdefault('zero_vote_skip',0.)
        write_json(folder/f'{name}-config.json',config);shutil.copyfile(logpath,folder/f'{name}-log.json')
        runs.append({'name':name,'completed_rounds':len(log),'scheduled_rounds':config['rounds'],'best_unbalanced_gap_pp':min(r['maximum_error_pp'] for r in log)})
    shutil.copyfile(CACHE/f'balance-{args.input}-log.json',folder/'balance-log.json')
    shutil.copyfile(CACHE/'fine.npz',folder/'fine.npz');shutil.copyfile(CACHE/'fine-graph.npz',folder/'fine-graph.npz')
    old_plan=np.load(CACHE/'candidate.npy');before=metrics(old_plan,b['pop'],v[:,-1,0],v[:,-1,1])
    report={'objective':'2024 district margins close to the statewide two-party margin','source_election':'24_PRES','target_margin_pp':fit['statewide_margin']*100,'selected_input':args.input,'final':fit,'original_sweep':before,'maximum_gap_reduction_percent':100*(1-fit['maximum_error_pp']/before['maximum_error_pp']),'constraints_pass':True,'exact_ratio_arithmetic':{'state_dem':int(v[:,-1,0].sum()),'state_rep':int(v[:,-1,1].sum()),'gcd':int(np.gcd(v[:,-1,0].sum(),v[:,-1,1].sum())),'positive_vote_districts':26,'exact_equality_possible':False},'retained_runs':runs,'optimality_proven':False}
    write_json(folder/'result.json',report);print(json.dumps(report),flush=True)
if __name__=='__main__':main()
