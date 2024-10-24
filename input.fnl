device cuda:0
#double_precision
matmul_prec highest
print_timings no
#model_file ../ani2x.fnx
#model_file mace_mp_large.fnx
model_file best_model.fnx

xyz_input{
  file IceVII_8.73.xyz
  # whether the first column is the atom index (Tinker format)
  indexed yes
  # whether a comment line is present
  has_comment_line no
}

# cell vectors (format:  ax ay az bx by bz cx cy cz)
#cell = 9.630019760 0. 0. 0. 9.630019760 0. 0. 0. 9.630019760
cell = 8.73 0. 0. 0. 8.73 0. 0. 0. 8.73
#cell = 18.943 0. 0. 0. 18.943 0. 0. 0. 18.943
# compute neighborlists using minimum image convention
minimum_image no
# whether to wrap the atoms inside the first unit cell
wrap_box yes
estimate_pressure yes

pressure_unit gpa

#graph_config{
#  cutoff 7.
#  k_space yes
#}

# number of steps to perform
nsteps = 2000000
# timestep of the dynamics
dt[fs] =  0.2

nblist_skin 2.

# format of the trajectory file (supported: xyz, arc, extxyz)
traj_format arc
#time between each saved frame
tdump[ps] = 0.1

# number of steps between each printing of the energy
nprint = 100
nsummary = 10000

## set the thermostat
#thermostat  NVE 
thermostat LGV 
#thermostat ADQTB 

#nbeads 32

## Thermostat parameters
temperature = 300.
#friction constant
gamma[THz] = 100.

## parameters for the Quantum Thermal Bath
qtb{
  # segment length for noise generation and spectra
  tseg[ps]=0.25
  # maximum frequency
  omegacut[cm1]=15000.
  # number of segments to skip before adaptation
  skipseg = 5
  # number of segments to wait before accumulation statistics on spectra
  startsave = 50
  # parameter controlling speed of adQTB adaptation 
  agamma  = 1.
}
