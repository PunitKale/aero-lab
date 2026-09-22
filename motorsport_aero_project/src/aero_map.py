"""Synthetic aero response and bounded interpolation. No extrapolation."""
import numpy as np
from scipy.interpolate import RegularGridInterpolator

HEIGHT_DOMAIN = ((0.015,0.065),(0.025,0.095))

def coefficients(setup, front_height=None, rear_height=None, yaw_deg=0., roll_deg=0., drs=False):
    """Synthetic quasi-steady map; operating envelope is wider than static setup bounds."""
    hf = np.asarray(setup.front_height_m if front_height is None else front_height)
    hr = np.asarray(setup.rear_height_m if rear_height is None else rear_height)
    yaw, roll = np.asarray(yaw_deg), np.asarray(roll_deg)
    if np.any(~np.isfinite(hf)) or np.any(~np.isfinite(hr)) or np.any(~np.isfinite(yaw)) or np.any(~np.isfinite(roll)):
        raise ValueError("Nonfinite aero map coordinate")
    if np.any((hf<.015)|(hf>.065)|(hr<.025)|(hr>.095)|(np.abs(yaw)>20)|(np.abs(roll)>4)):
        raise ValueError("Aero map extrapolation rejected: height/yaw/roll domain")
    # Floor peak and low-height stall are assumed, smooth, inspectable responses.
    floor = 1.25*np.exp(-((hf-.033)/.033)**2-((hr-.057)/.055)**2)
    floor *= 1 - .22*np.exp(-((hf-.015)/.004)**2)
    front = .56 + .025*setup.front_wing_deg + .40*floor
    rear = .63 + .031*setup.rear_wing_deg + .60*floor
    yawloss = np.exp(-.0009*yaw*yaw-.004*roll*roll)
    pack = {"standard":(1.,1.),"efficient":(.95,.92),"high_load":(1.06,1.07)}[setup.package]
    front, rear = front*yawloss*pack[0], rear*yawloss*pack[0]
    cd = (.34+.00045*setup.front_wing_deg**2+.00060*setup.rear_wing_deg**2+.035*floor+.0003*yaw*yaw)*pack[1]
    from .config import CONFIG
    policy=CONFIG["drs_policy"]
    rear=rear*np.where(drs,policy["rear_downforce_multiplier"],1.)
    cd=cd*np.where(drs,policy["drag_multiplier"],1.)
    return front, rear, cd

class AeroMap:
    """Interpolated synthetic map for a fixed wing/package configuration."""
    def __init__(self, setup):
        setup.validate()
        self.axes=(np.linspace(.015,.065,11),np.linspace(.025,.095,15),np.linspace(-20,20,9))
        hf,hr,yaw=np.meshgrid(*self.axes,indexing="ij")
        self.interpolator=RegularGridInterpolator(self.axes,np.stack(coefficients(setup,hf,hr,yaw),axis=-1),bounds_error=True)

    def evaluate(self, front_height: float, rear_height: float, yaw_deg: float=0.):
        """Return front Cl, rear Cl and Cd; raises outside support."""
        return self.interpolator([[front_height,rear_height,yaw_deg]])[0]
