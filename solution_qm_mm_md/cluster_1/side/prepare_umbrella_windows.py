#!/usr/bin/env python3
"""Prepare DFTB3 umbrella windows for CTAL."""
# Adapted from the umbrella sampling setup by Ahmed Hassanin.

from pathlib import Path

TOPOLOGY = 'CYL_capped_wat.prmtop'
STARTING_RESTART = 'cluster_1.rst7'
MD_INPUT = "md_dftb3.in"

# Window centers in hundredths of an angstrom, matching the original setup.
WINDOWS = range(200, -110, -10)
FORCE = 100
REACTION_COORDINATE = 'iat=6,1,1,24, rstwt=1,-1,'
CENTER_MASK = ':MOL'
START_HAS_VELOCITIES = False


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
        (window / f"{name}.RST").write_text(restraint)
        # Only a restart without velocities needs a fresh start.
        window_input = md_input
        if center == WINDOWS.start and not START_HAS_VELOCITIES:
            window_input = md_input.replace("irest=1, ntx=5,", "irest=0, ntx=1,", 1)
            if window_input == md_input:
                raise SystemExit(f"Expected irest=1, ntx=5 in {MD_INPUT}")
        (window / MD_INPUT).write_text(
            window_input
            + "&wt type='DUMPFREQ', istep1=1 /\n"
            + "&wt type='END' /\n"
            + f"DISANG={name}.RST\nDUMPAVE={name}.dat\n"
        )

        # Keep the solute whole before and after each window, as in the source runs.
        for label, incoming, outgoing in (
            ("pre", restart, f"{name}_start_whole.rst7"),
            ("post", f"{name}.rst7", f"{name}_whole.rst7"),
        ):
            (window / f"reimage_{label}.in").write_text(
                f"parm ../../../../{TOPOLOGY}\ntrajin {incoming}\n"
                f"autoimage\ncenter {CENTER_MASK} mass origin\n"
                f"image origin center familiar\ntrajout {outgoing} restart\nrun\n"
            )

        commands.append(
            f'(cd "{name}" && cpptraj -i reimage_pre.in > reimage_pre.log && '
            f'sander -O -i {MD_INPUT} -o {name}.log ' 
            f'-p "../../../../{TOPOLOGY}" -c "{name}_start_whole.rst7" -x {name}.nc -r {name}.rst7 && '
            f'cpptraj -i reimage_post.in > reimage_post.log)' 
        )
        cpptraj.append(f"trajin {name}/{name}.nc")
        plots.append(f"'{name}/{name}.dat' using 2:0 smooth kdensity with lines notitle")
        restart = f"../{name}/{name}_whole.rst7"

    (output / "run_QMMM.sh").write_text("\n".join(commands) + "\n")
    (output / "cpptraj.in").write_text("\n".join(cpptraj) + "\n")
    plot_header = "set term png size 1000, 600\nset output 'sampling.png'\n"
    (output / "gplot.in").write_text(plot_header + "plot " + ", ".join(plots) + "\n")


if __name__ == "__main__":
    main()
