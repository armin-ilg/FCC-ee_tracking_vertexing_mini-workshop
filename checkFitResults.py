import numpy as np
import math

import matplotlib
matplotlib.use("Agg") 
import matplotlib.pyplot as plt

import io
import base64
from scipy.interpolate import splrep, splev
from podio import root_io
import time
import sys
from scipy.stats import norm
from scipy.stats import chi2

import sys
import math
from podio import root_io

input_file_path_keep = sys.argv[1]
podio_reader_keep = root_io.Reader(input_file_path_keep)

diff_D0 = []
diff_Z0 = []
diff_pT = []  
chi2_ndf_arr = []
p_value_arr = []

for i, event in enumerate(podio_reader_keep.get("events")):

    MCParticle = event.get("MCParticles")
    tracks = event.get("FittedTracks")
    # tracks = event.get("FittedTracksWithFilteredHits")

    print("Processing event:", i, " with ", MCParticle.size(), 
          " MCParticles and ", tracks.size(), " tracks.")

    if tracks.size() > 1:
        print("Too many tracks!")
        continue

    

    for mcpart in MCParticle:

        true_D0 = 0
        true_Z0 = 0
        true_pT = 0
        E = 0

        if mcpart.getPDG() != 13 and mcpart.getPDG() != -13:
            continue

        px = mcpart.getMomentum().x
        py = mcpart.getMomentum().y
        pT = math.sqrt(px*px + py*py)
        
        true_pT = pT

        x0 = mcpart.getVertex().x
        y0 = mcpart.getVertex().y
        z0 = mcpart.getVertex().z

        print("Vertex:", x0, y0, z0)

        true_D0 = -(x0*py - y0*px)/pT
        true_Z0 = z0

        E = mcpart.getEnergy()
        break

    for track in tracks:
        trackStates = track.getTrackStates()
        for ts in trackStates:
            if ts.location != 1:
                print("Skippin track with location:", ts.location)
                continue
            else:
                print("Found track with location == 1, processing it.")

            print("Track state:", ts.omega, ts.D0, ts.Z0)
            reco_D0 = ts.D0
            reco_Z0 = ts.Z0

            c_mm_s = 2.998e11
            a = 1e-15 * c_mm_s
            reco_pT = abs(a * (2.0 / ts.omega))

            print("True D0:", true_D0, "Reco D0:", reco_D0,
                  "Diff:", reco_D0 - true_D0)
            print("True Z0:", true_Z0, "Reco Z0:", reco_Z0,
                  "Diff:", reco_Z0 - true_Z0)
            print("True pT:", true_pT, "Reco pT:", reco_pT,
                  "Diff:", reco_pT - true_pT)

            diff_D0.append(reco_D0 - true_D0)
            diff_Z0.append(reco_Z0 - true_Z0)
            diff_pT.append(reco_pT - true_pT)

        break

    chi2_obs = track.getChi2()
    ndf = track.getNdf()
    chi2_ndf = chi2_obs/ndf if ndf > 0 else -1
    chi2_ndf_arr.append(chi2_ndf)

   
    p_value = chi2.sf(chi2_obs, ndf)
    p_value_arr.append(p_value)

import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm
from scipy.optimize import minimize

def double_gaussian_pdf(x, mu, sigma1, sigma2, frac):
    return frac * norm.pdf(x, mu, sigma1) + (1 - frac) * norm.pdf(x, mu, sigma2)

def compute_sigma68(x, y):
    dx = x[1] - x[0]
    cdf = np.cumsum(y) * dx
    cdf /= cdf[-1]
    x_low = np.interp(0.16, cdf, x)
    x_high = np.interp(0.84, cdf, x)
    return 0.5 * (x_high - x_low)

def neg_log_likelihood(params, data):

    mu, sigma1, sigma2, frac = params
    if sigma1 <= 0 or sigma2 <= 0 or not (0 < frac < 1):
        return np.inf
    pdf_vals = double_gaussian_pdf(data, mu, sigma1, sigma2, frac)
    pdf_vals = np.clip(pdf_vals, 1e-12, None)
    return -np.sum(np.log(pdf_vals))

def fit_double_gaussian_likelihood(data):

    mu0 = np.mean(data)
    sigma0 = np.std(data)
    p0 = [mu0, sigma0/2, sigma0, 0.7]
    result = minimize(
        neg_log_likelihood,
        p0,
        args=(data,),
        bounds=[(-np.inf, np.inf), (1e-6, np.inf), (1e-6, np.inf), (1e-3, 1-1e-3)]
    )
    if not result.success:
        raise RuntimeError("Likelihood fit did not converge")
    mu, sigma1, sigma2, frac = result.x
    return mu, sigma1, sigma2, frac

def fit_and_plot(ax, data, plot_range, xlabel, title, unit=""):

    mu, sigma1, sigma2, frac = fit_double_gaussian_likelihood(data)
    sigma_core = min(sigma1, sigma2)
    x = np.linspace(mu - 4*sigma_core, mu + 4*sigma_core, 500)
    y = double_gaussian_pdf(x, mu, sigma1, sigma2, frac)
    sigma_eff = np.sqrt(frac * sigma1**2 + (1 - frac) * sigma2**2)
    sigma_68 = compute_sigma68(x, y)

    label = (
        fr"$\mu={mu:.4f}$ {unit}" "\n"
        fr"$\sigma_1={sigma1:.4f}$, $\sigma_2={sigma2:.4f}$" "\n"
        fr"$f={frac:.2f}$" "\n"
        fr"$\sigma_{{68}}={sigma_68:.4f}$ {unit}"
    )

    ax.hist(data, bins=100, range=plot_range, histtype="step", linewidth=2, density=True)
    y[y <= 0] = 1e-12
    ax.plot(x, y, 'r-', linewidth=2, label=label)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Probability density")
    ax.set_title(title)
    ax.set_yscale("log")
    ax.set_ylim(1e-4, None)
    ax.grid()
    ax.legend()

diff_D0 = np.asarray(diff_D0)
diff_Z0 = np.asarray(diff_Z0)
diff_pT = np.asarray(diff_pT)
chi2_ndf_arr = np.asarray(chi2_ndf_arr)
p_value_arr = np.asarray(p_value_arr)

fig, axes = plt.subplots(1, 5, figsize=(28, 6))

fit_and_plot(axes[0], diff_D0, (-0.1, 0.1), "Reco D0 - True D0 [mm]", "D0 Resolution", "mm")
fit_and_plot(axes[1], diff_Z0, (-0.1, 0.1), "Reco Z0 - True Z0 [mm]", "Z0 Resolution", "mm")
fit_and_plot(axes[2], diff_pT, (-0.1, 0.1), "Reco pT - True pT", "pT Resolution", "GeV")

axes[3].hist(chi2_ndf_arr, bins=100, range=(0, 5), histtype="step", linewidth=2)
axes[3].set_xlabel(r"$\chi^2 / \mathrm{NDF}$")
axes[3].set_ylabel("Entries")
axes[3].set_title(r"$\chi^2 / \mathrm{NDF}$ distribution")
axes[3].grid()

axes[4].hist(p_value_arr, bins=100, range=(0, 1), histtype="step", linewidth=2)
axes[4].set_xlabel(r"p-value")
axes[4].set_ylabel("Entries")
axes[4].set_yscale("log")
axes[4].set_title(r"p-value distribution")
axes[4].grid()

plt.tight_layout()
plt.savefig("D0_Z0_pT_resolution_and_chi2_p_value_log_likelihood.png")
plt.close()
