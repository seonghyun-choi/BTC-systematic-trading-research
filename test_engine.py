import unittest,numpy as np
from run import signals,trade,eligible,MINUTE,FUNDING
class Test(unittest.TestCase):
 def test_signal_causality_subset(self):
  fi=np.array([0.,0,0,0,.3,.3,.3,.3,0.,-.3,-.3,-.3]);si=fi.copy();v=np.ones(len(fi),bool)
  x=signals(fi,si,v);self.assertEqual(x['LONG'][0].tolist(),[6]);self.assertEqual(x['SHORT'][0].tolist(),[11])
  for end in [6,8,11]:
   a=signals(fi[:end],si[:end],v[:end]);np.testing.assert_array_equal(a['LONG'][0],x['LONG'][0][x['LONG'][0]<end])
  v[5]=False;self.assertEqual(signals(fi,si,v)['LONG'][0].tolist(),[])
 def test_delayed_entry_lock_and_cost(self):
  grid=np.arange(100)*MINUTE;op=100+np.arange(100)*.1;cf=np.ones(100,bool)
  r,a=trade(np.array([5,6,15]),cf,op,grid,'LONG',5,'SPOT_CONFIRMED')
  self.assertEqual(len(r),2);self.assertEqual(a['locked'],1);self.assertEqual(r[0]['entry_ms'],7*MINUTE);self.assertEqual(r[0]['exit_ms'],12*MINUTE)
  self.assertAlmostEqual(r[0]['fee_bp'],3*(1+op[12]/op[7]));self.assertAlmostEqual(r[0]['net8_bp'],r[0]['gross_bp']-r[0]['fee_bp']-2)
 def test_missing_exit_retained_and_short(self):
  grid=np.arange(50)*MINUTE;op=100-np.arange(50)*.1;op[12]=np.nan;cf=np.ones(50,bool)
  r,a=trade(np.array([5]),cf,op,grid,'SHORT',5,'FUTURES_ONLY');self.assertEqual(r[0]['exit_ms'],13*MINUTE);self.assertGreater(r[0]['gross_bp'],0);self.assertEqual(a['delayed_exit'],1)
  op[12:]=np.nan;r,a=trade(np.array([5]),cf,op,grid,'SHORT',5,'FUTURES_ONLY');self.assertEqual(a['unresolved'],1);self.assertEqual(r[0]['status'],'unresolved')
 def test_common_funding_cutoff(self):
  grid=np.arange(1000)*MINUTE
  self.assertTrue(eligible(np.array([440]),grid)[0]);self.assertFalse(eligible(np.array([448]),grid)[0]);self.assertFalse(eligible(np.array([478]),grid)[0])
if __name__=='__main__':unittest.main()
