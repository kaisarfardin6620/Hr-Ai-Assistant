from Compensation_backend import get_compensation_response
from Compliance_backend import get_compliance_response
from HR_Business_Partner_backend import get_hr_business_partner_response
from HR_Strategy_backend import get_hr_strategy_response
from Learning_And_Development_backend import get_learning_and_development_response
from Organizational_Development_backend import get_organizational_development_response
from Talent_Acquisition_backend import get_talent_acquisition_response
from Total_Rewards_backend import get_total_rewards_response

print('--- Compensation Persona ---')
result = get_compensation_response("What are the latest trends in employee compensation packages?", user_id="user123")
print(result)

print('--- Compliance Persona ---')
result = get_compliance_response("Help me understand compliance of HR?", user_id="user123")
print(result)

print('--- HR Business Partner Persona ---')
result = get_hr_business_partner_response("How does an HR business partner support organizational goals?", user_id="user123")
print(result)

print('--- HR Strategy Persona ---')
result = get_hr_strategy_response("What is the role of HR strategy in business success?", user_id="user123")
print(result)

print('--- Learning & Development Persona ---')
result = get_learning_and_development_response("What are best practices for employee learning and development?", user_id="user123")
print(result)

print('--- Organizational Development Persona ---')
result = get_organizational_development_response("How can organizational development improve company culture?", user_id="user123")
print(result)

print('--- Talent Acquisition Persona ---')
result = get_talent_acquisition_response("What are effective talent acquisition strategies?", user_id="user123")
print(result)

print('--- Total Rewards Persona ---')
result = get_total_rewards_response("Help me understand total rewards in HR.", user_id="user123")
print(result)