"""Command line interface for cfn-tools."""

import sys
from pathlib import Path

import click
import yaml

from cfn_tools.cfn_processing import load_yaml_file


@click.group()
def cli() -> None:
    """CloudFormation Tools - Process CloudFormation templates with custom tags."""
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
def process(template: Path, output: Path) -> None:
    """Process all CFNTools tags in the CloudFormation YAML file."""
    try:
        # Check if template exists
        if not template.exists():
            click.echo(f"Error: Template file not found: {template}", err=True)
            sys.exit(1)

        # Load and process the template
        processed_data = load_yaml_file(str(template))

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


if __name__ == "__main__":
    cli()
