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

Clone k4Reco
```bash
git clone -b conf-trk-ALLEGRO https://github.com/sfranchel/k4Reco.git
cd k4Reco

# N.B. using a fork of official repo, currently required for this commit
# https://github.com/sfranchel/k4Reco/commit/ed4288a15454285038cc99514e0d04eb170ea7fb
# which overrides the `createTrackStateAtCaloFace` function, not supported for ALLEGRO
# and adds a minimal working example.
# Main repo should work in the "near" future.
```

And compile k4RecTracker
```bash
cmake -B build -S . -DCMAKE_INSTALL_PREFIX=./install
cmake --build build --target install -j8

# Required to use local installation of k4Reco
k4_local_repo
```
Then, create a folder where to run.
```bash
mkdir ../run
cd ../run
```

# Conformal tracking with ALLEGRO

k4Reco has currently implemented a conformal tracking algorithm for CLD,
which was initially designed for all-silicon trackers (-> CLIC).
The latter implementation is extensively documented in
[arXiv:1908.00256](https://arxiv.org/abs/1908.00256).

From the paper:
> Conformal tracking is a pattern recognition technique for track reconstruction 
that combines the two concepts of **conformal mapping** and **cellular automata**.

With conformal mapping we can transform circles passing in the origin into straight lines.
This procedures makes the track finding procedure [^1] easier.
Given that tracks aren't perfect circles (e.g. multiple scattering)
and don't always cross the origin (e.g. displaced decay / imperfect PV reconstruction),
they wont always be straight lines. The cellular automata approach provides a robust track finding procedure (can find more details in the paper).
After tracks are found, fitting is done for parameter estimation. 
[TODO: maybe add more info on the fitting?]


[^1]: Aggregation of hits belonging to the same track.

## Generate sample
In the `run` folder
```
XML_FILE=$K4GEO/FCCee/ALLEGRO/compact/ALLEGRO_o1_v03/ALLEGRO_o1_v03.xml

DETECTOR=${COMPACT##*/}
DETECTOR=${DETECTOR%.xml}

ddsim --enableGun \
      --gun.distribution uniform \
      --gun.energy "10*GeV" \
      --gun.particle "mu-" \
      --gun.thetaMin "80*deg" \
      --gun.thetaMax "100*deg" \
      --numberOfEvents 1000 \
      --random.enableEventSeed \
      --random.seed 42 \
      --compactFile $XML_FILE \
      --outputFile $DETECTOR_mu10GeV.root
```
This generates a sample with 10 GeV muons uniformly distributed in phi and with 80° < theta < 100°, i.e. mostly perpendicular.
Feel free to adapt the gun to your taste.

### Digitization
This sample will contain only SIM hits, which have to be pass through the
digitization step.
Here we introduce peculiarities of the detectors response.
For ALLEGRO, the digitizers for trackers are still a simple gaussian smearing
transformation. But it's a very active area work and we might have
more realistic tools soon.

To run the digitization you should first copy the necessary files:
```bash
# create a sub folder to store files for digi and copy
mkdir digi-files 
cd digi-files
cp /eos/project/f/fccsw-web/www/filesForSimDigiReco/ALLEGRO/ALLEGRO_o1_v03/* .
wget --no-clobber https://fccsw.web.cern.ch/fccsw/filesForSimDigiReco/IDEA/DataAlgFORGEANT.root

cd ..

# Now get the script for running the digi job
curl  https://raw.githubusercontent.com/HEP-FCC/FCC-config/refs/heads/main/FCCee/FullSim/ALLEGRO/ALLEGRO_o1_v03/run_digi_reco.py -o run_digi_reco.py
```
To run the digi step:
```bash
# Here we enable explicitly the digitization of tracker hits
# and ask to run truth track reconstruction 
k4run run_digi_reco.py --dataFolder=./digi-files/ \
      --runTrkHitDigitization \
      --runTrkFinder \
      --IOSvc.Input=ALLEGRO_o1_v03_mu10GeV.root
```

## Run tracking script
...