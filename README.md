# Vector-Network-Analyzer
Use a Rigol DS1054Z Oscilloscope and Siglent SDG1025 Function Generator as a Vector Network Analyzer (VNA) to plot transfer functions or impedance vs. frequency.

This is a simple vector network analyzer using a function generator and an oscilloscope. A vector network analyzer measures the ratio between two signals -- both the amplitude and phase shift. 
The forcing signal is connected to Channel 1 of the oscilloscope; you can use a probe if desired.
The sensed signal is connected to Channel 2 of the oscilloscope. A probe can be used here too if desired. 
The sync signal from the signal generator is connected directly to Channel 4 of the oscilloscope. On the SDG1025, this cannot be used above 2 MHz, so the program switches to triggering directly from Channel 1 above this frequency. This has the added benefit of allowing 500 MS/s sample rate for the oscilloscope. 
The program has a number of command line options:

python VNA.py -b BEGIN_Freq -e END_Freq <-p Points_Per_Decade> <-f LOGFILE_Prefix>

The program takes logarithmically-spaced steps from BEGIN to END frequencies. The nominal signal amplitude is 1 Vpp.
Some options are:
```
  -s StepSize -- use linear steps instead of logarithmic scaling of frequency steps
  -l -- just list frequency steps to be taken; don't actually run
  -n -- don't plot the data. Program exits at the end of the run
  -f FILENAME_Prefix -- the prefix of the logfile with data in a CSV format with # comments
  -p points -- number of sample points per decade
  -z resistance -- resistance of current-sampling resistor. Plot then shows Z=(Channel2)/(Channel1-Channel2)*Z which is the complex Z of the structure under test. Note there is no calibration or deembeeding of the test fixture or probes
  -v voltage -- set the amplitude of the generator's output voltage
  -b Freq -- begin freqency of sweep
  -e Freq -- end frequency of sweep
  -h -- help & exit
```
  Since the signals will cover a wide dynamic range (over 60 dB), the program will dynamically adjust the 'scope vertical scale on each channel to optimally use the range available. The Rigol scope can use arbitrary vertical scales (i.e. not restricted to a 1:2:5 pattern).
  
  This VNA can be used from 1 Hz to 25 MHz, although resolution suffers at above 10 MHz. It can be used to characterize components, filters, and circuits such as voltage regulators where it can be used to measure loop gain and output impedance.
