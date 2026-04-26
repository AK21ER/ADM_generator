from typing import Literal
from pydantic import BaseModel, Field, field_validator

ModernizationType = Literal["Retire", "Retain", "Rehost", "Replatform", "Refactor", "Rearchitect"]
Criticality = Literal["High", "Medium", "Low"]
Complexity = Literal["Low", "Medium", "High"]
Sensitivity = Literal["Low", "Medium", "High"]
Hosting = Literal["OnPrem", "Cloud", "Hybrid"]
CenterType = Literal["onshore", "offshore", "nearshore"]

class Competitor(BaseModel):
    name: str
    strengths: list[str]
    weaknesses: list[str]
    gaps_vs_client: list[str]

class DeliveryCenter(BaseModel):
    location_name: str
    country: str
    city: str
    type: CenterType
    avg_cost_multiplier: float = Field(gt=0)

class Application(BaseModel):
    app_name: str
    business_unit_owner: str
    category: str
    criticality: Criticality
    annual_run_cost: float = Field(gt=0)
    age_years: int = Field(ge=0)
    hosting: Hosting
    tech_stack: list[str]
    integration_complexity: Complexity
    data_sensitivity: Sensitivity
    modernization_recommendation: ModernizationType

class TransformationTargets(BaseModel):
    cloud_migration_target_percent: float
    legacy_cost_reduction_target_percent: float
    ai_enablement_target_percent: float
    security_compliance_targets: list[str]

    @field_validator("cloud_migration_target_percent", "legacy_cost_reduction_target_percent", "ai_enablement_target_percent")
    @classmethod
    def validate_percent(cls, v: float) -> float:
        if not 0 <= v <= 100:
            raise ValueError("percentage must be between 0 and 100")
        return v

class ClientProfile(BaseModel):
    company_name: str
    industry: str
    headquarters: str
    regions_operating: list[str]
    annual_revenue: float = Field(gt=0)
    employees: int = Field(gt=0)
    business_overview: str
    strategic_priorities: list[str]
    annual_adm_spend: float = Field(gt=0)
    competitors: list[Competitor]
    delivery_centers_preferred: list[DeliveryCenter]
    application_inventory: list[Application]
    transformation_targets: TransformationTargets
    known_pain_points: list[str]
    known_risks: list[str]

class FinancialSummary(BaseModel):
    total_current_annual_run_cost: float
    baseline_5_year_run_cost: float
    investment_by_year: dict[str, float]
    savings_by_year: dict[str, float]
    offshore_arbitrage_savings_by_year: dict[str, float]
    cumulative_savings_5yr: float
    cumulative_investment_5yr: float
    total_contract_value_5yr: float
    roi: float
    npv: float
    payback_period_year: int | None
    legacy_cost_reduction_curve_by_year: dict[str, float]
