# Initial steps

Log in to lxplus
```
ssh -XY user@lxplus.cern.ch
```

Source the Key4hep nightly
```
source /cvmfs/sw-nightlies.hsf.org/key4hep/setup.sh
```

The exact release that we use is 
```
source /cvmfs/sw-nightlies.hsf.org/key4hep/setup.sh -r 2026-04-20
```

Clone k4RecTracker
```
git clone https://github.com/andread3vita/k4RecTracker.git
cd k4RecTracker
git checkout ef99ca0b73336437777727b1d5f90a39c7e10738 # This is the commit that is tested to work
```

And compile k4RecTracker
```
mkdir build install
cd build
cmake .. -DCMAKE_INSTALL_PREFIX=../install
make install -j 8
cd ../../
export K4RECTRACKER=$PWD/k4RecTracker/install/share/k4RecTracker; PATH=$PWD/k4RecTracker/install/bin/:$PATH; CMAKE_PREFIX_PATH=$PWD/k4RecTracker/install/:$CMAKE_PREFIX_PATH; LD_LIBRARY_PATH=$PWD/k4RecTracker/install/lib:$PWD/k4RecTracker/install/lib64:$LD_LIBRARY_PATH; export PYTHONPATH=$PWD/k4RecTracker/install/python:$PYTHONPATH
cd k4RecTracker
```

# GGTF track finding and GenFit2 track fitting

The whole GGTF+GenFit2 chain is described in detail in (this talk from the 2026 FCC Physics Workshop)[https://indico.cern.ch/event/1588696/timetable/#80-tracking-tools-status-and-p].

## Generate SIM sample
```
XML_FILE=$K4GEO/FCCee/IDEA/compact/IDEA_o1_v03/IDEA_o1_v03.xml
STEERING_FILE=Tracking/test/testTrackFinder/SteeringFile_IDEA_o1_v03.py

curl -o $STEERING_FILE https://raw.githubusercontent.com/key4hep/k4geo/master/example/SteeringFile_IDEA_o1_v03.py

ddsim --steeringFile $STEERING_FILE \
      --compactFile  $XML_FILE \
      -G --gun.distribution uniform --gun.particle mu- \
      --random.seed 42 \
      --numberOfEvents 1000 \
      --outputFile Tracking/test/testTrackFinder/out_sim_edm4hep.root
```

Let's have a look at the produced file (either directly on lxplus or download and use your local root install):
```
root Tracking/test/testTrackFinder/out_sim_edm4hep.root
events->Draw("sqrt(VertexBarrelCollection.position.x^2+VertexBarrelCollection.position.y^2):VertexBarrelCollection.position.z")
```

You should be able to see the barrel structure of the IDEA vertex detector barrel:
<img width="697" height="438" alt="Capture d’écran 2026-04-24 à 11 24 15" src="https://github.com/user-attachments/assets/2ab7df70-4c41-4ceb-88db-f3800db791ea" />

Let's also have a look at the silicon wrapper:
```
events->Draw("SiWrDCollection.position.x:SiWrDCollection.position.y:SiWrDCollection.position.z")
```
<img width="694" height="474" alt="Capture d’écran 2026-04-24 à 11 27 04" src="https://github.com/user-attachments/assets/6280e912-e74a-4bce-8737-f3eb06355801" />
Note: This is the old silicon wrapper version. Now, SiliconWrapper_o1_v02 is available inside IDEA_o1_v04.


## Run GGTF track finder (basically following `Tracking/test/testTrackFinder/test_trackFinder.sh`)

Geometric Graph Track Finding (GGTF) is a ML-based tracking algorithm that can deal with an arbitrary detector geometry. 
<img width="1197" height="442" alt="doi:10.1051/epjconf/202533701125" src="https://github.com/user-attachments/assets/2eb09c29-f38e-4d9d-877b-8e31a6cd40d7" />
Please check out the reference publication ((doi:10.1051/epjconf/202533701125)[https://doi.org/10.1051/epjconf/202533701125]) for more details.

We can use GGTF for track finding with the following commands:
```
MODEL_PATH=build/Tracking/test/inputFiles/SimpleGatrIDEAv3o1.onnx

TBETA=0.6
TD=0.3

k4run Tracking/test/testTrackFinder/runTestTrackFinder.py --inputFile Tracking/test/testTrackFinder/out_sim_edm4hep.root --outputFile Tracking/test/testTrackFinder/out_tracks.root --modelPath $MODEL_PATH --tbeta $TBETA --td $TD
```
Finding the tracks in all 1000 files will take some minutes. 

The ML model was trained on IDEA_o1_v03, so if you want to use another detector, retraining is needed (more details (https://github.com/key4hep/k4RecTracker/tree/main/Tracking#retraining-a-model)[here]).


## Run GenFit2 track fitter

GenFit2 (doi:10.48550/arXiv.1902.04405)[https://doi.org/10.48550/arXiv.1902.04405] provides track representation, track-fitting algorithms and can visualise graphically tracks and detectors (not used in our case) and is also detector agnostic. It features a Deterministic Annealing Fitter that can solve the left-right ambiguity present e.g. in drift chambers. GenFit2 track refitting is now being implemented in k4RecTracker by Andrea de Vita (CERN) and is soon usable for everyone. Let's refit the GGTF-built tracks with GenFit2 now!

```
k4run Tracking/test/testTrackFitter/runTestTrackFitter.py --inputFile Tracking/test/testTrackFinder/out_tracks.root --outputFile Tracking/test/testTrackFitter/out_tracks_refitted.root
```

The results can be validated with a simple script (thanks to Andrea de Vita (CERN) for sharing it!). It's, for the moment, hosted in this repository. Download it and run it:
```
wget https://raw.githubusercontent.com/armin-ilg/FCC-ee_tracking_vertexing_mini-workshop/refs/heads/main/checkFitResults.py
python3 checkFitResults.py Tracking/test/testTrackFitter/out_tracks_refitted.root
```
Now check out the output plot (D0_Z0_pT_resolution_and_chi2_p_value_log_likelihood.png):
<img width="2800" height="600" alt="D0_Z0_pT_resolution_and_chi2_p_value_log_likelihood" src="https://github.com/user-attachments/assets/4159c46d-bcce-4239-8eb2-8ce010c2e6ac" />

Beyond doing simple checks like this, work is ongoing to integrate tracking validation using CI/CD directly into Key4hep. The validation code will be hosted in [k4DetectorPerformance](https://github.com/key4hep/k4DetectorPerformance). A work-in-progress version of this code can be found under https://github.com/ArinaPon/k4DetectorPerformance/tree/pr-tracking-validation. More information on this can be found in [Arina Ponomareva's talk from 1st of April](https://indico.cern.ch/event/1664310/#48-tracking-performance-and-va).





## Get tracking validation code
```
cd ..
git clone git@github.com:ArinaPon/k4DetectorPerformance.git
cd k4DetectorPerformance
git switch -c pr-tracking-validation origin/pr-tracking-validation 

k4_local_repo
mkdir build
cd build
cmake .. -DCMAKE_INSTALL_PREFIX=../install
make install -j 8
cd ..
```

## Run tracking validation code
```
k4run TrackingPerformance/test/runTrackingValidation.py --inputFile ~/k4RecTracker/Tracking/test/testTrackFinder/out_tracks_refitted.root --runDigi 0 --runFinder 0 --runFitter 0 --runPerfectTracking 0 --runValidation 1 --doPerfectFit 1
```

# Looking at the results!!!
