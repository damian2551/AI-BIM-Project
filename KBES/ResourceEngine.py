from experta import Fact, Field, KnowledgeEngine, Rule, MATCH, TEST 

# --- 1. Define the Facts (Working Memory) ---
class ConstructionTask(Fact):
    # ... (Fact Fields remain the same) ...
    uid = Field(str, mandatory=True)
    name = Field(str, mandatory=True)
    duration_hours = Field(float, default=0.0)
    work_hours = Field(float, default=0.0)
    is_critical = Field(bool, default=False)
    has_slack = Field(bool, default=False)
    resources_predicted = Field(bool, default=False) 

class ResourceNeed(Fact):
    # ... (Fact Fields remain the same) ...
    task_uid = Field(str, mandatory=True)
    resource_type = Field(str, mandatory=True) 
    resource_name = Field(str, mandatory=True)
    required_units = Field(float, default=1.0)
    total_hours = Field(float, default=0.0)    

# --- 2. Define the Knowledge Engine (The Inference Engine) ---

class ResourcePredictionEngine(KnowledgeEngine):
    
    def get_rules_placeholder(self):
        return {
            "concrete": {"Labor": 4, "Equipment": ["Concrete Pump", "Vibrator"]},
            "formwork": {"Labor": 2, "Material": ["Plywood", "Lumber"]},
            "steel": {"Labor": 3, "Equipment": ["Crane"]}
        }

    # --- Rule Set 1: Inferring Labor and Equipment based on Task Name ---
    
    @Rule(
        # FIX: Use the '<<' binding syntax, which is the correct pattern for 
        # defining a match variable at the class level in experta.
        current_task << ConstructionTask(
            name=MATCH.task_name,
            duration_hours=MATCH.duration,
            work_hours=MATCH.work, 
            resources_predicted=False
        )
    )
    # The function signature must correctly receive the bound variable
    def rule_assign_base_resources(self, current_task):
        """
        Scans the task name for keywords and applies a base resource formula.
        """
        task_name_lower = current_task['name'].lower() 
        rules = self.get_rules_placeholder()
        
        if current_task['duration_hours'] > 0:
            base_crew_needed = current_task['work_hours'] / current_task['duration_hours'] 
        else:
            base_crew_needed = 0 
        
        matched_keywords = [k for k in rules.keys() if k in task_name_lower]
        
        if matched_keywords:
            rule = rules[matched_keywords[0]]
            
            if "Labor" in rule:
                required_labor = base_crew_needed * rule["Labor"]
                self.declare(ResourceNeed(
                    task_uid=current_task['uid'], 
                    resource_type='Labor',
                    resource_name='Skilled Tradesman', 
                    required_units=required_labor,
                    total_hours=current_task['work_hours']
                ))

            self.modify(current_task, resources_predicted=True)


    # --- Rule Set 2: Applying Risk/Priority Logic (Premium Cost) ---

    @Rule(
        current_task << ConstructionTask( # FIX: Use '<<' syntax
            is_critical=True,
            has_slack=False,
            resources_predicted=True
        )
    )
    def rule_critical_path_premium(self, current_task):
        """
        If a task is critical with no slack, assert a premium cost factor.
        """
        premium_hours = current_task['duration_hours'] * 0.20 
        
        self.declare(ResourceNeed(
            task_uid=current_task['uid'],
            resource_type='Alert',
            resource_name='Critical Path Overtime Factor',
            required_units=1.0, 
            total_hours=premium_hours 
        ))
        
        self.modify(current_task, resources_predicted=False) 

    # --- Rule Set 3: Handling Summary Tasks (Cleanup) ---

    @Rule(
        current_task << ConstructionTask( # FIX: Use '<<' syntax
            name=MATCH.task_name,
            is_critical=False,
            work_hours=0.0
        )
    )
    def rule_ignore_summary_tasks(self, current_task):
        """
        A rule to deliberately ignore tasks that are just headers/summaries.
        """
        print(f"Skipping summary task: {current_task['name']}")
        self.modify(current_task, resources_predicted=True)