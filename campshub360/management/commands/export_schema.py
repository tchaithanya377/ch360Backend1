from django.core.management.base import BaseCommand
from django.core.management import call_command
from pathlib import Path


class Command(BaseCommand):
    help = "Export OpenAPI schema to schema.yml and schema.json using drf-spectacular"

    def add_arguments(self, parser):
        parser.add_argument(
            "--out-dir",
            type=str,
            default=str(Path(__file__).resolve().parents[3]),
            help="Output directory for schema files (default: project root)",
        )

    def handle(self, *args, **options):
        out_dir = Path(options["out_dir"]).resolve()
        out_dir.mkdir(parents=True, exist_ok=True)

        yaml_path = out_dir / "schema.yml"
        json_path = out_dir / "schema.json"

        self.stdout.write(self.style.NOTICE(f"Exporting OpenAPI schema to {yaml_path} and {json_path}..."))

        # drf-spectacular infers format from extension
        call_command("spectacular", "--file", str(yaml_path))
        call_command("spectacular", "--file", str(json_path))

        self.stdout.write(self.style.SUCCESS("Schema exported successfully."))


