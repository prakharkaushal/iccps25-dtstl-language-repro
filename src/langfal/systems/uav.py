"""Quadrotor UAV model of the paper (Sec. 4.2) and our tracking controller (vectorised over a batch).

Dynamics (paper Sec. 4.2; state x1,y1,z1 positions, x2,y2,z2 velocities, phi1,theta1,psi1 roll/
pitch/yaw, phi2,theta2,psi2 angular rates; inputs thrust f_t and torques tau_x, tau_y, tau_z):
    x2' = f_t/m (sin phi1 sin psi1 + cos phi1 cos psi1 sin theta1)
    y2' = f_t/m (cos phi1 sin psi1 sin theta1 - cos psi1 sin phi1)
    z2' = -g + f_t/m cos phi1 cos theta1
    phi2'   = (Iy - Iz)/Ix theta2 psi2 + tau_x/Ix
    theta2' = (Iz - Ix)/Iy phi2 psi2   + tau_y/Iy
    psi2'   = (Ix - Iy)/Iz phi2 theta2 + tau_z/Iz
The paper prints the inertia ratios inverted (I_x/(I_y - I_z) ...). Its source, ref. [47]
(Sabatino, KTH 2015, Eq. 2.22), uses (I_y - I_z)/I_x, which we follow (deviation C2).

Everything below the dynamics is OUR design because the paper specifies neither parameters nor the
tracking controller (decisions D14, D15, D20):
  * parameters: m = 0.5 kg, Ix = Iy = 5e-3, Iz = 9e-3 kg m^2, g = 9.81 m/s^2 (typical small quadrotor);
  * one signal sample per second; the drone starts at rest at the origin (x1(0) = 0);
  * cascaded PD tracker: x-position PD (+ reference velocity feed-forward) -> pitch command
    (tilt limited to 35 deg), altitude hold at z = 0, roll/yaw held at 0, attitude PD, thrust and
    torque saturation; RK4 integration with dt = 0.01 s; the reference is linearly interpolated
    between its samples.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class UAVParams:
    m: float = 0.5
    Ix: float = 5e-3
    Iy: float = 5e-3
    Iz: float = 9e-3
    g: float = 9.81
    f_max_factor: float = 2.5          # thrust limit = factor * m * g
    tau_max: float = 0.5               # N m


@dataclass(frozen=True)
class TrackerGains:
    kp_x: float = 4.0
    kd_x: float = 4.0
    kp_z: float = 4.0
    kd_z: float = 4.0
    kp_att: float = 400.0
    kd_att: float = 40.0
    tilt_max_deg: float = 35.0
    dt: float = 0.01                   # integration step (s)
    sample_period: float = 1.0         # seconds per signal sample (D20)


def _deriv(s, u, p: UAVParams):
    """s: (B, 12) = [x1,y1,z1,x2,y2,z2,ph1,th1,ps1,ph2,th2,ps2]; u: (B, 4) = [f_t, tx, ty, tz]."""
    ph1, th1, ps1 = s[:, 6], s[:, 7], s[:, 8]
    ph2, th2, ps2 = s[:, 9], s[:, 10], s[:, 11]
    ft, tx, ty, tz = u[:, 0], u[:, 1], u[:, 2], u[:, 3]
    sph, cph, sth, cth, sps, cps = np.sin(ph1), np.cos(ph1), np.sin(th1), np.cos(th1), np.sin(ps1), np.cos(ps1)
    d = np.empty_like(s)
    d[:, 0:3] = s[:, 3:6]
    d[:, 3] = ft / p.m * (sph * sps + cph * cps * sth)
    d[:, 4] = ft / p.m * (cph * sps * sth - cps * sph)
    d[:, 5] = -p.g + ft / p.m * cph * cth
    d[:, 6:9] = s[:, 9:12]
    d[:, 9] = (p.Iy - p.Iz) / p.Ix * th2 * ps2 + tx / p.Ix
    d[:, 10] = (p.Iz - p.Ix) / p.Iy * ph2 * ps2 + ty / p.Iy
    d[:, 11] = (p.Ix - p.Iy) / p.Iz * ph2 * th2 + tz / p.Iz
    return d


class UAVTracker:
    """Track(x_ref) of Algorithm 3: closed-loop simulation following x-position references.

    ``planar=True`` (default) integrates only the x-z-pitch subsystem. This is exact, not an
    approximation: the drone starts at rest with zero roll/yaw and the tracker commands zero roll,
    yaw and lateral motion, so tau_x = tau_z = 0 and every lateral/roll/yaw state and every cross
    term of the full model stays identically 0 (checked in tests/test_control.py).
    """

    def __init__(self, params: UAVParams = UAVParams(), gains: TrackerGains = TrackerGains(),
                 planar: bool = True):
        self.p, self.k, self.planar = params, gains, planar

    def _track_planar(self, Xref):
        p, k = self.p, self.k
        B, N = Xref.shape
        steps_per = int(round(k.sample_period / k.dt))
        dt = k.dt
        tmax = np.deg2rad(k.tilt_max_deg)
        fmax = p.f_max_factor * p.m * p.g
        x = np.zeros(B); z = np.zeros(B); vx = np.zeros(B); vz = np.zeros(B); th = np.zeros(B); w = np.zeros(B)
        out = np.empty((B, N))
        out[:, 0] = x

        def f(x, z, vx, vz, th, w, xr, vr):
            # tracker (same law as _control with phi = psi = 0)
            ax = k.kp_x * (xr - x) + k.kd_x * (vr - vx)
            th_des = np.clip(np.arctan2(ax, p.g), -tmax, tmax)
            c = np.cos(th)
            ft = np.clip(p.m * (p.g + k.kp_z * (-z) - k.kd_z * vz) / np.maximum(c, 0.2), 0.0, fmax)
            ty = np.clip(p.Iy * (k.kp_att * (th_des - th) - k.kd_att * w), -p.tau_max, p.tau_max)
            return ft, ty

        for seg in range(N - 1):
            x0, x1 = Xref[:, seg], Xref[:, seg + 1]
            vr = (x1 - x0) / k.sample_period
            for i in range(steps_per):
                xr = x0 + (x1 - x0) * (i / steps_per)
                ft, ty = f(x, z, vx, vz, th, w, xr, vr)      # zero-order hold over dt
                a = ft / p.m
                alpha = ty / p.Iy

                def d(vx_, vz_, th_, w_):
                    return vx_, vz_, a * np.sin(th_), -p.g + a * np.cos(th_), w_, alpha

                k1 = d(vx, vz, th, w)
                k2 = d(vx + 0.5 * dt * k1[2], vz + 0.5 * dt * k1[3], th + 0.5 * dt * k1[4], w + 0.5 * dt * k1[5])
                k3 = d(vx + 0.5 * dt * k2[2], vz + 0.5 * dt * k2[3], th + 0.5 * dt * k2[4], w + 0.5 * dt * k2[5])
                k4 = d(vx + dt * k3[2], vz + dt * k3[3], th + dt * k3[4], w + dt * k3[5])
                x = x + dt / 6.0 * (k1[0] + 2 * k2[0] + 2 * k3[0] + k4[0])
                z = z + dt / 6.0 * (k1[1] + 2 * k2[1] + 2 * k3[1] + k4[1])
                vx = vx + dt / 6.0 * (k1[2] + 2 * k2[2] + 2 * k3[2] + k4[2])
                vz = vz + dt / 6.0 * (k1[3] + 2 * k2[3] + 2 * k3[3] + k4[3])
                th = th + dt / 6.0 * (k1[4] + 2 * k2[4] + 2 * k3[4] + k4[4])
                w = w + dt / 6.0 * (k1[5] + 2 * k2[5] + 2 * k3[5] + k4[5])
            out[:, seg + 1] = x
        return out

    def _control(self, s, xr, vr):
        p, k = self.p, self.k
        ax = k.kp_x * (xr - s[:, 0]) + k.kd_x * (vr - s[:, 3])
        tmax = np.deg2rad(k.tilt_max_deg)
        th_des = np.clip(np.arctan2(ax, p.g), -tmax, tmax)
        az = k.kp_z * (0.0 - s[:, 2]) - k.kd_z * s[:, 5]
        tilt = np.maximum(np.cos(s[:, 6]) * np.cos(s[:, 7]), 0.2)
        ft = np.clip(p.m * (p.g + az) / tilt, 0.0, p.f_max_factor * p.m * p.g)
        tx = np.clip(p.Ix * (k.kp_att * (0.0 - s[:, 6]) - k.kd_att * s[:, 9]), -p.tau_max, p.tau_max)
        ty = np.clip(p.Iy * (k.kp_att * (th_des - s[:, 7]) - k.kd_att * s[:, 10]), -p.tau_max, p.tau_max)
        tz = np.clip(p.Iz * (k.kp_att * (0.0 - s[:, 8]) - k.kd_att * s[:, 11]), -p.tau_max, p.tau_max)
        return np.stack([ft, tx, ty, tz], axis=1)

    def track(self, Xref: np.ndarray) -> np.ndarray:
        """Xref: (B, N) references (one sample per sample_period). Returns x1 at the sample times."""
        Xref = np.atleast_2d(np.asarray(Xref, dtype=float))
        if self.planar:
            return self._track_planar(Xref)
        B, N = Xref.shape
        k = self.k
        steps_per = int(round(k.sample_period / k.dt))
        s = np.zeros((B, 12))
        out = np.empty((B, N))
        out[:, 0] = s[:, 0]
        dt = k.dt
        for seg in range(N - 1):
            x0, x1 = Xref[:, seg], Xref[:, seg + 1]
            vr = (x1 - x0) / k.sample_period
            for i in range(steps_per):
                frac = i / steps_per
                xr = x0 + (x1 - x0) * frac
                u = self._control(s, xr, vr)           # zero-order hold of the control over dt
                k1 = _deriv(s, u, self.p)
                k2 = _deriv(s + 0.5 * dt * k1, u, self.p)
                k3 = _deriv(s + 0.5 * dt * k2, u, self.p)
                k4 = _deriv(s + dt * k3, u, self.p)
                s = s + dt / 6.0 * (k1 + 2 * k2 + 2 * k3 + k4)
            out[:, seg + 1] = s[:, 0]
        return out
