# agent/main.py (Unified Sequential Demo Driver)
import os
import time
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types  # Import standard GenAI type wrappers
from agent import create_swiftroute_agent

def execute_agent_scenario(runner, session_id, title, prompt):
    """
    Executes a single agent scenario, streams the tool calls, and prints the final output.
    """
    print("\n" + "="*80)
    print(f"🎬 RUNNING SCENARIO: {title}")
    print(f"💬 [USER PROMPT]: {prompt}")
    print("="*80)
    
    # 1. Wrap the prompt into a structured Content object
    user_content = types.Content(
        role="user",
        parts=[types.Part.from_text(text=prompt)]
    )
    
    # 2. Execute the prompt directly and capture the event stream
    events = runner.run(
        session_id=session_id,
        user_id="user_123",
        new_message=user_content
    )
    
    # 3. Iterate through the generator events safely, printing actions in real-time
    print("\n[Processing Agent Event Stream...]")
    for event in events:
        if event.content and event.content.parts:
            for part in event.content.parts:
                # Safe check for tool/function calls
                if hasattr(part, 'function_call') and part.function_call:
                    print(f"\n⚡ [AGENT ACTION]: Calling Tool '{part.function_call.name}'")
                    print(f"   [ARGUMENTS]: {part.function_call.args}")
                
                # Safe check for tool/function responses
                elif hasattr(part, 'function_response') and part.function_response:
                    print(f"\n✨ [TOOL OUTPUT]: {part.function_response.response}")

        # Check if the event is the final text response from the model
        if event.is_final_response() and event.content:
            final_answer = event.content.parts[0].text
            print(f"\n[Agent Response]:\n{final_answer}")

def main():
    # Setup Default Environment Variables for local dry-run testing
    os.environ["LAKEHOUSE_DRY_RUN"] = os.getenv("LAKEHOUSE_DRY_RUN", "true")
    project_id = os.getenv("GCP_PROJECT_ID", "dssetup-202519")
    os.environ["GCP_PROJECT_ID"] = project_id
    
    print(f"Initializing SwiftRoute Agent on Gemini Platform [Dry-Run Mode: {os.environ['LAKEHOUSE_DRY_RUN']}]...")
    agent = create_swiftroute_agent()
    
    # Initialize the Session Service and Runner
    session_service = InMemorySessionService()
    runner = Runner(
        agent=agent,
        app_name="swiftroute_app",
        session_service=session_service,
        auto_create_session=True  # Enables automatic session creation
    )
    
    # Define our three core business scenarios
    scenarios = [
        {
            "id": "session_pillar_1",
            "title": "Pillar 1: Mass Sensor Telemetry Cleansing (Auto-Spark)",
            "prompt": "Normalize the dirty, inconsistent country names across all 100 million sensor tracking rows in our shipments telemetry table. Ensure this is done safely so that we do not corrupt our production table in case of data quality failures."
        },
        {
            "id": "session_pillar_2",
            "title": "Pillar 2: Unstructured Damage Claim Analysis (Auto-SQL Join)",
            "prompt": "We have high-value shipments that were marked as DAMAGED. Locate these specific shipments, find the raw driver claim PDFs stored in our unstructured object bucket, and summarize the complaints."
        },
        {
            "id": "session_pillar_3",
            "title": "Pillar 3: Point-in-Time Billing Auditing (Auto-Time Travel)",
            "prompt": "A merchant is disputing their shipment invoice for TRX-10. Reconstruct what our dynamic shipping rate cards looked like exactly 3 days ago to verify if they were overcharged."
        }
    ]
    
    # Run all three scenarios sequentially
    for idx, scenario in enumerate(scenarios, 1):
        execute_agent_scenario(
            runner=runner,
            session_id=scenario["id"],
            title=scenario["title"],
            prompt=scenario["prompt"]
        )
        
        # Brief pause between scenarios for readability
        if idx < len(scenarios):
            print("\nPausing for 3 seconds before the next demonstration...")
            time.sleep(3)
            
    print("\n" + "="*80)
    print("🏆 DEMONSTRATION SUITE COMPLETED SUCCESSFULLY!")
    print("="*80)

if __name__ == "__main__":
    main()
