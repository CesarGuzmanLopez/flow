"""
Recompute RDKit-based ADMETSA properties for all families and molecules.

- Removes prior mock/provider properties by method/source detection
- Computes properties using the configured engine (expect CHEM_ENGINE=rdkit)
- Stores MolecularProperty with method="rdkit" and source_id="provider:rdkit"

Usage:
  python manage.py recompute_admetsa [--family <id>] [--all]

Defaults to recomputing for all families when --all is provided.
"""

from typing import Iterable

from django.core.management.base import BaseCommand

from chemistry import services as chem_services
from chemistry.models import Family, FamilyMember, MolecularProperty


class Command(BaseCommand):
    help = "Recompute RDKit-based ADMETSA properties and cleanup mock values"

    def add_arguments(self, parser):
        parser.add_argument("--family", type=int, help="Limit to a single family id")
        parser.add_argument(
            "--all",
            action="store_true",
            help="Recompute for all families",
        )

    def handle(self, *args, **options):
        fam_id = options.get("family")
        do_all = bool(options.get("all"))

        families: Iterable[Family]
        if fam_id:
            families = Family.objects.filter(id=fam_id)
        elif do_all:
            families = Family.objects.all()
        else:
            self.stdout.write(
                self.style.WARNING(
                    "Provide --family <id> or --all to select target families"
                )
            )
            return

        for fam in families:
            # Remove previous mock/source properties for member molecules
            member_ids = list(
                FamilyMember.objects.filter(family=fam).values_list(
                    "molecule_id", flat=True
                )
            )
            deleted, _ = MolecularProperty.objects.filter(
                molecule_id__in=member_ids, method__in=["mock", "test", "dev"]
            ).delete()
            if deleted:
                self.stdout.write(
                    self.style.WARNING(
                        f"Removed {deleted} mock/test/dev properties for family {fam.id}"
                    )
                )

            # Compute properties
            summary = chem_services.generate_admetsa_for_family(
                family_id=fam.id,
                created_by=fam.created_by if hasattr(fam, "created_by") else None,
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"Family {fam.id}: recomputed properties for {summary['count']} molecules"
                )
            )

        self.stdout.write(self.style.SUCCESS("Done."))
