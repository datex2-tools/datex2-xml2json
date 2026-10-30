from argparse import ArgumentParser

import geoparquet_io as gpio


def merge_partition(partion: str, outfile: str) -> None:
    """
    merge_partition reads all parquet files from a given partition (e.g. directory), merges them
    and writes them to geoparquet file `outfile`.

    Note: OGC_FID and index column are removed
    """

    # Read all partitions
    table = gpio.read_partition(partion)
    column_name = 'OGC_FID'
    index = table.schema.get_field_index(column_name)

    if index != -1:
        table._table = table._table.remove_column(index)
    table.write(outfile)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('partition', help='Partition (e.g. directory) of parquet files to merge')
    parser.add_argument(
        '-o',
        '--outfile',
        help='Path of merged parquet file',
        default='merged.parquet',
    )

    args = parser.parse_args()

    merge_partition(
        args.partition,
        args.outfile,
    )
