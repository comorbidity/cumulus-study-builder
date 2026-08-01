import os

ENCOUNTER_REF = os.environ.get("CUMULUS_ENCOUNTER_REF", "encounter_ref_link")
CUBE_AS_VIEW = int(os.environ.get("CUMULUS_CUBE_AS_VIEW") or 0)
CUBE_MIN_SUBJECTS = int(os.environ.get("CUMULUS_CUBE_MIN_SUBJECTS") or 10)
