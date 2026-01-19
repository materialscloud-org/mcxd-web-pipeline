#!/usr/bin/env python

import click

from mcxd_web_pipeline.mc2d.phonon_vis import populate_mc2d_phonon_vis
from mcxd_web_pipeline.mc3d.pbesol_v1 import fermisurf
from mcxd_web_pipeline.mc_mongo_injector import McMongoInjector
from mcxd_web_pipeline.s3_utils import MongoS3Uploader


@click.group()
def cli():
    """
    Run the MCXD web pipeline.
    """
    pass


# ========================
# mc3d
# ========================


@cli.group()
def mc3d():
    """MC3D pipeline commands."""
    pass


@mc3d.command("run-base")
@click.argument("method", type=str)
def mc3d_run_base(method):
    """
    Base & base-derived data. Fairly fast to run.

    METHOD - sub-db (e.g. 'pbesol-v2', 'all').
    """
    mmi = McMongoInjector(mcxd_type="mc3d")
    mmi.inject_file_data(method)
    mmi.populate_base_derived(method)
    mmi.populate_dataset_index()


@mc3d.command("run-xrd")
@click.argument("method", type=str)
@click.option(
    "--recheck",
    is_flag=True,
    help="Re-check that each individual XRD is calculated.",
)
def mc3d_run_xrd(method, recheck):
    """
    X-ray diffraction. One db can take 10h+. Make sure corresponding base is populated.

    METHOD - sub-db (e.g. 'pbesol-v2', 'all').
    """
    mmi = McMongoInjector(mcxd_type="mc3d")
    mmi.populate_xrd(method, recheck)
    mmi.populate_dataset_index()


@mc3d.command("run-supercon-phonon-vis")
@click.option(
    "--regen",
    is_flag=True,
    help="Re-generate all entries.",
)
def mc3d_run_supercon_phonon_vis(regen):
    """
    Supercon phonon visualization data.

    Default is to check/generate only missing entries.
    """
    mmi = McMongoInjector(mcxd_type="mc3d")
    mmi.populate_supercon_phonon_vis(regen)
    mmi.populate_dataset_index()


@mc3d.command("run-fermisurf-bxsf")
@click.option(
    "--prod",
    is_flag=True,
    help="Upload to production S3 path instead of dev.",
)
def mc3d_run_fermisurf_bxsf(prod=False):
    """Convert and upload all PBESOL v1 fermisurf BXSF files to S3."""
    fermisurf.convert_and_upload_all(dev_mode=not prod)


# ========================
# mc2d
# ========================


@cli.group()
def mc2d():
    """MC2D pipeline commands."""
    pass


@mc2d.command("run-base")
def mc2d_run_base():
    """
    Base & base-derived data. Fairly fast to run.

    METHOD - sub-db (e.g. 'pbesol-v2', 'all').
    """
    mmi = McMongoInjector(mcxd_type="mc2d")
    mmi.inject_file_data("pbe-v1")
    mmi.populate_base_derived("pbe-v1")
    mmi.populate_dataset_index()


@mc2d.command("run-phonon-vis")
def mc2d_run_phonon_vis():
    """
    Phonon visualization data.
    """
    mmi = McMongoInjector(mcxd_type="mc2d")
    populate_mc2d_phonon_vis(mmi.db)
    mmi.populate_dataset_index()


# ========================
# common
# ========================


@cli.command()
@click.argument(
    "method",
    type=str,
)
@click.argument(
    "selection",
    type=str,
)
def upload_s3(method, selection):
    """
    Upload collections to S3.

    METHOD - sub-db (e.g. 'pbesol-v2', 'all').

    SELECTION - 'base' for all small base collections, or a large collection name (xrd, supercon_phonon-vis).
    """
    mmi = McMongoInjector()
    su = MongoS3Uploader(mmi.mongo_uri, mmi.mongo_db_name)
    su.upload_collections(method, selection)


if __name__ == "__main__":
    cli()
