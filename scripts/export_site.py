"""Publish compact explorer assets plus complete, reusable block assignments."""
import argparse
import csv
import gzip
import json
import hashlib
import shutil
import numpy as np
import pandas as pd
import geopandas as gpd
import shapely
from scipy.sparse import load_npz
from common import ROOT,CACHE,PUBLIC,write_json
from validate import validate

def geometry_export(blocks,assignment,name):
    features=[];bboxes={}
    for district in range(26):
        geometries=blocks.geometry.to_numpy()[assignment==district]
        shape=shapely.union_all(geometries)
        bbox=shapely.bounds(shape).tolist();bboxes[district+1]=bbox
        # Display-only topology-preserving simplification. Exact block assignments
        # and full-resolution source geometry remain the analytical authority.
        simplified=shapely.simplify(shape,.00065,preserve_topology=True)
        features.append({'type':'Feature','id':district+1,'properties':{'district':district+1},'geometry':json.loads(shapely.to_geojson(simplified))})
        print('Export',name,district+1,flush=True)
    write_json(PUBLIC/f'{name}.geojson',{'type':'FeatureCollection','name':f'New York {name}; display simplification only','features':features})
    return bboxes

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--units',action='store_true');parser.add_argument('--reuse-geometry',action='store_true');args=parser.parse_args()
    block=np.load(CACHE/'blocks.npz');blocks=pd.read_pickle(CACHE/'blocks.pkl');votes=np.load(CACHE/'votes.npy');graph=load_npz(CACHE/'graph.npz')
    elections=json.loads((CACHE/'elections.json').read_text());coverage=json.loads((CACHE/'nyt-allocation-audit.json').read_text())
    plan_specs=[('candidate','2024 sweep',np.load(CACHE/'candidate.npy')),('stress','Historical stress search',np.load(CACHE/'stress.npy')),('reference','2024 adopted map',block['baseline'])]
    if (CACHE/'statewide.npy').exists():plan_specs.insert(0,('statewide','Statewide margin search',np.load(CACHE/'statewide.npy')))
    previous=json.loads((PUBLIC/'summary.json').read_text()) if args.reuse_geometry else None
    plans=[];audits={}
    for name,title,assignment in plan_specs:
        audit=validate(assignment,block,votes,graph);audits[name]=audit
        old=next((p for p in previous['plans'] if p['id']==name),None) if previous else None
        same=False
        if old:
            with gzip.open(PUBLIC/old['assignments'],'rt') as f:existing=np.array([int(r['district'])-1 for r in csv.DictReader(f)],np.int16)
            same=np.array_equal(existing,assignment)
        bbox={d['id']:d['bbox'] for d in old['districts']} if same else geometry_export(blocks,assignment,name)
        if not same:
            with gzip.open(PUBLIC/f'{name}-block-assignments.csv.gz','wt',newline='') as f:
                writer=csv.writer(f);writer.writerow(['GEOID20','district'])
                writer.writerows(zip(block['ids'],assignment+1))
        districts=audit['districts']
        for d in districts:d['bbox']=bbox[d['id']]
        plans.append({'id':name,'name':title,'description':'Targets the statewide 2024 two-party margin in every district. The remaining gap is reported explicitly; this finite search does not establish an optimum.' if name=='statewide' else 'Optimized for Democratic leads in all 26 districts in the modeled 2024 presidential vote. Earlier elections are stress tests, not guarantees.' if name=='candidate' else 'Optimized against each district’s weakest margin across all 13 elections. The displayed result is a finite search, not a proof of optimality.' if name=='stress' else 'Official February 28, 2024 congressional block assignments, evaluated using the same historical election panel.','file':f'{name}.geojson','assignments':f'{name}-block-assignments.csv.gz','validation':{k:v for k,v in audit.items() if k!='districts'},'districts':districts})
    summary={'schema_version':1,'state':'New York','built_date':'2026-11-17','blocks':len(block['ids']),'population':int(block['pop'].sum()),'district_count':26,'elections':elections,'plans':plans,'coverage':coverage,'source_vtd_count':14191,'source_precinct_count_2024':12984,'data_notice':'MIT applies to software only. DRA-derived historical data: CC BY-SA 4.0 plus no sale. NYT 2024 data and derived results: C-UDA, noncommercial with attribution. See docs/DATA-LICENSES.md.'}
    write_json(PUBLIC/'summary.json',summary);write_json(PUBLIC/'validation.json',audits)
    if args.units or not (PUBLIC/'voting-units.geojson').exists():
        v=pd.read_pickle(CACHE/'vtd.pkl');index={gid:i for i,gid in enumerate(v.GEOID20)}
        group=np.array([index[g] for g in block['vtd']])
        totals=np.zeros((len(v),votes.shape[1],3),np.int64);np.add.at(totals,group,votes)
        populations=np.bincount(group,weights=block['pop']).astype(int)
        features=[]
        for i,row in v.iterrows():
            props={'geoid':row.GEOID20,'population':int(populations[i])}
            for e in range(votes.shape[1]):
                d,r=totals[i,e,:2];props[f'm{e}']=round(100*float(d-r)/(d+r),3) if d+r else None
            features.append({'type':'Feature','properties':props,'geometry':json.loads(shapely.to_geojson(shapely.simplify(row.geometry,.0008,preserve_topology=True)))})
        write_json(PUBLIC/'voting-units.geojson',{'type':'FeatureCollection','features':features})
    write_json(PUBLIC/'source-manifest.json',json.loads((CACHE/'downloads.json').read_text()))
    research=ROOT/'research';research.mkdir(exist_ok=True)
    for filename in ['recombination-log.json','recombination-sweep-log.json','balance-sweep-log.json','balance-stress-log.json']:
        shutil.copyfile(CACHE/filename,research/filename)
    for filename in ['geometry-audit.json','nyt-allocation-audit.json']:
        shutil.copyfile(CACHE/filename,research/filename)
    for path in PUBLIC.glob('*'):
        if path.is_file():print(path.name,path.stat().st_size,flush=True)

if __name__=='__main__':main()
