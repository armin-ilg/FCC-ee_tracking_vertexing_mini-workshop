# Initial steps

Log in to lxplus
```
ssh -XY user@lxplus.cern.ch
```

Source the Key4hep nightly
```
source /cvmfs/sw-nightlies.hsf.org/key4hep/setup.sh
```

Clone k4RecTracker
```
git clone https://github.com/andread3vita/k4RecTracker.git
cd k4RecTracker
git checkout 52fb4662fd139a52a025f886a21b97c87350c4fe # This is the commit that is currently working
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

## Run GGTF track finder (basically following `Tracking/test/testTrackFinder/test_trackFinder.sh`)
```
MODEL_PATH=build/Tracking/test/inputFiles/SimpleGatrIDEAv3o1.onnx

TBETA=0.6
TD=0.3

k4run Tracking/test/testTrackFinder/runTestTrackFinder.py --inputFile Tracking/test/testTrackFinder/out_sim_edm4hep.root --outputFile Tracking/test/testTrackFinder/out_tracks.root --modelPath $MODEL_PATH --tbeta $TBETA --td $TD
```

## Run GenFit2 track fitter
```
k4run Tracking/test/testTrackFitter/runTestTrackFitter.py --inputFile Tracking/test/testTrackFinder/out_tracks.root --outputFile Tracking/test/testTrackFitter/out_tracks_refitted.root
```

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
