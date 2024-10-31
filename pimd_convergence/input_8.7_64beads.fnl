device cuda:0
matmul_prec highest
print_timings no
model_file ../best_model.fnx

xyz_input{
  file IceVII_8.7.xyz
  # whether the first column is the atom index (Tinker format)
  indexed yes
  # whether a comment line is present
  has_comment_line no
}

# cell vectors (format:  ax ay az bx by bz cx cy cz)
cell = 8.7 0. 0. 0. 8.7 0. 0. 0. 8.7
# compute neighborlists using minimum image convention
minimum_image no
# whether to wrap the atoms inside the first unit cell
wrap_box yes
estimate_pressure yes

pressure_unit gpa


# number of steps to perform
nsteps = 2000
# timestep of the dynamics
dt[fs] =  0.5

nblist_skin 2.

# format of the trajectory file (supported: xyz, arc, extxyz)
traj_format arc
#time between each saved frame
tdump[fs] = 25

# number of steps between each printing of the energy
nprint = 10
nsummary = 1000

## set the thermostat
#thermostat  NVE 
thermostat LGV 

system IceVII_8.7_64beads
nbeads 64

## Thermostat parameters
temperature = 300.
#friction constant
gamma[THz] = 10.

