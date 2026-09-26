"""Offline geometric roll study; stdlib only. Not an aircraft flight model."""
import math
import json
from pathlib import Path

G=9.80665
RAD=math.pi/180
START_HEIGHT=2000.0
# Local Hornet descriptor: empty mass 11382 kg, mission fuel 3500 kg,
# inherited reference wing area 37 m2, span 11.43 m. Fuel burn omitted.
MASS=11382+3500
AREA=37.0
SPAN=11.43
# Explicit provisional polar assumptions, not calibrated Hornet performance.
CD0=0.0172
EFFICIENCY=0.8
K=1/(math.pi*(SPAN*SPAN/AREA)*EFFICIENCY)
def density(h):
    temperature=288.15-0.0065*h
    pressure=101325*(temperature/288.15)**(G/(287.05287*0.0065))
    return pressure/(287.05287*temperature)
def drag_acceleration(v,h,n):
    q=0.5*density(h)*v*v
    cl=n*MASS*G/(q*AREA)
    return q*AREA*(CD0+K*cl*cl)/MASS
def smooth(u):
    u=max(0,min(1,u)); return u*u*u*(10+u*(-15+6*u))

def speed(h):
    # Initial 400 KCAS in ISA only; speed thereafter is an integrated state.
    t=288.15-0.0065*h
    p=101325*(t/288.15)**(G/(287.05287*0.0065))
    vc=400*1852/3600
    qc=101325*((1+vc*vc/(5*1.4*287.05287*288.15))**3.5-1)
    return math.sqrt(1.4*287.05287*t*5*((1+qc/p)**(2/7)-1))

def cas(v,h):
    t=288.15-0.0065*h;p=101325*(t/288.15)**(G/(287.05287*0.0065))
    qc=p*((1+v*v/(5*1.4*287.05287*t))**3.5-1)
    return math.sqrt(1.4*287.05287*288.15*5*((1+qc/101325)**(2/7)-1))*3600/1852

def bank(t,a,b,c,cut=300):
    # Monotone cubic Hermite interpolation, zero roll rate at both ends.
    lengths=[a,b,c]; angles=[0,60*RAD,cut*RAD,360*RAD]
    slopes=[(angles[i+1]-angles[i])/lengths[i] for i in range(3)]
    rates=[0]
    for i in range(2):
        w1=2*lengths[i+1]+lengths[i];w2=lengths[i+1]+2*lengths[i]
        rates.append((w1+w2)/(w1/slopes[i]+w2/slopes[i+1]))
    rates.append(0)
    i=0
    while i<2 and t>lengths[i]: t-=lengths[i];i+=1
    u=max(0,min(1,t/lengths[i]));h=lengths[i]
    return -((2*u**3-3*u*u+1)*angles[i]+(u**3-2*u*u+u)*h*rates[i]+(-2*u**3+3*u*u)*angles[i+1]+(u**3-u*u)*h*rates[i+1])

def derivative(t,y,phi,n):
    pitch,heading,x,h,z,v=y
    return [G/v*(n*math.cos(phi)-math.cos(pitch)),G*n*math.sin(phi)/(v*math.cos(pitch)),v*math.cos(pitch)*math.cos(heading),v*math.sin(pitch),v*math.cos(pitch)*math.sin(heading),THRUST_ACCEL-drag_acceleration(v,h,n)-G*math.sin(pitch)]

def rk4(t,y,dt,control):
    def f(t,y): return derivative(t,y,*control(t))
    k1=f(t,y);k2=f(t+dt/2,[v+dt*k/2 for v,k in zip(y,k1)])
    k3=f(t+dt/2,[v+dt*k/2 for v,k in zip(y,k2)]);k4=f(t+dt,[v+dt*k for v,k in zip(y,k3)])
    return [v+dt*(a+2*b+2*c+d)/6 for v,a,b,c,d in zip(y,k1,k2,k3,k4)]

def pull():
    y=[0,0,0,START_HEIGHT,0,speed(START_HEIGHT)];t=0
    control=lambda t:(0,1+0.8*smooth(t/4))
    while y[0]<14*RAD:
        nxt=rk4(t,y,0.01,control)
        if nxt[0]>=14*RAD:
            dt=0.01*(14*RAD-y[0])/(nxt[0]-y[0]);y=rk4(t,y,dt,control);t+=dt;break
        y=nxt;t+=0.01
    return t,y

THRUST_ACCEL=drag_acceleration(speed(START_HEIGHT),START_HEIGHT,1)
PULL_TIME,ENTRY=pull()
def simulate(a,b,c,cut=300,dt=0.025,collect=False):
    y=ENTRY[:];t=0;peak=y[0];low=y[0];rows=[]
    end=a+b+c
    def control(t): return bank(t,a,b,c,cut),1.8-0.8*smooth((t-end+6)/6)
    while t<end-1e-9:
        step=min(dt,end-t);y=rk4(t,y,step,control);t+=step
        peak=max(peak,y[0]);low=min(low,y[0])
        if collect: rows.append([t,*y,*control(t)])
    return peak/RAD,y[0]/RAD,low/RAD,y,rows

def linear_solve(matrix,rhs):
    a=[list(row)+[value] for row,value in zip(matrix,rhs)]
    for k in range(len(a)):
        pivot=max(range(k,len(a)),key=lambda i:abs(a[i][k]));a[k],a[pivot]=a[pivot],a[k]
        divisor=a[k][k];assert abs(divisor)>1e-12
        a[k]=[v/divisor for v in a[k]]
        for i in range(len(a)):
            if i!=k:
                scale=a[i][k];a[i]=[v-scale*w for v,w in zip(a[i],a[k])]
    return [row[-1] for row in a]

def residual(params):
    r=simulate(*params)
    return [r[0]-30,r[1],(r[3][3]-START_HEIGHT)/100,r[3][1]/RAD],r

def solve():
    params=[8.6450924228465,11.514688323778149,19.210161492904696,300.0]
    for iteration in range(30):
        f,r=residual(params)
        print(iteration,params,'peak/end/min',r[:3],'height',r[3][3],'heading',r[3][1]/RAD)
        if max(map(abs,f))<1e-6: return params
        eps=0.01;columns=[]
        for j in range(4):
            probe=params[:];probe[j]+=eps;fp,_=residual(probe)
            columns.append([(p-q)/eps for p,q in zip(fp,f)])
        delta=linear_solve(list(zip(*columns)),[-v for v in f])
        scale=min(1,5/max(map(abs,delta[:3])),20/max(1,abs(delta[3])))
        score=sum(v*v for v in f)
        for _ in range(15):
            trial=[v+scale*d for v,d in zip(params,delta)]
            if min(trial[:3])>1 and trial[2]>6 and 120<trial[3]<350:
                ft,_=residual(trial)
                if sum(v*v for v in ft)<score: break
            scale/=2
        else: raise RuntimeError('No convergent step')
        params=trial
    raise RuntimeError('No convergent equal-altitude solution')

if __name__=='__main__':
    a,b,c,cut=solve();peak,end,low,y,rows=simulate(a,b,c,cut,0.005,True)
    report={'pull_seconds':PULL_TIME,'entry_seconds':a,'middle_seconds':b,'exit_seconds':c,'exit_bank_degrees':cut,'recovery_seconds':6,'peak_pitch_degrees':peak,'end_pitch_degrees':end,'min_pitch_degrees':low,'entry_altitude':ENTRY[3],'start_altitude':START_HEIGHT,'end_altitude':y[3],'end_heading_degrees':y[1]/RAD,'min_speed':min(row[6] for row in rows),'max_speed':max(row[6] for row in rows),'initial_speed':speed(START_HEIGHT),'end_speed':y[5],'thrust_newtons':THRUST_ACCEL*MASS}
    report.update(min_cas_knots=min(cas(row[6],row[4]) for row in rows),end_cas_knots=cas(y[5],y[3]),
                  max_altitude=max(row[4] for row in rows),forward_displacement=y[2],left_displacement=-y[4])
    output=Path(__file__).parent/'package/hornet-roll';output.mkdir(parents=True,exist_ok=True)
    (output/'geometry.json').write_text(json.dumps(report,indent=2)+'\n')
    total=PULL_TIME+a+b+c
    def control(t):
        if t<=PULL_TIME: return 0,1+0.8*smooth(t/4)
        r=t-PULL_TIME
        return bank(r,a,b,c,cut),1.8-0.8*smooth((r-a-b-c+6)/6)
    # Continue the same thrust/drag model through the post-roll level segment.
    # Nose/bank are zero there, n=1: no speed reset or endpoint energy injection.
    t=0;y=[0,0,0,START_HEIGHT,0,speed(START_HEIGHT)];samples=[]
    while True:
        phi,n=control(t)
        samples.append([t,*y,phi,n])
        if t>=total+6: break
        step=min(0.02,total+6-t);y=rk4(t,y,step,control);t+=step
    header=['// Generated by solve_roll.py. 400 KCAS initially; constant modeled thrust, drag and gravity.',
            '#pragma once','#include <array>','namespace hornet_roll_data {',
            'struct Sample { double t,pitch,heading,x,height,z,speed,bank,load; };',
            f'constexpr double pull_duration={PULL_TIME:.15g}, entry_duration={a:.15g}, middle_duration={b:.15g}, exit_duration={c:.15g}, recovery_duration=6;',
            f'constexpr double maneuver_duration={total:.15g}, sample_duration={total+6:.15g};',
            f'constexpr double thrust_acceleration={THRUST_ACCEL:.15g}, mass={MASS}, area={AREA}, cd0={CD0}, induced_factor={K:.15g};',
            f'inline constexpr std::array<Sample,{len(samples)}> samples={{{{']
    header+=['    {'+','.join(f'{v:.15g}' for v in row)+'},' for row in samples]
    header+=['}};','}']
    (Path(__file__).parent/'hornet_roll_data.h').write_text('\n'.join(header)+'\n')
    print(json.dumps(report,indent=2))
