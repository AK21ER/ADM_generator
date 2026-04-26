from src.models import ClientProfile

def test_client_model_validation(sample_client_dict):
    c = ClientProfile.model_validate(sample_client_dict)
    assert c.company_name == "Northstar Retail Group"
    assert len(c.application_inventory) >= 25
