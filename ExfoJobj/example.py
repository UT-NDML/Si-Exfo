"""
ExfoJobj Basic Example
"""

# import everything
import ExfoJobj
import matplotlib.pyplot as plt

# make cool plots
plt.style.use('default')
plt.style.use('dark_background')
plt.rc('font', family='serif')
plt.rc('text', usetex=True)
plt.rc('font', size=14)
plt.rc('lines', linewidth=2)
plt.rc('legend', fontsize=12)
plt.rc('legend', labelspacing=.1)
# %% Example

# Initialize Object
Ex = ExfoJobj.ExfoJobj('example')
# Generate metamodel
# Ex.Make_Meta('data/ansys_dat_122.csv')
# Save metamodel for faster loading later
# Ex.Pickle_Meta('data/', 'example_meta')
Ex.Load_Meta('data/', 'example_meta')

# set limits for gage block size
llim = 40
ulim = 65

# Load tdms scans and pickle them
Ex.Load_Batch('data/example', filt=1000, llim=llim, ulim=ulim)
# Sync scans into wafer. interperolate and resample if encoder is sparse
Ex.Wafer_Sync(resamp=(llim, ulim))
# Make data into wafer stack
Ex.Wafer_Make(filt=11)
# Caclulate Stress
Ex.Get_Stress(filt=5)
# Caculate compensated load
Ex.Make_Load(ex=4, filt=5)
fig, ax1, ax2 = Ex.Plot_Wafer()
# Save load profile to export
Ex.Export_Load('data/example', 'example.csv', 2500, 200, window=5500)
