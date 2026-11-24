#!/usr/bin/env python3
"""Prepare DFTB3 umbrella windows for CTAL."""
# Adapted from the umbrella sampling setup by Ahmed Hassanin.

from pathlib import Path

TOPOLOGY = "sys_solv_cym.top"
STARTING_RESTART = "cluster_3.rst7"
MD_INPUT = "md_dftb3.in"

# Window centers in hundredths of an angstrom, matching the original setup.
WINDOWS = range(258, -110, -10)
FORCE = 100
REACTION_COORDINATE = 'iat=12233,12229,12233,12214, rstwt=1,-1,'
EXTRA_RESTRAINT = ''


def main():
    folder = Path(__file__).resolve().parent
    topology = folder.parents[1] / TOPOLOGY
    if not topology.is_file():
        raise SystemExit(f"Missing shared topology: {topology}")

    for filename in (STARTING_RESTART, MD_INPUT):
        if not (folder / filename).is_file():
            raise SystemExit(f"Missing input: {folder / filename}")

    md_input = (folder / MD_INPUT).read_text().rstrip() + "\n"
    output = folder / "umbrella_windows"
    output.mkdir()

    commands = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        'cd -- "$(dirname -- "${BASH_SOURCE[0]}")"',
    ]
    cpptraj = [f"parm ../../../{TOPOLOGY}", "trajout all_wins.nc", "trajout all_wins.pdb"]
    plots = []
    restart = f"../../{STARTING_RESTART}"

    for center in WINDOWS:
        distance = center / 100
        rc = f"{distance:.2f}"
        name = f"rc{rc}"
        window = output / name
        window.mkdir()

        restraint = (
            f"&rst\n{REACTION_COORDINATE}\n"
            f"r1={max(distance - 10, -10.0)}, r2={rc}, r3={rc}, "
            f"r4={min(distance + 10, 10.0)},\n"
            f"rk2={FORCE}, rk3={FORCE},\n/\n"
        )
        (window / f"{name}.RST").write_text(restraint + EXTRA_RESTRAINT)
        # The starting coordinates have no velocities. Later windows read them from restarts.
        window_input = md_input
        if center == WINDOWS.start:
            window_input = md_input.replace("irest=1, ntx=5,", "irest=0, ntx=1,", 1)
            if window_input == md_input:
                raise SystemExit(f"Expected irest=1, ntx=5 in {MD_INPUT}")
        (window / MD_INPUT).write_text(
            window_input
            + "&wt type='DUMPFREQ', istep1=1 /\n"
            + "&wt type='END' /\n"
            + f"DISANG={name}.RST\nDUMPAVE={name}.dat\n"
        )

        commands.append(
            f'(cd "{name}" && sander -O -i {MD_INPUT} -o {name}.log '
            f'-p "../../../../{TOPOLOGY}" -c "{restart}" -x {name}.nc -r {name}.rst7)'
        )
        cpptraj.append(f"trajin {name}/{name}.nc")
        plots.append(f"'{name}/{name}.dat' using 2:0 smooth kdensity with lines notitle")
        restart = f"../{name}/{name}.rst7"

    (output / "run_QMMM.sh").write_text("\n".join(commands) + "\n")
    (output / "cpptraj.in").write_text("\n".join(cpptraj) + "\n")
    plot_header = "set term png size 1000, 600\nset output 'sampling.png'\n"
    (output / "gplot.in").write_text(plot_header + "plot " + ", ".join(plots) + "\n")


if __name__ == "__main__":
    main()
