#!/usr/bin/env python3
# _*_ coding: utf-8 _*_

import sys
import argparse
import fnmatch
from mastersign_config import Configuration
from mastersign_mysql import connect, mirror


__version__ = '0.1.1'


def drop_schema(conn, name):
    with conn.cursor() as cur:
        cur.execute('DROP DATABASE IF EXISTS `{}`'.format(name))


def create_schema(conn, name):
    with conn.cursor() as cur:
        cur.execute(
            'CREATE DATABASE `{}` DEFAULT CHARACTER SET utf8mb4'.format(name))


def get_tables(conn):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT table_name, table_schema
            FROM information_schema.tables
            WHERE table_type = 'BASE TABLE'
              AND table_schema NOT IN ('mysql','sys','information_schema','performance_schema')
            """)
        return cur.fetchall()


def filter_table_names(tables, includes=None, excludes=None):
    def pred(name):
        if includes:
            if not any(map(lambda inc: fnmatch.fnmatch(name, inc), includes)):
                return False
        if excludes:
            if any(map(lambda exc: fnmatch.fnmatch(name, exc), excludes)):
                return False
        return True
    return list(filter(lambda t: pred(t), tables))


def mirror_table(cfg, table_name, table_schema, server_name):
    pass

def parse_args():
    parser = argparse.ArgumentParser(
        description='Copy tables from one database to another.')
    parser.add_argument('-v', '--version', action='version', version=__version__,
                        help='print the program version and exit')
    parser.add_argument('source',
                        help='The name of the source database configuration.')
    parser.add_argument('target',
                        help='The name of the target database configuration.')
    parser.add_argument('-t', '--table',
                        help='The name of a single table to copy. '
                        'Is ignored if --whole-database is used')
    parser.add_argument('-w', '--whole-database', dest='whole_database', action='store_true',
                        help='Mirror the database as a whole. '
                        'Ignore include and exclude configuration. '
                        'Is necessary if foreign keys have to be restored.')
    parser.add_argument('-d', '--dry', action='store_true',
                        help='List selected tables, do not copy any data.')

    Configuration.add_config_arguments(parser)
    return parser.parse_args()


def run():
    args = parse_args()
    config = Configuration.load(args)
    source_cfg_group = 'database.' + args.source
    target_cfg_group = 'database.' + args.target
    mirror_cfg_group = 'mirror.' + args.source + '.' + args.target

    source_schema = config.str(mirror_cfg_group, 'source_schema') or config.str(
        source_cfg_group, 'schema')
    if not source_schema:
        raise Exception('No source schema specified.')
    target_schema = config.str(mirror_cfg_group, 'target_schema') or config.str(
        target_cfg_group, 'schema')
    if not target_schema:
        raise Exception('No target schema specified.')

    if args.whole_database or config.bool(mirror_cfg_group, 'whole_schema'):
        print('Copying whole database ...\n  Source: {}/{}\n  Target: {}/{}'.format(
            config.str(source_cfg_group, 'host'), source_schema,
            config.str(target_cfg_group, 'host'), target_schema))

        if args.dry:
            return True

        mirror(config, args.source, args.target, source_schema, target_schema,
               drop_db=config.bool(mirror_cfg_group, 'drop_schema'),
               drop_table=False)
    else:
        print('Copying tables ...\n  Source: {}/{}\n  Target: {}/{}'.format(
            config.str(source_cfg_group, 'host'), source_schema,
            config.str(target_cfg_group, 'host'), target_schema))

        if args.table:
            selected_tables = [args.table]
        else:
            source_conn = connect(config, args.source)
            try:
                source_tables = [
                    t['table_name']
                    for t in get_tables(source_conn)
                    if t['table_schema'] == source_schema
                ]
                selected_tables = filter_table_names(
                    source_tables,
                    includes=config.str_list(mirror_cfg_group, 'include'),
                    excludes=config.str_list(mirror_cfg_group, 'exclude'))
                print('Selected tables')
                for t in selected_tables:
                    print('- ' + t)
            except KeyboardInterrupt:
                print("Cancelled by user.")
                return False
            finally:
                source_conn.close()

        if args.dry:
            return True

        if config.bool(mirror_cfg_group, 'drop_schema'):
            target_conn = connect(config, args.target)
            try:
                print("Dropping target database `{}` ...".format(target_schema))
                drop_schema(target_conn, target_schema)
                print("Recreating target database `{}` ...".format(target_schema))
                create_schema(target_conn, target_conn)
            finally:
                target_conn.close()
        for table in selected_tables:
            print('Copying table {}'.format(table))
            try:
                mirror(config, args.source, args.target, source_schema, target_schema,
                       table_name=table, drop_table=True)
            except KeyboardInterrupt:
                print("Cancelled by user.")
                return False

    return True


if __name__ == '__main__':
    sys.exit(0 if run() else 1)
