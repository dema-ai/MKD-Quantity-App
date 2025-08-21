from app.quantity_engine import run_engine
import sys

print("Starting MKD Quantity App...")
input_path = sys.argv[1] if len(sys.argv) > 1 else None
run_engine(input_path)