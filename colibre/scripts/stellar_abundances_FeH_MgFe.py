"""
Plots the stellar abundances of given snapshot
"""
import matplotlib.pyplot as plt
import numpy as np
import unyt
import glob
from swiftsimio import load
from swiftpipeline.argumentparser import ScriptArgumentParser
from velociraptor.observations import load_observation


def read_data(data):
    """
    Grabs the data
    """

    mH_in_cgs = unyt.mh
    mFe_in_cgs = 55.845 * unyt.mp
    mMg_in_cgs = 24.305 * unyt.mp

    # Asplund et al. (2009)
    Fe_H_Sun = 7.5
    Mg_H_Sun = 7.6

    Mg_Fe_Sun = Mg_H_Sun - Fe_H_Sun - np.log10(mFe_in_cgs / mMg_in_cgs)
    Fe_H_Sun = Fe_H_Sun - 12.0 - np.log10(mH_in_cgs / mFe_in_cgs)

    magnesium = data.stars.element_mass_fractions.magnesium
    iron = data.stars.element_mass_fractions.iron
    hydrogen = data.stars.element_mass_fractions.hydrogen

    Fe_H = np.log10(iron / hydrogen) - Fe_H_Sun
    Mg_Fe = np.log10(magnesium / iron) - Mg_Fe_Sun
    Fe_H[iron == 0] = -7  # set lower limit
    Fe_H[Fe_H < -7] = -7  # set lower limit
    Mg_Fe[iron == 0] = -2  # set lower limit
    Mg_Fe[magnesium == 0] = -2  # set lower limit
    Mg_Fe[Mg_Fe < -2] = -2  # set lower limit

    return Fe_H, Mg_Fe


arguments = ScriptArgumentParser(
    description="Creates an [Fe/H] - [Mg/Fe] plot for stars."
)

snapshot_filenames = [
    f"{directory}/{snapshot}"
    for directory, snapshot in zip(arguments.directory_list, arguments.snapshot_list)
]

names = arguments.name_list
output_path = arguments.output_directory

plt.style.use(arguments.stylesheet_location)

simulation_lines = []
simulation_labels = []

fig, ax = plt.subplots()
ax.grid(True)

for snapshot_filename, name in zip(snapshot_filenames, names):

    data = load(snapshot_filename)
    redshift = data.metadata.z

    Fe_H, Mg_Fe = read_data(data)

    # low zorder, as we want these points to be in the background
    dots = ax.plot(Fe_H, Mg_Fe, ".", markersize=0.5, alpha=0.2, zorder=-99)[0]

    bins = np.arange(-7.2, 1, 0.2)
    ind = np.digitize(Fe_H, bins)
    xm = [
        np.median(Fe_H[ind == i])
        for i in range(1, len(bins))
        if len(Fe_H[ind == i]) > 10
    ]
    ym = [
        np.median(Mg_Fe[ind == i])
        for i in range(1, len(bins))
        if len(Mg_Fe[ind == i]) > 10
    ]
    # high zorder, as we want the simulation lines to be on top of everything else
    # we steal the color of the dots to make sure the line has the same color
    simulation_lines.append(ax.plot(xm, ym, color=dots.get_color(), zorder=1000)[0])
    simulation_labels.append(f"{name} ($z={redshift:.1f}$)")

# we select all Tolstoy* files containing FeH-MgFe.
expr = f"{arguments.config.config_directory}/{arguments.config.observational_data_directory}/data/StellarAbundances/Tolstoy*.hdf5"
observational_data = glob.glob(expr)
for index, observation in enumerate(observational_data):
    obs = load_observation(observation)
    obs.plot_on_axes(ax)

ax.set_xlabel("[Fe/H]")
ax.set_ylabel("[Mg/Fe]")

ax.set_ylim(-2.0, 3.0)
ax.set_xlim(-7.2, 2.0)

observation_legend = ax.legend(markerfirst=True, loc="upper left")

ax.add_artist(observation_legend)

simulation_legend = ax.legend(
    simulation_lines, simulation_labels, markerfirst=False, loc="lower left"
)

ax.add_artist(simulation_legend)

plt.savefig(f"{output_path}/stellar_abundances_FeH_MgFe.png")
