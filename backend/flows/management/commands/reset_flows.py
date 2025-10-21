"""
Reset flows data and optionally create a CADMA-like flow with real chemistry data.

WARNING: This deletes Flow/FlowVersion/Step/ExecutionSnapshot/StepExecution data.
Use only in development or staging environments.

Usage:
  python manage.py reset_flows [--seed-cadma]
"""

from django.core.management.base import BaseCommand

from flows.models import (
    Artifact,
    ExecutionSnapshot,
    Flow,
    FlowBranch,
    FlowNode,
    FlowVersion,
    Step,
    StepDependency,
    StepExecution,
)


class Command(BaseCommand):
    help = "Delete all flows data and optionally seed a minimal CADMA flow"

    def add_arguments(self, parser):
        parser.add_argument(
            "--seed-cadma",
            action="store_true",
            help="Create a minimal CADMA flow after reset",
        )

    def handle(self, *args, **options):
        # Delete in safe order
        StepExecution.objects.all().delete()
        ExecutionSnapshot.objects.all().delete()
        StepDependency.objects.all().delete()
        Step.objects.all().delete()
        FlowBranch.objects.all().delete()
        FlowNode.objects.all().delete()
        FlowVersion.objects.all().delete()
        Artifact.objects.all().delete()
        Flow.objects.all().delete()
        self.stdout.write(self.style.SUCCESS("Flows data wiped."))

        if options.get("seed_cadma"):
            self.stdout.write(
                self.style.WARNING("Seeding CADMA is not implemented yet.")
            )
            # Placeholder: could call into builder with predefined definition
