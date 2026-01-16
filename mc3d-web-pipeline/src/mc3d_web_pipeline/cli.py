#!/usr/bin/env python

import click

from mc3d_web_pipeline.mc_data_injector import McDataInjector
from mc3d_web_pipeline.s3_utils import MongoS3Uploader


@click.group()
def cli():
    """
    Run the MC3D web pipeline.
    """
    pass


@cli.command()
@click.argument(
    "method",
    type=str,
)
def run_base(method):
    """
    Base & base-derived data. Fairly fast to run.

    METHOD - sub-db (e.g. 'pbesol-v2', 'all').
    """
    mdi = McDataInjector()
    mdi.inject_file_data(method)
    mdi.populate_base_derived(method)
    mdi.populate_contrib_index()


@cli.command()
@click.argument(
    "method",
    type=str,
)
@click.option(
    "--recheck",
    is_flag=True,
    help="Re-check that each individual XRD is calculated.",
)
def run_xrd(method, recheck):
    """
    X-ray diffraction. One db can take 10h+. Make sure corresponding base is populated.

    METHOD - sub-db (e.g. 'pbesol-v2', 'all').
    """
    mdi = McDataInjector()
    mdi.populate_xrd(method, recheck)
    mdi.populate_contrib_index()


@cli.command()
@click.option(
    "--regen",
    is_flag=True,
    help="Re-generate all entries.",
)
def run_supercon_phonon_vis(regen):
    """
    Supercon phonon visualization data.

    Default is to check/generate only missing entries.
    """
    mdi = McDataInjector()
    mdi.populate_supercon_phonon_vis(regen)
    mdi.populate_contrib_index()


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
    mdi = McDataInjector()
    su = MongoS3Uploader(mdi.mongo_uri, mdi.mongo_db_name)
    su.upload_collections(method, selection)


if __name__ == "__main__":
    cli()
