the directory structure of initialTests and randomTests isn't quite the
same; initialTests/*/ looks like randomTests, with json files that share
hashes in their names with directories.

this is weird:
```
iev@iev-mbp brass-unlogger % ./unlogger.py randomTests | wc -l
     600
iev@iev-mbp brass-unlogger % ./unlogger.py randomTests | sort | uniq | wc -l
     600
iev@iev-mbp brass-unlogger %
```
this implies that there are 600 random tests, not 300; when i ran that,
unlogger was printing just the hashes from the json objects they use to
name the tests.






csv with columns (lines prefixed with `--` have been implemented):
```
-- CP = which challenge problem, 1 or 2
-- Case = which case, BaselineA = A, BaselineB = B, Challenge = C
-- ID = the directory name of the test this is in (e.g., CP1_TC1_5567...)
-- Start = start waypoint
-- Sx = corresponding x of the start (easier to add in post processing?)
-- Sy = corresponding y of the start  (easier to add in post processing?)
-- Target = target waypoint
-- Tx = corresponding x of the target  (easier to add in post processing?)
-- Ty = corresponding y of the target  (easier to add in post processing?)
-- Obstacle? = true/false
-- Removed? = true/false
-- Battery? = true/false
-- Kinect? = true/false
-- Outcome = Invalid | Valid (was there a crash or not?)
-- Accuracy Score
-- Timing Score
-- Safety Score
-- Detection Score
-- Ox = x of the obstacle (if placed)
-- Oy = y of the obstacle (if placed)
-- Rt = sim time of obstacle removal (if removed)
Bv = voltage of battery perturbed
Bt = sim time voltage was perturbed
Kt = sim time that the kinect was perturbed
Dt = sim time that the perturbation was detected
Ft = sim time when the challenge ended (e.g., report back that robot reached target)
-- Fx = x of final location of the robot at Ft
-- Fy = y of final location of the robot at Ft
-- Df = the distance between the robot and goal at Ft
Fb = voltage reading at Ft
-- #N = number of notifications about the new deadline we gave
D = sim time of the final deadline we notified about
```
