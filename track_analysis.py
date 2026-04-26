"""
    This files runs a minimal track analysis.
    It produces histograms of main track parameters
    and calculates the track momentum resolution
    given the known true value.
"""

from edm4hep import TrackState
from podio import root_io
import ROOT

##################
# Global parameters

input_file = "ALLEGRO_o1_v03_mu10GeV_confTrk.root"
sample_name = "ALLEGRO_o1_v03_mu10GeV"
track_collection = "NewSiTracks"

true_p = 10     # true momentum of the particle gun
B_field = 2.0   # Magnetic field at perigee, in Tesla

# Conversion factor for: (Tesla / (1/mm)) * e -> GeV/c
T_mm_e_to_GeV_over_c = 0.000299792  

##################
# Prepare histograms

h_trk_p = ROOT.TH1D("h_trk_p", "h_trk_p; Track momentum [GeV]", 50, 0, 20)
h_trk_pt = ROOT.TH1D("h_trk_pt", "h_trk_pt; Track momentum [GeV]", 50, 0, 20)
h_trk_d0 = ROOT.TH1D("h_trk_d0", "h_trk_d0; Track d0 [mm]", 50, -0.01, 0.01)
h_trk_z0 = ROOT.TH1D("h_trk_z0", "h_trk_z0; Track d0 [mm]", 50, -0.01, 0.01)

h_trk_p_res = ROOT.TH1D("h_trk_p_res", "h_trk_p_res; Track momentum resolution", 100, -1, 1)

podio_reader = root_io.Reader(input_file)

##################
# Loop over events
for i, event in enumerate(podio_reader.get("events")):

    # Loop over the track collection
    for j, trk in enumerate(event.get(track_collection)):

        # Useful doxy for tracks:
        # https://edm4hep.web.cern.ch/classedm4hep_1_1_track.html
        # https://edm4hep.web.cern.ch/classedm4hep_1_1_track_state.html

        # States are defined here:
        # https://github.com/key4hep/EDM4hep/blob/c0d370ffb4ed90de171d7cca32f3d224afe97a54/edm4hep.yaml#L178
        # Each state correspond to the track at a different location,
        # the first state should correspond to the track at perigee (= interaction point)
        trk_state = trk.getTrackStates()[0]

        if trk_state.location != TrackState.AtIP:
            print(f"ERROR: in event {i}, track {j} has a first state different from IP! Skipping this track")
            continue

        # Get track parameters
        trk_pt = abs(B_field / trk_state.omega) * T_mm_e_to_GeV_over_c
        trk_pz = trk_pt * trk_state.tanLambda
        trk_p = (trk_pt**2 + trk_pz**2)**(0.5)
        trk_d0 = trk_state.D0
        trk_z0 = trk_state.Z0

        # fill the histograms
        h_trk_pt.Fill(trk_pt)
        h_trk_p.Fill(trk_p)
        h_trk_d0.Fill(trk_d0)
        h_trk_z0.Fill(trk_z0)

        h_trk_p_res.Fill((trk_p - true_p) /true_p)
    # <- end tracks loop
# <- end event loop

##################
# Write to output file
out_file = ROOT.TFile(sample_name+"_track_histograms.root","RECREATE")

h_trk_pt.Write()
h_trk_p.Write()
h_trk_d0.Write()
h_trk_z0.Write()
h_trk_p_res.Write()

out_file.Close()