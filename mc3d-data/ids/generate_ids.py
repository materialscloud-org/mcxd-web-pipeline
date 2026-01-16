#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Generate the list of IDs for the MC3D database."""
import random
import json
import click

from tqdm import tqdm
from pathlib import Path

from aiida import orm
from aiida.cmdline.params import options, types
from aiida.cmdline.utils import echo


@click.command()
@options.PROFILE(type=types.ProfileParamType(load_profile=True))
@options.GROUP(required=True,
    help='Group with unique `StructureData` from which to generate the IDs.',
)
@click.option('-I', '--current-id-file', type=click.Path(exists=True))
@click.option('-O', '--output-id-file', type=click.Path(exists=False), default='new-IDs.json')
def cli(profile, group, current_id_file, output_id_file):

    if current_id_file is None:
        echo.echo_warning(
            'No current ID file has been provided. This will generate a completely new ID JSON file and should only be '
            'used upon database initialization!'
        )
        click.confirm('Do you want to continue?', abort=True)
        current_dict = {}
    else:
        with Path(current_id_file).open('r') as handle:
            current_dict = json.load(handle)

    echo.echo_info('Loading the source from the structure extras...')

    source_list = []

    for struc in tqdm(group.nodes):
        source_list.append(struc.extras['source'])

    if current_id_file is None:
        echo.echo_info('Randomizing the source list for the first generation of the ID JSON file.')
        random.shuffle(source_list)
        append_list = source_list.copy()
    else:
        echo.echo_info('Looking for new source structures in group...')
        current_sources = [tuple(data.values()) for data in current_dict.values()]

        append_list = []

        for source in source_list:
            if tuple(source.values()) not in current_sources:
                append_list.append(source)

    echo.echo_info(f'Found {len(append_list)} new source structures for which to add IDs.')

    mc3d_id_dict = {f'mc3d-{i + len(current_dict) + 1}': source for i, source in enumerate(append_list)}

    with Path(output_id_file).open('w') as handle:
        json.dump(mc3d_id_dict, handle)

if __name__ == '__main__':
    cli()
