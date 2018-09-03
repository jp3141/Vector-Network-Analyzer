# Vector-Network-Analyzer
Use a Rigol DS1054Z Oscilloscope and Siglent SDG1025 Function Generator as a Vector Network Analyzer (VNA).
This is a simple vector network analyzer using a function generator and an oscilloscope. A vector network analyzer measures the ratio between two signals -- both the amplitude and phase shift. 
The forcing signal is connected to Channel 1 of the oscilloscope; you can use a probe if desired.
The sensed signal is connected to Channel 2 of the oscilloscope. A probe can be used here too if desired. 
The sync signal from the signal generator is connected directly to Channel 4 of the oscilloscope. On the SDG1025, this cannot be used above 2 MHz, so the program switches to triggering directly from Channel 1 above this frequency. This has the aded benefit of allowing 500 MS/s sample rate for the oscilloscope. 
The program has a number of command line options:
python VNA.py -b BEGIN_Freq -e END_Freq <-p Points_Per_Decade> <-f LOGFILE_Prefix>

The program takes logarithmically-spaced steps from BEGIN to END frequencies. The nominal signal amplitude is 1 Vpp.
Some options are:
  -s StepSize -- use linear steps instead of logarithmic scaling of frequency steps
  -l -- just list frequency steps to be taken; don't actually run
  -n -- don't plot the data. program exits at the end of the run
  Since the signals will cover a wide dynamic range (over 60 dB), the program will dynamically adjust the 'scope vertical scale on each channel to optimally use the range available. The Rigol scope can use arbitrary vertical scales (i.e. not restricted to a 1:2:5 pattern).
  
  This VNA can be used from 1 Hz to 25 MHz, although resolution suffers at above 10 MHz. It can be used to characterize components, filters, and circuits such as voltage regulators where it can be used to measure loop gain and output impedance.
