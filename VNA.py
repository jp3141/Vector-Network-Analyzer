import visa
import time
import math
import pdb
import sys
import numpy as np
import matplotlib.pyplot as plt
import re
import os
import keyboard

def HelpAndExit():
  print("Usage: ", sys.argv[0], " [-b BeginF] [-e EndF] [-p Points/Decade] [-f FILE_Prefix]\
  \noptional: [-n] Don't plot after gathering data\
  \noptional: [-z] Set current-measuring resistance and plot Z data\
\nFILE_Prefix defaults to RG1054Z\
\nJohn Pigott Sep 2, 2018"\
  )
  sys.exit(1)    

def NextArg(i): #Return the next command line argument (if there is one)
  if ((i+1) >= len(sys.argv)):
    Fatal("'%s' expected an argument" % sys.argv[i])
  return(1, sys.argv[i+1])

  
######################################### main ##################################
debug = 0
FILEPREFIX  = "RG1054Z"  
MDEPTH = 30000
#pdb.set_trace()
StartF = 1
StopF = 1e6
PlotOK = True
ListOnly = False
PointsPerDecade = 10 # Changed from 30, 8/28/2018 KEAP
HighFrequency = False # used to indicate crossed over max Sync frequency from SDG1025
SweepModeLog = True
Voltage = 1.0
Resistance = 0.0 # non-zero when -z resistance argument is used -> Z is plotted
Sine = True

# Parse command line
skip = 0
for i in range(1, len(sys.argv)):
  if not skip:
    if   sys.argv[i][:2] == "-d":  debug = 1
    elif sys.argv[i][:2] == "-f":  (skip,FILEPREFIX)  = NextArg(i)
    elif sys.argv[i][:2] == "-n":  PlotOK = False
    elif sys.argv[i][:2] == "-l":  ListOnly = True
    elif sys.argv[i][:2] == "-q":  Sine = False
    elif sys.argv[i][:2] == "-v":  (skip,Voltage)         = 1, float(NextArg(i)[1])
    elif sys.argv[i][:2] == "-z":  (skip,Resistance)      = 1, float(NextArg(i)[1])
    elif sys.argv[i][:2] == "-s":  (skip,StepSizeF)       = 1, float(NextArg(i)[1]); SweepModeLog = False
    elif sys.argv[i][:2] == "-b":  (skip,StartF)          = 1, float(NextArg(i)[1])
    elif sys.argv[i][:2] == "-e":  (skip,StopF)           = 1, float(NextArg(i)[1])
    elif sys.argv[i][:2] == "-p":  (skip,PointsPerDecade) = 1, int(NextArg(i)[1]); SweepModeLog = True
    elif sys.argv[i][:2] == "-h":  HelpAndExit()
    elif sys.argv[i][:1] == "-":  
            sys.stderr.write("%s: Bad argument\n" % (sys.argv[0]))
            sys.exit(1)
    else: pass
  else: skip = 0

#if (len(sys.argv) <= 1): HelpAndExit()

if (ListOnly): PlotOK = False # don't plot if just listing
   
GPIB = visa.ResourceManager()
#print(GPIB.list_resources())
GPIB_Resources = GPIB.list_resources()
for resource in GPIB_Resources: print(resource)
print()

LOGFile = open(FILEPREFIX+"_VNA.log" if (not ListOnly) else os.devnull, 'w')
#else: LOGFile = open(os.devnull, 'w')
print(time.strftime("# %Y-%m-%d %H:%M"), file = LOGFile)

#GPIB_BUS = GPIB.open_resource('GPIB0::INTFC')

SDG1025 = GPIB.open_resource([_ for _ in GPIB_Resources if re.search('^USB.*:SDG.*INSTR$', _)][0])
#SDG1025 = GPIB.open_resource('USB0::0xF4ED::0xEE3A::SDG00004120363::INSTR') 
Q = SDG1025.query("*IDN?")
print("SDG1025:", Q, end='')
print("# SDG1025:", Q, end='', file=LOGFile)

DS1054Z = GPIB.open_resource([_ for _ in GPIB_Resources if re.search('^USB.*:DS.*INSTR$', _)][0])
#DS1054Z = GPIB.open_resource('USB0::0x1AB1::0x04CE::DS1ZA201003553::INSTR') 
Q = DS1054Z.query("*IDN?")
print("DS1054Z:", Q)
print("# DS1054Z:", Q, end='', file=LOGFile)

DS1054Z.timeout = 2000 # ms

DecadesF = math.log10(StopF/StartF)

print(sys.argv)
if SweepModeLog:
  print(  "Analysing from %f Hz to %f Hz, %6.1f points/decade; %i decades" % (StartF, StopF, PointsPerDecade, DecadesF))
  print("# Analysing from %f Hz to %f Hz, %6.1f points/decade; %i decades" % (StartF, StopF, PointsPerDecade, DecadesF), file = LOGFile)
else:
  print(  "Analysing from %f Hz to %f Hz, %f Hz steps; %i total steps" % (StartF, StopF, StepSizeF, 1 + math.ceil((StopF-StartF)/StepSizeF)))
  print("# Analysing from %f Hz to %f Hz, %f Hz steps; %i total steps" % (StartF, StopF, StepSizeF, 1 + math.ceil((StopF-StartF)/StepSizeF)), file = LOGFile)

# Signal Generator
SYNCMax = 2.0e6
SDG1025.write("C1: BSWV FRQ, %11.3f" % StartF)
if (Sine): SDG1025.write("C1: BSWV WVTP,SINE,AMP,%5.2f,OFST,0,PHSE,0" % Voltage) # 1 Vpp
else:      SDG1025.write("C1: BSWV WVTP,SQUARE,AMP,%5.2f,OFST,0,PHSE,0" % Voltage) # 1 Vpp
SDG1025.write("C1:OUTP ON,LOAD,HZ")
SDG1025.write("C1:SYNC ON")

DS1054Z.write(":WAV:FORMAT BYTE;:WAV:MODE RAW")
#DS1054Z.write(":SYSTEM:BEEPER OFF")

DS1054Z.write(":STOP") # so preamble can get YINCR

#Channel 1
DS1054Z.write(":CHANNEL1:COUPLING AC")
DS1054Z.write(":CHANNEL1:DISPLAY ON")
DS1054Z.write(":CHANNEL1:SCALE 5")
DS1054Z.write(":CHANNEL1:BWLimit 20M")
print("1: ",DS1054Z.query(":WAV:SOURCE CHAN1;:WAV:PREAMBLE?"), end='')

#Channel 2
DS1054Z.write(":CHANNEL2:COUPLING AC")
DS1054Z.write(":CHANNEL2:DISPLAY ON")
DS1054Z.write(":CHANNEL2:SCALE 5")
DS1054Z.write(":CHANNEL2:BWLimit 20M")
print("2: ",DS1054Z.query(":WAV:SOURCE CHAN2;:WAV:PREAMBLE?"))

#Channel 4 (Trigger)
DS1054Z.write(":CHANNEL4:COUPLING DC")
DS1054Z.write(":CHANNEL4:DISPLAY OFF")
DS1054Z.write(":CHANNEL4:SCALE 5.0")
DS1054Z.write(":TRIGGER:MODE EDGE")
DS1054Z.write(":TRIGGER:EDGE:SOURCE CHANNEL4")
DS1054Z.write(":TRIGGER:COUPLING DC")
DS1054Z.write(":TRIGGER:EDGE:SLOPE POSITIVE")
DS1054Z.write(":TRIGGER:EDGE:LEVEL 2.5")

DS1054Z.write(":RUN")
DS1054Z.write(":ACQUIRE:MDEPTH %i" % MDEPTH)
VNA=[]
#DS1054Z.chunk_size = MDEPTH

print("#Sample,  Frequency,      Mag1,      Mag2, Ratio (dB),   Phase", file = LOGFile)

if SweepModeLog:
  LastTestPOINT = 1 + math.ceil(PointsPerDecade*math.log10(StopF/StartF))
else:
  LastTestPOINT = 1 + math.ceil((StopF-StartF)/StepSizeF)

#for TestPOINT in range(-1, 1+math.ceil(PointsPerDecade*math.log10(StopF/StartF))):
for TestPOINT in range(-1, LastTestPOINT):
  # 1st cycle which is used to initialize vertical scale isn't logged
  POINT = max(0, TestPOINT) # -1 maps to 0
  TestF = StartF*math.pow(10,POINT/PointsPerDecade) if SweepModeLog else StartF+POINT*StepSizeF
  if (TestF > StopF): break
  if (TestF > 25e6): break # Max frequency of SDG1025
  if keyboard.is_pressed('q'):
    print('Key pressed')
    break
  print("Sample %3i, %11.3f Hz" % (TestPOINT, TestF), end='')
  if (ListOnly): print();continue # only list sample frequencies

  if (TestF >= SYNCMax) and not HighFrequency: # Can't generate sync above 2 MHz -- so switch to Channel 1. This also allows S/s to double
    SDG1025.write("C1:SYNC OFF")
    DS1054Z.write(":CHANNEL4:DISPLAY OFF")
    DS1054Z.write(":TRIGGER:COUPLING LFReject")
    DS1054Z.write(":TRIGGER:MODE EDGE")
    DS1054Z.write(":TRIGGER:EDGE:SOURCE CHANNEL1")
    DS1054Z.write(":TRIGGER:EDGE:SLOPE POSITIVE")
    DS1054Z.write(":TRIGGER:EDGE:LEVEL 0")
    time.sleep(0.3) # wait for this to change

    MDEPTH *= 2  # double sample rate when Ch4 is not used by trigger
    HighFrequency = True # Only switchover once

  SDG1025.write("C1: BSWV FRQ, %11.3f" % TestF)
  #pdb.set_trace()
  DS1054Z.write(":TIMEBASE:MAIN:SCALE %13.9f" % (1./TestF/12.)) # Scope rounds up
  ActualTB = float(DS1054Z.query(":TIMEBASE:MAIN:SCALE?").rstrip())
  ActualSs = min(250e6 if (TestF < SYNCMax) else 500e6, round(MDEPTH/(ActualTB*12),0))
  ActualSs_ = str(int(ActualSs))
  if (ActualSs_[-9:] == "000000000"): ActualSs_ = ActualSs_[:-9] + " G"
  if (ActualSs_[-6:] ==    "000000"): ActualSs_ = ActualSs_[:-6] + " M"
  if (ActualSs_[-3:] ==       "000"): ActualSs_ = ActualSs_[:-3] + " k"
  print(", %sS/s" % ActualSs_, end='')
  
  DS1054Z.write(":RUN;:TRIGGER:SWEEP SINGLE")
  while (DS1054Z.query(":TRIGGER:STATUS?")[:4] != "STOP"): pass  
  
  PreambleList = DS1054Z.query(":WAV:SOURCE CHAN1;:WAV:PREAMBLE?").split(',')
  XINCR = float(PreambleList[4])
  YINCR1 = float(PreambleList[7])
  YOFF1 = int(PreambleList[8]) + int(PreambleList[9])
  
  NPOINTS_PerCycle =  1./(TestF*XINCR)  # Number of points for 1 cycle of this frequency
  NCYCLES = math.floor(MDEPTH/NPOINTS_PerCycle)
  NPOINTS = int(round(NPOINTS_PerCycle * NCYCLES))
  print(", %i points; %i cycle%s @ %10.1f/cycle" % (NPOINTS, NCYCLES, " " if (NCYCLES==1) else "s", NPOINTS_PerCycle))
  
  SAMPLEPOINTS = np.linspace(0, NCYCLES*2*np.pi, NPOINTS)
  SINEARRAY = np.sin(SAMPLEPOINTS)
  COSARRAY  = np.cos(SAMPLEPOINTS)
  
  # DS1054Z has transfer errors over USB if over ~ 8200; download whole array and truncate is simplest
  CURVE1=DS1054Z.query_binary_values(":WAV:START 1;:WAV:STOP %i;:WAV:DATA?" %(MDEPTH), datatype='b', container=np.array, header_fmt=u'ieee')[:NPOINTS]
  CURVE1 = (CURVE1-YOFF1)*YINCR1

  PreambleList = DS1054Z.query(":WAV:SOURCE CHAN2;:WAV:PREAMBLE?").split(',') # Refresh after range change
  YINCR2 = float(PreambleList[7])
  YOFF2 = int(PreambleList[8]) + int(PreambleList[9])
  CURVE2=DS1054Z.query_binary_values(":WAV:START 1;:WAV:STOP %i;:WAV:DATA?" %(MDEPTH), datatype='b', container=np.array, header_fmt=u'ieee')[:NPOINTS]
  CURVE2 = (CURVE2-YOFF2)*YINCR2
    
  SINDOT1 = np.dot(CURVE1,SINEARRAY)/NPOINTS
  COSDOT1 = np.dot(CURVE1,COSARRAY)/NPOINTS
  CHANNEL1 = complex(SINDOT1, COSDOT1)
  MAG1 = 2*abs(CHANNEL1)
  PHASE1 = np.angle(CHANNEL1)*180/math.pi
  DS1054Z.write(":CHANNEL1:SCALE %9.4f" % (MAG1/3)) 

  SINDOT2 = np.dot(CURVE2,SINEARRAY)/NPOINTS
  COSDOT2 = np.dot(CURVE2,COSARRAY)/NPOINTS
  CHANNEL2 = complex(SINDOT2, COSDOT2)
  MAG2 = 2*abs(CHANNEL2)
  PHASE2 = np.angle(CHANNEL2)*180/math.pi
  DS1054Z.write(":CHANNEL2:SCALE %9.4f" % (MAG2/3))
  
  Channel_Z = CHANNEL2/(CHANNEL1-CHANNEL2)*Resistance

  print("Ch1: Sin, Cos = %9.4f, %9.4f; Mag = %9.5f, Phase = %7.2f deg." % (SINDOT1, COSDOT1, MAG1, PHASE1))
  print("Ch2: Sin, Cos = %9.4f, %9.4f; Mag = %9.5f, Phase = %7.2f deg." % (SINDOT2, COSDOT2, MAG2, PHASE2))
  Mag_dB = 20*math.log10(MAG2/MAG1)
  Phase = (PHASE2-PHASE1) % 360
  if (Phase) > 180: Phase -= 360  # center around +/- 180
  CHZ = '%12.4f %sj%12.4f' % (Channel_Z.real, '+-'[Channel_Z.imag < 0], abs(Channel_Z.imag))
  print("Ch2:Ch1 = %7.2f dB @ %7.2f deg.; Z =" % (Mag_dB, Phase), CHZ, '\n')
  if (TestPOINT >= 0):  # only after 1st round
    VNA.append((TestF, Mag_dB, Phase, Channel_Z))
    print("%6i, %12.3f, %9.5f, %9.5f,    %7.2f, %7.2f, " %\
         (POINT, TestF, MAG1, MAG2, Mag_dB, Phase), CHZ, file = LOGFile)

LOGFile.close()
DS1054Z.close()
SDG1025.close()
GPIB.close()
print("Done")

if (PlotOK):
  fig, ax1 = plt.subplots()
  fig.canvas.set_window_title('VNA 2:1')
  plt.title("Channel 2 : Channel 1")

  color = 'tab:red'
  ax1.set_xlabel('Frequency (Hz)')
  ax1.set_ylabel('dB', color=color)
  if SweepModeLog: 
    ax1.semilogx([_[0] for _ in VNA], [_[1] for _ in VNA], color=color)
  else:
    ax1.plot([_[0] for _ in VNA], [_[1] for _ in VNA], color=color)
  ax1.tick_params(axis='y', labelcolor=color)
  ax1.grid(True)
  
  ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis
  
  color = 'tab:blue'
  ax2.set_ylabel('Phase (°)', color=color)  # we already handled the x-label with ax1
  if SweepModeLog: 
      ax2.semilogx([_[0] for _ in VNA], [_[2] for _ in VNA], color=color)
      ax2.semilogx([_[0] for _ in VNA], [_[2] for _ in VNA], color=color)
  else:
      ax2.plot([_[0] for _ in VNA], [_[2] for _ in VNA], color=color)
  ax2.tick_params(axis='y', labelcolor=color)
  #ax2.grid(True)
  
  fig.tight_layout()  # otherwise the right y-label is slightly clipped
  plt.show(block=False) # should only block if R=0 ?
  #plt.show(block=False)

if (PlotOK and Resistance != 0):
  fig, ax1 = plt.subplots()
  fig.canvas.set_window_title('VNA Z')

  plt.title("Impedance (ohms)")
  
  color = 'tab:green'
  ax1.set_xlabel('Frequency (Hz)')
  ax1.set_ylabel('|Z| (ohms)', color=color)
  if SweepModeLog: 
    ax1.loglog(  [_[0] for _ in VNA], [abs(_[3]) for _ in VNA], color=color)
  else:
    ax1.semilogy([_[0] for _ in VNA], [abs(_[3]) for _ in VNA], color=color) # Mag(Z)
  ax1.tick_params(axis='y', labelcolor=color)
  ax1.grid(True)
  
  ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis
  
  color = 'tab:purple'
  ax2.set_ylabel('Z∠ (°)', color=color)  # we already handled the x-label with ax1
  if SweepModeLog: 
      ax2.semilogx([_[0] for _ in VNA], [np.angle(_[3])*180/math.pi for _ in VNA], color=color)
  else:
      ax2.plot(    [_[0] for _ in VNA], [np.angle(_[3])*180/math.pi for _ in VNA], color=color)
  ax2.tick_params(axis='y', labelcolor=color)
  #ax2.grid(True)
  
  fig.tight_layout()  # otherwise the right y-label is slightly clipped
  plt.show(block=True)
