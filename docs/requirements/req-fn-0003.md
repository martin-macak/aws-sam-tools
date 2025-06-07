# REQ-FN-0003 - Command line interface

Add command line interface to the project.

## Acceptance Criteria

- this package can be executed as a command line tool
- the command line tool supports commands and subcommands and additional parameters

### Command `cfn`

This command processes the CloudFormation yaml file.
This command supports subcommands. The default command is `process`.

#### Subcommand `process`

This subcommand processes all `CFNTools` tags in the CloudFormation yaml file.

Parameters:
- **template**: str - optional parameter, this is the path to the CloudFormation yaml file. When the path is relative then the path is relative to the current working directory. The default is `template.yaml`.
- **output**: str - optional parameter, default is '-'. When '-' is used then the `stdout` is used. Otherwise the output is written to the file specified by the parameter. When the path is relative then the path is relative to the current working directory.

## Implementation notes

- use click to create the command line interface
- create new module `cfn_tools.cliheck
- use existing packages to implement the command line interface
- don't put any logic into the command line interface, use backend packages and modules