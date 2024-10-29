device cuda:0
matmul_prec highest
print_timings no
model_file ../best_model.fnx

xyz_input{
  file IceVII_7.8.xyz
  # whether the first column is the atom index (Tinker format)
  indexed yes
  # whether a comment line is present
  has_comment_line no
}

# cell vectors (format:  ax ay az bx by bz cx cy cz)
cell = 7.8 0. 0. 0. 7.8 0. 0. 0. 7.8
# compute neighborlists using minimum image convention
minimum_image no
# whether to wrap the atoms inside the first unit cell
wrap_box yes
estimate_pressure yes

pressure_unit gpa


# number of steps to perform
nsteps = 5000
# timestep of the dynamics
dt[fs] =  0.5

nblist_skin 2.

# format of the trajectory file (supported: xyz, arc, extxyz)
traj_format arc
#time between each saved frame
tdump[fs] = 20

# number of steps between each printing of the energy
nprint = 10
nsummary = 100

## set the thermostat
#thermostat  NVE 
thermostat LGV 


## Thermostat parameters
temperature = 300.
#friction constant
gamma[THz] = 10.

