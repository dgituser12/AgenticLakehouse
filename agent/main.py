# agent/main.py
import os
from agent import create_swiftroute_agent

def main():
    # Set default variables if not provided in environment
    project_id = os.getenv("GCP_PROJECT_ID", "dssetup-202519")
    os.environ["GCP_PROJECT_ID"] = project_id
    
    print("Initializing SwiftRoute Agent on Gemini Platform...")
    agent = create_swiftroute_agent()
    
    # Establish conversational session for testing
    session = agent.create_session()
    
    # Sample Test Query demonstrating temporal auditing
    test_prompt = """
    A customer is disputing their shipping cost for TRX-10. 
    Analyze why the transaction cost differs from what was recorded in the rate card 3 days ago.
    """
    print(f"\n[Test Prompt]: {test_prompt}")
    response = session.send_message(test_prompt)
    print(f"[Agent Response]:\n{response.text}")

if __name__ == "__main__":
    main()
