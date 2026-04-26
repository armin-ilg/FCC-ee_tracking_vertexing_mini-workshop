# Initial steps

Log in to lxplus
```bash
ssh -XY user@lxplus.cern.ch
```

Source the Key4hep nightly
```bash
source /cvmfs/sw-nightlies.hsf.org/key4hep/setup.sh
```

The exact release that we use is 
```bash
source /cvmfs/sw-nightlies.hsf.org/key4hep/setup.sh -r 2026-04-20
```

# Generate sample

Start by creating a folder where to run:
```bash
mkdir run
cd run
```

In the `run` folder
```bash
XML_FILE=$K4GEO/FCCee/ALLEGRO/compact/ALLEGRO_o1_v03/ALLEGRO_o1_v03.xml

DETECTOR=${XML_FILE##*/}
DETECTOR=${DETECTOR%.xml}

ddsim --enableGun \
 --gun.distribution uniform \
 --gun.energy "10*GeV" \
 --gun.particle "mu-" \
 --gun.thetaMin "80*deg" \
 --gun.thetaMax "100*deg" \
 --numberOfEvents 100 \
 --random.enableEventSeed \
 --random.seed 42 \
 --compactFile $XML_FILE \
 --outputFile ${DETECTOR}_mu10GeV.root
```
This generates a sample with 10 GeV muons uniformly distributed in phi and with 80° < theta < 100°, i.e. mostly perpendicular.
Feel free to adapt the gun to your taste.

> [!TIP]
> Copy paste the above command in a `pgun.sh` file
> and edit that file if you plan to change options. You can execute it with `sh pgun.sh`.

To run the with IDEA, change the `XML_FILE` path to:
```bash
XML_FILE=$K4GEO/FCCee/IDEA/compact/IDEA_o1_v03/IDEA_o1_v03.xml
```
and add the following argument to the `ddsim` command
```bash
--steeringFile $FCCCONFIG/FullSim/IDEA/IDEA_o1_v03/SteeringFile_IDEA_o1_v03.py
```

## Digitization
The sample produced with the particle gun contains only SIM hits,
which have to be pass through the digitization step before running reconstruction.
The digitizers introduce peculiarities of the detector response
(signal formation, noise effects, cross-talk etc.).
For ALLEGRO and IDEA, the tracker digitizers are still simple gaussian smearing. 
But it is a very active area work and we might have
more realistic tools soon.

The job steering files and recipes for running digitization
and some minimal reconstruction are contained in the 
[FCC-config](https://github.com/HEP-FCC/FCC-config) repository.
Below you can find instructions for ALLEGRO and IDEA.

### ALLEGRO
To run the digitization you should first copy the necessary files:
```bash
# create a sub folder to store files for digi and copy
mkdir digi-files 
cd digi-files
cp /eos/project/f/fccsw-web/www/filesForSimDigiReco/ALLEGRO/ALLEGRO_o1_v03/* .
wget --no-clobber https://fccsw.web.cern.ch/fccsw/filesForSimDigiReco/IDEA/DataAlgFORGEANT.root
wget --no-clobber https://fccsw.web.cern.ch/fccsw/filesForSimDigiReco/IDEA/IDEA_o1_v03/SimpleGatrIDEAv3o1.onnx

cd ..

# Now get the script for running the digi job
curl  https://raw.githubusercontent.com/HEP-FCC/FCC-config/refs/heads/main/FCCee/FullSim/ALLEGRO/ALLEGRO_o1_v03/run_digi_reco.py -o run_digi_reco_ALLEGRO.py
```
To run the digi step:
```bash
# Here we enable explicitly the digitization of tracker hits
# and ask to run truth track reconstruction 
k4run run_digi_reco_ALLEGRO.py --dataFolder=./digi-files/ \
 --runTrkHitDigitization \
 --runTrkFinder \
 --IOSvc.Input=ALLEGRO_o1_v03_mu10GeV.root \
 --IOSvc.Output=ALLEGRO_o1_v03_mu10GeV_digi_reco.root
```

To change the impact of digitizers and emulated different resolutions,
you can tune the smearing parameters for
the [vertex detector](https://github.com/HEP-FCC/FCC-config/blob/main/FCCee/FullSim/ALLEGRO/ALLEGRO_o1_v03/run_digi_reco.py#L275-L280)
and the [silicon wrapper](https://github.com/HEP-FCC/FCC-config/blob/main/FCCee/FullSim/ALLEGRO/ALLEGRO_o1_v03/run_digi_reco.py#L282-L285).


### IDEA
To run the digitization you should first copy the necessary files:
```bash
wget --no-clobber https://fccsw.web.cern.ch/fccsw/filesForSimDigiReco/IDEA/DataAlgFORGEANT.root
wget --no-clobber https://fccsw.web.cern.ch/fccsw/filesForSimDigiReco/IDEA/IDEA_o1_v03/SimpleGatrIDEAv3o1.onnx

# Script for running the job
curl  https://raw.githubusercontent.com/HEP-FCC/FCC-config/refs/heads/main/FCCee/FullSim/IDEA/IDEA_o1_v03/run_digi_reco.py -o run_digi_reco_IDEA.py
```
Note that in this case the files need to be in the same folder as the job script.
To run the digitization:
```
k4run run_digi_reco_IDEA.py
```


To change the impact of digitizers and emulated different resolutions,
you can tune the smearing parameters for
the [vertex detector](https://github.com/HEP-FCC/FCC-config/blob/main/FCCee/FullSim/IDEA/IDEA_o1_v03/run_digi_reco.py#L29-L34)
and the [silicon wrapper](https://github.com/HEP-FCC/FCC-config/blob/main/FCCee/FullSim/IDEA/IDEA_o1_v03/run_digi_reco.py#L59-L61).

# Conformal tracking with ALLEGRO/IDEA

k4Reco has currently implemented a conformal tracking algorithm for CLD,
which was initially designed for all-silicon trackers (-> CLIC).
The latter implementation is extensively documented in
[arXiv:1908.00256](https://arxiv.org/abs/1908.00256).

From the paper:
> Conformal tracking is a pattern recognition technique for track reconstruction 
that combines the two concepts of **conformal mapping** and **cellular automata**.

With conformal mapping we can transform circles passing in the origin into straight lines.
This procedures makes the track finding procedure easier.


Given that tracks aren't perfect circles (e.g. multiple scattering or energy losses)
and don't always cross the origin (e.g. displaced decay / imperfect PV reconstruction),
they wont always be straight lines. The cellular automata approach provides a robust track finding procedure (more details in the paper).


After tracks are found, fitting is done for parameter estimation
using Kalman Filter fitting (see e.g.: 
[doi.org/10.1016/0168-9002(87)90887-4](https://doi.org/10.1016/0168-9002(87)90887-4)
or [CDS:physics/9912034](https://cds.cern.ch/record/412374/)).

## Install k4Reco

Outside the `run` folder,
clone the `conf-trk-ALLEGRO` branch of the repository:
```bash
# N.B. for this tutorial we are using a fork of official repo
# to include this commit:
# https://github.com/sfranchel/k4Reco/commit/ed4288a15454285038cc99514e0d04eb170ea7fb
# The latter overrides the `createTrackStateAtCaloFace` function
# not supported for ALLEGRO and adds a minimal working example.
# Main repo should work in the near future.

cd ../
git clone -b conf-trk-ALLEGRO https://github.com/sfranchel/k4Reco.git
```

Move in the `k4Rco` folder and compile:
```bash
cd k4Reco

cmake -B build -S . -DCMAKE_INSTALL_PREFIX=./install
cmake --build build --target install -j8

# Required to use local installation of k4Reco
k4_local_repo
```
> [!IMPORTANT]
> Without the `k4_local_repo` command
> the central version of k4Reco is used, loaded from cvmfs. 
> The latter command can be used to install local
> versions of any repository of the key4hep stack,
> updating all the required paths.

## Run tracking script
Move back to `run` folder, where you have generated events
with the particle gun:
```
cd ../run
```
Now, to run the entire tracking chain
(conformal tracking + track fitting),
copy the file for the k4Reco checked out version:
```
cp ../k4Reco/k4Reco/ConformalTracking/options/runConformalTracking_ALLEGRO.py .
```
and run:
```
k4run runConformalTracking_ALLEGRO.py --IOSvc.Input ALLEGRO_o1_v03_mu10GeV_digi_reco.root --IOSvc.Output ALLEGRO_o1_v03_mu10GeV_confTrk.root
```

The main parameters of conformal track finding are specified
in the `parameters` dictionary, at the entry `params`:
```python
"params": {
    "MaxCellAngle": 0.01,
    "MaxCellAngleRZ": 0.01,
    "Chi2Cut": 100,
    "MinClustersOnTrack": 3,
    "MaxDistance": CT_MAX_DIST,
    "SlopeZRange": 10.0,
    "HighPTCut": 10.0,
},
```
You can find more details on their functioning in the same paper
already mentioned above
([arXiv:1908.00256](https://arxiv.org/abs/1908.00256)).
In that paper, the cellular tracks reconstruction
is run multiple times updating the parameters at each iteration.
The goal is to reconstruct harder cases after a first pass
where "easy" tracks are found.
The more difficult tracks to recover are e.g. displaced tracks
or loopers with soft transverse momentum.
A more complete configuration of the algorithm is reported in the original
[`runConformalTracking.py`](https://github.com/key4hep/k4Reco/blob/33a4a90f2e1a5edbd1e8198e6418a3e2df2e459e/k4Reco/ConformalTracking/options/runConformalTracking.py#L98-L183) script.

The output file contains the `NewSiTracks` which can now be analyzed.

