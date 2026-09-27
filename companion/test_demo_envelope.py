import csv, math, tempfile, unittest
from library import Library, SUPPORTED_BUILD

class DemoEnvelopeTests(unittest.TestCase):
    def test_fast_roll_at_any_recorded_altitude(self):
        with tempfile.TemporaryDirectory() as folder:
            library=Library({'saved_games': folder}, running=lambda: False)
            for altitude in (-50, 0, 76.2, 152.4, 2000, 6000):
                with self.subTest(altitude=altitude):
                    source=library.recordings/'demo.csv'
                    with source.open('w', newline='') as stream:
                        writer=csv.writer(stream)
                        writer.writerows([['DCSREC','1'],['aircraft','FA-18C_hornet'],['theatre','Caucasus'],['livery','Blue Angels Jet Team'],['capture_build',SUPPORTED_BUILD],['wind_ground','0'],['wind_2000','0'],['wind_8000','0']])
                        writer.writerow('t,x,y,z,fx,fy,fz,ux,uy,uz,rx,ry,rz,vx,vy,vz,speedbrake,rpm_left,rpm_right'.split(','))
                        for i in range(301):
                            t=i*.02; c=math.cos(math.pi*t); s=math.sin(math.pi*t)
                            writer.writerow([t,1000+180*t,altitude,500,1,0,0,0,c,s,0,-s,c,180,0,0,0,'',''])
                        writer.writerow(['END','user_stop',301])
                    original=source.read_bytes()
                    entry=library.entries()[0]
                    self.assertTrue(entry['supported'],entry['reason'])
                    self.assertEqual(entry['duration'],6)
                    self.assertEqual(source.read_bytes(),original)

if __name__=='__main__': unittest.main()
