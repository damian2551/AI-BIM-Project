# knowledge_base.py

# A dictionary mapping keywords to resource rules
# Format: { 'Keyword': {'Role': 'Carpenter', 'Productivity': 0.5 (hours/unit), 'Unit': 'm2'} }

CONSTRUCTION_RULES = {
    "Excavate": {
        "Resources": [
            {"Name": "Excavator", "Type": "Equipment", "Rate": 1.0}, # 1 machine
            {"Name": "Operator", "Type": "Labor", "Rate": 1.0},      # 1 operator
            {"Name": "Truck", "Type": "Equipment", "Rate": 2.0}      # 2 trucks
        ],
        "Base_Productivity": 20.0 # m3 per hour
    },
    "Formwork": {
        "Resources": [
            {"Name": "Carpenter", "Type": "Labor", "Rate": 2.0},
            {"Name": "Helper", "Type": "Labor", "Rate": 1.0}
        ],
        "Base_Productivity": 5.0 # m2 per hour
    },
    "Pour Concrete": {
        "Resources": [
            {"Name": "Concrete Pump", "Type": "Equipment", "Rate": 1.0},
            {"Name": "Laborer", "Type": "Labor", "Rate": 4.0},
            {"Name": "Vibrator", "Type": "Equipment", "Rate": 2.0}
        ],
        "Base_Productivity": 15.0 # m3 per hour
    }
}