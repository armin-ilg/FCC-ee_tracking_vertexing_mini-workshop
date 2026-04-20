### Initial steps

Log in to lxplus
```
ssh -XY user@lxplus.cern.ch
```

The Key4hep stable release can be sourced in the following way (not used in this tutorial!)
```
source /cvmfs/sw.hsf.org/key4hep/setup.sh
```

Instead, we use a specific version of the nightly release:
```
source /cvmfs/sw-nightlies.hsf.org/key4hep/setup.sh -r 2026-04-20
```

You should now be able to access all the Key4hep tools, such as e.g. `ddsim` that is used to run the full simulation:
```
ddsim --help
```

or `k4run` that is used to run jobs using Gaudi functionals:
```
k4run --help
```

### Note on other tutorials

Documentation on Key4hep can be found under https://key4hep.github.io/key4hep-doc/main/index.html. There are many tutorials, but some of them sadly are a bit outdated or not very useful anymore. There are also FCC tutorials (https://hep-fcc.github.io/fcc-tutorials/main/index.html) that complement the Key4hep ones. What we'll do is nitpicking certain parts of these tutorials that are useful for tracking detector R&D. If you want to learn more, please check out these tutorials in more details!

# Generating a simple process with central Key4hep release

Let's use the stable Key4hep release we sourced to generate some SIM samples! Let's start with shooting an electron particle gun into IDEA:
```
ddsim --enableGun --gun.distribution uniform --gun.energy "10*GeV" --gun.particle e- --numberOfEvents 10 --outputFile IDEA_sim.root --random.enableEventSeed --random.seed 42 --compactFile $K4GEO/FCCee/IDEA/compact/IDEA_o1_v03/IDEA_o1_v03.xml --steeringFile $FCCCONFIG/FullSim/IDEA/IDEA_o1_v03/SteeringFile_IDEA_o1_v03.py
```

`--compactFile` indicates which detector we use, in this case `IDEA_o1_v03`. We take this from the central [k4geo repository](https://github.com/key4hep/). `--steeringFile` defines options for the simulation, we take this from the central [FCC-Config repository](https://github.com/HEP-FCC/FCC-config).

Once the above is finished, we do some simplified digitisation and reconstruction:
```
wget --no-clobber https://fccsw.web.cern.ch/fccsw/filesForSimDigiReco/IDEA/DataAlgFORGEANT.root
k4run $FCCCONFIG/FullSim/IDEA/IDEA_o1_v03/run_digi_reco.py
```

You can download the resulting root file and look at the particle collections in root (on your laptop or [on the web](https://root.cern/js/latest/)), but one can also convert the root file to json:
```
edm4hep2json -e 0  IDEA_sim_digi_reco.root
```
Download this file and go to the Phoenix visualisation tool on [https://fccsw.web.cern.ch/fccsw/phoenix/fccee-idea/o1_v03](https://fccsw.web.cern.ch/fccsw/phoenix/fccee-idea/o1_v03). Load the json event (under 'import and export options') and open the detector (with 'Geometry clipping'). You should be able to see a track and associated calorimetry clusters!

<img width="1258" height="441" alt="Capture d’écran 2026-04-20 à 11 41 22" src="https://github.com/user-attachments/assets/cbe2f6e4-2bf7-4f8c-a387-69b82face4b4" />

Note: Almost all MC event generators are included in Key4hep. It is rather easy to generate your own `hepevt` files! See more [here](https://hep-fcc.github.io/fcc-tutorials/main/fast-sim-and-analysis/FccFastSimGeneration.html).

Now that we managed to generate full simulation samples from the central release, let's try to look a bit in more detail at the detector model and modify it ourselves!


# Cloning k4geo and compiling it locally

Let's clone [k4geo](https://github.com/key4hep/k4geo.git) (which hosts the detector geometry descriptions and algorithms to build the detectors using `DD4hep`). We actually use my branch of k4geo that updates the vertex detector and silicon wrapper used in IDEA and ALLEGRO. The pull request is not yet merged, but we can check it out in this way!

```
git clone https://github.com/armin-ilg/lcgeo.git k4geo
cd k4geo
git switch -c curved_vertex_correction --track origin/curved_vertex_correction 
mkdir build
cd build
cmake .. -DCMAKE_INSTALL_PREFIX=../InstallArea -DBoost_NO_BOOST_CMAKE=ON -D INSTALL_BEAMPIPE_STL_FILES=ON
make -j4 install
cd ../InstallArea
source bin/thisk4geo.sh
cd ..

k4_local_repo InstallArea/
```

The `k4_local_repo` command is important as we need to specify properly that we don't use k4geo from the Key4hep release, but instead our own, local k4geo that we just installed. 


# Understanding how a detector is built in DD4hep/k4geo

Let's now look in more detail how the detectors are built, using ALLEGRO as an example. Open the file `FCCee/ALLEGRO/compact/ALLEGRO_o1_v03/ALLEGRO_o1_v03.xml` with your favourite file viewer. Also check out `FCCee/ALLEGRO/compact/ALLEGRO_o1_v03/DectDimensions.xml` which defines many dimensions of the ALLEGRO detector and its subdetectors. 

To look at the detector in more detail, we export it to a root file using the `scripts/save_detector_to_root.sh` script! Execute the following command:
```
sh scripts/save_detector_to_root.sh FCCee/ALLEGRO/compact/ALLEGRO_o1_v03/ALLEGRO_o1_v03.xml
```

You'll see how the detector is built component by component. After the script is finished, download the resulting file (`detector_dd4hep2root.root`) to your laptop and open it again in root (I recommend the root web viewer: https://root.cern/js/latest/). Look at different parts of the detector by browsing the hierarchy and right-clicking and doing `draw -> all`. If something doesn't appear then try enabling/disabling 'logical vis' and 'daughters' in the right-click menu in the hierarchy. Try to draw nicely the vertex detector. How many layers close to the beam pipe does it have? What's their layout?

<img width="1168" height="990" alt="Capture d’écran 2026-04-20 à 14 52 52" src="https://github.com/user-attachments/assets/3511b7d7-7c04-4c8d-a765-4990ef137ab0" />
<img width="853" height="310" alt="Capture d’écran 2026-04-20 à 14 53 13" src="https://github.com/user-attachments/assets/4dea513a-d95b-40e1-a8e1-2b62947e20d9" />


# Making changes to a detector model

Let's look in more detail at the vertex detector used by ALLEGRO. You can see in the ALLEGRO xml file that ALLEGRO actually uses the IDEA vertex detector (`../../../IDEA/compact/IDEA_o1_v04/VertexComplete_o1_v04.xml`). Open that file and browse through the contents. Can you roughly understand what it's doing?

The xml file just describes the properties and attributes of the (sub)detector. In the end, it's C++ code below that actually is responsible for building the detector simulation. The algorithms used to build the vertex detector here are `VertexBarrel_detailed_o1_v03` and `VertexEndcap_detailed_o1_v03`. You can find the code in k4geo under [detectors/tracker](https://github.com/key4hep/k4geo/tree/main/detector/tracker).

Let's now change the inner vertex detector and use the ultra-light inner vertex detector instead! In the vertex detector xml file, change `nInnerVertexLayers` from `3` to `4` which does exactly this (see the description in the file for more information). Since we don't need to change the C++ code, we don't have to recompile the code. Let's now save the modified detector again to a root file, giving a second argument to have a different name for the resulting root file:
```
sh scripts/save_detector_to_root.sh FCCee/ALLEGRO/compact/ALLEGRO_o1_v03/ALLEGRO_o1_v03.xml ALLEGRO_ultraLightInnerVertex
```

Download the resulting ALLEGRO_ultraLightInnerVertex_dd4hep2root.root file and investigate the ultra-light inner vertex detector.
<img width="708" height="496" alt="Capture d’écran 2026-04-20 à 15 24 58" src="https://github.com/user-attachments/assets/d15d22ae-0539-4787-afc4-dabb3d5e5967" />
