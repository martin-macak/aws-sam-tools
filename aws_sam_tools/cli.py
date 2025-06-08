"""Command line interface for aws-sam-tools.

This module provides the command-line interface for aws-sam-tools, enabling users
to process CloudFormation templates and OpenAPI specifications from the command line.

Commands:
- template process: Process CloudFormation templates with CFNTools tags
- openapi process: Process OpenAPI specifications with rule-based transformations

The CLI supports various output formats and processing options, making it easy
to integrate aws-sam-tools into build pipelines and automation workflows.

Example usage:
    $ aws-sam-tools template process --template template.yaml --output processed.yaml --replace-tags
    $ aws-sam-tools openapi process --rule "path/method : delete : resource.security == 'none'"
"""

import sys
from pathlib import Path

import click
import yaml

from aws_sam_tools.cfn_processing import load_yaml_file
from aws_sam_tools.openapi import OutputFormat, process_openapi as process_openapi_spec


@click.version_option(prog_name="aws-sam-tools")
@click.group()
def cli() -> None:
    """AWS SAM Tools - Process CloudFormation templates with custom tags."""
    pass


@cli.group()
def template() -> None:
    """Commands for working with CloudFormation templates."""
    pass


@template.command()
@click.option(
    "--template",
    "-t",
    type=click.Path(path_type=Path),
    default="template.yaml",
    help="Path to the CloudFormation YAML file (default: template.yaml)",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    default="-",
    help="Output file path. Use '-' for stdout (default: -)",
)
@click.option(
    "--replace-tags",
    is_flag=True,
    default=False,
    help="Replace CloudFormation tags with intrinsic functions",
)
def process(template: Path, output: Path, replace_tags: bool) -> None:
    """Process all CFNTools tags in the CloudFormation YAML file."""
    try:
        # Check if template exists
        if not template.exists():
            click.echo(f"Error: Template file not found: {template}", err=True)
            sys.exit(1)

        # Load and process the template
        processed_data = load_yaml_file(str(template), replace_tags=replace_tags)

        # Convert to YAML string
        output_yaml = yaml.dump(
            processed_data,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
        )

        # Write output
        if str(output) == "-":
            # Write to stdout
            click.echo(output_yaml, nl=False)
        else:
            # Write to file
            output.write_text(output_yaml, encoding="utf-8")
            click.echo(f"Processed template written to: {output}", err=True)

    except FileNotFoundError:
        click.echo(f"Error: Template file not found: {template}", err=True)
        sys.exit(1)
    except yaml.YAMLError as e:
        click.echo(f"Error: Failed to parse YAML: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.group()
def openapi() -> None:
    """Commands for working with OpenAPI specifications."""
    pass


@openapi.command(name="process")
@click.option(
    "--rule",
    "-r",
    multiple=True,
    help="Rule to apply to the specification. Can be specified multiple times.",
)
@click.option(
    "--input",
    "-i",
    type=click.Path(),
    default="-",
    help="Input file path. Use '-' for stdin (default: -)",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    default="-",
    help="Output file path. Use '-' for stdout (default: -)",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["json", "yaml", "default"], case_sensitive=False),
    default="default",
    help="Output format (default: same as input)",
)
def process_openapi(rule: tuple, input: str, output: str, format: str) -> None:
    """Process OpenAPI specification with rules."""
    try:
        # Read input
        if input == "-":
            input_content = sys.stdin.read()
            input_path = None
        else:
            input_path = Path(input)
            if not input_path.exists():
                click.echo(f"Error: Input file not found: {input}", err=True)
                sys.exit(1)
            input_content = input_path.read_text(encoding="utf-8")

        # Convert format string to enum
        format_enum = OutputFormat(format) if format != "default" else OutputFormat.DEFAULT

        # Process the specification
        processed_content = process_openapi_spec(
            input_content,
            list(rule),
            input_format=None,  # Let the processor auto-detect
            output_format=format_enum,
        )

        # Write output
        if output == "-":
            click.echo(processed_content, nl=False)
        else:
            output_path = Path(output)
            output_path.write_text(processed_content, encoding="utf-8")
            click.echo(f"Processed specification written to: {output}", err=True)

    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
