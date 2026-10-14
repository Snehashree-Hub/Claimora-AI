# backend/app/insurer_config.py

INSURERS = {
    "star_health": {
        "name": "Star Health and Allied Insurance",
        "type": "Standalone Health Insurer",
        "claim_support": True,
        "email_processing": True,
    },

    "care_health": {
        "name": "Care Health Insurance",
        "type": "Standalone Health Insurer",
        "claim_support": True,
        "email_processing": True,
    },

    "niva_bupa": {
        "name": "Niva Bupa Health Insurance",
        "type": "Standalone Health Insurer",
        "claim_support": True,
        "email_processing": True,
    },

    "manipal_cigna": {
        "name": "ManipalCigna Health Insurance",
        "type": "Standalone Health Insurer",
        "claim_support": True,
        "email_processing": True,
    },

    "aditya_birla": {
        "name": "Aditya Birla Health Insurance",
        "type": "Standalone Health Insurer",
        "claim_support": True,
        "email_processing": True,
    },
}


def get_all_insurers():
    return INSURERS


def get_insurer(insurer_id: str):
    return INSURERS.get(insurer_id)


def insurer_exists(insurer_id: str):
    return insurer_id in INSURERS