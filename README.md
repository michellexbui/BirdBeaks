# BirdBeaks

A package for interpolating magnetic field data across CONUS to explore
potential effects of magnetic field fluctuations on migrating birds. 

Magnetic field data was accessed through SuperMag (http://supermag.jhuapl.edu), a global database of ground-based magnetometer data hosted by JHU Applied Physics Laboratory. The region of data selected for the example data file includes the entire continental United States as well as Canada, Mexico, and the Carribean region for the most accurate interpolation. There are about 90 total magnetometers in the region, but data availability varies per year. Data availability ranges from 1975 to the previous year, and data files can be accessed through SuperMag in yearly increments. 

# Bird Migrational Patterns and Their Relation to Magnetic Field Fluctuations

Birds are commonly known to have an internal magnetic compass to direct their  migrations. 
Currently, studies seek to observe exactly which aspects of avian anatomy contribute to a bird’s magnetic compass.

The cranial anatomy of a bird contains several elements of magnetoreception. A study in 2010 showed a high frequency of an iron mineral containing sensory dendrites in the dermal lining of many bird beaks [1]. 

The iron mineral has been hypothesized as a potential sensory basis for magnetically dependent behavior. Since this is in the lining of many bird beaks, the growth of bird beaks can be attributed to greater surface area of the iron mineral. Variances in surface area of iron could increase sensitivity to fluctuations in magnetic field. Another aspect involving magnetodetection is the ophthalmic branch of the trigeminal nerve, which is commonly located in the upper beak of birds. This feature has been recorded for sensitivities to magnetic field changes of at most 200 nT [2]. 


## Large Files

Large files are stored using Github's LFS system. This includes the high-resolution world map
for plotting magnetometer and radar locations. Once `git-lfs` is installed, use `git-lfs pull` in the
data directory to obtain the larger files.

# Citations

[1] Falkenberg G, Fleissner G, Schuchardt K, Kuehbacher M, Thalau P, Mouritsen H, et al. (2010) Avian Magnetoreception: Elaborate Iron Mineral Containing Dendrites in the Upper Beak Seem to Be a Common Feature of Birds. PLoS ONE 5(2): e9231. https://doi.org/10.1371/journal.pone.0009231

[2] Semm, P. and RC Beason. (1990) Responses to small magnetic variations by the trigeminal system of the bobolink. Brain Res Bull 25(5): 735-740., https://doi.org/10.1016/0361-9230(90)90051-Z
