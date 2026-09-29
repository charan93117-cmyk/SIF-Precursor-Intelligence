import os
import random
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

random.seed(42)

OUTPUT_DIR = "data"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "synthetic_reports.csv")

NUM_REPORTS = 250


# ============================================================
# MASTER DATA
# ============================================================

sites = [
    "Duliajan",
    "Digboi",
    "Naharkatiya",
    "Moran",
    "Bokakhat",
    "KGB",
    "Jorhat",
    "Tinsukia"
]

locations = [
    "Well Pad",
    "Drilling Rig",
    "Production Area",
    "Gas Gathering Station",
    "Processing Plant",
    "Workshop",
    "Tank Farm",
    "Pipeline Corridor",
    "Maintenance Area",
    "Compressor Station",
    "Warehouse",
    "Electrical Substation"
]

activities = [
    "Maintenance",
    "Drilling",
    "Hot Work",
    "Electrical Work",
    "Mechanical Work",
    "Lifting Operation",
    "Vehicle Movement",
    "Pipeline Work",
    "Inspection",
    "Confined Space Entry",
    "Production Operation",
    "Valve Maintenance"
]

report_types = [
    "Unsafe Act",
    "Unsafe Condition",
    "Near Miss"
]


# ============================================================
# RECURRING SIF PRECURSOR PATTERNS
# ============================================================

patterns = [

    {
        "name": "Energy Isolation Failure",
        "activity": "Maintenance",
        "hazard": "Unexpected Energy Release",
        "energy": "Electrical Energy",
        "barrier": "Lockout Tagout",
        "lsr": "Energy Isolation",
        "texts": [
            "Technician started maintenance without confirming electrical isolation.",
            "Equipment was opened before LOTO verification was completed.",
            "Maintenance activity observed with energy source not positively isolated.",
            "Worker prepared to work on equipment while electrical supply remained connected.",
            "Isolation was not properly verified before maintenance began.",
            "Electrical panel was accessed without checking lockout status.",
            "Worker nearly contacted an energized component during maintenance.",
            "LOTO procedure was not followed before opening the equipment."
        ]
    },

    {
        "name": "Line of Fire Exposure",
        "activity": "Mechanical Work",
        "hazard": "Line of Fire",
        "energy": "Mechanical Energy",
        "barrier": "Barricading",
        "lsr": "Line of Fire",
        "texts": [
            "Worker stood close to moving machinery during maintenance.",
            "Employee was positioned in the line of fire while equipment was operating.",
            "Person entered the danger zone near moving mechanical equipment.",
            "Worker was exposed to stored mechanical energy during repair.",
            "Technician placed hands near moving components.",
            "Maintenance personnel were working close to an active machine.",
            "Worker entered the equipment swing area without adequate separation.",
            "Personnel were observed inside the potential line of fire."
        ]
    },

    {
        "name": "Hot Work Control Failure",
        "activity": "Hot Work",
        "hazard": "Fire",
        "energy": "Thermal Energy",
        "barrier": "Permit to Work",
        "lsr": "Hot Work",
        "texts": [
            "Welding activity started without a valid hot work permit.",
            "Hot work was observed without confirming the required permit.",
            "Grinding was carried out near combustible material without proper controls.",
            "Worker began welding before gas testing was completed.",
            "Hot work area did not have adequate fire prevention controls.",
            "Welding activity was performed without verifying authorization.",
            "Sparks from grinding were observed close to combustible material.",
            "Hot work permit requirements were not fully followed."
        ]
    },

    {
        "name": "Working at Height Failure",
        "activity": "Maintenance",
        "hazard": "Fall from Height",
        "energy": "Gravity",
        "barrier": "Fall Protection",
        "lsr": "Working at Height",
        "texts": [
            "Worker was working at height without connecting the safety harness.",
            "Personnel accessed an elevated platform without adequate fall protection.",
            "Technician was observed near an open edge without a lanyard.",
            "Worker climbed onto an elevated structure without proper protection.",
            "Fall arrest equipment was not connected during maintenance.",
            "Employee worked close to an unprotected edge.",
            "Harness was available but was not attached while working at height.",
            "Elevated work was performed without complete fall protection."
        ]
    },

    {
        "name": "Confined Space Control Failure",
        "activity": "Confined Space Entry",
        "hazard": "Toxic Gas Exposure",
        "energy": "Chemical Energy",
        "barrier": "Gas Testing",
        "lsr": "Confined Spaces",
        "texts": [
            "Worker prepared to enter a confined space without gas testing.",
            "Atmospheric testing was not completed before entry.",
            "Personnel approached the vessel without confirming oxygen levels.",
            "Confined space entry was initiated before checking the atmosphere.",
            "Gas detector was not used before entering the tank.",
            "Worker was exposed to a potentially hazardous atmosphere during entry preparation.",
            "Required confined space atmospheric checks were incomplete.",
            "Entry team did not verify gas test results before access."
        ]
    },

    {
        "name": "Lifting Operation Failure",
        "activity": "Lifting Operation",
        "hazard": "Dropped Object",
        "energy": "Gravity",
        "barrier": "Lifting Plan",
        "lsr": "Safe Mechanical Lifting",
        "texts": [
            "Worker entered below a suspended load during lifting.",
            "Personnel were observed inside the lifting exclusion zone.",
            "A person stood beneath a suspended component during crane operation.",
            "Load was being lifted while workers remained nearby.",
            "Lifting activity continued without maintaining a clear exclusion zone.",
            "Worker entered the drop zone while the load was suspended.",
            "Crane lifting operation was conducted with personnel too close to the load.",
            "Suspended load created a potential dropped-object exposure."
        ]
    },

    {
        "name": "Vehicle-Pedestrian Interaction",
        "activity": "Vehicle Movement",
        "hazard": "Vehicle Strike",
        "energy": "Vehicle Energy",
        "barrier": "Traffic Control",
        "lsr": "Driving",
        "texts": [
            "Pedestrian walked close to a moving vehicle in the work area.",
            "Vehicle reversed while personnel were present nearby.",
            "Worker entered the vehicle movement path without separation.",
            "A light vehicle moved through an area occupied by pedestrians.",
            "Pedestrian and vehicle routes were not adequately separated.",
            "Worker was exposed to a moving vehicle during site movement.",
            "Vehicle reversing activity occurred without clear pedestrian control.",
            "Personnel were observed within the vehicle operating zone."
        ]
    },

    {
        "name": "Safety Control Bypass",
        "activity": "Production Operation",
        "hazard": "Unexpected Energy Release",
        "energy": "Stored Energy",
        "barrier": "Safety Interlock",
        "lsr": "Bypassing Safety Controls",
        "texts": [
            "Safety interlock was bypassed during equipment operation.",
            "Operator temporarily defeated a safety control to continue production.",
            "Equipment was operated with a protective interlock bypassed.",
            "Safety control was overridden without an approved procedure.",
            "Operator bypassed the equipment protection system.",
            "Interlock was found defeated during operation.",
            "Production continued while a safety protection was intentionally bypassed.",
            "Protective control was not active during equipment operation."
        ]
    },

    {
        "name": "Unauthorised Work",
        "activity": "Pipeline Work",
        "hazard": "Pressure Release",
        "energy": "Pressure",
        "barrier": "Permit to Work",
        "lsr": "Work Authorisation",
        "texts": [
            "Work started before the required permit was issued.",
            "Maintenance activity began without proper work authorization.",
            "Workers started pipeline work before permit approval.",
            "Job was initiated without confirming the work permit.",
            "Personnel began work without completing authorization requirements.",
            "Work activity was observed before formal permit approval.",
            "Required authorization was missing when the task commenced.",
            "Pipeline maintenance started without valid work authorization."
        ]
    }
]


# ============================================================
# NON-SIF REPORT TYPES
# ============================================================

non_sif_reports = [
    {
        "activity": "Inspection",
        "hazard": "Housekeeping",
        "energy": "None",
        "barrier": "Housekeeping Control",
        "text": "Minor housekeeping issue observed in the work area."
    },
    {
        "activity": "Inspection",
        "hazard": "Poor Storage",
        "energy": "None",
        "barrier": "Storage Control",
        "text": "Small amount of waste material found near the walkway."
    },
    {
        "activity": "Maintenance",
        "hazard": "Housekeeping",
        "energy": "None",
        "barrier": "Housekeeping Control",
        "text": "Housekeeping improvement required around the equipment."
    },
    {
        "activity": "Inspection",
        "hazard": "Minor Spill",
        "energy": "None",
        "barrier": "Spill Control",
        "text": "Minor oil stain observed near the maintenance area."
    },
    {
        "activity": "Maintenance",
        "hazard": "Poor Tool Storage",
        "energy": "None",
        "barrier": "Tool Storage",
        "text": "Some tools were left outside the designated storage location."
    },
    {
        "activity": "Inspection",
        "hazard": "Walkway Obstruction",
        "energy": "None",
        "barrier": "Housekeeping Control",
        "text": "Walkway requires better housekeeping."
    },
    {
        "activity": "Inspection",
        "hazard": "Material Obstruction",
        "energy": "None",
        "barrier": "Housekeeping Control",
        "text": "Small material obstruction noticed near the work area."
    },
    {
        "activity": "Inspection",
        "hazard": "Housekeeping",
        "energy": "None",
        "barrier": "Housekeeping Control",
        "text": "General housekeeping condition requires attention."
    },
    {
        "activity": "Inspection",
        "hazard": "Minor PPE Issue",
        "energy": "None",
        "barrier": "PPE",
        "text": "Minor PPE compliance issue observed with no exposure to high energy."
    },
    {
        "activity": "Inspection",
        "hazard": "Housekeeping",
        "energy": "None",
        "barrier": "Housekeeping Control",
        "text": "Worker was reminded to maintain good housekeeping practices."
    },
    {
        "activity": "Inspection",
        "hazard": "Poor Storage",
        "energy": "None",
        "barrier": "Storage Control",
        "text": "Loose packaging material was found near the warehouse."
    },
    {
        "activity": "Inspection",
        "hazard": "Poor Storage",
        "energy": "None",
        "barrier": "Storage Control",
        "text": "Storage area requires better organization."
    },
    {
        "activity": "Inspection",
        "hazard": "Water Accumulation",
        "energy": "None",
        "barrier": "Housekeeping Control",
        "text": "Small water accumulation observed near the walkway."
    },
    {
        "activity": "Inspection",
        "hazard": "Poor Lighting",
        "energy": "None",
        "barrier": "Lighting Control",
        "text": "Minor lighting issue noticed in the work area."
    },
    {
        "activity": "Maintenance",
        "hazard": "Poor Tool Storage",
        "energy": "None",
        "barrier": "Tool Storage",
        "text": "Tools were not properly arranged after maintenance."
    }
]


# ============================================================
# CREATE ONE REPORT
# ============================================================

def create_report(report_number):

    # Approximately 25% SIF-potential reports.
    is_sif = random.random() < 0.25

    date = pd.Timestamp("2025-01-01") + pd.Timedelta(
        days=random.randint(0, 500)
    )

    site = random.choice(sites)
    location = random.choice(locations)

    # --------------------------------------------------------
    # SIF REPORT
    # --------------------------------------------------------

    if is_sif:

        pattern = random.choice(patterns)

        text = random.choice(pattern["texts"])

        prefixes = [
            "",
            "During routine inspection, ",
            "Field observation: ",
            "During site activity, ",
            "It was observed that ",
            "Safety observation: "
        ]

        text = random.choice(prefixes) + text

        text = text.replace("nearthe", "near the")
        text = text.replace("supplyremained", "supply remained")

        return {
            "report_id": f"OIL-SYN-{report_number:04d}",
            "date": date.strftime("%Y-%m-%d"),
            "site": site,
            "location": location,
            "activity": pattern["activity"],
            "report_type": random.choice(report_types),
            "free_text": text,
            "ground_truth_hazard": pattern["hazard"],
            "ground_truth_energy": pattern["energy"],
            "ground_truth_barrier": pattern["barrier"],
            "ground_truth_sif": "YES",
            "ground_truth_lsr": pattern["lsr"],
            "ground_truth_pattern": pattern["name"]
        }

    # --------------------------------------------------------
    # NON-SIF REPORT
    # --------------------------------------------------------

    report = random.choice(non_sif_reports)

    return {
        "report_id": f"OIL-SYN-{report_number:04d}",
        "date": date.strftime("%Y-%m-%d"),
        "site": site,
        "location": location,
        "activity": report["activity"],
        "report_type": random.choice(report_types),
        "free_text": report["text"],
        "ground_truth_hazard": report["hazard"],
        "ground_truth_energy": report["energy"],
        "ground_truth_barrier": report["barrier"],
        "ground_truth_sif": "NO",
        "ground_truth_lsr": "",
        "ground_truth_pattern": ""
    }


# ============================================================
# GENERATE DATASET
# ============================================================

def main():

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    reports = []

    for i in range(1, NUM_REPORTS + 1):
        reports.append(create_report(i))

    df = pd.DataFrame(reports)

    df.to_csv(OUTPUT_FILE, index=False)

    print("=" * 60)
    print("SIF PRECURSOR INTELLIGENCE")
    print("SYNTHETIC DATA GENERATOR")
    print("=" * 60)

    print(f"\nGenerated reports : {len(df)}")

    print(
        f"SIF YES           : "
        f"{(df['ground_truth_sif'] == 'YES').sum()}"
    )

    print(
        f"SIF NO            : "
        f"{(df['ground_truth_sif'] == 'NO').sum()}"
    )

    print("\nColumns:")

    for column in df.columns:
        print(f"  - {column}")

    print(f"\nSaved to:")
    print(OUTPUT_FILE)

    print("\nFirst 5 reports:")
    print(df.head().to_string(index=False))


if __name__ == "__main__":
    main()