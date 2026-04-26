from src.models import ClientProfile
from src.financials import compute_financials

def test_financials_positive(sample_client_dict):
    client = ClientProfile.model_validate(sample_client_dict)
    fs = compute_financials(client)
    assert fs.total_current_annual_run_cost > 0
    assert fs.cumulative_investment_5yr > 0
    assert fs.roi > 0

def test_roi_consistency(sample_client_dict):
    client = ClientProfile.model_validate(sample_client_dict)
    fs = compute_financials(client)
    assert round(fs.roi, 8) == round(fs.cumulative_savings_5yr / fs.cumulative_investment_5yr, 8)
