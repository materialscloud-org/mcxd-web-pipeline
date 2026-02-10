import click
import subprocess
import os

# ---------- Helper ----------


def run_step(script, env):
    click.echo(f"\n▶ Running {script}")
    subprocess.run(["python", script], env=env, check=True)


# ---------- CLI ----------


@click.command()
@click.option("--r-cut", default=7.0, type=float, show_default=True)
@click.option("--n-max", default=4, type=int, show_default=True)
@click.option("--l-max", default=2, type=int, show_default=True)
def run_pipeline(r_cut, n_max, l_max):
    """Run full similarity pipeline."""

    env = os.environ.copy()
    env["R_CUT"] = str(r_cut)
    env["N_MAX"] = str(n_max)
    env["L_MAX"] = str(l_max)

    click.echo("\nPipeline configuration:")
    click.echo(f"  R_CUT = {r_cut}")
    click.echo(f"  N_MAX = {n_max}")
    click.echo(f"  L_MAX = {l_max}")

    # Run stages sequentially
    run_step("download_structures.py", env)
    run_step("generate_soap_vector.py", env)
    run_step("calculate_similarity.py", env)
    run_step("prepare_final_json.py", env)

    click.echo("\nData pipeline complete")
    click.echo("\n Generating verification plots")
    run_step("verification.py", env)
    run_step("plot_verification.py")


if __name__ == "__main__":
    run_pipeline()
