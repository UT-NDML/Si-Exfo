#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 23 12:00:22 2020.

@author: myo
"""
from nptdms import TdmsFile
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import pickle
from scipy import signal
import AxZoom


class ExfoJobj(object):
    """
    Object to create and manage exfoliation tool data.

    Parameters
    ----------
        Paths
    Attributes
    ----------
        Scan Vectors
        Load Vector
    """

    scans = {'b': 'base',
             'w': 'wafer',
             'n': 'nickel',
             's': 'stress',
             'l': 'load',
             'e': 'exfo'}

    def __init__(self, name):
        """
        Init.

        Parameters
        ----------
        name : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        self.name = name

    def Load_Scan(self, filepath, file, trim=False, scan=False, filt=None, llim=26, ulim=74):
        """
        Load scan.

        Parameters
        ----------
        filepath : String
            /path/to/file/
        file : String
            file (.tdms or .dat)
        scan : String
            'base'
            'wafer'
            'nickel'
            'stress'
            'load'
            'exfo'
        filt : Function, optional
            filtering function lzr = filt(lzr)

        Returns
        -------
        None.
        """
        if not scan:
            scan = self.scans.get(Path(file).name[0], 'base')
        print(scan)

        if Path(file).suffix == '.tdms':
            # import tdms - SLOW
            print('Loading ', Path(file).name)
            tdms_file = TdmsFile(Path(Path(filepath).joinpath(file)).with_suffix(".tdms"))
            group = tdms_file['Untitled']
            channel1 = group['encoder']
            enc = channel1.data
            # zero data and convert to mm
            # enc=(enc-min(enc)+1)/100

            time = group['Untitled']
            # elapsed time in seconds
            time = time - time[0]

            channel2 = group['laser']
            lzr = channel2.data
            # zero data and convert to mm
            # enc = (enc-min(enc)+1) / 100
            # convert to mm, but leave enc at lv zero
            # enc = enc / 100
            channel2 = group['load']
            lod = channel2.data

        elif 'trim' in Path(file).name:
            [time, enc, lzr, trim] = pickle.load(
                open(Path(Path(filepath).joinpath(file)).with_suffix(".dat"), 'rb'))
            print('Loading ', Path(file).name)

        elif Path(file).suffix == '.dat':
            if scan == 'load':
                [time, lod, enc, lzr] = pickle.load(
                    open(Path(Path(filepath).joinpath(file)).with_suffix(".dat"), 'rb'))
            else:
                [time, enc, lzr] = pickle.load(
                    open(Path(Path(filepath).joinpath(file)).with_suffix(".dat"), 'rb'))
            print('Loading ', Path(file).name)

        else:
            raise ValueError('file load error')

        if scan == 'load':
            self.Load_Load_Scan(time, lod, enc, lzr, filt=filt, llim=llim, ulim=ulim)
        else:
            setattr(self, scan, Scan(time, enc, lzr, trim=trim, filt=filt, llim=llim, ulim=ulim))

    def Load_Load_Scan(self, time, lod, enc, lzr, filt=None, llim=26, ulim=74):
        self.load = Lscan()
        tempst = np.stack([enc, lod, lzr, time])
        y = np.delete(tempst, (tempst[0, :] > ulim) | (tempst[0, :] < llim), 1)
        self.load.time = y[3, :]
        self.load.encr = y[0, :].copy()
        enc = signal.medfilt(y[0, :], 21)
        # convert to mm
        enc = enc / 100
        # shift from laser to roller
        enc = enc-32.6
        self.load.enc = y[0, :]
        self.load.lzrr = y[2, :].copy()
        self.load.lzr = y[2, :].copy()
        if filt:
            print('Filtering Laser')
            self.load.lzr = filt(lzr)
        # filters
        # lzr = signal.medfilt(lzr, 21)
        # self.trim = trim
        self.load.lod = y[1, :]
        # self.load.time = time
        self.load.enc = enc
        # self.load.lzr = lzr

    def Load_Batch(self, directory, trim=False, filt=None, llim=26, ulim=74):
        """
        Load a batch of scan data thats describes one exfoliation

        Parameters
        ----------
        directory : String
            'directory full of a set of scans. tmds and/or dat'
        trim : array or slice, optional
            Specify which scans to skip. The default is False.
        filt : Function, optional
            filtering function lzr = filt(lzr)

        Returns
        -------
        None.
        """
        names = set([Path(d.stem).stem for d in [*Path(directory).iterdir()]])
        for n in names:
            filepath = directory
            if Path(directory).joinpath(n).with_suffix('.trim.dat').exists():
                file = Path(n).with_suffix('.trim.dat')
            elif Path(directory).joinpath(n).with_suffix('.dat').exists():
                file = Path(n).with_suffix('.dat')
            elif Path(directory).joinpath(n).with_suffix('.tdms').exists():
                file = Path(n).with_suffix('.tdms')
                print(file)
                self.Load_Scan(filepath, file, trim, scan=False, filt=None, llim=llim, ulim=ulim)
                scan = self.scans.get(Path(file).name[0], 'base')
                getattr(self, scan).Pickle_TDMS(directory, file)
            else:
                print('load error')
                print(n)
                continue
            self.Load_Scan(filepath, file, trim, scan=False, filt=filt, llim=llim, ulim=ulim)

    def Get_Stress(self, win=100, wafer_thickness=500E-6, filt=None):
        MSi = 1.803E11
        ENi = 180E9
        nuNi = .31
        # wafer_thickness = 500E-6
        # s = filt(self.sync_stress)
        z = np.polyfit(self.sync_stress_x, self.sync_stress, 2)
        p = np.poly1d(z)
        # s = p(self.sync_stress_x)
        dp = np.polyder(p)
        ds = dp(self.sync_stress_x)
        ddp = np.polyder(p, 2)
        dds = ddp(self.sync_stress_x)
        R = abs(((1+ds**2)**1.5)/dds)
        # mask = np.isnan(R)
        # R[mask] = np.interp(np.flatnonzero(mask), np.flatnonzero(~mask), R[~mask])
        ni = self.ni
        if filt:
            # R = filt(R)
            ni = filt(self.ni)
        # Convert to meters
        R = R*1E-3
        self.S = (MSi*wafer_thickness**2)/(6*ni*R)
        +(2*ni*ENi)/(3*R*(1-nuNi))
        self.R = R

    def Wafer_Sync(self, d='f', resamp=False):
        """
        Take scan means and sync them togther to process as a wafer

        Parameters
        ----------
        d : string, optional
            specify scan direction forward 'f' or backward 'b'. The default is 'f'.

        Returns
        -------
        None.
        """

        scans = [scan for scan in self.scans.values() if getattr(self, scan, False)]
        if 'load' in scans:
            scans.remove('load')

        if resamp:
            X = np.arange(resamp[0], resamp[1], .01)
            for scan in scans:
                m = [*getattr(getattr(self, scan), d+'means')]
                x = m[4]
                y = m[0]
                Y = np.interp(X, x, y)
                m[0] = Y
                m[4] = X

                setattr(getattr(self, scan), d+'means', m)

        trim_min = max([getattr(getattr(self, scan), d+'means')[4].min() for scan in scans])
        trim_max = min([getattr(getattr(self, scan), d+'means')[4].max() for scan in scans])

        idx_min = []
        idx_max = []
        for scan in scans:
            scan_x = getattr(getattr(self, scan), d+'means')[4]
            idx_min.append(np.where(scan_x == trim_min)[0][0])
            idx_max.append(np.where(scan_x == trim_max)[0][0])

        x_len = min(idx_max)-max(idx_min)

        for scan in scans:
            scan_mean = getattr(getattr(self, scan), d+'means')[0]
            scan_x = getattr(getattr(self, scan), d+'means')[4]
            x_min = np.where(scan_x == trim_min)[0][0]
            setattr(self, 'sync_'+scan, scan_mean[x_min:x_min+x_len])
            setattr(self, 'sync_'+scan+'_x', scan_x[x_min:x_min+x_len])

        # need to add scaling if enc is not uniform
    def Wafer_Make(self, w=.546, wo=.017, glass=1.8631, k=.101, filt=None):

        self.x = self.sync_base_x
        self.w = glass+w+k-wo
        toolfloor = self.sync_base-self.w
        self.ni = (self.sync_nickel-toolfloor)*1E-3
        # self.ni = ((self.sync_base-self.sync_nickel)-toolfloor)*1E-3
        if hasattr(self, 'sync_exfo'):
            # self.ex = ((self.sync_base-self.sync_exfo)-toolfloor)*1E-3
            self.ex = (self.sync_exfo-toolfloor+wo)*1E-3
            if filt:
                self.ex = filt(self.ex)
        # self.Get_Stress()
        # self.Wafer = np.vstack((ni, ex, S)).T
        if filt:
            self.ni = filt(self.ni)
        if hasattr(self, 'load'):
            self.load.enc = self.load.enc-self.x[0]

    def Pickle_Wafer(self, filepath, file):
        """Pickle the wafer data so it can be loaded faster."""
        print('Pickling ', Path(file).name)
        pickle.dump([self.x, self.w, self.ni, self.ex, self.S, self.Load, self.load], open(
            Path(filepath).joinpath(file).with_suffix(".dat"), 'wb'))

    def Load_Wafer(self, filepath, file):
        [self.x, self.w, self.ni, self.ex, self.S, self.Load, self.load] = pickle.load(
            open(Path(Path(filepath).joinpath(file)).with_suffix(".dat"), 'rb'))
        print('Loading ', Path(file).name)

    def Make_Meta(self, file, i=2):
        """
        i: 0-Ni (um),1-Si (um), 2-T (N), 3-S (MPa),4-a (um), 5-h (um), 6-K2, 7-K1
        """
        from sklearn.gaussian_process import GaussianProcessRegressor
        from sklearn.gaussian_process.kernels import DotProduct
        from sklearn.gaussian_process.kernels import ConstantKernel as C
        from sklearn import preprocessing

        kernel = C(.1, (0.01, 10.0)) * (DotProduct(sigma_0=7.74, sigma_0_bounds=(0.01, 10.0)) ** 2)

        adat = np.genfromtxt(file, delimiter=",")[1:, :]
        X = np.concatenate((adat[:, :i], adat[:, i+1:]), 1)
        self.scalerX = preprocessing.StandardScaler().fit(X)
        y = np.expand_dims(adat[:, i], 1)
        self.scalery = preprocessing.StandardScaler().fit(y)

        self.gpr = GaussianProcessRegressor(
            kernel=kernel, random_state=0, n_restarts_optimizer=0, alpha=.001).fit(
                self.scalerX.transform(X), self.scalery.transform(y))

    def Pickle_Meta(self, filepath, file):
        """Pickle the meta so it can be loaded faster."""
        print('Pickling ', Path(file).name)
        pickle.dump([self.scalerX, self.scalery, self.gpr], open(
            Path(filepath).joinpath(file).with_suffix(".dat"), 'wb'))

    def Load_Meta(self, filepath, file):
        [self.scalerX, self.scalery, self.gpr] = pickle.load(
            open(Path(Path(filepath).joinpath(file)).with_suffix(".dat"), 'rb'))
        print('Loading ', Path(file).name)

    def Make_Load(self, ex=8, a=1500, h=150, k2=0, k1=730, filt=None, floor=False):
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

        const = np.array([0, ex, 0, a, h, k2, k1])
        C = np.ones((self.ni.shape[0], 7))*const

        ni = self.ni
        if filt:
            ni = filt(self.ni)
        Xtest = C
        Xtest[:, 0] = ni*1E6
        Xtest[:, 2] = self.S*1E-6

        # Compute load with scaling
        self.Load = self.scalery.inverse_transform(self.gpr.predict(self.scalerX.transform(Xtest)))
        if floor:
            self.Load[self.Load < floor] = floor

    def Export_Load(self, filepath, file, wafer_points=3000, ramp=False, window=False):
        # Interp load to fit export
        Load = np.interp(np.linspace(0, len(self.Load)-1, wafer_points),
                         np.arange(0, len(self.Load)), np.squeeze(self.Load))
        # Convert to N?
        Load = Load/9.81
        if window:
            pad = np.ones(int((window-wafer_points)/2))
            Load = np.concatenate((pad*Load[0], Load, pad*Load[-1]))
        if ramp:
            Load = np.concatenate((np.linspace(0, Load[0], ramp), Load.flatten()))
        np.savetxt(Path(Path(filepath).joinpath(file)).with_suffix(".csv"),
                   Load, delimiter=',')

    def Load_exLoad(self, filepath, file, trim=False, filt=None):
        tdms_file = TdmsFile(Path(Path(filepath).joinpath(file)).with_suffix(".tdms"))
        group = tdms_file['Untitled']
        channel1 = group['encoder']
        enc = channel1.data
        # zero data and convert to mm
        # enc=(enc-min(enc)+1)/100

        time = group['Untitled']
        # elapsed time in seconds
        time = time - time[0]
        channel3 = group['load']
        load = channel3.data
        self.exLoad = Scan(time, enc, load, trim=trim, filt=filt)

    def Load_exLoadalt(self, filepath, file):
        tdms_file = TdmsFile(Path(Path(filepath).joinpath(file)).with_suffix(".tdms"))
        group = tdms_file['Untitled']
        channel1 = group['encoder']
        enc = channel1.data
        channel3 = group['load']
        load = channel3.data
        self.exLoad = enc, load
        # %% plot zone

    def Plot_Wafer(self):

        color = plt.rcParams['axes.prop_cycle'].by_key()['color'][0]
        fig, ax1 = plt.subplots(figsize=(8, 4))
        ax1.plot(self.x, self.ni*1E6, color=color, linestyle='--', label='Ni Thickness')
        if hasattr(self, 'ex'):
            ax1.plot(self.x, self.ex*1E6, color=color, linestyle='-', label='Si Thickness')
        ax1.tick_params(axis='y', labelcolor=color)
        # ax1.set_title('Wafer Profile')
        ax1.set_xlabel('Chuck (mm)')
        ax1.set_ylabel('Si and Ni Film Thickness (µm)', color=color)

        color = plt.rcParams['axes.prop_cycle'].by_key()['color'][1]
        ax2 = ax1.twinx()
        ax2.plot(self.x, self.S/1E8, color=color, linestyle='-.', label='Ni Stress')
        ax2.plot(self.x, self.Load/9.81, color=color, linestyle='-', label='Handle Tension')
        if hasattr(self, 'load'):
            x, _, y = syncstuff(self.x, self.Load, self.load.enc, self.load.lod, dm=False)
            ax2.plot(x, y, color=color, linestyle=':', label='Measured Tension')
        ax2.tick_params(axis='y', labelcolor=color)
        ax2.set_ylabel(r'Ni Stress (Pa$\cdot 10^8$) and Handle Tension (Kg)', color=color)
        # lines, labels = ax1.get_legend_handles_labels()
        # lines2, labels2 = ax2.get_legend_handles_labels()
        # ax2.legend(lines + lines2, labels + labels2, loc=0)
        fig.legend(bbox_to_anchor=(0.03, 0.5, .93, 0.5), loc='upper left', ncol=5, mode="expand", borderaxespad=0., handletextpad=0.1)

        fig.tight_layout(pad=0.1)
        # ax1.set_xlim(left=0, right=25)
        ax1.margins(x=0)
        ax1.set_title('')
        ax1.set_xlabel('Distance from Stable Crack Start (mm)')
        return fig, ax1, ax2

    def Plot_Batch(self):
        scans = [scan for scan in self.scans.values() if getattr(self, scan, False)]
        [(getattr(self, scan).plot_check(), plt.suptitle(scan)) for scan in scans]
        [(getattr(self, scan).plot_scans_sub(), plt.suptitle(scan)) for scan in scans]


# %%


class Scan(object):
    """Object to stor LabView scans."""

    def __init__(self, time, enc, lzr, llim=41, ulim=65, trim=False, filt=None):
        """
        Init.

        Parameters
        ----------
        time : np.array from tdms import
            Time in unix format
        enc : np.array from tdms import
            Encoder data 10um unit
        lzr : np.array from tdms import
            Laser measurement data (mm)
        llim : int, optional
            Lower scan cutoff in mm. The default is 20.
        ulim : int, optional
            Upper scan cutoff in mm. The default is 80.
        trim : array or slice, optional
            Specify which scans to skip. The default is False.

        Raises
        ------
        ValueError
            When encoder data is really bad.
        """
        # zero data and convert to mm
        # enc = (enc-min(enc)+1) / 100
        # convert to mm, but leave enc at lv zero

        self.time = time
        self.encr = enc.copy()
        enc = signal.medfilt(enc, 21)
        enc = enc / 100
        self.enc = enc
        self.lzrr = lzr.copy()
        self.lzr = lzr.copy()
        # if filt:
        #     print('Filtering Laser')
        #     self.lzr = filt(lzr)
        # filters
        # lzr = signal.medfilt(lzr, 21)
        self.trim = trim

        self.g = np.gradient(self.enc/self.enc.max())
        if any(*np.where(self.g > .005)):
            print('JUMPS AT', np.where(self.g > .005))

        def zero_runs(a):
            """Create an array that is 1 where a is 0, and pad each end with an extra 0."""
            iszero = np.concatenate(
                ([0], np.logical_not(np.equal(a, 0).view(np.int8)), [0]))
            absdiff = np.abs(np.diff(iszero))
            # Runs start and end where absdiff is 1.
            ranges = np.where(absdiff == 1)[0].reshape(-1, 2)
            return ranges

        # Stack data to trim into individual scans
        tempst = np.stack([self.enc, self.lzr])
        # trim edges of scans
        tempst[:, ((tempst[0, :] > ulim) | (tempst[0, :] < llim))] = 0
        # find indices of runs start stop
        self.idx = zero_runs(tempst[0, :])
        print('Loaded ', self.idx.shape[0] / 2, ' scans')

        if np.asarray(trim).any():
            self.idx = np.delete(self.idx, trim, 0)
            print(self.idx.shape)

        if self.idx.size == 0:
            raise ValueError('encoder data is very bad')

        # %% Stack scans
        # find shortest scan and trim others to match. then stack them
        def stack_scans(idx, enc, lzr, fb):
            minL = min(abs(idx[:, 0]-idx[:, 1])[fb:][::2])
            estack = np.empty((0, minL))
            lstack = estack.copy()
            for ii in idx[fb:][::2, :]:
                ef = enc[range(*ii.tolist())]
                if filt:
                    # print('Filtering Laser')
                    lf = filt(lzr[range(*ii.tolist())])
                else:
                    lf = lzr[range(*ii.tolist())]
                estack = np.append(estack, np.expand_dims(ef[:minL], axis=0), axis=0)
                lstack = np.append(lstack, np.expand_dims(lf[:minL], axis=0), axis=0)
            return [estack, lstack]

        self.eforward, self.lforward = stack_scans(self.idx, self.enc, self.lzr, 0)
        self.ebackward, self.lbackward = stack_scans(self.idx, self.enc, self.lzr, 1)

        # %%Calculate measurements per position
        def lasers_per_enc(ence, lzre):
            from collections import defaultdict
            fd = []
            for ii, jj in zip(ence, lzre):
                fd.append(dict(zip(ii, jj)))

            p_error = defaultdict(list)
            # you can list as many input dicts as you want here
            for d in fd:
                for key, value in d.items():
                    p_error[key].append(value)
            return p_error

        self.flper_enc = lasers_per_enc(self.eforward, self.lforward)
        self.blper_enc = lasers_per_enc(self.ebackward, self.lbackward)

        # %% Calculate errors relative to position
        def err_by_pos(error_dict):
            x = []
            for key, value in error_dict.items():
                value = np.array(value)
                value = value-value.mean()
                error_dict.update({key: value})
                x.append(abs(value).mean())
            x = np.array(x)
            x = x[~np.isnan(x)]
            return x

        self.error_byp_f = err_by_pos(self.flper_enc.copy())
        self.error_byp_b = err_by_pos(self.blper_enc.copy())

        # %% Get mean scan and std
        def get_mean(lzr_per_enc):
            mn = np.array([])
            std = np.array([])
            n = np.array([])
            encm = np.array([])
            for key, value in lzr_per_enc.items():
                mn = np.append(mn, np.array(value).mean())
                std = np.append(std, np.std(value))
                n = np.append(n, len(value))
                encm = np.append(encm, key)
            SEM = std/np.sqrt(n)
            t = np.vstack((mn, std, n, SEM, encm)).T
            x = t[t[:, 4].argsort()].T
            mn, std, n, SEM, encm = [*x]
            return mn, std, n, SEM, encm

        self.fmeans = get_mean(self.flper_enc)
        self.bmeans = get_mean(self.blper_enc)

        # %% Get error along scan for each scan
        def scan_error(estack, lstack, means):
            [mn, std, n, SEM, encm] = means
            M = dict(zip(encm, mn))
            # covert to microns
            scan_err = [1000 * np.array([l-M[e] for e, l in zip(*scan)])
                        for scan in zip(estack, lstack)]
            smean, sstd, smed = zip(*[
                [scan.std(), abs(scan).mean(), np.median(abs(scan))]
                for scan in scan_err])
            return [scan_err, smean, smed, sstd]

        [self.fscan_error, self.fsmean, self.fsmed, self.fsstd] = scan_error(
            self.eforward, self.lforward, self.fmeans)
        [self.bscan_error, self.bsmean, self.bsmed, self.bsstd] = scan_error(
            self.ebackward, self.lbackward, self.bmeans)

        # %%

    def Pickle_TDMS(self, filepath, file, Trim=False):
        """Pickle the TDMS so it can be loaded faster."""
        print('Pickling ', Path(file).name)
        if Trim is not False:
            pickle.dump([self.time, self.encr, self.lzrr, self.trim], open(
                Path(filepath).joinpath(file).with_suffix(".trim.dat"), 'wb'))
        elif Path(file).name[0] == 'l':
            pickle.dump([self.time, self.lod, self.encr, self.lzrr], open(
                Path(filepath).joinpath(file).with_suffix(".dat"), 'wb'))
        else:
            pickle.dump([self.time, self.encr, self.lzrr], open(
                Path(filepath).joinpath(file).with_suffix(".dat"), 'wb'))
        # %% plot zone

    def plot_check(self):
        """
        Plot quick check of enc data vs time to check for jumps and junk.

        Returns
        -------
        fig : TYPE
            DESCRIPTION.
        ax1 : TYPE
            DESCRIPTION.
        ax2 : TYPE
            DESCRIPTION.
        """
        fig, ax1 = plt.subplots()
        for ii in self.idx:
            ax1.scatter(self.idx[:, 0], self.enc[self.idx[:, 0]], marker='x')
        for ii in self.idx:
            ax1.scatter(self.idx[:, 1]-1, self.enc[self.idx[:, 1]-1], marker='x', color='blue')
        ax1.plot(self.enc)
        plt.title('Check Start and Stop')
        plt.xlabel('time steps')
        plt.ylabel('encoder distance')

        ax2 = ax1.twinx()
        c = plt.rcParams['axes.prop_cycle'].by_key()['color'][2]
        ax2.plot(self.g/self.g.max(), color=c)
        plt.ylabel('encoder gradient')
        # check errors
        fx = np.array(self.idx[1:][::2, :].mean(axis=1), dtype='int')
        bx = np.array(self.idx[0:][::2, :].mean(axis=1), dtype='int')
        # median or mean?
        ax2.plot(fx, self.fsmean)
        ax2.plot(bx, self.bsmean)
        return fig, ax1, ax2

    def plot_scans(self):
        """
        Plot forwards and backwards scans calculated from idx.

        Returns
        -------
        fig2 : TYPE
            DESCRIPTION.
        ax2 : TYPE
            DESCRIPTION.
        fig3 : TYPE
            DESCRIPTION.
        ax3 : TYPE
            DESCRIPTION.

        """
        fig2, ax2 = plt.subplots()
        # grab every other scan from idices
        # forward
        for ii in self.idx[0:][::2, :]:
            ef = self.enc[range(*ii.tolist())]
            lf = self.lzr[range(*ii.tolist())]
            ax2.plot(ef, lf)
        ax2.set_title('Forward Chuck Scans')
        ax2.set_xlabel('Chuck (mm)')
        ax2.set_ylabel('Laser Distance (mm)')

        fig3, ax3 = plt.subplots()
        for ii in self.idx[1:][::2, :]:
            eb = self.enc[range(*ii.tolist())]
            lb = self.lzr[range(*ii.tolist())]
            ax3.plot(eb, lb)
        ax3.set_title('Backward Chuck Scans')
        ax3.set_xlabel('Chuck (mm)')
        ax3.set_ylabel('Laser Distance (mm)')
        return fig2, ax2, fig3, ax3

    def plot_scans2(self, trim=np.s_[:]):
        """
        Plot forwards and backwards scans.

        Parameters
        ----------
        trim : TYPE, optional
            DESCRIPTION. The default is np.s_[50:-500].

        Returns
        -------
        fig2 : TYPE
            DESCRIPTION.
        ax2 : TYPE
            DESCRIPTION.
        fig3 : TYPE
            DESCRIPTION.
        ax3 : TYPE
            DESCRIPTION.

        """
        fig2, ax2 = plt.subplots()
        # grab every other scan from idices using attributes
        # forward
        for ii, jj in zip(self.eforward, self.lforward):
            plt.plot(ii[trim], jj[trim])
        ax2.set_title('Forward Chuck Scans')
        ax2.set_xlabel('Chuck (mm)')
        ax2.set_ylabel('Laser Distance (mm)')

        fig3, ax3 = plt.subplots()
        for ii, jj in zip(self.ebackward, self.lbackward):
            plt.plot(ii[trim], jj[trim])
        ax3.set_title('Backward Chuck Scans')
        ax3.set_xlabel('Chuck (mm)')
        ax3.set_ylabel('Laser Distance (mm)')
        return fig2, ax2, fig3, ax3

    def plot_scans_sub(self, trim=np.s_[:]):
        fig, (ax1, ax2) = plt.subplots(2, 1, sharey=True, sharex=True)
        for ii, jj in zip(self.eforward, self.lforward):
            ax1.plot(ii[trim], jj[trim])
        ax1.set_title('Forward Chuck Scans')
        ax1.set_xlabel('Chuck (mm)')
        # ax1.set_ylabel('Laser Distance (mm)')

        for ii, jj in zip(self.ebackward, self.lbackward):
            ax2.plot(ii[trim], jj[trim])
        ax2.set_title('Backward Chuck Scans')
        ax2.set_xlabel('Chuck (mm)')
        # ax2.set_ylabel('Laser Distance (mm)')

        AxZoom.suplabel(ax1, 'Laser Distance (mm)', labelpad=10)
        return ax1, ax2, fig

    def plot_mean(self, trim=np.s_[:]):
        """
        Plot the means of F-B scans with 1 std window.

        Parameters
        ----------
        trim : TYPE, optional
            DESCRIPTION. The default is np.s_[50:-500].

        Returns
        -------
        fig : TYPE
            DESCRIPTION.
        ax : TYPE
            DESCRIPTION.

        """
        def mean_plot(means):
            means = [ii[trim] for ii in means]
            mn, std, n, SEM, encm = means
            fig, ax = plt.subplots()
            # ax.fill_between(x, mn - SEM, mn + SEM, alpha=0.2)
            ax.fill_between(encm, mn - std, mn + std, alpha=0.2)
            ax.plot(encm, mn)
            return fig, ax

        fig, ax = mean_plot(self.fmeans)
        ax.set_title('Forward Scan Mean')
        ax.set_xlabel('Chuck (mm)')
        ax.set_ylabel('Laser Distance (mm)')

        fig2, ax2 = mean_plot(self.bmeans)
        ax2.set_title('Backward Scan Mean')
        ax2.set_xlabel('Chuck (mm)')
        ax2.set_ylabel('Laser Distance (mm)')

    def plot_mean_sub(self, trim=np.s_[:]):
        def mean_plot(means, ax):
            means = [ii[trim] for ii in means]
            mn, std, n, SEM, encm = means
            ax.fill_between(encm, mn - std, mn + std, alpha=0.2)
            ax.plot(encm, mn)

        fig, (ax1, ax2) = plt.subplots(2, 1, sharey=True, sharex=True)
        mean_plot(self.fmeans, ax1)
        mean_plot(self.bmeans, ax2)
        # fig.tight_layout()
        ax1.set_title('Scan Means')
        # fig.suptitle('Scan Means')
        # ax1.set_title('Forward')
        # ax2.set_title('Backward')
        AxZoom.suplabel(ax1, 'Laser Distance (mm)', labelpad=10)
        ax1.set_ylabel('Forward')
        ax2.set_ylabel('Backward')
        ax2.set_xlabel('Chuck (mm)')
        return ax1, ax2, fig

    def plot_error_byp(self, m=2, bins=50):
        """
        Plot histograms of error from mean for each unique encoder position for F-B and combined.
        Plot error to mean for each unique encoder value.

        Trim outliers for more legible axis.

        Parameters
        ----------
        m : int, optional
            exclude outliers m standard deviations out. The default is 2.
        bins : int, optional
            Histogram bins. The default is 500.

        Returns
        -------
        ax and fig handles
            forward, backwards, and combined.

        """
        def reject_outliers(data, m=m):
            return data[abs(data - np.mean(data)) < m * np.std(data)]

        fig1, (ax1, ax2) = plt.subplots(2, 1, sharey=True, sharex=True, constrained_layout=True)
        # fig1.tight_layout()
        # fig1, ax1 = plt.subplots()
        ax1.hist(reject_outliers(self.error_byp_f * 1000), bins)
        ax1.set_title('Forward Height Error by Position')
        ax1.set_ylabel('Counts')
        # ax1.set_xlabel('Laser Distance Error (µm)')

        # fig2, ax2 = plt.subplots()
        ax2.hist(reject_outliers(self.error_byp_b * 1000), bins)
        ax2.set_title('Backward Height Error by Position')
        ax2.set_ylabel('Counts')
        ax2.set_xlabel('Laser Distance Error (µm)')

        fig3, ax3 = plt.subplots()
        x = np.concatenate((self.error_byp_f, self.error_byp_b)) * 1000
        ax3.hist(reject_outliers(x[~np.equal(x, 0)]), bins)
        ax3.set_title('Combined F-B Height Error by Position')
        ax3.set_ylabel('Counts')
        ax3.set_xlabel('Laser Distance Error (µm)')
        return ax1, fig1, ax2, ax3, fig3

    def plot_scan_error(self):
        """Plot median error and std for each scan."""
        fig, ax = plt.subplots()
        ax.plot(self.fsmed, label='Forward Median')
        ax.plot(self.bsmed, label='Backward Median')
        ax.legend()
        ax.set_title('Per Scan Error')
        ax.set_xlabel('Scan')
        ax.set_ylabel('Laser Median Error (µm)')

        ax2 = ax.twinx()
        ax2.plot(self.fsstd, label='Forward Std', linestyle='--')
        ax2.plot(self.bsstd, label='Backward Std', linestyle='--')
        ax2.set_ylabel('Laser Error Std (µm)')
        ax2.legend()
        # fig.legend(loc="upper right", bbox_to_anchor=(1,1), bbox_transform=ax.transAxes)
        return fig, ax, ax2

    def plot_densities(self):
        """Plot freq domain stuff."""
        # plt.csd(mn, mnb, NFFT = 1024, detrend='mean')
        # plt.csd(mn, mnb, NFFT = 64, Fs = 1, noverlap = 32, pad_to=150, detrend='mean')
        fig, ax = plt.subplots()
        ax.csd(self.fmeans[0], self.bmeans[0],
               NFFT=129, Fs=2, noverlap=12, pad_to=900, detrend='mean')
        ax.set_xlabel('Normalized Frequency')
        ax.set_xlabel('Combined F-B Spectral Density')
        ax.set_title('CSD')

        # plt.set_cmap('inferno')
        # fig2, ax2 = plt.subplots()
        # ax2.specgram(self.fmeans[0],
        #              NFFT=65, Fs=1, noverlap=32, detrend='mean', pad_to=200, mode='magnitude')
        # t = signal.butter(10, .0005, btype='lowpass', output='sos')
        # tt = signal.sosfilt(t, self.fmeans[0]-self.fmeans[0].mean())
        # ttb = signal.sosfilt(t, self.bmeans[0]-self.bmeans[0].mean())
        # fig3, ax3 = plt.subplots()
        # plt.plot(tt)
        # plt.plot(ttb)

    # %%
    def plot_all(self):
        """Run all the plots."""
        self.plot_check()
        self.plot_scans2()
        self.plot_error_byp(bins=50)
        self.plot_mean()
        self.plot_scan_error()
        # self.plot_densities()


# %%
class Lscan(Scan):
    def __init__(self):
        pass


# %%
def syncstuff(x1, y1, x2, y2, dm=False, r=2):
    if r:
        x1 = x1.round(2)
        x2 = x2.round(2)

    if dm:
        f = dict(zip(x1, y1-y1.mean()))
        b = dict(zip(x2, y2-y2.mean()))
    else:
        f = dict(zip(x1, y1))
        b = dict(zip(x2, y2))

    X = [*set.intersection(set(x1), set(x2))]
    X.sort()

    Y1 = []
    Y2 = []

    for i in X:
        if i in f.keys() and i in b.keys():
            Y1.append(f[i])
            Y2.append(b[i])
    return map(lambda x: np.array(x), [X, Y1, Y2])
