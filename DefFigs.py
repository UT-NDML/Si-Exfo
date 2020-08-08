#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Aug  6 22:42:25 2020

@author: myo

Defense Figs
"""

import ExfoJobj
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal
from scipy.ndimage import uniform_filter1d
from cycler import cycler
from AxZoom import *
from sklearn.decomposition import FastICA, PCA
from scipy.integrate import cumtrapz
import AxZoom
from matplotlib import rcParams


plt.style.use('default')
z = cycler('color', [(0, 0.45, 0.83), (0.8, 0.4, 0.47), (0.867, 0.8, 0.467), (0.067, 0.467, 0.2)])
plt.rc('axes', prop_cycle=cycler('color', z))
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.serif'] = ['Segoe UI'] + plt.rcParams['font.sans-serif']
plt.rc('font', size=14)
plt.rc('lines', linewidth=2.5)
plt.rc('legend', fontsize=12)
plt.rc('legend', labelspacing=.1)


def exFilter(size):
    def filt(lzr):
        lzr = signal.medfilt(lzr, 65)
        lzr = uniform_filter1d(lzr, size)
        return lzr
    return filt


def wFilter(size):
    def filt(lzr):
        lzr = signal.medfilt(lzr, size)
        return lzr
    return filt


def sFilter(size):
    def filt(lzr):
        lzr = signal.medfilt(lzr, 129)
        z = np.polyfit(Ex.sync_stress_x, lzr, 5)
        p = np.poly1d(z)
        lzr = p(Ex.sync_stress_x)
        return lzr
    return filt


def nFilter(size):
    def filt(lzr):
        z = np.polyfit(Ex.sync_stress_x, lzr, 5)
        p = np.poly1d(z)
        lzr = p(Ex.sync_stress_x)
        return lzr
    return filt


# %% Compensation Result
filt = exFilter(1000)
sfilt = sFilter(1000)
nfilt = nFilter(1000)
wfilt = wFilter(11)

Ex = ExfoJobj.ExfoJobj('12')
Ex.Load_Wafer('12/eh', '12.dat')
ext = 4

# Ex = ExfoJobj.ExfoJobj('12')
# Ex.Load_Meta('', 'testmeta')
# # Ex.Make_Meta('ansys_dat_122.csv')
# llim = 40
# ulim = 65
# Ex.Load_Batch('12', filt=filt, llim=llim, ulim=ulim)

# Ex.Wafer_Sync(resamp=(llim, ulim))
# Ex.Wafer_Make(w=.545, wo=.017, glass=1.8631, k=.101, filt=wfilt)
# # zero x axis
# Ex.x = Ex.x-Ex.x[0]
# # calibrate
# Ex.Get_Stress(win=50, wafer_thickness=580E-6, filt=sfilt)
# Ex.Make_Load(ex=ext, filt=nfilt, floor=5)
print('Exfo average error from target: {:02.2f} µm'.format(abs(Ex.ex*1E6-ext).mean()))

def Plot_Wafer_Def(Ex, n, lim=None):

    color = plt.rcParams['axes.prop_cycle'].by_key()['color'][0]
    fig, ax1 = plt.subplots(figsize=(9, 4.5))
    ax1.plot(Ex.x, Ex.ni*1E6, color=color, linestyle='--', label='Ni Thickness')
    if n > 1:
        if hasattr(Ex, 'ex'):
            ax1.plot(Ex.x, Ex.ex*1E6, color=color, linestyle='-', label='Si Thickness')
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.set_title('Wafer Profile')
    ax1.set_xlabel('Chuck (mm)')
    ax1.set_ylabel('Si and Ni Film Thickness (µm)', color=color)

    color = plt.rcParams['axes.prop_cycle'].by_key()['color'][1]
    ax2 = ax1.twinx()
    ax2.plot(Ex.x, Ex.S/1E8, color=color, linestyle='-.', label='Ni Stress')
    if n > 0:
        ax2.plot(Ex.x, Ex.Load/9.81, color=color, linestyle='-', label='Handle Tension')
        if n > 1:
            if hasattr(Ex, 'load'):
                x, _, y = ExfoJobj.syncstuff(Ex.x, Ex.Load, Ex.load.enc, Ex.load.lod, dm=False)
                ax2.plot(x, y, color=color, linestyle=':', label='Measured Tension')
    ax2.tick_params(axis='y', labelcolor=color)
    ax2.set_ylabel(r'Ni Stress (Pa$\cdot 10^8$) and Handle Tension (Kg)', color=color)
    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    fig.legend(bbox_to_anchor=(0.03, 0.5, .93, 0.5), loc='upper left', ncol=5, mode="expand", borderaxespad=0., handletextpad=0.1)
    ax1.margins(x=0)
    ax1.set_title('')
    ax1.set_xlabel('Distance from Stable Crack Start (mm)')
    if lim:
        ax1.set_xlim(lim[0])
        ax1.set_ylim(lim[1])
        ax2.set_ylim(lim[2])
    fig.tight_layout(pad=0.1)
    return fig, ax1, ax2


n = 2
fig, ax1, ax2 = Plot_Wafer_Def(Ex, n)
xl = ax1.get_xlim()
y1l = ax1.get_ylim()
y2l = ax2.get_ylim()
lim = [xl, y1l, y2l]
plt.close(fig)

n = 0
fig, ax1, ax2 = Plot_Wafer_Def(Ex, n, lim)
plt.savefig('D/figs/result0.png', dpi=600, transparent=True)
n = 1
fig, ax1, ax2 = Plot_Wafer_Def(Ex, n, lim)
plt.savefig('D/figs/result1.png', dpi=600, transparent=True)
n = 2
fig, ax1, ax2 = Plot_Wafer_Def(Ex, n, lim)
plt.savefig('D/figs/result2.png', dpi=600, transparent=True)


# %% Uniformity
# Load wafer 141 data
pdat = np.genfromtxt('P.csv', delimiter=",")[1:, :]
# shrink to comperable window
pdat = pdat[70:144, :]
e = pdat[:, 1]
n = pdat[:, 0]
sstd141 = np.std(e)
uni141 = (sstd141/np.std(n))
sstd12 = np.std(Ex.ex)
uni12 = (sstd12/np.std(Ex.ni))

e12 = np.interp(np.arange(*e.shape), np.arange(*Ex.ex.shape), Ex.ex)

print('Si STD without LC: {:04.2f} µm'.format(sstd141))
print('Si STD with LC: {:04.2f} µm'.format(sstd12*1E6))

print('Si/Ni Uniformity Ratio without LC: {:04.2f}'.format(uni141))
print('Si/Ni Uniformity Ratio with LC: {:04.2f}'.format(uni12))

print('{:2.0f}% improvement in uniformity'.format((uni141-uni12)/uni141*100))
print('{:2.0f}% improvement in STD'.format((sstd141-sstd12*1E6)/sstd141*100))

fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True)
Px = np.linspace(Ex.x[0], Ex.x[-1], len(e))
ax1.plot(Px, e, label='Silicon')
ax1.plot(Px, n)
ax1.set_title('Uncompensated')
fig.legend(bbox_to_anchor=(.15, .52), loc='center left', ncol=1, handles=[ax1.lines[0]])
ax2.plot(Ex.x, Ex.ex*1E6)
ax2.plot(Ex.x, Ex.ni*1E6, label='Nickel')
ax2.set_title('Compensated')
ax2.set_xlabel('Distance from Stable Crack Start (mm)')
fig.legend(bbox_to_anchor=(.9, .52), loc='center right', ncol=1, handles=[ax2.lines[1]])
fig.tight_layout()
suplabel(ax1, 'Thickness (µm)', labelpad=6.75)
plt.savefig('D/figs/uniformity.png', dpi=600, transparent=True)
# %% No Compensation Simulation
Ex.Make_Meta('ansys_dat_122.csv', i=1)


def Make_Ex(Ex, T=1, a=1500, h=150, k2=0, k1=730, filt=None, floor=False):
    """
    Make compensated Load profile

    Parameters
    ----------
    ex : int, optional
        Desired exfoliated film thickness in um. The default is 8.
    a : int, optional
        Crack length in um. The default is 1500.
    h : int, optional
        Roller height in um. The default is 150.
    k1 : int, optional
        Mode I stress intensity target in MPa*mm*(.5). The default is 730.
    k2 : int, optional
        Mode II stress intensity target in MPa*mmd*(.5). The default is 0.

    Returns
    -------
    None.
    """

    const = np.array([0, T, 0, a, h, k2, k1])
    C = np.ones((Ex.ni.shape[0], 7))*const

    ni = Ex.ni
    if filt:
        ni = filt(Ex.ni)
    Xtest = C
    Xtest[:, 0] = ni*1E6
    Xtest[:, 2] = Ex.S*1E-6

    # Compute load with scaling
    ex = Ex.scalery.inverse_transform(Ex.gpr.predict(Ex.scalerX.transform(Xtest)))
    # if floor:
    #     Ex.Load[Ex.Load < floor] = floor
    return ex


ex = Make_Ex(Ex, filt=exFilter(200))
fig, ax = plt.subplots(figsize=(8, 4))
ax.plot(Ex.x, Ex.ex*1E6, label='Compenstaed (Measured)')
ax.plot(Ex.x, ex, label='Uncompenstaed (Predicted)')
ax.legend()
ax.set_xlabel('Distance from Stable Crack Start (mm)')
ax.set_ylabel('Si Thickness (µm)')
ax.margins(x=0)
fig.tight_layout(pad=0.1)

plt.savefig('D/figs/compcomp.png', dpi=600, transparent=True)


# %% Repeatablility Hours
def Trimmer(sections):
    """Create array to index deletes from Scan.idx."""
    a = [np.arange(*s) for s in sections]
    return np.concatenate(a)


sections = [(0, 18), (34, 50)]
filepath = 'dat'
Ex3 = ExfoJobj.ExfoJobj('rep')
llim = 21
ulim = 69
Ex3.Load_Scan(filepath, 'w-03-26-2020_19-49-27.dat', trim=np.s_[:34], scan='base', llim=llim, ulim=ulim, filt=exFilter(100))
Ex3.Load_Scan(filepath, 'w-03-26-2020_19-49-27.dat', trim=Trimmer(sections), llim=llim, ulim=ulim, filt=exFilter(100))

ax1, fig1, ax2, ax3, fig2 = Ex3.wafer.plot_error_byp(m=10)
plt.close(fig1)
ax3.set_xlim(0, .5)
ax3.set_title('')
fig2.set_size_inches(4.3, 3.3)
fig2.tight_layout(pad=0.1)

nfs = np.percentile(Ex3.wafer.error_byp_b*1000, (2.5, 97.5))
print('Error mean: {:02.2f} µm'.format(nfs.mean()))
print('Error 95% confidence interval: {:02.2f}-{:02.2f} µm'.format(nfs[0], nfs[1]))

plt.savefig('D/figs/repeat25.png', dpi=600, transparent=True)
# %% Repeatability Days
mnw, std, n, SEM, xw = Ex3.base.fmeans
mnb, std, n, SEM, xb = Ex3.wafer.fmeans

shift = 0
w = mnw[shift:] * 1000
x = xw[shift:]
b = mnb[0:len(w)] * 1000
z = w-b

fig3, (ax1, ax2) = plt.subplots(2, 1)
ax2 = plt.subplot(211)
ax1 = plt.subplot(212)

ax1.plot(x, w-w.mean(), label='Scan 1')
ax1.plot(x, b-b.mean(), label='Scan 2')
ax1.plot(x, z, label='Remainder')

ax2.plot(x, w-w.mean(), label='Scan 1')
ax2.plot(x, b-b.mean(), label='Scan 2')
ax2.plot(x, z, label='Remainder')

ax2.set_xlim(42, 50)
ax2.set_ylim(-15, 15)
ax1.set_xlabel('Chuck (mm)')
ax1.legend(loc=2)
fig3.set_size_inches(6, 5)
# fig3.tight_layout(pad=0.3)
fig3.tight_layout(w_pad=.01)
suplabel(ax1, 'Laser Distance (µm)', labelpad=9)
zoom_effect02(ax2, ax1, alpha=.2)

nfsz = np.percentile(abs(z), (2.5, 97.5))
print('Error mean: {:02.2f} µm'.format(nfsz.mean()))
print('Error 95% confidence interval: {:02.2f}-{:02.2f} µm'.format(nfsz[0], nfsz[1]))

plt.savefig('D/figs/repeatd.png', dpi=600, transparent=True)


# %% Remove repeatable error
w = .545
wo = .017
glass = 1.8631
k = .101

Exr = ExfoJobj.ExfoJobj('12')
Exr.Load_Meta('', 'testmeta')
# Ex.Make_Meta('ansys_dat_122.csv')
llim = 40
ulim = 65
Exr.Load_Batch('12', filt=exFilter(1000), llim=llim, ulim=ulim)

Exr.Wafer_Sync(resamp=(llim, ulim))

fig, ax = plt.subplots(3, 1)
ax[0].plot(Exr.sync_base_x, (Exr.sync_base-glass-w-k+wo)*1E3)
ax[0].set_title('Gage Block')
ax[1].plot(Exr.sync_nickel_x, Exr.sync_nickel*1E3)
ax[1].set_title('Raw Nickel Scan')
ax[2].plot(Exr.sync_nickel_x, Ex.ni*1E6)
ax[2].set_title('Recovered Nickel Scan')
ax[2].set_xlabel('Chuck Distance (mm)')
fig.tight_layout(pad=1.2)
AxZoom.suplabel(ax, 'Laser Distance (µm)', labelpad=11)

plt.savefig('D/figs/remainder.png', dpi=600, transparent=True)
