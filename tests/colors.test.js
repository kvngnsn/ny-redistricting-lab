import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { colorLimit, colorSettings, defaults } from '../src/colors.js';
import { margin } from '../src/model.js';

test('focused scales include all published margins and gaps, across elections and swing extremes', () => {
  const data=JSON.parse(readFileSync(new URL('../public/data/summary.json',import.meta.url)));
  for(const plan of data.plans) for(const [e,election] of data.elections.entries()) for(const swing of [-10,0,10]) {
    const margins=plan.districts.map(d=>margin(d.votes[e],swing));
    const gaps=margins.map(m=>m-margin(election.source_totals,swing));
    for(const [mode,values] of [['margin',margins],['gap',gaps]]) {
      const limit=colorLimit(mode,'focused',values);
      assert.ok(limit>0 && values.every(v=>Math.abs(v)<=limit),`${plan.id} ${election.id} ${mode}`);
    }
  }
  const plan=data.plans.find(p=>p.id==='statewide'), e=data.elections.length-1;
  const gaps=plan.districts.map(d=>margin(d.votes[e])-margin(data.elections[e].source_totals));
  assert.equal(colorLimit('gap','focused',gaps),5,'The ±4.84 pp result must use a readable ±5 scale');
});

test('fixed scales stay comparable; empty or tied views retain a valid symmetric domain', () => {
  for(const values of [[],[0],[null,NaN],[-1,90]]) {
    assert.equal(colorLimit('margin','fixed',values),100);
    assert.equal(colorLimit('gap','fixed',values),200);
    assert.equal(colorLimit('margin','focused',values,true),100);
    assert.ok(colorLimit('margin','focused',values)>0);
  }
  assert.equal(colorLimit('population','focused',[-.115,.885]),1);
  assert.equal(colorLimit('population','fixed',[-1.115,.885]),2);
});

test('malformed or obsolete stored preferences fall back safely', () => {
  for(const value of [null,42,{}, {palette:'__proto__',scale:'old',borders:'bright'}]) assert.deepEqual(colorSettings(value),defaults);
});
