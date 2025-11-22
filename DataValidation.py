import xml.etree.ElementTree as ET
import pandas as pd
import re

# ---------------------------------------------------------------------------
# CONFIGURATION: ALL FIELDS FROM YOUR XML SNIPPET
# ---------------------------------------------------------------------------
# We list all simple text fields here to automate extraction.
# PredecessorLink is handled separately because it is a nested list.
XML_FIELDS = [
    "UID", "GUID", "ID", "Name", "Active", "Manual", "Type", "IsNull", 
    "CreateDate", "WBS", "OutlineNumber", "OutlineLevel", "Priority", 
    "Start", "Finish", "Duration", "ManualStart", "ManualFinish", 
    "ManualDuration", "DurationFormat", "FreeformDurationFormat", "Work", 
    "ResumeValid", "EffortDriven", "Recurring", "OverAllocated", "Estimated", 
    "Milestone", "Summary", "DisplayAsSummary", "Critical", "IsSubproject", 
    "IsSubprojectReadOnly", "ExternalTask", "EarlyStart", "EarlyFinish", 
    "LateStart", "LateFinish", "StartVariance", "FinishVariance", "WorkVariance", 
    "FreeSlack", "TotalSlack", "StartSlack", "FinishSlack", "FixedCost", 
    "FixedCostAccrual", "PercentComplete", "PercentWorkComplete", "Cost", 
    "OvertimeCost", "OvertimeWork", "ActualDuration", "ActualCost", 
    "ActualOvertimeCost", "ActualWork", "ActualOvertimeWork", "RegularWork", 
    "RemainingDuration", "RemainingCost", "RemainingWork", "RemainingOvertimeCost", 
    "RemainingOvertimeWork", "ACWP", "CV", "ConstraintType", "CalendarUID", 
    "LevelAssignments", "LevelingCanSplit", "LevelingDelay", "LevelingDelayFormat", 
    "IgnoreResourceCalendar", "HideBar", "Rollup", "BCWS", "BCWP", 
    "PhysicalPercentComplete", "EarnedValueMethod", "IsPublished", "CommitmentType"
]

# ---------------------------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------------------------

def _duration_str_to_hours(duration_str: str) -> float:
    """
    Parses MS Project 'PT' duration strings (e.g., 'PT8H0M0S') to float hours.
    Returns 0.0 if format is invalid or input is not a string.
    """
    if not isinstance(duration_str, str):
        return 0.0
    
    # Simple check: if it's just a number (like slack sometimes is), return it directly
    if duration_str.isdigit():
        return float(duration_str)

    # Regex for Standard ISO 8601 durations used by MS Project
    hours_match = re.search(r'PT(\d+)H', duration_str)
    mins_match = re.search(r'(\d+)M', duration_str)
    
    hours = float(hours_match.group(1)) if hours_match else 0.0
    minutes = float(mins_match.group(1)) if mins_match else 0.0
    
    return hours + (minutes / 60.0)

# ---------------------------------------------------------------------------
# CORE LOADING FUNCTION
# ---------------------------------------------------------------------------

def load_tasks_from_msproject_xml(xml_file_path: str) -> pd.DataFrame:
    """
    Loads comprehensive task data from MS Project XML including predecessors.
    """
    print(f"Loading data from {xml_file_path}...")
    
    try:
        tree = ET.parse(xml_file_path)
        root = tree.getroot()
    except Exception as e:
        print(f"Error parsing XML: {e}")
        return pd.DataFrame()

    # Namespace map
    ns = {"ns": "http://schemas.microsoft.com/project"}

    tasks = []

    for task_node in root.findall(".//ns:Task", ns):
        row = {}
        
        # 1. Extract standard fields dynamically
        for field in XML_FIELDS:
            val = task_node.findtext(f"ns:{field}", default=None, namespaces=ns)
            row[field] = val
            
        # 2. Extract Predecessors (Nested Logic)
        # We combine multiple predecessors into a single string like "5;6"
        predecessors = []
        for link in task_node.findall("ns:PredecessorLink", ns):
            pred_uid = link.findtext("ns:PredecessorUID", default="", namespaces=ns)
            if pred_uid:
                predecessors.append(pred_uid)
        row["Predecessors"] = ";".join(predecessors)

        tasks.append(row)

    if not tasks:
        print("Warning: No tasks found.")
        return pd.DataFrame()

    df = pd.DataFrame(tasks)
    print(f"Successfully loaded {len(df)} tasks with {len(df.columns)} columns.")
    return df

# ---------------------------------------------------------------------------
# PREPROCESSING FUNCTION
# ---------------------------------------------------------------------------

def preprocess_task_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Converts raw XML strings into usable ML data types (Floats, Integers, Datetimes).
    """
    print("Starting data preprocessing...")
    df_clean = df.copy()

    # 1. Convert Cost Fields to Float
    cost_cols = [
        "Cost", "FixedCost", "ActualCost", "RemainingCost", 
        "OvertimeCost", "ActualOvertimeCost", "RemainingOvertimeCost", 
        "ACWP", "BCWS", "BCWP", "CV"
    ]
    for col in cost_cols:
        if col in df_clean.columns:
            df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce').fillna(0.0)

    # 2. Convert Percentage Fields to Float
    pct_cols = ["PercentComplete", "PercentWorkComplete", "PhysicalPercentComplete"]
    for col in pct_cols:
        if col in df_clean.columns:
            df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce').fillna(0.0)

    # 3. Convert 'PT...H' Duration Fields to Numeric Hours
    duration_cols = [
        "Duration", "ManualDuration", "Work", "ActualDuration", 
        "ActualWork", "RemainingDuration", "RemainingWork", 
        "OvertimeWork", "ActualOvertimeWork", "RegularWork"
    ]
    for col in duration_cols:
        if col in df_clean.columns:
            # Create a new column name, e.g., Duration -> Duration_Hours
            new_col = f"{col}_Hours"
            df_clean[new_col] = df_clean[col].apply(_duration_str_to_hours)

    # 4. Convert Slack/Integer Fields
    # Note: MS Project XML Slack is usually in 'tenths of minutes' or similar units.
    # We convert to numeric, but you may need to divide by 10 or 600 depending on exact needs.
    int_cols = [
        "UID", "ID", "Priority", "WBS", "OutlineLevel", 
        "FreeSlack", "TotalSlack", "StartSlack", "FinishSlack",
        "StartVariance", "FinishVariance"
    ]
    for col in int_cols:
        if col in df_clean.columns:
            df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce').fillna(0)

    # 5. Convert Boolean-like Fields (0 or 1)
    bool_cols = [
        "Critical", "Milestone", "Summary", "Active", "OverAllocated", 
        "EffortDriven", "Recurring", "ExternalTask", "IsPublished"
    ]
    for col in bool_cols:
        if col in df_clean.columns:
            df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce').fillna(0).astype(int)

    # 6. Convert Dates
    date_cols = [
        "CreateDate", "Start", "Finish", "ManualStart", "ManualFinish", 
        "EarlyStart", "EarlyFinish", "LateStart", "LateFinish"
    ]
    for col in date_cols:
        if col in df_clean.columns:
            df_clean[col] = pd.to_datetime(df_clean[col], errors='coerce')

    print("Preprocessing complete.")
    return df_clean