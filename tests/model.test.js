import test from 'node:test';
import assert from 'node:assert/strict';
import { voteShare,margin,seatCounts,robustMargin,csvForPlan } from '../src/model.js';

test('two-party margins exclude other votes and swing changes share, not margin',()=>{
  assert.equal(voteShare([60,40,20]),.6);
  assert.ok(Math.abs(margin([60,40,20])-20)<1e-10);
  assert.ok(Math.abs(margin([60,40,20],5)-30)<1e-10);
  assert.equal(voteShare([99,1,0],10),1);
  assert.equal(voteShare([0,0,1]),null);
});
test('ties and missing votes never count as Democratic or Republican wins',()=>{
  const districts=[{votes:[[5,5,0]]},{votes:[[0,0,7]]},{votes:[[6,4,0]]},{votes:[[4,6,0]]}];
  assert.deepEqual(seatCounts(districts,0),{dem:1,rep:1,tie:2});
});
test('a difficult election cannot disappear inside a strong average',()=>{
  assert.ok(robustMargin({votes:[[90,10,0],[49,51,0]]})<0);
});
test('CSV retains raw counts and does not apply a displayed swing scenario',()=>{
  const csv=csvForPlan({districts:[{id:1,population:776971,components:1,votes:[[60,40,5]]}]},[{id:'24_PRES'}]);
  assert.match(csv,/"60","40","5","0.6"/);
});
