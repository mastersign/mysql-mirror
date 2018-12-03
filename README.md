# MySQL Mirror

> Clones database tables from one MySQL server to another MySQL server.

## Usage
Clone tables from _a_, to the server _b_.
For the `config.ini` see section _Example Configuration_.

~~~sh
mirror_mysql_database.py -c config.ini a b
~~~

## Docker Usage
This tool is published as a Docker container as `mastersign/mysql-mirror`.
To run `mirror_mysql_database` in a Docker container use the following command.
For the `config.ini` see section _Example Configuration_.

~~~sh
docker run --rm -ti \
    -v $(pwd)/config.ini:/app/config.ini \
    mastersign/mysql-mirror \
    a b
~~~

## Example Configuration

The configuration contains the connection information for the servers
in individual sections of the INI file.
The server sections must be called `database.<name>`.
The name used here is not the actual hostname of the server,
but rather an alias inside the configuration.
There can be more than two server sections in the configuration.

The fields in a server section are:

* `host`: The IP address or hostname, optionally with a port number like `servername:3306`
* `schema`: (_optional_) The default schema on this server
* `user`: (_optional_) The username the login at the MySQL server (default is `root`)
* `password`: (_optional_) The password for the login at the MySQL server (default is empty)

There can be multiple sections to customize the mirroring between two databases.
They must be called `mirror.<source-alias>.<target-alias>`.
Both aliases point to a server specified in a server section.

A mirror section supports the following fields:

* `include`: A comma separated list with tablename patterns to include in the linking
* `exclude`: A comma separated list with tablename patterns to exclude from the linking
* `source_schema`: Override for the schema on the source server
* `target_schema`: Override for the schema on the target server
* `drop_schema`: Drop the target schema before copying tables
* `whole_schema`: Copy all tables in one operation (necessary for foreign keys), ignore `include` and `exclude`

Example for `config.ini`:

~~~ini
[database.a]
host = server-a
schema = source_db
user = root
password =

[database.b]
host = server-b:3306
schema = target_db
user = root
password =

[mirror.b.a]
include = abc_*
exclude = abc_*_x, abc_?y
drop_schema = yes
whole_schema = no
~~~

## Help Text

~~~
usage: mirror_mysql_database.py [-h] [-v] [-t TABLE] [-w] [-d]
                                [-c CONFIG_FILES] [-o OPTIONS [OPTIONS ...]]
                                source target

Copy tables from one database to another.

positional arguments:
  source                The name of the source database configuration.
  target                The name of the target database configuration.

optional arguments:
  -h, --help            show this help message and exit
  -v, --version         print the program version and exit
  -t TABLE, --table TABLE
                        The name of a single table to copy. Is ignored if
                        --whole-database is used
  -w, --whole-database  Mirror the database as a whole. Ignore include and
                        exclude configuration. Is necessary if foreign keys
                        have to be restored.
  -d, --dry             List selected tables, do not copy any data.
  -c CONFIG_FILES, --config-file CONFIG_FILES
                        A path to a configuration file in UTF-8 encoded INI
                        format. This argument can be used multiple times.
  -o OPTIONS [OPTIONS ...], --options OPTIONS [OPTIONS ...]
                        One or more configuration options, given in the format
                        <section>.<option>=<value>.
~~~

## License

This project is published under the BSD-3-Clause license.

Copyright &copy; 2018 Tobias Kiertscher <dev@mastersign.de>.
