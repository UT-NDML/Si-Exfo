#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 29 22:27:13 2020

@author: myo

Dissertation Figs
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

plt.style.use('default')
z = cycler('color', [(0, 0.45, 0.83), (0.8, 0.4, 0.47), (0.867, 0.8, 0.467), (0.067, 0.467, 0.2)])
plt.rc('axes', prop_cycle=cycler('color', z))
plt.rc('font', family='serif')
plt.rc('text', usetex=True)
plt.rc('font', size=14)
plt.rc('lines', linewidth=2)
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
Ex.Load_Wafer('data/', '12.dat')
ext = 4

# Ex = ExfoJobj.ExfoJobj('12')
# Ex.Load_Meta('data/', 'testmeta')
# # Ex.Make_Meta('data/ansys_dat_122.csv')
# llim = 40
# ulim = 65
# Ex.Load_Batch('12', filt=filt, llim=llim, ulim=ulim)

# Ex.Wafer_Sync(resamp=(llim, ulim))
# Ex.Wafer_Make(w=.545, wo=.017, glass=1.8631, k=.101, filt=wfilt)
# # zero x axis
# Ex.x = Ex.x-Ex.x[0]
# # calibrate
# Ex.Get_Stress(win=50, wafer_thickness=580E-6, filt=sfilt)
# Ex.Make_Load(ex=4, filt=nfilt, floor=5)

print('Exfo average error from target: {:02.2f} µm'.format(abs(Ex.ex*1E6-ext).mean()))
fig, ax1, ax2 = Ex.Plot_Wafer()

plt.savefig('figs/result.pdf', dpi=300, transparent=True)

# %% Uniformity
# Load wafer 141 data
pdat = np.genfromtxt('data/P.csv', delimiter=",")[1:, :]
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

# %% No Compensation Simulation
Ex.Make_Meta('data/ansys_dat_122.csv', i=1)


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

plt.savefig('figs/compcomp.pdf', dpi=300, transparent=True)


# %% Repeatablility Hours
def Trimmer(sections):
    """Create array to index deletes from Scan.idx."""
    a = [np.arange(*s) for s in sections]
    return np.concatenate(a)


sections = [(0, 18), (34, 50)]
filepath = 'data'
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

plt.savefig('figs/repeat25.pdf', dpi=300, transparent=True)
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

plt.savefig('figs/repeatd.pdf', dpi=300, transparent=True)


# %% Remove Repeatable Error by Integration
def plot_PICA(x1, x2, b1, b2):
    S = np.c_[x1, x2]
    X = np.c_[b1, b2]
    ica = FastICA(n_components=2)
    S_ = ica.fit_transform(X)  # Reconstruct signals
    A_ = ica.mixing_  # Get estimated mixing matrix
    # We can `prove` that the ICA model applies by reverting the unmixing.
    assert np.allclose(X, np.dot(S_, A_.T) + ica.mean_)
    # For comparison, compute PCA
    pca = PCA(n_components=2)
    H = pca.fit_transform(X)  # Reconstruct signals based on orthogonal components
    # #############################################################################
    pca = PCA(n_components=2)
    H = pca.fit_transform(X)  # Reconstruct signals based on orthogonal components
    # #############################################################################
    # Plot results
    plt.figure()
    models = [X, S, S_, H]
    names = ['Observations (mixed signal)', 'True Sources', 'ICA recovered signals', 'PCA recovered signals']
    names = ['Observations (mixed signal)',
             'True Sources',
             'ICA recovered signals',
             'PCA recovered signals']
    colors = ['red', 'steelblue', 'orange']
    for ii, (model, name) in enumerate(zip(models, names), 1):
        plt.subplot(4, 1, ii)
        plt.title(name)
        for sig, color in zip(model.T, colors):
            # plt.plot(sig, color=color)
            plt.plot(sig)
        plt.xticks([])
        plt.yticks([])
    plt.tight_layout()


def ICR(t, x1, x2, x3, b1, b2, d, dm=False, n=None, filt=None):

    if n is not None:
        noise = filt(np.random.normal(0, abs(b1).mean()*n, b1.shape))
        b1 += noise
        b1 = filt(b1)
        noise2 = filt(np.random.normal(0, abs(b1).mean()*n, b1.shape))
        b2 += noise2
        b2 = filt(b2)

    fig, axs = plt.subplots(5, 1, figsize=(8, 10))
    axs[0].plot(t, x1, color=plt.rcParams['axes.prop_cycle'].by_key()['color'][2])
    axs[0].set_title('Base Signal')
    plt.xticks([])
    plt.yticks([])
    axs[1].plot(t, x2, t, x3)
    axs[1].set_title('Phase-Shifted Signals')
    plt.xticks([])
    plt.yticks([])
    axs[2].plot(t, b1, t, b2)
    axs[2].set_title('Combined Signals')
    plt.xticks([])
    plt.yticks([])

    t, x1, x2 = ExfoJobj.syncstuff(t, b1, t+d, b2, dm=dm)

    axs[3].plot(t, x1, t, x2)
    axs[3].set_title('Shift Back by Known Phase')

    r = (cumtrapz(x2-x1, t)+np.flip(cumtrapz(np.flip(x2-x1), np.flip(t))))/2/abs(d)
    # r = cumtrapz((x2-x1)/abs(d), t)
    # integrate forward/backward fixes meaning issue

    # test shift back phase/2 issue
    tr, rr, r, = ExfoJobj.syncstuff(t[1:], r, t[1:]-d/2, r, dm=dm)
    # tr, y, rr, r, yy = syncstuff(t[1:], r, t[1:], r, dm=dm)

    axs[4].plot(tr, r, color=plt.rcParams['axes.prop_cycle'].by_key()['color'][3])
    axs[4].set_title('Integrate Difference')

    for a in axs:
        a.set_xticks([])
        a.set_yticks([])

    plt.tight_layout()

    if n is not None:
        return tr, r, noise, noise2
    else:
        return tr, r


def plot_error(t, x1, tr, r, dm=False):
    fig, ax = plt.subplots()
    ax.plot(t, x1, label='Original', color=plt.rcParams['axes.prop_cycle'].by_key()['color'][2])
    # tr, y, rr, r, yy = syncstuff(tr, r, tr-d/2, r, dm=dm)
    ax.plot(tr, r, label='Recovered', color=plt.rcParams['axes.prop_cycle'].by_key()['color'][3])
    t, x1, x3 = ExfoJobj.syncstuff(t, x1, tr, r, dm=dm)
    ax.plot(t, x1-x3, label='Error', linestyle='--', color=plt.rcParams['axes.prop_cycle'].by_key()['color'][1])
    plt.xticks([])
    plt.yticks([])
    # ax.set_title('Error')
    ax.legend()


def fake_func(t, d):
    x1 = np.sin(t)*2
    x2 = abs(signal.sawtooth((t)*3))+abs(signal.sawtooth((t)*5-1))-1+np.sin((t)*9)/5
    b1 = x1 + x2
    x3 = abs(signal.sawtooth((t+d)*3))+abs(signal.sawtooth((t+d)*5-1))-1+np.sin((t+d)*9)/5
    b2 = x1 + x3
    return x1, x2, x3, b1, b2


# %% PICA
t = np.arange(0, 2*np.pi, .001)
d = -.2
x1, x2, x3, b1, b2 = fake_func(t, d)
plot_PICA(x1, x2, b1, b2)
plt.savefig('figs/PICA.pdf', dpi=300, transparent=True)

tr, r = ICR(t, x1, x2, x3, b1, b2, d)
plt.savefig('figs/ICRexam.pdf', dpi=300, transparent=True)
plot_error(t, x1, tr, r)
plt.savefig('figs/ICRexamEr.pdf', dpi=300, transparent=True)

# %% Test ICR on real fake data
filt = exFilter(50)
Ex1 = ExfoJobj.ExfoJobj('1')
Ex1.Load_Batch('data/TB4', filt=filt)
Ex2 = ExfoJobj.ExfoJobj('2')
Ex2.Load_Batch('data/TB6', filt=filt)
Ex1.Wafer_Sync()
Ex2.Wafer_Sync()
d = -.05

# mix two scans
t, x1, x2 = ExfoJobj.syncstuff(Ex1.sync_base_x, Ex1.sync_base, Ex2.sync_base_x, Ex2.sync_nickel, dm=True)
t, x1, x3 = ExfoJobj.syncstuff(t, x1, (t-d), x2, dm=True)
t, x1, x2 = ExfoJobj.syncstuff(t, x1, Ex2.sync_base_x, Ex2.sync_nickel, dm=True)

# mix with random instead
x2 = filt(np.random.normal(0, 1, x1.shape))
x3 = np.roll(x2, int(d*-100))

b1 = x1 + x2
b2 = x1 + x3

b1 -= b1.mean()
b2 -= b2.mean()

# noise = filt(np.random.normal(0, abs(b1).mean()*.25, b1.shape))

tr, r = ICR(t, x1, x2, x3, b1, b2, d, dm=True)
plt.close()
plot_error(t, x1, tr, r, dm=True)
plt.savefig('figs/realeICR.pdf', dpi=300, transparent=True)
# %% with noise
t = np.arange(0, 2*np.pi, .001)

d = -.2
x1, x2, x3, b1, b2 = fake_func(t, d)

filt = exFilter(50)
tr, r, noise, noise2 = ICR(t, x1, x2, x3, b1, b2, d, n=.03, filt=filt)
plt.close()
plot_error(t, x1, tr, r)
plt.savefig('figs/ICRexamNoise.pdf', dpi=300, transparent=True)
d = -.05

# mix two scans
t, x1, x2 = ExfoJobj.syncstuff(Ex1.sync_base_x, Ex1.sync_base, Ex2.sync_base_x, Ex2.sync_nickel, dm=True)
t, x1, x3 = ExfoJobj.syncstuff(t, x1, (t-d), x2, dm=True)
t, x1, x2 = ExfoJobj.syncstuff(t, x1, Ex2.sync_base_x, Ex2.sync_nickel, dm=True)

# mix with random instead
x2 = filt(np.random.normal(0, 1, x1.shape))
x3 = np.roll(x2, int(d*-100))

b1 = x1 + x2
b2 = x1 + x3

b1 -= b1.mean()
b2 -= b2.mean()

# noise = filt(np.random.normal(0, abs(b1).mean()*.25, b1.shape))

# plot_PICA(x1, x2, b1, b2)

tr, r, noise, noise2 = ICR(t, x1, x2, x3, b1, b2, d, dm=True, n=.03, filt=filt)
plt.close()
plot_error(t, x1, tr, r, dm=True)
plt.savefig('figs/realeICRnoise.pdf', dpi=300, transparent=True)

# %% Remove repeatable error
w = .545
wo = .017
glass = 1.8631
k = .101

Exr = ExfoJobj.ExfoJobj('12')
Exr.Load_Meta('data/', 'testmeta')
# Ex.Make_Meta('ansys_dat_122.csv')
llim = 40
ulim = 65
Exr.Load_Batch('data/12', filt=exFilter(1000), llim=llim, ulim=ulim)

Exr.Wafer_Sync(resamp=(llim, ulim))

fig, ax = plt.subplots(3, 1)
ax[0].plot(Exr.sync_base_x, (Exr.sync_base-glass-w-k+wo)*1E3)
ax[0].set_title('Gage Block')
ax[0].margins(x=0)
ax[1].plot(Exr.sync_nickel_x, Exr.sync_nickel*1E3)
ax[1].set_title('Raw Nickel Scan')
ax[1].margins(x=0)
ax[2].plot(Exr.sync_nickel_x, Ex.ni*1E6)
ax[2].set_title('Recovered Nickel Scan')
ax[2].set_xlabel('Chuck Distance (mm)')
fig.tight_layout(pad=1)
ax[2].margins(x=0)
AxZoom.suplabel(ax, 'Laser Distance (µm)', labelpad=9)

plt.savefig('figs/remainder.pdf', dpi=300, transparent=True)
