from typing import Final

import rapidfuzz
from django.core.management import BaseCommand
from django.core.management import CommandError

from documents.models import Document


class Command(BaseCommand):
    help = "Manages the document index."

    def add_arguments(self, parser):
        parser.add_argument(
            "--ratio",
            default=85.0,
            type=float,
            help="Ratio to consider documents a match",
        )

    def handle(self, *args, **options):
        RATIO_MIN: Final[float] = 0.0
        RATIO_MAX: Final[float] = 100.0

        opt_ratio = options["ratio"]
        match_pairs = set()

        # Ratio is a float from 0.0 to 100.0
        if opt_ratio < RATIO_MIN or opt_ratio > RATIO_MAX:
            raise CommandError("The ratio must be between 0 and 100")

        all_docs = Document.objects.all().order_by("id")

        for first_doc in all_docs:
            for second_doc in all_docs:
                if first_doc.pk == second_doc.pk:
                    continue

                # Normalize the string some, lower case, whitespace, etc
                first_string = rapidfuzz.utils.default_process(first_doc.content)
                second_string = rapidfuzz.utils.default_process(second_doc.content)

                # Basic matching ratio
                match = rapidfuzz.fuzz.ratio(first_string, second_string)

                if match >= opt_ratio:
                    # Skip matching which have already been matched together
                    # doc 1 to doc 2 is the same as doc 2 to doc 1
                    if (first_doc.pk, second_doc.pk) in match_pairs or (
                        second_doc.pk,
                        first_doc.pk,
                    ) in match_pairs:
                        continue
                    else:
                        match_pairs.add((first_doc.pk, second_doc.pk))
                        match_pairs.add((second_doc.pk, first_doc.pk))

                    self.stdout.write(
                        self.style.NOTICE(
                            f"Document {first_doc.pk} fuzzy match"
                            f" to {second_doc.pk} (confidence {match:.3f})",
                        ),
                    )